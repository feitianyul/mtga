from __future__ import annotations

import contextlib
import json
import logging
import os
import ssl
import time
import uuid
from collections.abc import Generator

import requests
import yaml
from flask import Flask, Response, jsonify, request
from requests.adapters import HTTPAdapter

from modules.runtime.resource_manager import ResourceManager, is_packaged


class SSLContextAdapter(HTTPAdapter):
    """支持自定义 SSLContext 的适配器，用于调整验证策略。"""

    def __init__(self, ssl_context, *args, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs.setdefault("ssl_context", self.ssl_context)
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs.setdefault("ssl_context", self.ssl_context)
        return super().proxy_manager_for(proxy, **proxy_kwargs)


class ProxyApp:
    """代理服务的领域逻辑：配置解析 + Flask 路由 + 上游转发。"""

    def __init__(self, config=None, log_func=print, *, resource_manager: ResourceManager):
        self.config = config or {}
        self.log_func = log_func
        self.resource_manager = resource_manager
        self.app: Flask | None = None
        self.valid = True

        self.global_config = self._load_global_config()
        self.target_api_base_url = self.config.get(
            "api_url", "YOUR_REVERSE_ENGINEERED_API_ENDPOINT_BASE_URL"
        )
        global_mapped_model_id = (self.global_config.get("mapped_model_id") or "").strip()
        legacy_group_mapped_model_id = (self.config.get("mapped_model_id") or "").strip()
        self.custom_model_id = (
            global_mapped_model_id or legacy_group_mapped_model_id or "CUSTOM_MODEL_ID"
        )

        target_model_id = self.config.get("model_id", "").strip()
        self.target_model_id = target_model_id if target_model_id else self.custom_model_id
        self.stream_mode = self.config.get("stream_mode")  # None, 'true', 'false'
        self.debug_mode = self.config.get("debug_mode", False)
        self.disable_ssl_strict_mode = self.config.get("disable_ssl_strict_mode", False)
        self.http_client = self._create_http_client()

        if self.target_api_base_url == "YOUR_REVERSE_ENGINEERED_API_ENDPOINT_BASE_URL":
            self.log_func("错误: 请在配置中设置正确的 API URL")
            self.valid = False
            return

        self._create_app()

    def close(self) -> None:
        if self.http_client:
            with contextlib.suppress(Exception):
                self.http_client.close()

    def _load_global_config(self):
        try:
            config_file = self.resource_manager.get_user_config_file()
            if os.path.exists(config_file):
                with open(config_file, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
        except Exception as exc:
            self.log_func(f"加载全局配置失败: {exc}")
        return {}

    def _create_http_client(self):
        session = requests.Session()
        if self.disable_ssl_strict_mode:
            try:
                ctx = ssl.create_default_context()
                ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
                adapter = SSLContextAdapter(ctx)
                session.mount("https://", adapter)
                self.log_func("关闭 SSL 严格模式: 使用自定义 HTTPS 上下文")
            except Exception as exc:  # noqa: BLE001
                self.log_func(f"配置非严格 SSL 上下文失败，继续使用默认设置: {exc}")
        return session

    @staticmethod
    def _new_request_id() -> str:
        return uuid.uuid4().hex[:6]

    @staticmethod
    def _timestamp_ms() -> str:
        now = time.time()
        base = time.strftime("%H:%M:%S", time.localtime(now))
        ms = int((now % 1) * 1000)
        return f"{base}.{ms:03d}"

    def _log_request(self, request_id: str, message: str):
        self.log_func(f"{self._timestamp_ms()} [{request_id}] {message}")

    def _prepare_sse_log_path(self) -> str:
        base_dir = (
            self.resource_manager.user_data_dir
            if is_packaged()
            else self.resource_manager.program_resource_dir
        )
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"sse_{timestamp}_{int(time.time() * 1000)}.log"
        return os.path.join(log_dir, filename)

    def _extract_sse_events(
        self, response, *, log_file=None, log
    ) -> Generator[tuple[int, bytes]]:
        buffer = b""
        chunk_index = 0
        for chunk in response.iter_content(chunk_size=None):
            chunk_index += 1
            if log_file:
                try:
                    log_file.write(chunk)
                    log_file.flush()
                except Exception as write_exc:  # noqa: BLE001
                    log(f"SSE 日志写入失败，停止记录: {write_exc}")
                    with contextlib.suppress(Exception):
                        log_file.close()
                    log_file = None
            buffer += chunk
            while True:
                sep = buffer.find(b"\n\n")
                if sep == -1:
                    break
                event = buffer[:sep]
                buffer = buffer[sep + 2 :]
                yield chunk_index, event
        if buffer.strip():
            log("警告: 上游 SSE 结束时存在未完整分隔的残留数据")
            yield chunk_index, buffer

    def _normalize_openai_event(
        self, data_str: str, event_index: int, *, model_name: str, log
    ) -> tuple[bytes, str | None]:
        try:
            payload = json.loads(data_str)
        except Exception as exc:  # noqa: BLE001
            log(f"chunk#{event_index} JSON 解析失败，原样透传: {exc}")
            return f"data: {data_str}\n\n".encode(), None

        choices = payload.get("choices") or []
        choice0 = choices[0] if choices else {}
        raw_delta = choice0.get("delta") or {}
        message = choice0.get("message") or {}

        delta: dict[str, object] = {}
        role = raw_delta.get("role") or message.get("role")
        if role or event_index == 1:
            delta["role"] = role or "assistant"

        content = raw_delta.get("content") or message.get("content")
        if content:
            delta["content"] = content

        for key in ("tool_calls", "function_calls", "reasoning_content"):
            value = raw_delta.get(key)
            if value not in (None, []):
                delta[key] = value

        finish_reason = choice0.get("finish_reason")
        normalized_finish = finish_reason if finish_reason not in (None, "") else None

        chunk_obj = {
            "id": payload.get("id") or self._new_request_id(),
            "object": "chat.completion.chunk",
            "created": int(payload.get("created") or time.time()),
            "model": payload.get("model") or model_name,
            "choices": [
                {
                    "index": choice0.get("index", 0),
                    "delta": delta,
                    "logprobs": None,
                    "finish_reason": normalized_finish,
                }
            ],
        }
        chunk_json = json.dumps(chunk_obj, ensure_ascii=False)
        return f"data: {chunk_json}\n\n".encode(), normalized_finish

    def _get_mapped_model_id(self):
        return self.custom_model_id

    def _verify_auth(self, auth_header):
        if not auth_header:
            return False

        mtga_auth_key = self.global_config.get("mtga_auth_key", "")
        if not mtga_auth_key:
            return True

        provided_key = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
        return provided_key == mtga_auth_key

    def _create_app(self):
        self.app = Flask(__name__)

        if self.debug_mode:
            logging.getLogger().setLevel(logging.INFO)
            self.app.logger.setLevel(logging.INFO)

        self.app.add_url_rule("/v1/models", "get_models", self._get_models, methods=["GET"])
        self.app.add_url_rule(
            "/v1/chat/completions", "chat_completions", self._chat_completions, methods=["POST"]
        )

    def _get_models(self):
        self.log_func("收到模型列表请求 /v1/models")

        auth_header = request.headers.get("Authorization")
        if not self._verify_auth(auth_header):
            self.log_func("模型列表请求鉴权失败")
            return jsonify(
                {"error": {"message": "Invalid authentication", "type": "authentication_error"}}
            ), 401

        mapped_model_id = self._get_mapped_model_id()

        model_data = {
            "object": "list",
            "data": [
                {
                    "id": mapped_model_id,
                    "object": "model",
                    "owned_by": "openai",
                    "created": int(time.time()),
                    "permission": [
                        {
                            "id": f"modelperm-{mapped_model_id}",
                            "object": "model_permission",
                            "created": int(time.time()),
                            "allow_create_engine": False,
                            "allow_sampling": True,
                            "allow_logprobs": True,
                            "allow_search_indices": False,
                            "allow_view": True,
                            "allow_fine_tuning": False,
                            "organization": "*",
                            "group": None,
                            "is_blocking": False,
                        }
                    ],
                }
            ],
        }

        self.log_func(f"返回映射模型: {mapped_model_id}")
        return jsonify(model_data)

    def _chat_completions(self):  # noqa: PLR0911, PLR0912, PLR0915
        request_id = self._new_request_id()

        def log(message: str):
            self._log_request(request_id, message)

        log("收到聊天补全请求 /v1/chat/completions")

        if self.debug_mode:
            headers_str = "\\n".join(f"{k}: {v}" for k, v in request.headers.items())
            log_message = (
                f"--- 请求头 (调试模式) ---\\n{headers_str}\\n"
                "--------------------------------------"
            )
            try:
                body_str = request.get_data(as_text=True)
                log_message += (
                    f"--- 请求体 (调试模式) ---\\n{body_str}\\n"
                    "--------------------------------------"
                )
            except Exception as body_exc:
                error_msg = f"读取请求体数据时出错: {body_exc}\\n"
                log(error_msg)
                log_message += error_msg
            log(log_message)

        request_data = request.get_json(silent=True)

        if request_data is None:
            log("解析 JSON 失败或请求不是 JSON 格式")
            log(f"Content-Type: {request.headers.get('Content-Type')}")
            return jsonify(
                {
                    "error": "Invalid JSON or Content-Type",
                    "message": (
                        "The request body must be valid JSON and the Content-Type header "
                        "must be 'application/json'."
                    ),
                }
            ), 400

        client_requested_stream = request_data.get("stream", False)
        log(f"客户端请求的流模式: {client_requested_stream}")

        if "model" in request_data:
            original_model = request_data["model"]
            log(f"替换模型名: {original_model} -> {self.target_model_id}")
            request_data["model"] = self.target_model_id
        else:
            log(f"请求中没有 model 字段，添加 model: {self.target_model_id}")
            request_data["model"] = self.target_model_id

        if self.stream_mode is not None:
            stream_value = self.stream_mode == "true"
            if "stream" in request_data:
                original_stream_value = request_data["stream"]
                log(f"强制修改流模式: {original_stream_value} -> {stream_value}")
                request_data["stream"] = stream_value
            else:
                log(f"请求中没有 stream 参数，设置为 {stream_value}")
                request_data["stream"] = stream_value

        auth_header = request.headers.get("Authorization")
        if not self._verify_auth(auth_header):
            log("聊天补全请求MTGA鉴权失败")
            return jsonify(
                {"error": {"message": "Invalid authentication", "type": "authentication_error"}}
            ), 401

        target_api_key = self.config.get("api_key", "")
        forward_headers = {"Content-Type": "application/json"}
        if target_api_key:
            forward_headers["Authorization"] = f"Bearer {target_api_key}"
            log("使用配置组中的API key")
        elif auth_header:
            forward_headers["Authorization"] = auth_header
            log("透传原始Authorization header")

        try:
            target_url = f"{self.target_api_base_url.rstrip('/')}/v1/chat/completions"
            log(f"转发请求到: {target_url}")

            is_stream = request_data.get("stream", False)
            log(f"流模式: {is_stream}")

            response_from_target = self.http_client.post(
                target_url,
                json=request_data,
                headers=forward_headers,
                stream=is_stream,
                timeout=300,
            )
            response_from_target.raise_for_status()
            if self.debug_mode:
                log(f"上游响应状态码: {response_from_target.status_code}")
                log(f"上游 Content-Type: {response_from_target.headers.get('content-type')}")

            if is_stream:
                log("返回流式响应")

                log_file = None
                log_file_stack = None
                log_path = None
                if self.debug_mode:
                    try:
                        log_path = self._prepare_sse_log_path()
                        log_file_stack = contextlib.ExitStack()
                        log_file = log_file_stack.enter_context(open(log_path, "wb"))  # noqa: SIM115
                        log(f"SSE 原始数据将记录到: {log_path}")
                    except Exception as log_exc:  # noqa: BLE001
                        log(f"SSE 日志文件创建失败: {log_exc}")

                def generate_stream():  # noqa: PLR0915, PLR0912
                    nonlocal log_file, log_file_stack
                    event_index = 0
                    done_sent = False
                    finish_reason_seen = None
                    try:
                        for upstream_chunk_index, raw_event in self._extract_sse_events(
                            response_from_target, log_file=log_file, log=log
                        ):
                            event_index += 1
                            event_text = raw_event.decode("utf-8", errors="replace")
                            data_lines = [
                                line[len("data:") :].lstrip()
                                for line in event_text.splitlines()
                                if line.startswith("data:")
                            ]
                            if not data_lines:
                                log(f"evt#{event_index} 跳过无 data 行的事件: {event_text!r}")
                                continue
                            data_str = "\n".join(data_lines)

                            if self.debug_mode:
                                log(
                                    f"UP<< evt#{event_index} src_chunk#{upstream_chunk_index} "
                                    f"bytes={len(raw_event)} | {data_str.strip()}"
                                )

                            if data_str.strip() == "[DONE]":
                                done_sent = True
                                done_bytes = b"data: [DONE]\n\n"
                                try:
                                    yield done_bytes
                                except GeneratorExit:
                                    log(
                                        f"DOWN 连接提前中断，已读取上游 evt#{event_index} (DONE)"
                                    )
                                    raise
                                except Exception as downstream_exc:  # noqa: BLE001
                                    log(f"DOWN 写入异常 (DONE)，停止向下游发送: {downstream_exc}")
                                    break
                                log("已转发 [DONE]")
                                break

                            normalized_bytes, finish_reason = self._normalize_openai_event(
                                data_str,
                                event_index,
                                model_name=self.target_model_id,
                                log=log,
                            )
                            if finish_reason:
                                finish_reason_seen = finish_reason
                            try:
                                yield normalized_bytes
                            except GeneratorExit:
                                log(
                                    f"DOWN 连接提前中断，已读取上游 evt#{event_index} "
                                    f"finish={finish_reason_seen}"
                                )
                                raise
                            except Exception as downstream_exc:  # noqa: BLE001
                                log(f"DOWN 写入异常，停止向下游发送: {downstream_exc}")
                                break
                        if not done_sent:
                            tail_bytes = b"data: [DONE]\n\n"
                            with contextlib.suppress(Exception):
                                yield tail_bytes
                            if self.debug_mode:
                                extra = (
                                    f"，finish_reason={finish_reason_seen}"
                                    if finish_reason_seen
                                    else ""
                                )
                                log(f"未收到上游 [DONE]，已补发终止事件{extra}")
                    finally:
                        if log_file_stack:
                            with contextlib.suppress(Exception):
                                log_file_stack.close()
                        if log_path:
                            log(f"SSE 记录完成: {log_path}")
                        with contextlib.suppress(Exception):
                            response_from_target.close()
                        if self.debug_mode:
                            log(f"UP 流结束，累计 {event_index} 个事件")

                downstream_content_type = response_from_target.headers.get(
                    "content-type", "text/event-stream"
                )
                if self.debug_mode:
                    log(f"下游响应 Content-Type: {downstream_content_type}")

                return Response(
                    generate_stream(),
                    content_type=downstream_content_type,
                )

            response_json = response_from_target.json()

            if client_requested_stream and self.stream_mode == "false":
                log("将非流式响应转换为流式格式返回给客户端")

                def simulate_stream():
                    choices = response_json.get("choices", [])
                    if not choices:
                        log("响应中没有找到 choices 字段")
                        yield f"data: {json.dumps({'error': 'No choices in response'})}\\n\\n"
                        return

                    first_choice = choices[0]
                    message = first_choice.get("message", {})
                    content = message.get("content", "")

                    if not content:
                        log("响应中没有找到内容")
                        yield f"data: {json.dumps({'error': 'No content in response'})}\\n\\n"
                        return

                    model = response_json.get("model", "")
                    id_value = response_json.get("id", "")
                    created = response_json.get("created", 0)

                    chunk_size = 10
                    total_chars = len(content)

                    for i in range(0, total_chars, chunk_size):
                        chunk = content[i : i + chunk_size]

                        chunk_data = {
                            "id": id_value,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": chunk},
                                    "finish_reason": None
                                    if i + chunk_size < total_chars
                                    else first_choice.get("finish_reason", "stop"),
                                }
                            ],
                        }

                        yield f"data: {json.dumps(chunk_data)}\\n\\n"
                        time.sleep(0.01)

                    yield "data: [DONE]\\n\\n"

                return Response(simulate_stream(), content_type="text/event-stream")

            if self.debug_mode:
                response_str = json.dumps(response_json, indent=2, ensure_ascii=False)
                log(
                    f"--- 完整响应体 (调试模式) ---\\n{response_str}\\n"
                    "--------------------------------------"
                )
            else:
                log("返回非流式 JSON 响应")
            return jsonify(response_json), response_from_target.status_code

        except requests.exceptions.HTTPError as e:
            error_msg = f"目标 API HTTP 错误: {e.response.status_code} - {e.response.text}"
            log(error_msg)
            return jsonify(
                {"error": f"Target API error: {e.response.status_code}", "details": e.response.text}
            ), e.response.status_code
        except requests.exceptions.RequestException as e:
            error_msg = f"连接目标 API 时出错: {e}"
            log(error_msg)
            return jsonify({"error": f"Error contacting target API: {str(e)}"}), 503
        except Exception as e:
            error_msg = f"发生意外错误: {e}"
            log(error_msg)
            return jsonify({"error": "An internal server error occurred"}), 500


__all__ = ["ProxyApp"]
