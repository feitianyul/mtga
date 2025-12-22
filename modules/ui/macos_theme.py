from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from typing import Any

try:
    if sys.platform == "darwin":
        import Cocoa  # pyright: ignore[reportMissingImports]
        import Foundation  # pyright: ignore[reportMissingImports]
        import objc  # pyright: ignore[reportMissingImports]
    else:
        Cocoa = None
        Foundation = None
        objc = None
except ImportError:
    Cocoa = None
    Foundation = None
    objc = None

NSDistributedNotificationCenter = (
    getattr(Cocoa, "NSDistributedNotificationCenter", None) if Cocoa else None
)
NSObject = getattr(Foundation, "NSObject", None) if Foundation else None

_THEME_OBSERVER_CLASS_HOLDER: dict[str, type[Any] | None] = {"cls": None}


def detect_macos_dark_mode() -> bool:
    if sys.platform != "darwin":
        return False

    apple_script = (
        'tell application "System Events" to tell appearance preferences to get dark mode'
    )
    commands = [
        (["osascript", "-e", apple_script], {"true"}),
        (["defaults", "read", "-g", "AppleInterfaceStyle"], {"dark"}),
    ]
    for cmd, expected in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except (FileNotFoundError, OSError):
            continue
        output = (result.stdout or "").strip().lower()
        if result.returncode == 0 and output in expected:
            return True
    return False


def register_macos_theme_observer(
    callback: Callable[[], None],
) -> tuple[Any | None, Any | None]:
    if (
        sys.platform != "darwin"
        or NSDistributedNotificationCenter is None
        or NSObject is None
        or objc is None
    ):
        return None, None

    observer_class = _THEME_OBSERVER_CLASS_HOLDER["cls"]
    if observer_class is None:

        class ThemeObserver(NSObject):  # type: ignore[misc]
            def initWithCallback_(self, cb):
                obj = objc.super(ThemeObserver, self).init()  # type: ignore[attr-defined]
                if obj is None:
                    return None
                obj._callback = cb
                return obj

            def themeChanged_(self, _notification):
                if getattr(self, "_callback", None):
                    self._callback()

        _THEME_OBSERVER_CLASS_HOLDER["cls"] = ThemeObserver
        observer_class = ThemeObserver

    observer = observer_class.alloc().initWithCallback_(callback)  # type: ignore[call-arg]
    center = NSDistributedNotificationCenter.defaultCenter()
    selector_factory: Any = objc.selector  # type: ignore[attr-defined]
    selector = selector_factory(  # type: ignore[call-arg]
        observer_class.themeChanged_, signature=b"v@:@"
    )
    center.addObserver_selector_name_object_(
        observer,
        selector,
        "AppleInterfaceThemeChangedNotification",
        None,
    )
    return center, observer
