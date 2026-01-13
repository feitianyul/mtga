from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pytauri import Commands

from modules.services.app_metadata import DEFAULT_METADATA
from modules.services.app_version import resolve_app_version
from modules.services.update_service import check_for_updates_result

from .common import build_result_payload, collect_logs


@lru_cache(maxsize=1)
def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def register_update_commands(commands: Commands) -> None:
    @commands.command()
    async def check_updates() -> dict[str, Any]:
        logs, log_func = collect_logs()
        version = resolve_app_version(project_root=_get_project_root())
        result = check_for_updates_result(
            repo=DEFAULT_METADATA.github_repo,
            app_version=version,
        )
        return build_result_payload(result, logs, "更新检查完成")
