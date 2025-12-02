"""
证书清理模块
提供跨平台的 CA 证书删除能力，避免在 GUI 中直接嵌入平台脚本。
"""

from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Iterable

from .macos_privileged_helper import get_mac_privileged_session
from .process_utils import run_command


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
    entries: Iterable[dict[str, str]], ca_common_name: str
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


def _clear_ca_on_windows(ca_common_name: str, log_func=print) -> bool:
    """使用 cmd + certutil 清除 Windows 本地计算机根存储中的 CA 证书。"""

    log_func("开始清除 Windows 受信任根中的CA证书...")
    # 先列出根存储，避免 PowerShell 模块回归问题
    list_cmd = ["cmd", "/d", "/s", "/c", "certutil -store Root"]
    return_code, stdout, stderr = run_command(list_cmd)

    _log_lines(stderr, log_func)
    if return_code != 0:
        log_func(f"❌ 读取证书存储失败 (返回码: {return_code})")
        return False

    entries = _parse_certutil_store(stdout)
    targets = _filter_certs_by_name(entries, ca_common_name)
    if not targets:
        log_func(f"未找到匹配证书: {ca_common_name}")
        return True

    log_func(f"找到 {len(targets)} 个匹配证书，准备删除...")
    any_failed = False

    for cert in targets:
        thumbprint = cert.get("thumbprint")
        subject = cert.get("subject", "")
        if not thumbprint:
            any_failed = True
            log_func(f"⚠️ 跳过缺少哈希的证书: {subject or '[未知证书]'}")
            continue

        log_func(f"Deleting from Root store: {thumbprint}")
        if subject:
            log_func(f"Subject: {subject}")

        delete_cmd = ["cmd", "/d", "/s", "/c", f"certutil -delstore Root {thumbprint}"]
        rc, del_stdout, del_stderr = run_command(delete_cmd)
        _log_lines(del_stdout, log_func)
        _log_lines(del_stderr, log_func)
        if rc != 0:
            any_failed = True
            log_func(f"❌ 删除失败 (返回码: {rc})")

    if any_failed:
        log_func("❌ CA证书清除失败 (部分证书未能删除)")
        return False

    log_func("✅ CA证书清除完成")
    return True


def _clear_ca_on_mac(ca_common_name: str, log_func=print) -> bool:
    """通过 macOS helper 清除系统钥匙串中的 CA 证书。"""

    session = get_mac_privileged_session(log_func=log_func)
    if not session:
        log_func("❌ 无法获取管理员权限，无法清除CA证书")
        return False

    log_func("开始清除系统钥匙串中的CA证书...")
    command = (
        f"security find-certificate -a -c {shlex.quote(ca_common_name)} "
        "-Z /Library/Keychains/System.keychain "
        "| awk '/SHA-1 hash:/ {print $3}' "
        "| while read -r hash; do "
        'echo \"Deleting from System.keychain: $hash\"; '
        'sudo security delete-certificate -Z \"$hash\" /Library/Keychains/System.keychain; '
        "done"
    )
    success, data = session.run_command(["bash", "-lc", command], log_func=log_func)
    if not isinstance(data, dict):
        data = {}
    _log_lines(data.get("stdout"), log_func)
    _log_lines(data.get("stderr"), log_func)
    if success:
        log_func("✅ CA证书清除完成")
        return True

    return_code = data.get("returncode")
    rc_text = return_code if return_code is not None else "未知"
    log_func(f"❌ CA证书清除失败 (返回码: {rc_text})")
    return False


def clear_ca_cert(ca_common_name: str, log_func=print) -> bool:
    """根据平台清除系统信任存储中的 CA 证书。"""

    if sys.platform == "darwin":
        return _clear_ca_on_mac(ca_common_name, log_func=log_func)
    if os.name == "nt":
        return _clear_ca_on_windows(ca_common_name, log_func=log_func)

    log_func("⚠️ 当前平台不支持自动清除CA证书")
    return False


__all__ = ["clear_ca_cert"]
