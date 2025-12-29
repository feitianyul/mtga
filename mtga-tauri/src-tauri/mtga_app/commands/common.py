from __future__ import annotations

from typing import Any

from modules.runtime.operation_result import OperationResult
from modules.runtime.result_messages import describe_result


def collect_logs() -> tuple[list[str], Any]:
    logs: list[str] = []

    def _log(message: Any) -> None:
        if message is None:
            return
        logs.append(str(message))

    return logs, _log


def build_result_payload(
    result: OperationResult,
    logs: list[str],
    default_message: str,
) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "message": describe_result(result, default_message),
        "code": str(result.code) if result.code else None,
        "details": result.details,
        "logs": logs,
    }
