"""Turn model JSON into actions Bubble is willing to show or run.

Nothing here runs a shell command. Unknown types are dropped. A video_search
URL from the model is ignored; the program builds the Bilibili link itself.
"""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

from bubble.safety import (
    build_bilibili_url,
    is_official_video_search,
    is_safe_https_url,
    log_discard,
    site_homepage,
)

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
MAX_ACTIONS = 3
_ALLOWED = {"open_url", "video_search", "brief"}


@dataclass(frozen=True)
class Action:
    kind: str
    text: str
    url: str | None = None
    uses_taste: bool = False
    keyword: str = ""
    title: str = ""
    fell_back: bool = False

    @property
    def type(self) -> str:
        return self.kind


def _load_items(raw: str) -> list:
    if not isinstance(raw, str) or not raw.strip():
        return []
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    items = data.get("actions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return items


def _kind_of(item: dict) -> str | None:
    kind = item.get("kind", item.get("type"))
    if isinstance(kind, str) and kind in _ALLOWED:
        return kind
    return None


def _text_and_title(item: dict) -> tuple[str, str]:
    raw_text = item.get("text") if isinstance(item.get("text"), str) else ""
    raw_title = item.get("title") if isinstance(item.get("title"), str) else ""
    text = raw_text if raw_text else raw_title
    title = raw_title if raw_title else raw_text
    return text, title


def _collect(items: list, check_url: Callable[[str], bool]) -> tuple[list[Action], int]:
    kept: list[Action] = []
    dropped = 0
    fell_back = 0
    for item in items:
        if len(kept) == MAX_ACTIONS:
            break
        if not isinstance(item, dict):
            log_discard("discard non-object action")
            continue
        kind = _kind_of(item)
        uses_taste = item.get("uses_taste") is True
        text, title = _text_and_title(item)
        if kind == "brief":
            if not text.strip():
                log_discard("discard brief without text")
                continue
            kept.append(
                Action(kind="brief", text=text.strip(), title=title.strip(), uses_taste=uses_taste)
            )
            continue
        if kind == "video_search":
            keyword = item.get("keyword")
            if not isinstance(keyword, str) or not keyword.strip():
                log_discard("discard video_search without keyword")
                continue
            cleaned = keyword.strip()
            url = build_bilibili_url(cleaned)
            if not is_official_video_search(url):
                log_discard(f"discard video_search malformed: {url}")
                continue
            kept.append(
                Action(
                    kind="video_search",
                    text=text,
                    title=title,
                    url=url,
                    keyword=cleaned,
                    uses_taste=uses_taste,
                )
            )
            continue
        if kind == "open_url":
            url = item.get("url")
            if not isinstance(url, str) or not is_safe_https_url(url):
                dropped += 1
                log_discard(f"丢弃 open_url unsafe: {url!r}")
                continue
            if check_url(url):
                kept.append(
                    Action(
                        kind="open_url",
                        text=text or title or "链接",
                        title=title or text or "链接",
                        url=url,
                        uses_taste=uses_taste,
                    )
                )
                continue
            home = site_homepage(url)
            if home is not None and check_url(home):
                fell_back += 1
                log_discard(f"退回首页 {url} -> {home}")
                kept.append(
                    Action(
                        kind="open_url",
                        text="首页",
                        title="首页",
                        url=home,
                        uses_taste=uses_taste,
                        fell_back=True,
                    )
                )
                continue
            dropped += 1
            log_discard(f"丢弃 open_url unreachable: {url}")
            continue
        log_discard(f"discard unknown type: {item.get('kind', item.get('type'))!r}")
    if fell_back:
        log_discard(f"计数 退回首页 {fell_back}")
    if dropped:
        log_discard(f"计数 丢弃 {dropped}")
        log_discard(dropped_line(dropped))
    return kept, dropped


def process(raw: str, check_url: Callable[[str], bool]) -> tuple[list[Action], int]:
    """Parse model output. Malformed JSON yields no actions and does not raise."""
    try:
        items = _load_items(raw)
    except (TypeError, ValueError):
        return [], 0
    return _collect(items, check_url)


def prepare_actions(
    raw_actions: list[dict],
    probe: Callable[[str], bool],
) -> tuple[list[Action], int]:
    """Same filtering as ``process``, for an already parsed action list."""
    return _collect(raw_actions, probe)


def display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return width


def _clip(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if display_width(text) <= width:
        return text
    ellipsis = "…"
    limit = width - display_width(ellipsis)
    if limit <= 0:
        return ellipsis
    kept: list[str] = []
    used = 0
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        if used + char_width > limit:
            break
        kept.append(char)
        used += char_width
    return "".join(kept) + ellipsis


def action_body(action: Action) -> str:
    if action.kind == "open_url":
        title = (action.title or action.text or "链接").strip()
        if title.startswith("打开"):
            return title
        return f"打开 {title}"
    if action.kind == "video_search":
        keyword = (action.keyword or action.text or "视频").strip()
        return f"B站搜索「{keyword}」"
    topic = (action.title or action.text or "这个").strip()
    topic = topic.removeprefix("看一份 200 字的").removesuffix("简介").strip() or "这个"
    return f"看一份 200 字的{topic}简介"


def menu_lines(actions: list[Action]) -> list[str]:
    lines: list[str] = []
    for index, action in enumerate(actions):
        tags: list[str] = []
        if index == 0:
            tags.append("推荐先做")
        if action.uses_taste:
            tags.append("按你的 taste")
        if action.fell_back:
            tags.append("原页面打不开，已换成首页")
        suffix = f"  {' · '.join(tags)}" if tags else ""
        number = CIRCLED[index] if index < len(CIRCLED) else f"{index + 1}."
        prefix = f"{number} "
        room = 80 - display_width(prefix) - display_width(suffix)
        body = _clip(action_body(action), room)
        lines.append(prefix + body + suffix)
    return lines


def dropped_line(count: int) -> str:
    return f"有 {count} 条链接打不开，已略过"


def execute(action: Action, open_browser: Callable[[str], object], confirm: bool = False) -> object:
    """Run one action. ``open_browser`` is injected; brief text is printed, never executed."""
    if action.kind == "brief":
        print(action.text)
        return None
    if not confirm or not action.url:
        return None
    if action.kind == "open_url" and not is_safe_https_url(action.url):
        return None
    if action.kind == "video_search" and not is_official_video_search(action.url):
        return None
    return open_browser(action.url)


def perform(action: Action, *, opener: Callable[[str], None], writer: Callable[[str], None]) -> None:
    """Test helper: brief goes to ``writer`` instead of stdout."""
    if action.kind == "brief":
        writer(action.text)
        return
    execute(action, opener, True)
