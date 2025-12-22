from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.actions import shutdown_actions


@dataclass(frozen=True)
class WindowLifecycleDeps:
    window: Any
    log: Any
    thread_manager: Any
    stop_proxy_and_restore: Any
    proxy_runner: Any
    shutdown_state: shutdown_actions.ShutdownState


def bind_window_close(deps: WindowLifecycleDeps) -> None:
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
