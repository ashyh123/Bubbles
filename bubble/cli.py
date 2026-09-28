"""Command-line entry: ``bubble \"想法\"`` and ``bubble remember \"文字\"``."""

from __future__ import annotations

import sys
import webbrowser
from collections.abc import Callable
from typing import Any

import httpx
from openai import OpenAIError

from bubble.actions import Action, dropped_line, menu_lines, perform, prepare_actions
from bubble.config import Config
from bubble.planner import PlanParseError, plan_actions
from bubble.safety import probe_url
from bubble.taste import TasteError, read_taste, remember

USAGE = """\
用法：
  bubble "学习想法"
  bubble remember "一句偏好"

配置从环境变量读取（见 .env.example）：
  BUBBLE_API_KEY            必填
  BUBBLE_BASE_URL           默认 https://api.deepseek.com
  BUBBLE_MODEL              必填
  BUBBLE_REASONING_EFFORT   默认 low，模型不支持时会去掉后重试
  BUBBLE_TASTE_PATH         默认 ~/.bubble/taste.md
"""


def console_main() -> None:
    raise SystemExit(main())


def make_client(config: Config) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def _parse_choice(text: str, count: int) -> int | None:
    raw = text.strip()
    if raw in "①②③④⑤⑥⑦⑧⑨⑩":
        index = "①②③④⑤⑥⑦⑧⑨⑩".index(raw)
        if index < count:
            return index
        return None
    if raw.isdigit():
        number = int(raw)
        if 1 <= number <= count:
            return number - 1
    return None


def _confirmed(answer: str) -> bool:
    return answer.strip().lower() in {"", "y", "yes"}


def _open_browser(url: str) -> None:
    opened = webbrowser.open(url)
    if opened is False:
        print("无法打开浏览器。", file=sys.stderr)


def run_session(
    idea: str,
    *,
    config: Config,
    client: Any,
    probe: Callable[[str], bool],
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[..., None] | None = None,
    opener: Callable[[str], None] | None = None,
) -> int:
    if input_fn is None:
        input_fn = input
    if print_fn is None:
        print_fn = print
    if opener is None:
        opener = _open_browser
    print_fn("正在拆分…")
    taste = read_taste(config.taste_path)
    try:
        raw_actions = plan_actions(
            client,
            model=config.model,
            reasoning_effort=config.reasoning_effort,
            idea=idea,
            taste=taste,
        )
    except PlanParseError:
        print("模型输出无法解析，请再试一次。", file=sys.stderr)
        return 1
    except (OpenAIError, httpx.HTTPError) as exc:
        print(f"调用模型失败：{exc}", file=sys.stderr)
        return 1

    actions, dropped = prepare_actions(raw_actions, probe)
    for line in menu_lines(actions):
        print_fn(line)
    if dropped:
        print_fn(dropped_line(dropped))
    if not actions:
        print_fn("没有可执行的动作。")
        return 0

    while True:
        choice = input_fn("选一条（回车退出）：")
        if choice.strip() == "":
            return 0
        index = _parse_choice(choice, len(actions))
        if index is None:
            print_fn("请输入序号，或直接回车退出。")
            continue
        _confirm_and_run(actions[index], input_fn=input_fn, print_fn=print_fn, opener=opener)


def _confirm_and_run(
    action: Action,
    *,
    input_fn: Callable[[str], str],
    print_fn: Callable[..., None],
    opener: Callable[[str], None],
) -> None:
    if action.type in {"open_url", "video_search"}:
        print_fn(action.url)
        answer = input_fn("确认？[Y/n] ")
        if not _confirmed(answer):
            return
        perform(action, opener=opener, writer=print_fn)
        return
    if action.type == "brief":
        perform(action, opener=opener, writer=print_fn)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print(USAGE, end="")
        return 0 if argv else 2
    config = Config.from_env()
    if argv[0] == "remember":
        text = " ".join(argv[1:]).strip()
        if not text:
            print(USAGE, end="", file=sys.stderr)
            return 2
        try:
            line = remember(config.taste_path, text)
        except TasteError:
            print("没有可记住的文字。", file=sys.stderr)
            return 2
        print(f"已记下：{line}")
        return 0

    idea = " ".join(argv).strip()
    if not idea:
        print(USAGE, end="", file=sys.stderr)
        return 2
    if not config.api_key:
        print("缺少环境变量 BUBBLE_API_KEY。参见 .env.example。", file=sys.stderr)
        return 2
    if not config.model:
        print("缺少环境变量 BUBBLE_MODEL。参见 .env.example。", file=sys.stderr)
        return 2

    client = make_client(config)
    with httpx.Client(timeout=httpx.Timeout(5.0), follow_redirects=True) as http:
        return run_session(idea, config=config, client=client, probe=_bind_probe(http))


def _bind_probe(http: httpx.Client) -> Callable[[str], bool]:
    def probe(url: str) -> bool:
        return probe_url(url, http)

    return probe
