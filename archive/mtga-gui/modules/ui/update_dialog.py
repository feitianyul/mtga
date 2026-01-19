from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk
from typing import Any

from modules.ui.ui_helpers import center_window


@dataclass(frozen=True)
class UpdateDialogDeps:
    window: tk.Tk
    notes_html: str
    release_url: str
    version_label: str
    create_tkinterweb_html_widget: Callable[..., tuple[type[Any] | None, Any]]
    program_resource_dir: str
    log: Callable[[str], None]


def show_release_notes_dialog(deps: UpdateDialogDeps) -> None:
    notes_html = (
        deps.notes_html
        or (
            "<html><head><meta charset='utf-8'></head><body>"
            "<p>该版本暂无更新说明。</p>"
            "</body></html>"
        )
    )
    dialog = tk.Toplevel(deps.window)
    dialog.title("更新检查")
    dialog.geometry("520x420")
    dialog.minsize(480, 360)
    dialog.transient(deps.window)

    heading_font = tkfont.nametofont("TkDefaultFont").copy()
    heading_font.configure(weight="bold", size=heading_font.cget("size") + 1)

    header_frame = ttk.Frame(dialog)
    header_frame.pack(fill=tk.X, padx=12, pady=(12, 6))
    ttk.Label(
        header_frame,
        text=f"发现新版本：{deps.version_label}",
        anchor="w",
        font=heading_font,
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    if deps.release_url:
        ttk.Button(
            header_frame,
            text="前往发布页",
            command=lambda: webbrowser.open(deps.release_url),
        ).pack(side=tk.RIGHT, padx=(8, 0))
    html_frame_cls, notes_widget = deps.create_tkinterweb_html_widget(
        dialog,
        program_resource_dir=deps.program_resource_dir,
        log_fn=deps.log,
    )
    notes_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

    if html_frame_cls and isinstance(notes_widget, html_frame_cls):
        frame_widget = notes_widget
        frame_widget.load_html(notes_html)

        default_link_handler = frame_widget.html.on_link_click

        def handle_link_click(url, decode=None, force=False):
            if url.startswith(("http://", "https://")):
                webbrowser.open(url)
            else:
                default_link_handler(url, decode=decode, force=force)

        frame_widget.html.on_link_click = handle_link_click

    def on_close():
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", on_close)
    center_window(dialog)
    dialog.grab_set()
