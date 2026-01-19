from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from modules.actions import proxy_actions, proxy_ui_coordinator, runtime_options_actions
from modules.runtime.operation_result import OperationResult
from modules.services.config_service import ConfigStore
from modules.ui import runtime_options_panel


@dataclass(frozen=True)
class ProxyContextDeps:
    parent: Any
    tooltip: Callable[..., None]
    log: Callable[[str], None]
    config_store: ConfigStore
    thread_manager: Any
    check_network_environment: Callable[..., Any]
    modify_hosts_file: Callable[..., OperationResult]
    get_proxy_instance: Callable[[], Any | None]
    set_proxy_instance: Callable[[Any | None], None]
    hosts_runner: Any
    has_existing_ca_cert: Callable[..., Any]
    generate_certificates: Callable[..., Any]
    install_ca_cert: Callable[..., Any]
    ca_common_name: str


@dataclass(frozen=True)
class ProxyContext:
    runtime_options: runtime_options_panel.RuntimeOptions
    proxy_ui: proxy_ui_coordinator.ProxyUiCoordinator
    proxy_runner: proxy_actions.ProxyTaskRunner


def build_proxy_context(deps: ProxyContextDeps) -> ProxyContext:
    debug_toggle_handler = runtime_options_actions.DebugModeToggleHandler()
    runtime_options = runtime_options_panel.build_runtime_options_panel(
        runtime_options_panel.RuntimeOptionsPanelDeps(
            parent=deps.parent,
            tooltip=deps.tooltip,
            on_debug_mode_toggle=debug_toggle_handler,
        )
    )
    proxy_ui = proxy_ui_coordinator.ProxyUiCoordinator(
        proxy_ui_coordinator.ProxyUiDeps(
            log=deps.log,
            config_store=deps.config_store,
            runtime_options=runtime_options,
            thread_manager=deps.thread_manager,
            check_network_environment=deps.check_network_environment,
            modify_hosts_file=deps.modify_hosts_file,
            get_proxy_instance=deps.get_proxy_instance,
            set_proxy_instance=deps.set_proxy_instance,
            hosts_runner=deps.hosts_runner,
        )
    )
    debug_toggle_handler.bind(proxy_ui=proxy_ui, runtime_options=runtime_options)
    proxy_ui.set_network_env_precheck_enabled(bool(runtime_options.debug_mode_var.get()))
    proxy_runner = proxy_actions.ProxyTaskRunner(
        log_func=deps.log,
        thread_manager=deps.thread_manager,
        deps=proxy_actions.ProxyTaskDependencies(
            ensure_global_config_ready=proxy_ui.ensure_global_config_ready,
            build_proxy_config=proxy_ui.build_proxy_config,
            get_current_config=proxy_ui.get_current_config,
            restart_proxy=proxy_ui.restart_proxy,
            stop_proxy_and_restore=proxy_ui.stop_proxy_and_restore,
            has_existing_ca_cert=deps.has_existing_ca_cert,
            generate_certificates=deps.generate_certificates,
            install_ca_cert=deps.install_ca_cert,
            modify_hosts_file=deps.modify_hosts_file,
            ca_common_name=deps.ca_common_name,
        ),
    )

    return ProxyContext(
        runtime_options=runtime_options,
        proxy_ui=proxy_ui,
        proxy_runner=proxy_runner,
    )
