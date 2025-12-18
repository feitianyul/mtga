from __future__ import annotations

import sys
from dataclasses import dataclass, field
from tkinter import font as tkfont
from tkinter import ttk
from typing import Literal

_FONT_CANDIDATES = (
    "Maple Mono NF CN",
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "PingFang SC",
    "Hiragino Sans GB",
    "Segoe UI",
    "Arial",
)


@dataclass(slots=True)
class FontManager:
    cache: dict[tuple[int, Literal["normal", "bold"]], tkfont.Font] = field(default_factory=dict)

    def get_preferred_font(
        self,
        *,
        size: int = 10,
        weight: Literal["normal", "bold"] = "normal",
    ) -> tkfont.Font:
        """返回跨平台首选字体对象，缺失时回退到默认字体。

        注意：需要在 Tk 根窗口创建之后调用（否则 tkfont.families 可能不可用）。
        """
        effective_size = size
        if sys.platform == "darwin":
            effective_size = max(size + 1, round(size * 1.15))

        key = (effective_size, weight)
        cached = self.cache.get(key)
        if cached is not None:
            print(
                f"[字体] 使用缓存字体: {cached.cget('family')} "
                f"size={cached.cget('size')} weight={cached.cget('weight')}",
            )
            return cached

        available = {name.lower(): name for name in tkfont.families()}
        chosen = None
        for candidate in _FONT_CANDIDATES:
            matched = available.get(candidate.lower())
            if matched:
                chosen = matched
                break

        if chosen is None:
            font_obj = tkfont.nametofont("TkDefaultFont").copy()
            font_obj.configure(size=effective_size, weight=weight)
        else:
            font_obj = tkfont.Font(family=chosen, size=effective_size, weight=weight)

        self.cache[key] = font_obj
        print(
            f"[字体] 选用字体: {font_obj.cget('family')} "
            f"size={font_obj.cget('size')} weight={font_obj.cget('weight')}",
        )
        return font_obj


def apply_global_font(*, root, default_font: tkfont.Font) -> None:
    """全局字体覆盖，避免 ttk 控件仍然使用系统默认字体。"""
    root.option_add("*Font", default_font)
    ttk.Style().configure(".", font=default_font)


__all__ = ["FontManager", "apply_global_font"]
