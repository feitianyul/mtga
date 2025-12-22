from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk
from typing import Any

from modules.actions import shutdown_actions


@dataclass(frozen=True)
class FooterActionsDeps:
    left_frame: ttk.Frame
    window: Any
    log: Any
    thread_manager: Any
    stop_proxy_and_restore: Any
    proxy_runner: Any
    shutdown_state: shutdown_actions.ShutdownState


def build_footer_actions(deps: FooterActionsDeps) -> ttk.Button:
    start_button = ttk.Button(
        deps.left_frame,
        text="一键启动全部服务",
        command=deps.proxy_runner.start_all,
    )
    start_button.grid(row=1, column=0, sticky="ew", padx=5, pady=0)

    deps.window.protocol(
        "WM_DELETE_WINDOW",
        lambda: shutdown_actions.handle_window_close(
            deps=shutdown_actions.ShutdownDeps(
                window=deps.window,
                log=deps.log,
                thread_manager=deps.thread_manager,
                stop_proxy_and_restore=deps.stop_proxy_and_restore,
                proxy_runner=deps.proxy_runner,
            ),
            state=deps.shutdown_state,
        ),
    )

    return start_button
