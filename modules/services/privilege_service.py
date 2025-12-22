from __future__ import annotations

import ctypes
import os
import sys


def check_is_admin() -> bool:
    """检查是否具有管理员权限"""
    try:
        if os.name == "nt":  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin()
        if os.name == "posix":  # Unix/Linux/macOS
            return os.geteuid() == 0
        return False
    except Exception:
        return False


def run_as_admin() -> None:
    """请求管理员权限并重启脚本"""
    if check_is_admin():
        return
    if os.name == "nt":  # Windows
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    if os.name == "posix":  # Unix/Linux/macOS
        print("此程序需要管理员权限才能运行。")
        print("请使用以下命令重新运行：")
        print(f"sudo {sys.executable} {' '.join(sys.argv)}")
        sys.exit(1)
    print("不支持的操作系统")
    sys.exit(1)
