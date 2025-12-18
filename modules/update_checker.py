"""封装 GitHub 最新版本查询与版本号比较逻辑。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

import requests

_SEMVER_PATTERN = re.compile(r"v?(?P<version>\d+(?:\.\d+)*)", re.IGNORECASE)


@dataclass(slots=True)
class HtmlFontOptions:
    family: str | None = None
    size: int | None = None
    weight: str | None = None


@dataclass(slots=True)
class ReleaseInfo:
    """GitHub 最新发行版的核心信息。"""

    version_label: str | None
    release_notes: str
    release_url: str


def render_markdown_via_github_api(
    markdown_text: str | None,
    *,
    repo: str,
    timeout: int = 10,
    user_agent: str | None = None,
    font: HtmlFontOptions | None = None,
) -> str:
    """调用 GitHub /markdown API 渲染 Markdown 为 HTML。

    说明：
    - 该接口返回的是 HTML 片段；这里会包装成一个完整 HTML 文档，便于 GUI 直接 load_html。
    - 可选注入仅与字体相关的最小 CSS（用于沿用 GUI 的全局字体设置）。
    - 渲染失败时会降级为 <pre> 纯文本。
    """
    safe_source = markdown_text or ""

    font_family = font.family if font else None
    font_size = font.size if font else None
    font_weight = font.weight if font else None

    escaped_family = (font_family or "").replace('"', r"\"").strip()
    font_stack = (
        f'"{escaped_family}", "Maple Mono NF CN", "Microsoft YaHei UI", "Microsoft YaHei", '
        '"PingFang SC", "Hiragino Sans GB", "Segoe UI", "Arial", sans-serif'
        if escaped_family
        else '"Maple Mono NF CN", "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", '
        '"Hiragino Sans GB", "Segoe UI", "Arial", sans-serif'
    )
    css_rules: list[str] = []
    if font_family:
        css_rules.append(f"font-family: {font_stack};")
    if font_size:
        css_rules.append(f"font-size: {int(font_size)}px;")
    if font_weight:
        css_rules.append(f"font-weight: {font_weight};")
    base_style = (
        f"<style>body{{{''.join(css_rules)}}}</style>" if css_rules else ""
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    if user_agent:
        headers["User-Agent"] = user_agent

    try:
        response = requests.post(
            "https://api.github.com/markdown",
            json={"text": safe_source, "mode": "gfm", "context": repo},
            timeout=timeout,
            headers=headers,
        )
        if response.status_code == requests.codes.ok:  # type: ignore[attr-defined]
            rendered_fragment = response.text or ""
            return "".join(
                (
                    "<html><head><meta charset='utf-8'>",
                    base_style,
                    "</head><body>",
                    rendered_fragment,
                    "</body></html>",
                )
            )
    except requests.RequestException:
        pass

    return "".join(
        (
            "<html><head><meta charset='utf-8'>",
            base_style,
            "</head><body><pre>",
            html.escape(safe_source),
            "</pre></body></html>",
        )
    )


def _normalize_version_tuple(version_text: str | None) -> tuple[int, ...]:
    """Convert 版本字符串为整数元组，便于比较。"""
    if not version_text:
        return ()
    match = _SEMVER_PATTERN.search(version_text.strip())
    if not match:
        return ()
    numeric_part = match.group("version").split("-")[0]
    tokens: list[int] = []
    for chunk in numeric_part.split("."):
        digits = re.match(r"\d+", chunk)
        if not digits:
            continue
        tokens.append(int(digits.group()))
    return tuple(tokens)


def extract_version_label(text: str | None) -> str | None:
    """从标题或标签中抓取形如 vX.Y.Z 的片段。"""
    if not text:
        return None
    match = _SEMVER_PATTERN.search(text.strip())
    if not match:
        return None
    version = match.group(0)
    if not version.lower().startswith("v"):
        version = f"v{match.group('version')}"
    return version


def is_remote_version_newer(remote_version: str | None, local_version: str | None) -> bool:
    """比较远程与本地版本号，先看主版本，若相同则比较次版本。"""
    remote_tuple = _normalize_version_tuple(remote_version)
    local_tuple = _normalize_version_tuple(local_version)
    if not remote_tuple:
        return False
    if not local_tuple:
        return True
    major_remote = remote_tuple[0]
    major_local = local_tuple[0]
    if major_remote == major_local:
        return remote_tuple > local_tuple
    return major_remote > major_local


def fetch_latest_release(
    repo: str,
    *,
    timeout: int = 10,
    user_agent: str | None = None,
    font: HtmlFontOptions | None = None,
) -> ReleaseInfo:
    """从 GitHub API 获取 latest 发行版信息。"""
    if not repo:
        raise ValueError("repo 不能为空")
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github+json"}
    if user_agent:
        headers["User-Agent"] = user_agent

    response = requests.get(api_url, timeout=timeout, headers=headers)
    if response.status_code != requests.codes.ok:  # type: ignore[attr-defined]
        raise RuntimeError(f"GitHub 返回 {response.status_code}")

    data = response.json()
    version_label = extract_version_label(data.get("name")) or extract_version_label(
        data.get("tag_name")
    )
    release_notes = render_markdown_via_github_api(
        data.get("body") or "",
        repo=repo,
        timeout=timeout,
        user_agent=user_agent,
        font=font,
    )
    release_url = data.get("html_url") or ""
    return ReleaseInfo(
        version_label=version_label,
        release_notes=release_notes,
        release_url=release_url,
    )


__all__ = [
    "HtmlFontOptions",
    "ReleaseInfo",
    "extract_version_label",
    "is_remote_version_newer",
    "fetch_latest_release",
    "render_markdown_via_github_api",
]
