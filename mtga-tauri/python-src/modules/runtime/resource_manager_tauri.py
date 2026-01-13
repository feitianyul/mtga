from __future__ import annotations

import os

from . import resource_manager_shared as _shared
from .resource_manager_shared import *  # noqa: F401,F403


def _tauri_runtime_provider() -> str:
    runtime = os.environ.get("MTGA_RUNTIME", "").strip().lower()
    if runtime == "tauri":
        return "tauri"
    return "dev"


_shared.set_packaging_runtime_provider(_tauri_runtime_provider)
