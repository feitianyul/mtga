"""
证书安装模块
处理 CA 证书的系统安装和信任设置
"""

import os
import sys

from .macos_privileged_helper import get_mac_privileged_session
from .process_utils import run_command
from .resource_manager import ResourceManager


def install_ca_cert_windows(ca_cert_file, log_func=print):
    """
    在 Windows 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 Windows 系统中安装 CA 证书...")

    try:
        cmd = f'certutil -addstore -f "ROOT" "{ca_cert_file}"'
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code == 0:
            log_func("CA 证书安装成功！")
            return True
        else:
            log_func(f"证书安装失败，返回码: {return_code}")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert_macos(ca_cert_file, log_func=print):  # noqa: PLR0912, PLR0915
    """
    在 macOS 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 macOS 系统中安装 CA 证书...")

    try:
        session = get_mac_privileged_session(log_func=log_func)
        if not session:
            log_func("❌ 无法获取管理员权限，证书未安装")
            return False

        log_func("请求以管理员权限将证书安装到系统钥匙串并设为信任...")
        success, data = session.install_trusted_cert(
            ca_cert_file,
            keychain="/Library/Keychains/System.keychain",
            log_func=log_func,
        )
        stdout = data.get("stdout") if isinstance(data, dict) else None
        stderr = data.get("stderr") if isinstance(data, dict) else None
        if stdout:
            log_func(stdout.strip())
        if stderr:
            log_func(stderr.strip())

        if success:
            log_func("✅ CA 证书已添加到系统钥匙串并设为信任")
            return True

        return_code = data.get("returncode") if isinstance(data, dict) else None
        error_msg = ""
        if isinstance(data, dict):
            error_msg = stderr or data.get("error") or ""
        log_func(
            f"❌ 证书安装失败 (返回码: {return_code if return_code is not None else '未知'})"
        )
        if error_msg:
            log_func(f"错误信息: {error_msg}")
        return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert_linux(ca_cert_file, log_func=print):
    """
    在 Linux 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 Linux 系统中安装 CA 证书...")

    try:
        # 复制证书到系统目录
        cmd = f'sudo cp "{ca_cert_file}" /usr/local/share/ca-certificates/'
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code != 0:
            log_func(f"复制证书失败，返回码: {return_code}")
            return False

        # 更新 CA 证书
        cmd = "sudo update-ca-certificates"
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code == 0:
            log_func("CA 证书安装成功！")
            return True
        else:
            log_func(f"更新证书失败，返回码: {return_code}")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert(log_func=print):
    """
    根据操作系统安装 CA 证书

    参数:
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("开始安装 CA 证书...")

    # 初始化资源管理器
    resource_manager = ResourceManager()

    # 检查可能的 CA 证书文件名
    possible_cert_files = [
        resource_manager.get_ca_cert_file(),
        os.path.join(resource_manager.ca_path, "rootCA.crt"),
        os.path.join(resource_manager.ca_path, "ca.cer"),
        os.path.join(resource_manager.ca_path, "rootCA.cer"),
    ]

    ca_cert_file = None
    for cert_file in possible_cert_files:
        if os.path.exists(cert_file):
            ca_cert_file = cert_file
            log_func(f"找到 CA 证书文件: {ca_cert_file}")
            break

    if ca_cert_file is None:
        log_func(f"错误: 未找到 CA 证书文件，已检查以下路径: {', '.join(possible_cert_files)}")
        return False

    try:
        if os.name == "nt":  # Windows
            return install_ca_cert_windows(ca_cert_file, log_func)
        elif sys.platform == "darwin":  # macOS
            return install_ca_cert_macos(ca_cert_file, log_func)
        elif os.name == "posix":  # Linux
            return install_ca_cert_linux(ca_cert_file, log_func)
        else:
            log_func("错误: 不支持的操作系统")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书失败: {e}")
        return False
