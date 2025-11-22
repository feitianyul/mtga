"""提供 Markdown 渲染到 HTML 的工具函数，复用在 GUI 各处。"""

from __future__ import annotations

import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor

_MARKDOWN_BASE_EXTENSIONS = (
    "markdown.extensions.extra",
    "markdown.extensions.sane_lists",
    "markdown.extensions.smarty",
    "markdown.extensions.fenced_code",
    "markdown.extensions.tables",
    "markdown.extensions.nl2br",
)

_BASE_FALLBACK_FONTS = (
    '"Maple Mono NF CN", "Microsoft YaHei", "PingFang SC", "Helvetica", sans-serif'
)


def _escape_css_font_family(family: str | None) -> str:
    """简单转义字体名中的双引号，避免破坏 CSS。"""
    if not family:
        return ""
    return family.replace('"', r"\"")


def _build_style(
    *,
    dark_mode: bool,
    font_family: str | None,
    font_size: int | None,
    font_weight: str | None,
) -> str:
    """根据亮/暗主题和传入字体信息构造样式。"""
    escaped_family = _escape_css_font_family(font_family)
    font_stack = (
        f'"{escaped_family}", {_BASE_FALLBACK_FONTS}'
        if escaped_family
        else _BASE_FALLBACK_FONTS
    )
    font_size_css = f"{font_size}px" if font_size else "12px"
    font_weight_css = font_weight if font_weight else "normal"

    if dark_mode:
        return f"""
<style>
body.md-body {{
    font-family: {font_stack};
    font-size: {font_size_css};
    font-weight: {font_weight_css};
    color: #f5f5f7;
    background-color: #1c1c1e;
    line-height: 1.6;
    margin: 0;
    padding: 12px;
}}
.md-body a {{ color: #4da0ff; }}
.md-body a:hover {{ text-decoration: underline; }}
.md-body pre, .md-body code {{
    background-color: #2c2c2e;
    border-color: #3a3a3c;
}}
.md-body del {{ color: #a1a1a6; }}
</style>
"""

    return f"""
<style>
body.md-body {{
    font-family: {font_stack};
    font-size: {font_size_css};
    font-weight: {font_weight_css};
    color: #1f2328;
    background-color: #ffffff;
    line-height: 1.5;
    margin: 0;
    padding: 12px;
}}
.md-body a {{ color: #0969da; }}
.md-body a:hover {{ text-decoration: underline; }}
.md-body pre, .md-body code {{
    background-color: #f6f8fa;
    border-color: #d0d7de;
}}
</style>
"""


class StrikeThroughExtension(Extension):
    """扩展 Markdown 语法以支持 ~~删除线~~。"""

    def extendMarkdown(self, md):  # noqa: D401
        pattern = SimpleTagInlineProcessor(r"(~{2})(.+?)(~{2})", "del")
        md.inlinePatterns.register(pattern, "strikethrough", 175)


def convert_markdown_to_html(
    markdown_text: str | None,
    *,
    dark_mode: bool = False,
    font_family: str | None = None,
    font_size: int | None = None,
    font_weight: str | None = None,
) -> str:
    """使用 markdown 库渲染 HTML，支持删除线/粗体/链接等语法。"""
    extensions: list[str | Extension] = list(_MARKDOWN_BASE_EXTENSIONS)
    extensions.append("markdown.extensions.admonition")
    extensions.append(StrikeThroughExtension())
    try:
        html_body = markdown.markdown(
            markdown_text or "",
            extensions=extensions,
            output_format="html",
        )
        return "".join(
            (
                "<html><head>",
                _build_style(
                    dark_mode=dark_mode,
                    font_family=font_family,
                    font_size=font_size,
                    font_weight=font_weight,
                ),
                "</head><body class='md-body'>",
                html_body,
                "</body></html>",
            )
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Markdown 渲染失败，降级为纯文本: {exc}")
        fallback_source = (markdown_text or "").replace("&", "&amp;")
        fallback_text = fallback_source.replace("<", "&lt;").replace(">", "&gt;")
        return "".join(
            (
                "<html><head>",
                _build_style(
                    dark_mode=dark_mode,
                    font_family=font_family,
                    font_size=font_size,
                    font_weight=font_weight,
                ),
                "</head><body class='md-body'><pre>",
                fallback_text,
                "</pre></body></html>",
            )
        )


__all__ = ["convert_markdown_to_html"]
