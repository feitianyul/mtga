"""为打包环境下的 tkinterweb/Tkhtml 提供导入修复与加载辅助。"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def _init_packaged_tkhtml_dir(program_resource_dir: str | Path) -> Path | None:
    """在打包资源目录中初始化 Tkhtml 解压目录，并注入 tkinterweb_tkhtml 伪模块。"""
    base_dir = Path(program_resource_dir)
    pkg_dir = base_dir / "tkinterweb_tkhtml"
    candidate = pkg_dir / "tkhtml"

    if not candidate.exists():
        return None

    # DLL 搜索路径（主要用于 Windows 打包）
    os.environ["PATH"] = f"{candidate}{os.pathsep}{os.environ.get('PATH', '')}"

    # 伪造 tkinterweb_tkhtml 模块，强制指向解压目录
    sys.modules.pop("tkinterweb_tkhtml", None)
    binaries = sorted([f for f in os.listdir(candidate) if "libTkhtml" in f])

    fake_mod = ModuleType("tkinterweb_tkhtml")
    fake_mod.__file__ = str(pkg_dir / "__init__.py")
    fake_mod.__path__ = [str(pkg_dir)]
    cast(Any, fake_mod).TKHTML_ROOT_DIR = str(candidate)
    cast(Any, fake_mod).ALL_TKHTML_BINARIES = binaries

    def _get_tkhtml_file(version=None, index=-1, experimental=False):  # noqa: ANN001
        files = sorted(cast(Any, fake_mod).ALL_TKHTML_BINARIES)
        if not files:
            raise OSError("No Tkhtml binaries found in packaged root")
        chosen = files[index]
        exp = experimental or ("exp" in chosen)
        ver = chosen.replace("libTkhtml", "").replace("exp", "").replace(".dll", "")
        return os.path.join(cast(Any, fake_mod).TKHTML_ROOT_DIR, chosen), ver, exp

    def _load_tkhtml_file(master, file):  # noqa: ANN001
        master.tk.call("load", file)

    def _load_tkhtml(master):  # noqa: ANN001
        path, ver, exp = _get_tkhtml_file()
        _load_tkhtml_file(master, path)
        with suppress(Exception):
            master.tk.call("package", "provide", "Tkhtml", ver or "0")

    def _get_loaded_tkhtml_version(master):  # noqa: ANN001
        try:
            return master.tk.call("package", "present", "Tkhtml")
        except Exception:
            return ""

    cast(Any, fake_mod).get_tkhtml_file = _get_tkhtml_file
    cast(Any, fake_mod).load_tkhtml_file = _load_tkhtml_file
    cast(Any, fake_mod).load_tkhtml = _load_tkhtml
    cast(Any, fake_mod).get_loaded_tkhtml_version = _get_loaded_tkhtml_version

    sys.modules["tkinterweb_tkhtml"] = fake_mod
    return candidate


def load_packaged_tkhtml(master: Any, *, program_resource_dir: str | Path) -> Path | None:
    """尝试从打包资源初始化并加载 Tkhtml；不可用则静默返回 None。"""
    tkhtml_dir = _init_packaged_tkhtml_dir(program_resource_dir)
    if not tkhtml_dir:
        return None

    with suppress(Exception):
        import tkinterweb_tkhtml as tkhtml_mod  # type: ignore  # noqa: PLC0415

        load_fn = getattr(tkhtml_mod, "load_tkhtml", None)
        if callable(load_fn):
            load_fn(master)

    return tkhtml_dir


def create_tkinterweb_html_widget(
    parent: Any,
    *,
    program_resource_dir: str | Path | None = None,
    log_fn: Callable[[str], Any] | None = None,
) -> tuple[type[Any] | None, Any]:
    """创建 release notes 的 HTML 组件；失败则降级为 Label，并可记录异常。"""
    if program_resource_dir is not None:
        load_packaged_tkhtml(parent, program_resource_dir=program_resource_dir)

    try:
        from tkinterweb import HtmlFrame  # noqa: PLC0415

        html_frame_cls: type[Any] | None = HtmlFrame
        notes_widget = HtmlFrame(
            parent,
            horizontal_scrollbar="auto",
            vertical_scrollbar="auto",
            relief="solid",
            borderwidth=1,
            messages_enabled=False,
        )
        return html_frame_cls, notes_widget
    except Exception as exc:  # noqa: BLE001
        from tkinter import font as tkfont  # noqa: PLC0415
        from tkinter import ttk  # noqa: PLC0415

        html_frame_cls = None
        notes_widget = ttk.Label(
            parent,
            anchor="w",
            font=tkfont.nametofont("TkDefaultFont"),
        )
        if log_fn is not None:
            log_fn(f"tkhtml导入失败，捕获到异常:\n{exc}")
        return html_frame_cls, notes_widget


__all__ = ["create_tkinterweb_html_widget", "load_packaged_tkhtml"]
