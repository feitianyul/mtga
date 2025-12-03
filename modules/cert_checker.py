"""
证书存在性检查模块
提供跨平台检测，避免重复生成或安装。
"""
from __future__ import annotations

import os
import sys

from .process_utils import run_command

MAC_KEYCHAIN_ITEM_NOT_FOUND = 44


def _log_lines(lines: str | None, log_func=print):
    """逐行输出日志，自动跳过空行。"""

    if not lines:
        return
    for line in lines.splitlines():
        if line.strip():
            log_func(line.strip())


def _parse_certutil_store(output: str) -> list[dict[str, str]]:
    """解析 certutil -store 输出，提取 subject/issuer/thumbprint。"""

    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}

    def flush():
        if current:
            entries.append(current.copy())
            current.clear()

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower.startswith("================"):
            flush()
            continue

        if lower.startswith(("使用者:", "subject:")):
            current["subject"] = line.split(":", 1)[1].strip()
            continue

        if lower.startswith(("颁发者:", "issuer:")):
            current["issuer"] = line.split(":", 1)[1].strip()
            continue

        if "证书哈希" in line or lower.startswith("certificate hash"):
            current["thumbprint"] = line.split(":", 1)[1].strip().replace(" ", "")
            continue

    flush()
    return entries


def _filter_certs_by_name(
    entries: list[dict[str, str]], ca_common_name: str
) -> list[dict[str, str]]:
    """根据 CA common name 过滤证书条目。"""

    target = ca_common_name.lower()
    matched: list[dict[str, str]] = []
    for entry in entries:
        subject = entry.get("subject", "")
        issuer = entry.get("issuer", "")
        if target in subject.lower() or target in issuer.lower():
            matched.append(entry)
    return matched


def _has_ca_on_windows(ca_common_name: str, log_func=print) -> bool:
    """检查 Windows 根存储中是否存在指定 CA。"""

    log_func("检查 Windows 受信任根证书存储中的 CA 证书...")
    list_cmd = ["cmd", "/d", "/s", "/c", "certutil -store Root"]
    return_code, stdout, stderr = run_command(list_cmd)

    _log_lines(stderr, log_func)
    if return_code != 0:
        log_func(f"? 读取证书存储失败 (返回码: {return_code})")
        return False

    entries = _parse_certutil_store(stdout)
    targets = _filter_certs_by_name(entries, ca_common_name)
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
        _log_lines(stderr, log_func)
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
