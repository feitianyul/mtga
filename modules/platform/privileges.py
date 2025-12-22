from __future__ import annotations

import ctypes
import os
import sys

from .system import is_posix, is_windows


def is_windows_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_windows_elevated() -> bool:
    if not is_windows():
        return False

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    TOKEN_QUERY = 0x0008
    TokenElevation = 20

    token = ctypes.wintypes.HANDLE()  # type: ignore[attr-defined]
    try:
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(),
            TOKEN_QUERY,
            ctypes.byref(token),
        ):
            return False

        elevation = ctypes.wintypes.DWORD()  # type: ignore[attr-defined]
        returned_size = ctypes.wintypes.DWORD()  # type: ignore[attr-defined]
        if not advapi32.GetTokenInformation(
            token,
            TokenElevation,
            ctypes.byref(elevation),
            ctypes.sizeof(elevation),
            ctypes.byref(returned_size),
        ):
            return False
        return bool(elevation.value)
    except Exception:
        return False
    finally:
        try:
            if token:
                kernel32.CloseHandle(token)
        except Exception:
            pass


def is_admin() -> bool:
    """Return True when the current process is elevated/admin on this platform."""
    if is_windows():
        return is_windows_admin()
    if is_posix():
        get_euid = getattr(os, "geteuid", None)
        if get_euid is None:
            return False
        try:
            return get_euid() == 0
        except Exception:
            return False
    return False


def check_is_admin() -> bool:
    return is_admin()


def run_as_admin() -> None:
    """Request admin privileges and relaunch the script when possible."""
    if check_is_admin():
        return
    if is_windows():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    if is_posix():
        print("此程序需要管理员权限才能运行。")
        print("请使用以下命令重新运行：")
        print(f"sudo {sys.executable} {' '.join(sys.argv)}")
        sys.exit(1)
    print("不支持的操作系统")
    sys.exit(1)


__all__ = [
    "check_is_admin",
    "is_admin",
    "is_windows_admin",
    "is_windows_elevated",
    "run_as_admin",
]
