import json
from types import SimpleNamespace

import httpx
from openai import APITimeoutError

from bubble.actions import Action, display_width, dropped_line, menu_lines
from bubble.cli import TIMEOUT_MESSAGE, WAITING, main, make_client, run_session
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


def test_long_title_is_clipped_to_eighty_columns():
    action = Action(
        kind="open_url",
        text="页面",
        title="课程站点 · " + ("很长的页面标题" * 20),
        url="https://example.com/p",
        uses_taste=True,
    )
    line = menu_lines([action])[0]
    assert display_width(line) <= 80
    assert line.endswith("  推荐先做 · 按你的 taste")
    assert "…" in line


def test_menu_marks_first_item_and_taste():
    from bubble.actions import prepare_actions

    actions, dropped = prepare_actions(PLAN["actions"], probe=lambda _url: True)
    lines = menu_lines(actions)
    assert dropped == 0
    assert lines[0] == "① 打开说明页  推荐先做 · 按你的 taste"
    assert lines[1] == "② B站搜索「CS61B Project 1」"
    assert "按你的 taste" not in lines[1]
    assert lines[2] == "③ 看一份 200 字的作业简介"
    assert all(display_width(line) <= 80 for line in lines)
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
    assert printed[0] == "正在拆分…（通常 10 秒内）"
    assert "① 打开说明页  推荐先做 · 按你的 taste" in printed
    assert "② B站搜索「CS61B Project 1」" in printed
    assert "③ 看一份 200 字的作业简介" in printed
    assert printed[-1] == "已打开。"
    assert prompts == [
        "选一条 [1-3]，回车退出 › ",
        "将打开 https://example.com/proj1  确认？[Y/n] › ",
    ]
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
    prompts = []
    answers = iter(["2", "y"])

    def probe(url: str) -> bool:
        if "bilibili" in url or "evil.com" in url:
            raise AssertionError(url)
        return True

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(answers)

    run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=probe,
        input_fn=fake_input,
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=opened.append,
    )
    expected = build_video_search_url("CS61B Project 1")
    assert prompts[-1] == f"将打开 {expected}  确认？[Y/n] › "
    assert opened == [expected]
    assert "已打开。" in printed
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
    assert all("确认？[Y/n]" not in prompt for prompt in prompts)
    assert prompts[0] == "选一条 [1-3]，回车退出 › "
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
    assert printed[0] == "正在拆分…（通常 10 秒内）"


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
    assert "① 看一份 200 字的还能看的简介  推荐先做 · 按你的 taste" in printed
    assert dropped_line(2) in printed
    assert "file:///etc/passwd" not in text


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
    assert events[0] == ("print", "正在拆分…（通常 10 秒内）")
    assert events.index("llm") < events.index("probe")
    menu_at = events.index(("print", "① 打开说明页  推荐先做 · 按你的 taste"))
    assert events.index("probe") < menu_at
    sent = client.chat.completions.calls[0]["messages"][1]["content"]
    assert "CS61B 用 sp21 版" in sent


def test_main_remember_and_missing_key(monkeypatch, capsys):
    assert main([]) == 2
    assert "bubble remember" in capsys.readouterr().out
    monkeypatch.setenv("BUBBLE_MODEL", "deepseek-chat")
    assert main(["做一个小演示"]) == 2
    captured = capsys.readouterr()
    assert captured.out.strip() == "缺少 BUBBLE_API_KEY，请参考 .env.example 配置"
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_out_of_range_prompts_once_then_waits(tmp_path):
    prompts = []
    printed = []
    answers = iter(["9", "0", ""])

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(answers)

    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(PLAN, ensure_ascii=False)]),
        probe=lambda _url: True,
        input_fn=fake_input,
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: (_ for _ in ()).throw(AssertionError("opened")),
    )
    assert code == 0
    assert printed.count("请输入 1-3") == 2


def test_no_usable_action_exits_nonzero(tmp_path):
    plan = {
        "actions": [
            {"type": "open_url", "title": "坏", "url": "file:///etc/passwd", "uses_taste": False},
            {"type": "open_url", "title": "也坏", "url": "http://example.com", "uses_taste": False},
            {"type": "shell", "title": "命令", "command": "rm -rf /", "uses_taste": False},
        ]
    }
    printed = []
    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(plan, ensure_ascii=False)]),
        probe=lambda _url: True,
        input_fn=lambda _prompt="": (_ for _ in ()).throw(AssertionError("asked")),
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: (_ for _ in ()).throw(AssertionError("opened")),
    )
    assert code == 1
    assert "这次没拆出能用的动作，换个说法再试一次？" in printed
    assert "有 2 条链接打不开，已略过" in printed
    assert "Traceback" not in "\n".join(printed)


def _timeout_client(exc: BaseException):
    class Completions:
        def create(self, **_kwargs):
            raise exc

    return SimpleNamespace(chat=SimpleNamespace(completions=Completions()))


def test_fallback_confirms_the_homepage_url(tmp_path):
    deep = "https://sp21.datastructur.es/materials/proj/proj1/proj1"
    home = "https://sp21.datastructur.es/"
    plan = {
        "actions": [
            {
                "type": "open_url",
                "title": "CS61B sp21 · Project 1 说明页",
                "url": deep,
                "uses_taste": True,
            },
            {"type": "brief", "title": "作业", "text": "简介正文", "uses_taste": False},
            {"type": "brief", "title": "备选", "text": "另一段", "uses_taste": False},
        ]
    }
    opened = []
    prompts = []
    printed = []
    answers = iter(["1", ""])

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(answers)

    def probe(url):
        return url == home

    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=FakeClient([json.dumps(plan, ensure_ascii=False)]),
        probe=probe,
        input_fn=fake_input,
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=opened.append,
    )
    assert code == 0
    assert "① 打开 首页  推荐先做 · 按你的 taste · 原页面打不开，已换成首页" in printed
    assert deep not in "\n".join(printed)
    assert prompts[1] == f"将打开 {home}  确认？[Y/n] › "
    assert opened == [home]


def test_llm_timeout_prints_one_chinese_sentence(tmp_path):
    printed = []
    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=_timeout_client(httpx.ReadTimeout("timed out")),
        probe=lambda _url: (_ for _ in ()).throw(AssertionError("probed")),
        input_fn=lambda _prompt="": (_ for _ in ()).throw(AssertionError("asked")),
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: (_ for _ in ()).throw(AssertionError("opened")),
    )
    assert code == 1
    assert printed == [WAITING, TIMEOUT_MESSAGE]
    assert "Traceback" not in "\n".join(printed)
    assert "这次没拆出能用的动作" not in "\n".join(printed)


def test_api_timeout_error_uses_the_same_sentence(tmp_path):
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    printed = []
    code = run_session(
        "完成 CS61B Project 1",
        config=_config(tmp_path),
        client=_timeout_client(APITimeoutError(request)),
        probe=lambda _url: True,
        input_fn=lambda _prompt="": "",
        print_fn=lambda *args, **_kwargs: printed.append(args[0] if args else ""),
        opener=lambda _url: None,
    )
    assert code == 1
    assert printed == [WAITING, TIMEOUT_MESSAGE]


def test_make_client_uses_config_timeout(monkeypatch, tmp_path):
    seen = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    make_client(_config(tmp_path))
    assert seen["timeout"] == 45.0
    assert seen["base_url"] == "https://api.deepseek.com"
    assert seen["api_key"] == "sk-test"
