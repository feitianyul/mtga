from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import scrolledtext, ttk

from modules.ui_helpers import build_text_logger


@dataclass(frozen=True)
class WindowLayout:
    main_frame: ttk.Frame
    main_paned: ttk.PanedWindow
    left_frame: ttk.Frame
    left_content: ttk.Frame
    right_frame: ttk.Frame
    log_text: scrolledtext.ScrolledText
    log: Callable[[str], None]


def build_main_layout(window: tk.Tk) -> WindowLayout:
    main_frame = ttk.Frame(window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    title_label = ttk.Label(
        main_frame,
        text="MTGA - 代理服务器管理工具",
        font=("TkDefaultFont", 16, "bold"),
    )
    title_label.pack(pady=10)

    main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    main_paned.pack(fill=tk.BOTH, expand=True, pady=5)

    left_frame = ttk.Frame(main_paned, width=1)
    main_paned.add(left_frame, weight=1)

    left_frame.grid_rowconfigure(0, weight=1)
    left_frame.grid_columnconfigure(0, weight=1)
    left_content = ttk.Frame(left_frame)
    left_content.grid(row=0, column=0, sticky="nsew")

    right_frame = ttk.Frame(main_paned, width=1)
    main_paned.add(right_frame, weight=1)

    log_frame = ttk.LabelFrame(right_frame, text="日志")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = scrolledtext.ScrolledText(log_frame, height=10, width=1)
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    log = build_text_logger(log_text)

    return WindowLayout(
        main_frame=main_frame,
        main_paned=main_paned,
        left_frame=left_frame,
        left_content=left_content,
        right_frame=right_frame,
        log_text=log_text,
        log=log,
    )


def init_paned_layout(main_paned: ttk.PanedWindow, main_frame: ttk.Frame, window: tk.Tk) -> None:
    first_layout_done = {"value": False}

    def on_main_paned_configure(_event) -> None:
        if first_layout_done["value"]:
            return
        window.update_idletasks()
        total_width = main_paned.winfo_width() or main_frame.winfo_width() or window.winfo_width()
        if total_width > 0:
            main_paned.sashpos(0, total_width // 2)
            first_layout_done["value"] = True
            main_paned.unbind("<Configure>")

    main_paned.bind("<Configure>", on_main_paned_configure)
