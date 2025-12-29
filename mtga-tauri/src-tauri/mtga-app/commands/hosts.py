from __future__ import annotations

from typing import Any

from modules.services.hosts_service import (
    backup_hosts_file_result,
    modify_hosts_file_result,
    open_hosts_file_result,
    remove_hosts_entry_result,
    restore_hosts_file_result,
)
from pytauri import Commands

from .common import build_result_payload, collect_logs


def register_hosts_commands(commands: Commands) -> None:
    @commands.command()
    async def hosts_modify(
        mode: str,
        domain: str | None = None,
        ip: list[str] | str | None = None,
    ) -> dict[str, Any]:
        logs, log_func = collect_logs()
        domain_value = domain or "api.openai.com"

        if mode == "add":
            result = modify_hosts_file_result(
                domain=domain_value,
                action="add",
                ip=ip,
                log_func=log_func,
            )
            return build_result_payload(result, logs, "hosts 修改完成")
        if mode == "remove":
            result = remove_hosts_entry_result(
                domain=domain_value,
                ip=ip,
                log_func=log_func,
            )
            return build_result_payload(result, logs, "hosts 删除完成")
        if mode == "backup":
            result = backup_hosts_file_result(log_func=log_func)
            return build_result_payload(result, logs, "hosts 备份完成")
        if mode == "restore":
            result = restore_hosts_file_result(log_func=log_func)
            return build_result_payload(result, logs, "hosts 还原完成")

        return {
            "ok": False,
            "message": f"不支持的 hosts 操作: {mode}",
            "code": None,
            "details": {},
            "logs": logs,
        }

    @commands.command()
    async def hosts_open() -> dict[str, Any]:
        logs, log_func = collect_logs()
        result = open_hosts_file_result(log_func=log_func)
        return build_result_payload(result, logs, "hosts 打开完成")
