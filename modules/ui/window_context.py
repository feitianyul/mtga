from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from modules.macos_theme import detect_macos_dark_mode
from modules.ui import layout_builders, window_setup
from modules.ui_helpers import build_tk_error_handler, create_tooltip


@dataclass(frozen=True)
class WindowContext:
    window: tk.Tk
    get_preferred_font: Callable[..., Any]
    default_font: Any
    layout: layout_builders.WindowLayout
    main_frame: Any
    main_paned: Any
    left_frame: Any
    left_content: Any
    log: Callable[[str], None]
    tooltip: Callable[..., None]


def build_window_context(
    *,
    log_error: Callable[[str, Any], None],
    get_icon_file: Callable[[str], str],
) -> WindowContext:
    window = tk.Tk()
    window.report_callback_exception = build_tk_error_handler(
        log_error,
        "Tkinter 回调异常",
    )

    window_setup_result = window_setup.setup_main_window(
        window,
        get_icon_file=get_icon_file,
    )
    get_preferred_font = window_setup_result.get_preferred_font
    default_font = get_preferred_font()

    layout = layout_builders.build_main_layout(
        window,
        get_preferred_font=get_preferred_font,
    )

    macos_dark_mode = detect_macos_dark_mode()
    tooltip = partial(
        create_tooltip,
        font_getter=get_preferred_font,
        is_dark_mode=macos_dark_mode,
    )

    return WindowContext(
        window=window,
        get_preferred_font=get_preferred_font,
        default_font=default_font,
        layout=layout,
        main_frame=layout.main_frame,
        main_paned=layout.main_paned,
        left_frame=layout.left_frame,
        left_content=layout.left_content,
        log=layout.log,
        tooltip=tooltip,
    )
