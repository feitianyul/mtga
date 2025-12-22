#!/usr/bin/env python3
# ruff: noqa: E402,I001

# 在最早阶段设置 UTF-8 编码环境变量 - 必须在任何导入之前
import locale
import os
import sys
import tkinter as tk
from contextlib import suppress
from functools import partial
from pathlib import Path
from tkinter import messagebox


from modules.ui_helpers import center_window

os.environ.setdefault("LANG", "zh_CN.UTF-8")
os.environ.setdefault("LC_ALL", "zh_CN.UTF-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if sys.platform == "darwin":
    try:
        locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
    except Exception:
        with suppress(Exception):
            locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

"""
MTGA GUI - 重构版本
采用单进程模块化架构，解决 Nuitka 打包兼容性问题

功能:
1. 一键生成证书（模块化调用）
2. 导入证书到系统信任存储
3. 修改 hosts 文件
4. 启动代理服务器（线程模式）
"""


try:
    from modules.services import (
        app_metadata,
        env_setup,
        environment_service,
        io_service,
    )
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 modules 目录及其模块文件存在")
    sys.exit(1)

env_setup.setup_environment()
io_service.ensure_utf8_stdio()

# 导入自定义模块
try:
    from modules.cert_generator import generate_certificates
    from modules.cert_checker import has_existing_ca_cert
    from modules.cert_installer import install_ca_cert
    from modules.hosts_manager import (
        modify_hosts_file,
        open_hosts_file,
    )
    from modules.network_environment import check_network_environment
    from modules.resource_manager import (
        copy_template_files,
        get_user_data_dir,
        is_packaged,
    )
    from modules.tkhtml_compat import create_tkinterweb_html_widget
    from modules import macos_privileged_helper
    from modules.services import (
        bootstrap,
        app_metadata,
        app_version,
        logging_service,
        privilege_service,
        proxy_state,
        startup_context,
        update_service,
    )
    from modules.ui import (
        main_window_builder,
        update_dialog,
    )
    from modules import resource_manager as resource_manager_module
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 modules 目录及其模块文件存在")
    sys.exit(1)

# 处理 macOS 持久化 helper CLI 调用
if macos_privileged_helper.HELPER_FLAG in sys.argv:
    macos_privileged_helper.main()
    sys.exit(0)

# 全局变量
APP_CONTEXT = bootstrap.build_app_context()
resource_manager = APP_CONTEXT.resource_manager
thread_manager = APP_CONTEXT.thread_manager

APP_METADATA = app_metadata.DEFAULT_METADATA


ERROR_LOG_PATH = logging_service.setup_error_logging(
    get_user_data_dir=get_user_data_dir,
    error_log_filename=APP_METADATA.error_log_filename,
)
log_error = logging_service.log_error
logging_service.install_global_exception_hook(log_error=log_error)

STARTUP_CONTEXT = startup_context.build_startup_context()

APP_VERSION = app_version.resolve_app_version(project_root=Path(__file__).resolve().parent)



get_proxy_instance = proxy_state.get_proxy_instance
set_proxy_instance = proxy_state.set_proxy_instance


check_is_admin = privilege_service.check_is_admin
run_as_admin = privilege_service.run_as_admin


check_environment = partial(
    environment_service.check_environment,
    check_resources=resource_manager.check_resources,
)


config_store = APP_CONTEXT.config_store


def create_main_window() -> tk.Tk | None:
    """创建主窗口"""
    return main_window_builder.build_main_window(
        main_window_builder.MainWindowDeps(
            get_icon_file=resource_manager.get_icon_file,
            thread_manager=thread_manager,
            config_store=config_store,
            log_error=log_error,
            check_environment=check_environment,
            is_packaged=is_packaged,
            check_network_environment=check_network_environment,
            modify_hosts_file=modify_hosts_file,
            open_hosts_file=open_hosts_file,
            get_user_data_dir=get_user_data_dir,
            copy_template_files=copy_template_files,
            app_metadata=APP_METADATA,
            app_version=APP_VERSION,
            update_service=update_service,
            update_dialog=update_dialog,
            create_tkinterweb_html_widget=create_tkinterweb_html_widget,
            program_resource_dir=resource_manager_module.get_program_resource_dir(),
            startup_context=STARTUP_CONTEXT,
            generate_certificates=generate_certificates,
            install_ca_cert=install_ca_cert,
            has_existing_ca_cert=has_existing_ca_cert,
            center_window=center_window,
            get_proxy_instance=get_proxy_instance,
            set_proxy_instance=set_proxy_instance,
            messagebox=messagebox,
        )
    )


def main():
    """主函数"""
    # 不再在启动时检查管理员权限
    # 只在需要时（安装证书）请求权限

    try:
        # 创建并运行GUI
        root = create_main_window()
        if root is None:
            log_error("GUI initialization returned None; aborting.")
            sys.exit(1)
        root.mainloop()
    except Exception as e:
        # 如果 GUI 创建失败，至少尝试记录错误
        error_msg = f"GUI initialization failed: {e}"
        log_error(error_msg, exc_info=True)

        # 在 macOS 上，如果是从 Finder 启动，显示错误对话框并指明日志路径
        if sys.platform == "darwin":
            with suppress(Exception):
                messagebox.showerror(
                    "MTGA GUI Error",
                    f"{error_msg}\n\n详细日志: {ERROR_LOG_PATH}",
                )

        # 退出程序
        sys.exit(1)


if __name__ == "__main__":
    main()
