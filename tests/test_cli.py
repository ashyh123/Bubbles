import json

from bubble.actions import dropped_line, menu_lines
from bubble.cli import main, run_session
from bubble.config import Config
from bubble.safety import build_video_search_url
from tests.fakes import FakeClient

PLAN = {
    "actions": [
        {
            "type": "open_url",
            "title": "打开说明页",
            "url": "https://example.com/proj1",
            "uses_taste": True,
        },
        {
            "type": "video_search",
            "title": "B站搜索「CS61B Project 1」",
            "keyword": "CS61B Project 1",
            "url": "https://bilibili.com.evil.com/all?keyword=phishing",
            "uses_taste": False,
        },
        {
            "type": "brief",
            "title": "作业简介",
            "text": "Project 1 要求实现一个数据结构。这里只做介绍，不给实现。",
            "uses_taste": False,
        },
    ]
}


def _config(tmp_path, taste="CS61B 用 sp21 版\n"):
    path = tmp_path / "taste.md"
    path.write_text(taste, encoding="utf-8")
    return Config(
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        reasoning_effort="low",
        taste_path=path,
    )


def test_menu_marks_first_item_and_taste():
    from bubble.actions import prepare_actions

    actions, dropped = prepare_actions(PLAN["actions"], probe=lambda _url: True)
    lines = menu_lines(actions)
    assert dropped == 0
    assert lines[0] == "① 打开说明页 （推荐先做 · 按你的 taste）"
    assert lines[1] == "② B站搜索「CS61B Project 1」"
    assert "按你的 taste" not in lines[1]
    assert lines[2] == "③ 作业简介"
    assert actions[1].url == build_video_search_url("CS61B Project 1")


def test_session_lists_actions_and_asks_before_opening(tmp_path):
    opened = []
    prompts = []
    printed = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        if len(prompts) == 1:
            return "1"
        return ""

    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=lambda url: url.startswith("https://example.com"),
        input_fn=fake_input,
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=opened.append,
    )
    assert code == 0
    assert printed[0] == "正在拆分…"
    assert printed[1:] == [
        "① 打开说明页 （推荐先做 · 按你的 taste）",
        "② B站搜索「CS61B Project 1」",
        "③ 作业简介",
        "https://example.com/proj1",
    ]
    assert prompts == ["选一条（回车退出）：", "确认？[Y/n] ", "选一条（回车退出）："]
    assert opened == ["https://example.com/proj1"]
    assert "bilibili.com.evil.com" not in "\n".join(printed)


def test_declining_confirmation_does_not_open(tmp_path):
    opened = []
    answers = iter(["2", "n", ""])
    run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=lambda _url: True,
        input_fn=lambda _prompt="": next(answers),
        print_fn=lambda *_args, **_kwargs: None,
        opener=opened.append,
    )
    assert opened == []


def test_video_search_confirmation_prints_program_url_not_model_url(tmp_path):
    opened = []
    printed = []
    answers = iter(["2", "y", ""])

    def probe(url: str) -> bool:
        if "bilibili" in url or "evil.com" in url:
            raise AssertionError(url)
        return True

    run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=probe,
        input_fn=lambda _prompt="": next(answers),
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=opened.append,
    )
    expected = build_video_search_url("CS61B Project 1")
    assert expected in printed
    assert opened == [expected]
    assert all("evil.com" not in line for line in printed)


def test_brief_prints_text_without_url_confirmation(tmp_path):
    prompts = []
    printed = []
    answers = iter(["3", ""])

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(answers)

    run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=lambda _url: True,
        input_fn=fake_input,
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: (_ for _ in ()).throw(AssertionError("browser opened")),
    )
    assert "确认？[Y/n] " not in prompts
    assert prompts[0] == "选一条（回车退出）："
    assert printed[-1] == PLAN["actions"][2]["text"]


def test_enter_exits(tmp_path):
    opened = []
    printed = []
    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=lambda _url: True,
        input_fn=lambda _prompt="": "",
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=opened.append,
    )
    assert code == 0
    assert opened == []
    assert printed[0] == "正在拆分…"


def test_dead_links_are_hidden_and_counted(tmp_path):
    plan = {
        "actions": [
            {
                "type": "open_url",
                "title": "不要显示这个坏链接",
                "url": "file:///etc/passwd",
                "uses_taste": False,
            },
            {
                "type": "open_url",
                "title": "打不开的官网",
                "url": "https://example.com/missing",
                "uses_taste": False,
            },
            {
                "type": "brief",
                "title": "还能看的简介",
                "text": "简介正文",
                "uses_taste": True,
            },
        ]
    }
    printed = []
    run_session(
        "准备操作系统期中",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(plan, ensure_ascii=False)]),
        probe=lambda _url: False,
        input_fn=lambda _prompt="": "",
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: (_ for _ in ()).throw(AssertionError("opened")),
    )
    text = "\n".join(printed)
    assert "不要显示这个坏链接" not in text
    assert "file:///etc/passwd" not in text
    assert "https://example.com/missing" not in text
    assert "打不开的官网" not in text
    assert printed[1] == "① 还能看的简介 （推荐先做 · 按你的 taste）"
    assert dropped_line(2) in printed


def test_probe_happens_before_the_menu_is_shown(tmp_path):
    events = []

    def probe(url):
        events.append("probe")
        assert url == "https://example.com/proj1"
        return True

    client = FakeClient([json.dumps(PLAN, ensure_ascii=False)])
    original = client.chat.completions.create

    def create(**kwargs):
        events.append("llm")
        return original(**kwargs)

    client.chat.completions.create = create
    printed = []

    def print_fn(*args, **_kwargs):
        printed.append(args[0] if args else "")
        events.append(("print", printed[-1]))

    run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path, taste="CS61B 用 sp21 版"),
        client=client,
        probe=probe,
        input_fn=lambda _prompt="": "",
        print_fn=print_fn,
        opener=lambda _url: None,
    )
    assert events[0] == ("print", "正在拆分…")
    assert events.index("llm") < events.index("probe")
    menu_at = events.index(("print", "① 打开说明页 （推荐先做 · 按你的 taste）"))
    assert events.index("probe") < menu_at
    sent = client.chat.completions.calls[0]["messages"][1]["content"]
    assert "CS61B 用 sp21 版" in sent


def test_main_remember_and_missing_key(monkeypatch, capsys):
    assert main([]) == 2
    assert "bubble remember" in capsys.readouterr().out
    monkeypatch.setenv("BUBBLE_MODEL", "deepseek-chat")
    assert main(["做一个小演示"]) == 2
    assert "BUBBLE_API_KEY" in capsys.readouterr().err
