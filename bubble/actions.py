"""Turn model JSON into actions Bubble is willing to show or run.

Nothing here invokes a shell. Unknown types are dropped. A video_search URL
supplied by the model is ignored; the program builds the Bilibili link itself.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bubble.safety import (
    build_video_search_url,
    is_official_video_search,
    is_safe_https_url,
    log_discard,
)

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


@dataclass(frozen=True)
class Action:
    type: str
    title: str
    uses_taste: bool
    url: str = ""
    keyword: str = ""
    text: str = ""


def _title(item: dict, fallback: str) -> str:
    title = item.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return fallback


def prepare_actions(
    raw_actions: list[dict],
    probe: Callable[[str], bool],
) -> tuple[list[Action], int]:
    """Validate actions before they are shown.

    ``probe`` is called only for a syntactically safe open_url. video_search
    never calls it. The returned count is how many open_url links were dropped.
    """
    kept: list[Action] = []
    dropped_links = 0
    for item in raw_actions:
        if not isinstance(item, dict):
            log_discard("discard non-object action")
            continue
        kind = item.get("type")
        uses_taste = item.get("uses_taste") is True
        if kind == "open_url":
            url = item.get("url")
            if not isinstance(url, str) or not is_safe_https_url(url):
                dropped_links += 1
                log_discard(f"discard open_url unsafe: {url!r}")
                continue
            if not probe(url):
                dropped_links += 1
                log_discard(f"discard open_url unreachable: {url}")
                continue
            kept.append(
                Action(
                    type="open_url",
                    title=_title(item, "打开链接"),
                    uses_taste=uses_taste,
                    url=url,
                )
            )
            continue
        if kind == "video_search":
            keyword = item.get("keyword")
            if not isinstance(keyword, str) or not keyword.strip():
                log_discard("discard video_search without keyword")
                continue
            cleaned = keyword.strip()
            url = build_video_search_url(cleaned)
            if not is_official_video_search(url):
                log_discard(f"discard video_search malformed: {url}")
                continue
            kept.append(
                Action(
                    type="video_search",
                    title=_title(item, f"B站搜索「{cleaned}」"),
                    uses_taste=uses_taste,
                    url=url,
                    keyword=cleaned,
                )
            )
            continue
        if kind == "brief":
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                log_discard("discard brief without text")
                continue
            kept.append(
                Action(
                    type="brief",
                    title=_title(item, "简介"),
                    uses_taste=uses_taste,
                    text=text.strip(),
                )
            )
            continue
        log_discard(f"discard unknown type: {kind!r}")
    return kept, dropped_links


def menu_lines(actions: list[Action]) -> list[str]:
    lines: list[str] = []
    for index, action in enumerate(actions):
        tags: list[str] = []
        if index == 0:
            tags.append("推荐先做")
        if action.uses_taste:
            tags.append("按你的 taste")
        suffix = f" （{' · '.join(tags)}）" if tags else ""
        number = CIRCLED[index] if index < len(CIRCLED) else f"{index + 1}."
        lines.append(f"{number} {action.title}{suffix}")
    return lines


def dropped_line(count: int) -> str:
    return f"有 {count} 条链接打不开，已略过"


def perform(action: Action, *, opener: Callable[[str], None], writer: Callable[[str], None]) -> None:
    """Run one confirmed action. Only a validated URL is passed to ``opener``."""
    if action.type == "brief":
        writer(action.text)
        return
    if action.type == "open_url" and is_safe_https_url(action.url):
        opener(action.url)
        return
    if action.type == "video_search" and is_official_video_search(action.url):
        opener(action.url)
