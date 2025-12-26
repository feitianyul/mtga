from __future__ import annotations

import os
import sys
from pathlib import Path

from anyio.from_thread import start_blocking_portal
from pytauri import Commands
from pytauri_wheel.lib import builder_factory, context_factory


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


@commands.command()
async def greet(name: str) -> str:
    return f"Hello, {name}! from Python {sys.version.split()[0]}"


def main() -> int:
    # 开发期：让 Tauri 加载 Nuxt dev server
    dev_server = os.environ.get("DEV_SERVER")

    with start_blocking_portal("asyncio") as portal:
        app = builder_factory().build(
            context=context_factory(
                # ✅ v2：context 根通常用 src-tauri 目录
                src_tauri_dir=Path(__file__).resolve().parent.parent,
                tauri_config=dev_server,
            ),
            invoke_handler=commands.generate_handler(portal),
        )
        return app.run_return()
