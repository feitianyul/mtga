"""
证书工具函数（跨模块复用）
用于证书检查/清理等场景的日志输出与 certutil 解析。
"""

from __future__ import annotations

from collections.abc import Iterable


def log_lines(lines: str | None, log_func=print) -> None:
    """逐行输出日志，自动跳过空行。"""
    if not lines:
        return
    for line in lines.splitlines():
        if line.strip():
            log_func(line.strip())


def parse_certutil_store(output: str) -> list[dict[str, str]]:
    """解析 certutil -store 输出，提取 subject/issuer/thumbprint。"""
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}

    def flush() -> None:
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


def filter_certs_by_name(
    entries: Iterable[dict[str, str]],
    ca_common_name: str,
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


__all__ = ["filter_certs_by_name", "log_lines", "parse_certutil_store"]
