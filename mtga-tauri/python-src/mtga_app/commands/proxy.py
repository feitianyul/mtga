from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel
from pytauri import Commands

from modules.network.network_environment import check_network_environment
from modules.runtime.log_bus import push_log as default_push_log
from modules.runtime.operation_result import OperationResult
from modules.runtime.resource_manager import ResourceManager
from modules.runtime.thread_manager import ThreadManager
from modules.services import proxy_orchestration
from modules.services.app_metadata import DEFAULT_METADATA
from modules.services.cert_service import (
    generate_certificates_result,
    has_existing_ca_cert,
    install_ca_cert_result,
)
from modules.services.config_service import ConfigStore
from modules.services.hosts_service import modify_hosts_file_result

from .common import build_result_payload, collect_logs


class ProxyStartPayload(BaseModel):
    debug_mode: bool = False
    disable_ssl_strict_mode: bool = False
    force_stream: bool = False
    stream_mode: str | None = None


@dataclass
class ProxyRuntimeState:
    thread_manager: ThreadManager
    proxy_instance: Any | None = None


@lru_cache(maxsize=1)
def _get_resource_manager() -> ResourceManager:
    return ResourceManager()


@lru_cache(maxsize=1)
def _get_config_store() -> ConfigStore:
    resource_manager = _get_resource_manager()
    return ConfigStore(resource_manager.get_user_config_file())


@lru_cache(maxsize=1)
def _get_proxy_state() -> ProxyRuntimeState:
    return ProxyRuntimeState(thread_manager=ThreadManager())


def _set_proxy_instance(instance: Any | None) -> None:
    state = _get_proxy_state()
    state.proxy_instance = instance


def _get_proxy_instance() -> Any | None:
    return _get_proxy_state().proxy_instance


def stop_proxy_for_shutdown(*, log_func=None) -> OperationResult:
    if log_func is None:
        log_func = default_push_log
    def _log(message: str) -> None:
        with suppress(Exception):
            log_func(message)

    _log("收到退出信号，准备停止代理服务器...")
    result = proxy_orchestration.stop_proxy_instance_result(
        get_proxy_instance=_get_proxy_instance,
        set_proxy_instance=_set_proxy_instance,
        log=_log,
        reason="shutdown",
        show_idle_message=True,
    )
    hosts_result = modify_hosts_file_result(action="remove", log_func=_log)
    if not hosts_result.ok:
        _log(f"⚠️ {hosts_result.message or 'hosts 条目清理失败'}")
    return result


def _stop_proxy_instance_result(
    *,
    log_func,
    reason: str = "stop",
    show_idle_message: bool = False,
) -> OperationResult:
    return proxy_orchestration.stop_proxy_instance_result(
        get_proxy_instance=_get_proxy_instance,
        set_proxy_instance=_set_proxy_instance,
        log=log_func,
        reason=reason,
        show_idle_message=show_idle_message,
    )


def _start_proxy_instance_result(
    config: dict[str, Any],
    *,
    log_func,
    success_message: str = "✅ 代理服务器启动成功",
    hosts_modified: bool = False,
) -> OperationResult:
    state = _get_proxy_state()
    return proxy_orchestration.start_proxy_instance_result(
        config=config,
        deps=proxy_orchestration.StartProxyDeps(
            log=log_func,
            thread_manager=state.thread_manager,
            check_network_environment=check_network_environment,
            set_proxy_instance=_set_proxy_instance,
            modify_hosts_file=_modify_hosts_file,
            network_env_precheck_enabled=False,
        ),
        success_message=success_message,
        hosts_modified=hosts_modified,
    )


def _restart_proxy_result(
    *,
    config: dict[str, Any],
    log_func,
    success_message: str = "✅ 代理服务器启动成功",
    hosts_modified: bool = False,
) -> OperationResult:
    return proxy_orchestration.restart_proxy_result(
        config=config,
        deps=proxy_orchestration.RestartProxyDeps(
            log=log_func,
            stop_proxy_instance=lambda **kwargs: _stop_proxy_instance_result(
                log_func=log_func,
                **kwargs,
            ),
            start_proxy_instance=lambda cfg, **kwargs: _start_proxy_instance_result(
                cfg,
                log_func=log_func,
                **kwargs,
            ),
        ),
        success_message=success_message,
        hosts_modified=hosts_modified,
    )


def _ensure_global_config_ready(*, log_func) -> OperationResult:
    config_store = _get_config_store()
    result = proxy_orchestration.ensure_global_config_ready(
        load_global_config=config_store.load_global_config,
    )
    if result.ok:
        return OperationResult.success()
    missing_display = "、".join(result.missing_fields)
    log_func(f"⚠️ 全局配置缺失: {missing_display} 不能为空，请在左侧“全局配置”中填写后再试。")
    return OperationResult.failure("全局配置缺失")


