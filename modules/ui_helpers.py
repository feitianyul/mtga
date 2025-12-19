from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont
from types import TracebackType


def build_tk_error_handler(
    log_error: Callable[..., None],
    message: str,
) -> Callable[[type[BaseException], BaseException, TracebackType | None], None]:
    def handler(exc: type[BaseException], val: BaseException, tb: TracebackType | None) -> None:
        log_error(message, exc_info=(exc, val, tb))

    return handler


def build_text_logger(
    log_text: tk.Text,
    *,
    print_func: Callable[[str], None] | None = None,
) -> Callable[[str], None]:
    printer = print_func or print

    def log(message: str) -> None:
        formatted_message = message.replace("\\n", "\n")
        log_text.insert(tk.END, f"{formatted_message}\n")
        log_text.see(tk.END)
        log_text.update()
        try:
            printer(formatted_message)
        except UnicodeEncodeError:
            fallback = formatted_message.encode("unicode_escape").decode("ascii", errors="replace")
            printer(fallback)

    return log


def create_tooltip(
    widget: tk.Widget,
    text: str,
    *,
    font_getter: Callable[..., tkfont.Font],
    is_dark_mode: bool,
    wraplength: int = 300,
) -> None:
    tooltip_window: tk.Toplevel | None = None
    bg_color = "#2C2C2E" if is_dark_mode else "lightyellow"
    fg_color = "#F5F5F7" if is_dark_mode else "black"

    def on_enter(event) -> None:
        nonlocal tooltip_window
        tooltip_window = tk.Toplevel()
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        tooltip_window.configure(bg=bg_color, relief="solid", bd=1, highlightthickness=0)
        label = tk.Label(
            tooltip_window,
            text=text,
            bg=bg_color,
            fg=fg_color,
            font=font_getter(size=9),
            wraplength=wraplength,
        )
        label.pack()

    def on_leave(_event) -> None:
        nonlocal tooltip_window
        if tooltip_window:
            tooltip_window.destroy()
            tooltip_window = None

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def center_window(toplevel: tk.Toplevel | tk.Tk) -> None:
    toplevel.withdraw()
    toplevel.update_idletasks()
    width = max(toplevel.winfo_width(), toplevel.winfo_reqwidth())
    height = max(toplevel.winfo_height(), toplevel.winfo_reqheight())
    x = (toplevel.winfo_screenwidth() // 2) - (width // 2)
    y = (toplevel.winfo_screenheight() // 2) - (height // 2)
    toplevel.geometry(f"+{x}+{y}")
    toplevel.deiconify()
