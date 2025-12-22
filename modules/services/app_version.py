from __future__ import annotations

import os
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def resolve_app_version(*, project_root: Path) -> str:
    """从构建期注入的版本信息或 pyproject.toml 解析应用版本。"""

    def normalize_version(raw_value: str | None) -> str | None:
        if not raw_value:
            return None
        raw_value = raw_value.strip()
        if not raw_value:
            return None
        return raw_value if raw_value.startswith("v") else f"v{raw_value}"

    env_version = normalize_version(os.getenv("MTGA_VERSION"))
    if env_version:
        return env_version

    baked_version: str | None = None
    try:
        from modules.runtime import _build_version as build_version_module  # type: ignore  # noqa: PLC0415,I001

        baked_version = normalize_version(
            getattr(build_version_module, "BUILT_APP_VERSION", None)
        )
    except Exception:
        baked_version = None

    if baked_version:
        return baked_version

    if tomllib is None:
        return "v0.0.0"

    pyproject_path = project_root / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        version = normalize_version(data.get("project", {}).get("version"))
        if not version:
            return "v0.0.0"
        return version
    except Exception:
        return "v0.0.0"