def _build_proxy_config(payload: ProxyStartPayload, *, log_func) -> dict[str, Any] | None:
    config_store = _get_config_store()
    stream_mode = payload.stream_mode if payload.force_stream else None
    config = proxy_orchestration.build_proxy_config(
        get_current_config=config_store.get_current_config,
        debug_mode=payload.debug_mode,
        disable_ssl_strict_mode=payload.disable_ssl_strict_mode,
        stream_mode=stream_mode,
    )
    if not config:
        log_func("❌ 错误: 没有可用的配置组")
        return None
    return config


def _modify_hosts_file(*, log_func, **kwargs: Any) -> OperationResult:
    return modify_hosts_file_result(log_func=log_func, **kwargs)


def register_proxy_commands(commands: Commands) -> None:
    @commands.command()
    async def proxy_start(body: ProxyStartPayload) -> dict[str, Any]:
        logs, log_func = collect_logs()
        ready = _ensure_global_config_ready(log_func=log_func)
        if not ready.ok:
            return build_result_payload(ready, logs, "代理服务器启动失败")

        config = _build_proxy_config(body, log_func=log_func)
        if not config:
            return build_result_payload(
                OperationResult.failure("没有可用的配置组"),
                logs,
                "代理服务器启动失败",
            )

        result = _restart_proxy_result(
            config=config,
            log_func=log_func,
            success_message="✅ 代理服务器启动成功",
        )
        return build_result_payload(result, logs, "代理服务器启动完成")

    @commands.command()
    async def proxy_stop() -> dict[str, Any]:
        logs, log_func = collect_logs()
        result = proxy_orchestration.stop_proxy_instance_result(
            get_proxy_instance=_get_proxy_instance,
            set_proxy_instance=_set_proxy_instance,
            log=log_func,
            show_idle_message=True,
        )
        hosts_result = modify_hosts_file_result(action="remove", log_func=log_func)
        if not hosts_result.ok:
            log_func(f"⚠️ {hosts_result.message or 'hosts 条目清理失败'}")
        return build_result_payload(result, logs, "代理服务器停止完成")

    @commands.command()
    async def proxy_check_network() -> dict[str, Any]:
        logs, log_func = collect_logs()
        report = check_network_environment(log_func=log_func, emit_logs=True)
        if not report.explicit_proxy_detected:
            log_func("✅ 未检测到系统/环境变量层面的显式代理配置。")
            log_func(
                "ℹ️ 若仍无法连接，请检查 Trae 的代理设置，"
                "或是否启用了 TUN/VPN/安全软件网络防护。"
            )
        result = OperationResult.success(report=report)
        return build_result_payload(result, logs, "网络环境检查完成")

    @commands.command()
    async def proxy_start_all(body: ProxyStartPayload) -> dict[str, Any]:
        logs, log_func = collect_logs()
        ready = _ensure_global_config_ready(log_func=log_func)
        if not ready.ok:
            return build_result_payload(ready, logs, "一键启动失败")

        config = _build_proxy_config(body, log_func=log_func)
        if not config:
            return build_result_payload(
                OperationResult.failure("没有可用的配置组"),
                logs,
                "一键启动失败",
            )

        log_func("=== 开始一键启动全部服务 ===")
        has_existing = has_existing_ca_cert(
            DEFAULT_METADATA.ca_common_name,
            log_func=log_func,
        )
        if has_existing:
            log_func(
                f"检测到系统已存在 CA 证书 ({DEFAULT_METADATA.ca_common_name})，"
                "跳过证书生成和安装"
            )
        else:
            log_func("步骤 1/4: 生成证书")
            gen_result = generate_certificates_result(
                log_func=log_func,
                ca_common_name=DEFAULT_METADATA.ca_common_name,
            )
            if not gen_result.ok:
                return build_result_payload(gen_result, logs, "一键启动失败")

            log_func("步骤 2/4: 安装CA证书")
            install_result = install_ca_cert_result(log_func=log_func)
            if not install_result.ok:
                return build_result_payload(install_result, logs, "一键启动失败")

        log_func("步骤 3/4: 修改hosts文件")
        hosts_result = modify_hosts_file_result(log_func=log_func)
        if not hosts_result.ok:
            return build_result_payload(hosts_result, logs, "一键启动失败")

        log_func("步骤 4/4: 启动代理服务器")
        start_result = _restart_proxy_result(
            config=config,
            log_func=log_func,
            success_message="✅ 全部服务启动成功",
            hosts_modified=True,
        )
        return build_result_payload(start_result, logs, "一键启动完成")
