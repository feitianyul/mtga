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
    from modules.platform import macos_privileged_helper
    from modules.runtime.resource_manager import get_user_data_dir
    from modules.services import app_bootstrap, privilege_service
    from modules.ui import (
        main_window_builder,
        main_window_deps,
    )
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 modules 目录及其模块文件存在")
    sys.exit(1)

# 处理 macOS 持久化 helper CLI 调用
if macos_privileged_helper.HELPER_FLAG in sys.argv:
    macos_privileged_helper.main()
    sys.exit(0)

BOOTSTRAP = app_bootstrap.build_app_bootstrap(
    project_root=Path(__file__).resolve().parent,
    get_user_data_dir=get_user_data_dir,
)
APP_CONTEXT = BOOTSTRAP.app_context
resource_manager = APP_CONTEXT.resource_manager
thread_manager = APP_CONTEXT.thread_manager
APP_METADATA = BOOTSTRAP.app_metadata
APP_VERSION = BOOTSTRAP.app_version
STARTUP_CONTEXT = BOOTSTRAP.startup_context
ERROR_LOG_PATH = BOOTSTRAP.error_log_path
log_error = BOOTSTRAP.log_error



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
        main_window_deps.build_main_window_deps(
            main_window_deps.MainWindowDepsInputs(
                app_context=APP_CONTEXT,
                app_metadata=APP_METADATA,
                app_version=APP_VERSION,
                log_error=log_error,
                check_environment=check_environment,
                startup_context=STARTUP_CONTEXT,
            )
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
