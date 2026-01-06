from __future__ import annotations

from . import resource_manager_shared as _shared
from .resource_manager_shared import *  # noqa: F401,F403

_shared.set_packaging_runtime_provider(_shared._legacy_runtime_provider)
