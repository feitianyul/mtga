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

_LIGHT_STYLE = """
<style>
body.md-body {
    font-family: "Microsoft YaHei", "PingFang SC", "Helvetica", sans-serif;
    font-size: 12px;
    color: #1f2328;
    background-color: #ffffff;
    line-height: 1.5;
    margin: 0;
    padding: 12px;
}
.md-body a { color: #0969da; }
.md-body a:hover { text-decoration: underline; }
.md-body pre, .md-body code {
    background-color: #f6f8fa;
    border-color: #d0d7de;
}
</style>
"""

_DARK_STYLE = """
<style>
body.md-body {
    font-family: "Microsoft YaHei", "PingFang SC", "Helvetica", sans-serif;
    font-size: 12px;
    color: #f5f5f7;
    background-color: #1c1c1e;
    line-height: 1.6;
    margin: 0;
    padding: 12px;
}
.md-body a { color: #4da0ff; }
.md-body a:hover { text-decoration: underline; }
.md-body pre, .md-body code {
    background-color: #2c2c2e;
    border-color: #3a3a3c;
}
.md-body del { color: #a1a1a6; }
</style>
"""


class StrikeThroughExtension(Extension):
    """扩展 Markdown 语法以支持 ~~删除线~~。"""

    def extendMarkdown(self, md):  # noqa: D401
        pattern = SimpleTagInlineProcessor(r"(~{2})(.+?)(~{2})", "del")
        md.inlinePatterns.register(pattern, "strikethrough", 175)


def convert_markdown_to_html(markdown_text: str | None, *, dark_mode: bool = False) -> str:
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
                _DARK_STYLE if dark_mode else _LIGHT_STYLE,
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
                _DARK_STYLE if dark_mode else _LIGHT_STYLE,
                "</head><body class='md-body'><pre>",
                fallback_text,
                "</pre></body></html>",
            )
        )


__all__ = ["convert_markdown_to_html"]
