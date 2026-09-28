"""Homepage fallback when a safe open_url cannot be opened. check_url is mocked."""

import json
from pathlib import Path

from bubble.actions import menu_lines, process
from bubble.safety import site_homepage

DEEP = "https://sp21.datastructur.es/materials/proj/proj1/proj1"
HOME = "https://sp21.datastructur.es/"


def _raw(url: str, *, text: str = "作业") -> str:
    return json.dumps(
        {"actions": [{"kind": "open_url", "text": text, "url": url}]},
        ensure_ascii=False,
    )


def _log() -> str:
    path = Path.home() / ".bubble" / "log"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def test_site_homepage_keeps_port_and_skips_root():
    assert site_homepage(DEEP) == HOME
    assert site_homepage("https://example.com:8443/a/b") == "https://example.com:8443/"
    assert site_homepage("https://example.com:443/a") == "https://example.com/"
    assert site_homepage(HOME) is None
    assert site_homepage("https://example.com") is None
    assert site_homepage("https://example.com/?q=1") == "https://example.com/"
    assert site_homepage("javascript:alert(1)") is None
    assert site_homepage("https://user@evil.example/path") is None


def test_unreachable_page_falls_back_to_homepage():
    calls: list[str] = []

    def check(url: str) -> bool:
        calls.append(url)
        return url == HOME

    kept, dropped = process(_raw(DEEP), check)
    assert dropped == 0
    assert calls == [DEEP, HOME]
    assert len(kept) == 1
    assert kept[0].url == HOME
    assert kept[0].title == "首页"
    assert kept[0].fell_back is True
    line = menu_lines(kept)[0]
    assert "打开 首页" in line
    assert "原页面打不开，已换成首页" in line
    assert "推荐先做" in line
    log = _log()
    assert "退回首页" in log
    assert "计数 退回首页 1" in log
    assert "计数 丢弃" not in log
    assert "丢弃 open_url" not in log


def test_homepage_also_unreachable_is_discarded():
    calls: list[str] = []

    def check(url: str) -> bool:
        calls.append(url)
        return False

    kept, dropped = process(
        json.dumps(
            {
                "actions": [
                    {"kind": "open_url", "text": "官网", "url": DEEP},
                    {"kind": "brief", "text": "简介"},
                ]
            },
            ensure_ascii=False,
        ),
        check,
    )
    assert [action.kind for action in kept] == ["brief"]
    assert dropped == 1
    assert calls == [DEEP, HOME]
    log = _log()
    assert "丢弃 open_url unreachable" in log
    assert "计数 丢弃 1" in log
    assert "计数 退回首页" not in log
    assert "原页面打不开" not in "\n".join(menu_lines(kept))


def test_root_url_is_not_probed_twice():
    calls: list[str] = []

    def check(url: str) -> bool:
        calls.append(url)
        return False

    kept, dropped = process(_raw(HOME, text="首页"), check)
    assert kept == []
    assert dropped == 1
    assert calls == [HOME]
    assert "计数 丢弃 1" in _log()
    assert "计数 退回首页" not in _log()


def test_unsafe_url_is_not_fetched_and_has_no_homepage():
    calls: list[str] = []

    def check(url: str) -> bool:
        calls.append(url)
        return True

    kept, dropped = process(_raw("javascript:alert(1)"), check)
    assert kept == []
    assert dropped == 1
    assert calls == []
    assert "计数 丢弃 1" in _log()
    assert "退回首页" not in _log()
