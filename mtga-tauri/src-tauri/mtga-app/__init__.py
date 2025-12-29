from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from anyio.from_thread import start_blocking_portal
from modules.runtime.resource_manager import (
    ResourceManager,
)
from modules.runtime.resource_manager import (
    is_packaged as resource_is_packaged,
)
from modules.services.app_metadata import DEFAULT_METADATA
from modules.services.app_version import resolve_app_version
from modules.services.config_service import ConfigStore
from pytauri import Commands
from pytauri_wheel.lib import builder_factory, context_factory

from .commands.hosts import register_hosts_commands


def find_repo_root(start: Path) -> Path:
    p = start
    while True:
        if (p / "modules").exists() and (p / "mtga-tauri").exists():
            return p
        if p.parent == p:
            raise RuntimeError("Repo root not found (expected modules/ and mtga-tauri/).")
        p = p.parent


# 迁移期：允许直接 import 根目录 modules/
REPO_ROOT = find_repo_root(Path(__file__).resolve())
sys.path.insert(0, str(REPO_ROOT))

commands = Commands()
register_hosts_commands(commands)


@lru_cache(maxsize=1)
def _get_resource_manager() -> ResourceManager:
    return ResourceManager()


@lru_cache(maxsize=1)
def _get_config_store() -> ConfigStore:
    resource_manager = _get_resource_manager()
    return ConfigStore(resource_manager.get_user_config_file())


@commands.command()
async def greet(name: str) -> str:
    return f"Hello, {name}! from Python {sys.version.split()[0]}"


@commands.command()
async def load_config() -> dict[str, Any]:
    config_store = _get_config_store()
    config_groups, current_index = config_store.load_config_groups()
    mapped_model_id, mtga_auth_key = config_store.load_global_config()
    return {
        "config_groups": config_groups,
        "current_config_index": current_index,
        "mapped_model_id": mapped_model_id,
        "mtga_auth_key": mtga_auth_key,
    }


@commands.command()
async def save_config(
    config_groups: list[dict[str, Any]],
    current_config_index: int,
    mapped_model_id: str | None = None,
    mtga_auth_key: str | None = None,
) -> bool:
    config_store = _get_config_store()
    return config_store.save_config_groups(
        config_groups,
        current_config_index,
        mapped_model_id,
        mtga_auth_key,
    )


@commands.command()
async def get_app_info() -> dict[str, Any]:
    metadata = DEFAULT_METADATA
    version = resolve_app_version(project_root=REPO_ROOT)
    return {
        "display_name": metadata.display_name,
        "version": version,
        "github_repo": metadata.github_repo,
        "ca_common_name": metadata.ca_common_name,
        "api_key_visible_chars": metadata.api_key_visible_chars,
    }


@commands.command()
async def is_packaged() -> bool:
    return resource_is_packaged()


def main() -> int:
    # 开发期：让 Tauri 加载 Nuxt dev server
    dev_server = os.environ.get("DEV_SERVER")

    with start_blocking_portal("asyncio") as portal:
        context_factory_any = cast(Any, context_factory)
        context = context_factory_any(
            # ✅ v2：context 根通常用 src-tauri 目录
            src_tauri_dir=Path(__file__).resolve().parent.parent,
            tauri_config=dev_server,
        )
        app = builder_factory().build(
            context=context,
            invoke_handler=commands.generate_handler(portal),
        )
        return app.run_return()
