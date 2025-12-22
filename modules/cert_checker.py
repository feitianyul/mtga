"""
证书存在性检查模块
提供跨平台检测，避免重复生成或安装。
"""
from __future__ import annotations

import os
import sys

from .cert_utils import filter_certs_by_name, log_lines, parse_certutil_store
from .process_utils import run_command

MAC_KEYCHAIN_ITEM_NOT_FOUND = 44


def _has_ca_on_windows(ca_common_name: str, log_func=print) -> bool:
    """检查 Windows 根存储中是否存在指定 CA。"""

    log_func("检查 Windows 受信任根证书存储中的 CA 证书...")
    list_cmd = ["cmd", "/d", "/s", "/c", "certutil -store Root"]
    return_code, stdout, stderr = run_command(list_cmd)

    log_lines(stderr, log_func)
    if return_code != 0:
        log_func(f"? 读取证书存储失败 (返回码: {return_code})")
        return False

    entries = parse_certutil_store(stdout)
    targets = filter_certs_by_name(entries, ca_common_name)
    if targets:
        log_func(f"检测到 {len(targets)} 个匹配的 CA 证书")
        return True

    log_func("未找到匹配的 CA 证书")
    return False


def _has_ca_on_mac(ca_common_name: str, log_func=print) -> bool:
    """检查 macOS 系统钥匙串中是否存在指定 CA。"""

    log_func("检查 macOS 系统钥匙串中的 CA 证书...")
    cmd = [
        "security",
        "find-certificate",
        "-a",
        "-c",
        ca_common_name,
        "-Z",
        "/Library/Keychains/System.keychain",
    ]
    return_code, stdout, stderr = run_command(cmd)

    if (
        return_code == MAC_KEYCHAIN_ITEM_NOT_FOUND
        and stderr
        and "could not be found" in stderr.lower()
    ):
        log_func("未在系统钥匙串中找到匹配的 CA 证书")
        return False

    if return_code not in (0, MAC_KEYCHAIN_ITEM_NOT_FOUND):
        log_func(f"? 检查系统钥匙串失败 (返回码: {return_code})")
        log_lines(stderr, log_func)
        return False

    if stdout.strip():
        log_func("检测到系统钥匙串中存在匹配的 CA 证书")
        return True

    log_func("未在系统钥匙串中找到匹配的 CA 证书")
    return False


def has_existing_ca_cert(ca_common_name: str, log_func=print) -> bool:
    """跨平台检查系统中是否已存在指定 Common Name 的 CA 证书。"""

    if sys.platform == "darwin":
        return _has_ca_on_mac(ca_common_name, log_func=log_func)
    if os.name == "nt":
        return _has_ca_on_windows(ca_common_name, log_func=log_func)

    log_func("?? 当前平台不支持自动检查系统CA证书")
    return False


__all__ = ["has_existing_ca_cert"]
