from __future__ import annotations

from dataclasses import dataclass
from tkinter import messagebox
from typing import Any

from modules.network.network_environment import check_network_environment
from modules.runtime import resource_manager as resource_manager_module
from modules.runtime.resource_manager import copy_template_files, get_user_data_dir, is_packaged
from modules.services import cert_service, hosts_service, proxy_state, update_service
from modules.services.app_metadata import AppMetadata
from modules.services.bootstrap import AppContext
from modules.services.startup_context import StartupContext
from modules.ui import update_dialog
from modules.ui.main_window_builder import MainWindowDeps
from modules.ui.tkhtml_compat import create_tkinterweb_html_widget
from modules.ui.ui_helpers import center_window


@dataclass(frozen=True)
class MainWindowDepsInputs:
    app_context: AppContext
    app_metadata: AppMetadata
    app_version: str
    log_error: Any
    check_environment: Any
    startup_context: StartupContext


def build_main_window_deps(inputs: MainWindowDepsInputs) -> MainWindowDeps:
    return MainWindowDeps(
        get_icon_file=inputs.app_context.resource_manager.get_icon_file,
        thread_manager=inputs.app_context.thread_manager,
        config_store=inputs.app_context.config_store,
        log_error=inputs.log_error,
        check_environment=inputs.check_environment,
        is_packaged=is_packaged,
        check_network_environment=check_network_environment,
        modify_hosts_file=hosts_service.modify_hosts_file_result,
        open_hosts_file=hosts_service.open_hosts_file_result,
        get_user_data_dir=get_user_data_dir,
        copy_template_files=copy_template_files,
        app_metadata=inputs.app_metadata,
        app_version=inputs.app_version,
        update_service=update_service,
        update_dialog=update_dialog,
        create_tkinterweb_html_widget=create_tkinterweb_html_widget,
        program_resource_dir=resource_manager_module.get_program_resource_dir(),
        startup_context=inputs.startup_context,
        generate_certificates=cert_service.generate_certificates,
        install_ca_cert=cert_service.install_ca_cert,
        has_existing_ca_cert=cert_service.has_existing_ca_cert,
        center_window=center_window,
        get_proxy_instance=proxy_state.get_proxy_instance,
        set_proxy_instance=proxy_state.set_proxy_instance,
        messagebox=messagebox,
    )
