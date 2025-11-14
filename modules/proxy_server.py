# -*- coding: utf-8 -*-
"""
代理服务器模块
将 trae_proxy.py 的功能模块化，支持在线程中运行并可优雅停止
"""

import threading
import time
import ssl
import os
import logging
import yaml
from werkzeug.serving import WSGIRequestHandler, BaseWSGIServer
from flask import Flask, request, jsonify, Response
import requests
from .resource_manager import ResourceManager


class StoppableWSGIServer(BaseWSGIServer):
    """可停止的 WSGI 服务器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
    
    def server_close(self):
        """关闭服务器"""
        self._stop_event.set()
        super().server_close()
    
    def serve_forever(self, poll_interval=0.5):
        """运行服务器直到停止"""
        while not self._stop_event.is_set():
            try:
                self.handle_request()
            except OSError:
                # 服务器已关闭
                break


class ProxyServer:
    """代理服务器类，支持在线程中运行并可优雅停止"""
    
    def __init__(self, config=None, log_func=print):
        """
        初始化代理服务器
        
        参数:
            config: 配置字典，包含 api_url、model_id、target_model_id、stream_mode
            log_func: 日志输出函数
        """
        self.config = config or {}
        self.log_func = log_func
        self.resource_manager = ResourceManager()
        self.app = None
        self.server = None
        self.server_thread = None
        self.running = False
        
        # 从配置中获取参数
        self.target_api_base_url = self.config.get('api_url', 'YOUR_REVERSE_ENGINEERED_API_ENDPOINT_BASE_URL')
        self.custom_model_id = self.config.get('model_id', 'CUSTOM_MODEL_ID')
        # 如果 target_model_id 为空或未设置，使用 custom_model_id
        target_model_id = self.config.get('target_model_id', '').strip()
        self.target_model_id = target_model_id if target_model_id else self.custom_model_id
        self.stream_mode = self.config.get('stream_mode')  # None, 'true', 'false'
        self.debug_mode = self.config.get('debug_mode', False)
        
        # 加载全局配置（用于模型映射和鉴权）
        self.global_config = self._load_global_config()
        
        # 验证配置
        if self.target_api_base_url == 'YOUR_REVERSE_ENGINEERED_API_ENDPOINT_BASE_URL':
            self.log_func("错误: 请在配置中设置正确的 API URL")
            return
        
        # 创建 Flask 应用
        self._create_app()
    
    def _load_global_config(self):
        """加载全局配置文件"""
        try:
            config_file = self.resource_manager.get_user_config_file()
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            self.log_func(f"加载全局配置失败: {e}")
        return {}
    
    def _get_mapped_model_id(self):
        """获取映射的模型ID，用于 /v1/models 接口返回"""
        return self.global_config.get('mapped_model_id', self.custom_model_id)
    
    def _verify_auth(self, auth_header):
        """验证鉴权header"""
        if not auth_header:
            return False
        
        # 获取配置的MTGA鉴权key
        mtga_auth_key = self.global_config.get('mtga_auth_key', '')
        if not mtga_auth_key:
            # 如果没有配置鉴权key，则跳过验证
            return True
        
        # 解析Authorization header (格式: "Bearer key" 或 "key")
        if auth_header.startswith('Bearer '):
            provided_key = auth_header[7:]  # 移除 "Bearer " 前缀
        else:
            provided_key = auth_header
        
        return provided_key == mtga_auth_key
    
    def _create_app(self):
        """创建 Flask 应用并配置路由"""
        self.app = Flask(__name__)
        
        # 设置日志级别
        if self.debug_mode:
            logging.getLogger().setLevel(logging.INFO)
            self.app.logger.setLevel(logging.INFO)
        
        # 配置路由
        self.app.add_url_rule('/v1/models', 'get_models', self._get_models, methods=['GET'])
        self.app.add_url_rule('/v1/chat/completions', 'chat_completions', 
                             self._chat_completions, methods=['POST'])
    
    def _get_models(self):
        """处理模型列表请求，支持映射模型ID和鉴权验证"""
        self.log_func("收到模型列表请求 /v1/models")
        
        # 验证鉴权
        auth_header = request.headers.get('Authorization')
        if not self._verify_auth(auth_header):
            self.log_func("模型列表请求鉴权失败")
            return jsonify({
                "error": {
                    "message": "Invalid authentication",
                    "type": "authentication_error"
                }
            }), 401
        
        # 获取映射的模型ID
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
                            "is_blocking": False
                        }
                    ]
                }
            ]
        }
        
        self.log_func(f"返回映射模型: {mapped_model_id}")
        return jsonify(model_data)
    
    def _chat_completions(self):
        """处理聊天补全请求"""
        self.log_func("收到聊天补全请求 /v1/chat/completions")
        
        if self.debug_mode:
            # 调试模式下记录请求头和请求体
            headers_str = "\\n".join(f"{k}: {v}" for k, v in request.headers.items())
            log_message = f"--- 请求头 (调试模式) ---\\n{headers_str}\\n--------------------------------------"
            try:
                body_str = request.get_data(as_text=True)
                log_message += f"--- 请求体 (调试模式) ---\\n{body_str}\\n--------------------------------------"
            except Exception as body_exc:
                error_msg = f"读取请求体数据时出错: {body_exc}\\n"
                self.log_func(error_msg)
                log_message += error_msg
            self.log_func(log_message)
        
        # 尝试获取 JSON 数据
        request_data = request.get_json(silent=True)
        
        if request_data is None:
            self.log_func("解析 JSON 失败或请求不是 JSON 格式")
            self.log_func(f"Content-Type: {request.headers.get('Content-Type')}")
            return jsonify({
                "error": "Invalid JSON or Content-Type",
                "message": "The request body must be valid JSON and the Content-Type header must be 'application/json'."
            }), 400
        
        # 记录客户端请求的流模式设置
        client_requested_stream = request_data.get('stream', False)
        self.log_func(f"客户端请求的流模式: {client_requested_stream}")
        
        # 替换请求体中的模型名
        if 'model' in request_data:
            original_model = request_data['model']
            self.log_func(f"替换模型名: {original_model} -> {self.target_model_id}")
            request_data['model'] = self.target_model_id
        else:
            self.log_func(f"请求中没有 model 字段，添加 model: {self.target_model_id}")
            request_data['model'] = self.target_model_id
        
        # 强制修改流模式
        if self.stream_mode is not None:
            stream_value = True if self.stream_mode == 'true' else False
            if 'stream' in request_data:
                original_stream_value = request_data['stream']
                self.log_func(f"强制修改流模式: {original_stream_value} -> {stream_value}")
                request_data['stream'] = stream_value
            else:
                self.log_func(f"请求中没有 stream 参数，设置为 {stream_value}")
                request_data['stream'] = stream_value
        
        # 准备转发的请求头
        # 验证MTGA鉴权（用于访问代理服务）
        auth_header = request.headers.get('Authorization')
        if not self._verify_auth(auth_header):
            self.log_func("聊天补全请求MTGA鉴权失败")
            return jsonify({
                "error": {
                    "message": "Invalid authentication",
                    "type": "authentication_error"
                }
            }), 401
        
        # 使用配置组中的 API key（如果有的话）
        target_api_key = self.config.get('api_key', '')
        forward_headers = {'Content-Type': 'application/json'}
        if target_api_key:
            # 使用配置组中的API key
            forward_headers['Authorization'] = f'Bearer {target_api_key}'
            self.log_func("使用配置组中的API key")
        elif auth_header:
            # 如果配置组没有API key，则透传原始的Authorization header
            forward_headers['Authorization'] = auth_header
            self.log_func("透传原始Authorization header")
        
        try:
            target_url = f"{self.target_api_base_url.rstrip('/')}/v1/chat/completions"
            self.log_func(f"转发请求到: {target_url}")
            
            # 从解析后的 request_data 中获取 stream 参数
            is_stream = request_data.get('stream', False)
            self.log_func(f"流模式: {is_stream}")
            
            response_from_target = requests.post(
                target_url,
                json=request_data,
                headers=forward_headers,
                stream=is_stream,
                timeout=300
            )
            response_from_target.raise_for_status()
            
            if is_stream:
                self.log_func("返回流式响应")
                def generate_stream():
                    for chunk in response_from_target.iter_content(chunk_size=None):
                        yield chunk
                
                return Response(generate_stream(), 
                              content_type=response_from_target.headers.get('content-type', 'text/event-stream'))
            else:
                # 获取完整的非流式响应
                response_json = response_from_target.json()
                
                # 如果客户端请求了流式响应但我们强制使用了非流式请求，则将完整响应转换为流式格式
                if client_requested_stream and self.stream_mode == 'false':
                    self.log_func("将非流式响应转换为流式格式返回给客户端")
                    
                    def simulate_stream():
                        import json
                        
                        # 提取响应中的内容
                        choices = response_json.get('choices', [])
                        if not choices:
                            self.log_func("响应中没有找到 choices 字段")
                            yield f"data: {json.dumps({'error': 'No choices in response'})}\\n\\n"
                            return
                        
                        # 获取第一个 choice 的内容
                        first_choice = choices[0]
                        message = first_choice.get('message', {})
                        content = message.get('content', '')
                        
                        if not content:
                            self.log_func("响应中没有找到内容")
                            yield f"data: {json.dumps({'error': 'No content in response'})}\\n\\n"
                            return
                        
                        # 获取模型信息和其他元数据
                        model = response_json.get('model', '')
                        id = response_json.get('id', '')
                        created = response_json.get('created', 0)
                        
                        # 分割内容并模拟流式输出
                        chunk_size = 10
                        total_chars = len(content)
                        
                        for i in range(0, total_chars, chunk_size):
                            chunk = content[i:i+chunk_size]
                            
                            # 构建符合 OpenAI 流式格式的响应块
                            chunk_data = {
                                "id": id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "content": chunk
                                        },
                                        "finish_reason": None if i + chunk_size < total_chars else first_choice.get('finish_reason', 'stop')
                                    }
                                ]
                            }
                            
                            yield f"data: {json.dumps(chunk_data)}\\n\\n"
                            time.sleep(0.01)
                        
                        yield "data: [DONE]\\n\\n"
                    
                    return Response(simulate_stream(), content_type='text/event-stream')
                else:
                    # 正常返回非流式响应
                    if self.debug_mode:
                        import json
                        response_str = json.dumps(response_json, indent=2, ensure_ascii=False)
                        self.log_func(f"--- 完整响应体 (调试模式) ---\\n{response_str}\\n--------------------------------------")
                    else:
                        self.log_func("返回非流式 JSON 响应")
                    return jsonify(response_json), response_from_target.status_code
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"目标 API HTTP 错误: {e.response.status_code} - {e.response.text}"
            self.log_func(error_msg)
            return jsonify({"error": f"Target API error: {e.response.status_code}", 
                           "details": e.response.text}), e.response.status_code
        except requests.exceptions.RequestException as e:
            error_msg = f"连接目标 API 时出错: {e}"
            self.log_func(error_msg)
            return jsonify({"error": f"Error contacting target API: {str(e)}"}), 503
        except Exception as e:
            error_msg = f"发生意外错误: {e}"
            self.log_func(error_msg)
            return jsonify({"error": "An internal server error occurred"}), 500
    
    def start(self, host='0.0.0.0', port=443):
        """
        启动代理服务器
        
        参数:
            host: 监听主机地址
            port: 监听端口
            
        返回:
            成功返回 True，失败返回 False
        """
        if self.running:
            self.log_func("代理服务器已在运行")
            return True
        
        if not self.app:
            self.log_func("Flask 应用未初始化")
            return False
        
        # 检查证书文件
        cert_file = self.resource_manager.get_cert_file()
        key_file = self.resource_manager.get_key_file()
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            self.log_func(f"证书文件不存在: {cert_file} 或 {key_file}")
            return False
        
        try:
            # 创建 SSL 上下文
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_file, key_file)
            
            self.log_func(f"启动代理服务器，监听 https://{host}:{port}")
            self.log_func(f"目标 API 地址: {self.target_api_base_url}")
            self.log_func(f"自定义模型 ID: {self.custom_model_id}")
            self.log_func(f"实际模型 ID: {self.target_model_id}")
            if self.stream_mode:
                self.log_func(f"强制流模式: {self.stream_mode}")
            
            # 创建可停止的服务器
            try:
                self.server = StoppableWSGIServer(host, port, self.app, 
                                                ssl_context=ssl_context)
                # 设置请求处理器
                self.server.RequestHandlerClass = WSGIRequestHandler
                self.log_func("服务器实例创建成功")
            except Exception as e:
                self.log_func(f"创建服务器实例失败: {e}")
                return False
            
            def run_server():
                try:
                    if self.server:
                        self.server.serve_forever()
                    else:
                        self.log_func("服务器实例为空，无法启动")
                except Exception as e:
                    self.log_func(f"服务器运行出错: {e}")
                finally:
                    self.running = False
                    self.log_func("服务器线程已退出")
            
            # 在线程中启动服务器
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.running = True
            
            # 等待一小段时间确保服务器启动
            time.sleep(1)
            
            if self.running:
                self.log_func("代理服务器已成功启动")
                return True
            else:
                self.log_func("代理服务器启动失败")
                return False
                
        except PermissionError:
            self.log_func(f"权限不足，无法监听 {port} 端口。请以管理员身份运行。")
            return False
        except OSError as e:
            if "address already in use" in str(e).lower():
                self.log_func(f"端口 {port} 已被占用。请检查是否有其他服务占用了该端口。")
            else:
                self.log_func(f"启动服务器时发生 OS 错误: {e}")
            return False
        except Exception as e:
            self.log_func(f"启动代理服务器时发生意外错误: {e}")
            return False
    
    def stop(self):
        """停止代理服务器"""
        if not self.running:
            self.log_func("代理服务器未运行")
            return
        
        self.log_func("正在停止代理服务器...")
        self.running = False
        
        # 停止服务器
        if self.server:
            try:
                self.server.server_close()
                self.log_func("服务器已停止")
            except Exception as e:
                self.log_func(f"停止服务器时出错: {e}")
        
        # 等待线程结束
        if self.server_thread and self.server_thread.is_alive():
            try:
                self.server_thread.join(timeout=5)  # 最多等待5秒
                if self.server_thread.is_alive():
                    self.log_func("服务器线程未能在5秒内停止")
                else:
                    self.log_func("服务器线程已安全停止")
            except Exception as e:
                self.log_func(f"等待线程结束时出错: {e}")
        
        # 清理资源
        self.server = None
        self.server_thread = None
        self.log_func("代理服务器已完全停止")
    
    def is_running(self):
        """检查代理服务器是否正在运行"""
        return self.running and self.server_thread and self.server_thread.is_alive()


def start_proxy_server(config, log_func=print):
    """
    启动代理服务器的便捷函数
    
    参数:
        config: 配置字典
        log_func: 日志输出函数
        
    返回:
        ProxyServer 实例，失败返回 None
    """
    proxy = ProxyServer(config, log_func)
    if proxy.start():
        return proxy
    return None
