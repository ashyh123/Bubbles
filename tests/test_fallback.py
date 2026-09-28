"""Homepage fallback when a safe open_url cannot be opened. check_url is mocked."""

import json
from pathlib import Path

from bubble.actions import Action, action_body, clip_brief, homepage_label, menu_lines, process
from bubble.safety import log_discard, site_homepage

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
    assert kept[0].title == "sp21.datastructur.es · 首页"
    assert kept[0].fell_back is True
    line = menu_lines(kept)[0]
    assert "打开 sp21.datastructur.es · 首页" in line
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


def test_homepage_label_uses_course_then_host():
    home = "https://www.example.com/"
    assert homepage_label("CS61B sp21 · Project 1 说明页", home) == "CS61B sp21 · 首页"
    assert homepage_label("打开 CS61B · 作业", home) == "CS61B · 首页"
    assert homepage_label("官网", home) == "example.com · 首页"
    assert homepage_label("", "https://sp21.datastructur.es/materials/x") == "sp21.datastructur.es · 首页"


def test_brief_clips_to_two_hundred_characters():
    early = "开头。" + ("甲" * 300)
    assert clip_brief(early) == early[:200] + "…"
    windowed = ("甲" * 150) + "！" + ("乙" * 100)
    assert clip_brief(windowed) == ("甲" * 150) + "！"
    assert len(clip_brief(windowed)) >= 150
    plain = "乙" * 250
    assert clip_brief(plain) == ("乙" * 200) + "…"
    assert clip_brief("短句。") == "短句。"


def test_brief_breaks_on_semicolon_after_an_early_period():
    fullwidth = "前言。" + ("甲" * 160) + "；" + ("乙" * 80)
    assert clip_brief(fullwidth) == "前言。" + ("甲" * 160) + "；"
    assert len(clip_brief(fullwidth)) >= 150
    halfwidth = "前言。" + ("甲" * 160) + ";" + ("乙" * 80)
    assert clip_brief(halfwidth).endswith(";")
    assert "乙" not in clip_brief(halfwidth)
    assert len(clip_brief(halfwidth)) >= 150


def test_brief_hard_cuts_when_the_break_is_under_150():
    early = "开头。" + ("甲" * 300)
    assert clip_brief(early) == early[:200] + "…"
    assert len(clip_brief(early)) == 201
    short_semi = ("甲" * 40) + "；" + ("乙" * 300)
    assert clip_brief(short_semi) == short_semi[:200] + "…"
    assert not clip_brief(short_semi).endswith("；")


def test_brief_menu_spaces_chinese_and_english():
    action = Action(kind="brief", text="正文", title="rebase原理")
    assert action_body(action) == "看一份 200 字的 rebase 原理简介"


def test_log_follows_taste_directory(monkeypatch, tmp_path):
    taste = tmp_path / "box" / "taste.md"
    monkeypatch.setenv("BUBBLE_TASTE_PATH", str(taste))
    log_discard("计数 丢弃 1")
    assert "计数 丢弃 1" in (tmp_path / "box" / "log").read_text(encoding="utf-8")


def test_log_path_env_overrides_taste_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("BUBBLE_TASTE_PATH", str(tmp_path / "taste.md"))
    custom = tmp_path / "other" / "events.log"
    monkeypatch.setenv("BUBBLE_LOG_PATH", str(custom))
    log_discard("退回首页")
    assert "退回首页" in custom.read_text(encoding="utf-8")
