"""Command-line entry: ``bubble \"想法\"`` and ``bubble remember \"文字\"``."""

from __future__ import annotations

import sys
import webbrowser
from collections.abc import Callable
from typing import Any

import httpx
from openai import APITimeoutError, OpenAIError

from bubble.actions import Action, dropped_line, execute, menu_lines, prepare_actions
from bubble.config import Config
from bubble.planner import PlanParseError, plan_actions
from bubble.safety import probe_url
from bubble.taste import TasteError, read_taste, remember

NO_ACTIONS = "这次没拆出能用的动作，换个说法再试一次？"
MISSING_KEY = "缺少 BUBBLE_API_KEY，请参考 .env.example 配置"
WAITING = "正在拆分…（通常 10 秒内）"
TIMEOUT_MESSAGE = "这次拆分太久了，请稍后再试一次"

USAGE = """\
用法：
  bubble "学习想法"
  bubble remember "一句偏好"

配置从环境变量读取（见 .env.example）：
  BUBBLE_API_KEY 或 DEEPSEEK_API_KEY   必填
  BUBBLE_BASE_URL                      默认 https://api.deepseek.com
  BUBBLE_MODEL                         必填
  BUBBLE_REASONING_EFFORT              默认 low，模型不支持时会去掉后重试
  BUBBLE_TIMEOUT                       默认 45，模型请求超时秒数
  BUBBLE_TASTE_PATH                    默认 ~/.bubble/taste.md
"""


def console_main() -> None:
    raise SystemExit(main())


def make_client(config: Config) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=config.timeout)


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


def _open_browser(url: str) -> bool:
    opened = webbrowser.open(url)
    if opened is False:
        print("无法打开浏览器。", file=sys.stderr)
        return False
    return True


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
    print_fn(WAITING)
    if print_fn is print:
        sys.stdout.flush()
    taste = read_taste(config.taste_path)
    try:
        raw_actions = plan_actions(
            client,
            model=config.model,
            reasoning_effort=config.reasoning_effort,
            idea=idea,
            taste=taste,
            timeout=config.timeout,
        )
    except (APITimeoutError, httpx.TimeoutException):
        print_fn(TIMEOUT_MESSAGE)
        return 1
    except (PlanParseError, OpenAIError, httpx.HTTPError):
        print_fn(NO_ACTIONS)
        return 1

    actions, dropped = prepare_actions(raw_actions, probe)
    print_fn("")
    for line in menu_lines(actions):
        print_fn(line)
    if dropped:
        print_fn(dropped_line(dropped))
    if not actions:
        print_fn(NO_ACTIONS)
        return 1
    print_fn("")

    while True:
        choice = input_fn(f"选一条 [1-{len(actions)}]，回车退出 › ")
        if choice.strip() == "":
            return 0
        index = _parse_choice(choice, len(actions))
        if index is None:
            print_fn(f"请输入 1-{len(actions)}")
            continue
        if _confirm_and_run(actions[index], input_fn=input_fn, print_fn=print_fn, opener=opener):
            return 0


def _confirm_and_run(
    action: Action,
    *,
    input_fn: Callable[[str], str],
    print_fn: Callable[..., None],
    opener: Callable[[str], object],
) -> bool:
    """Return True when a page was opened and the session should end."""
    if action.kind in {"open_url", "video_search"}:
        answer = input_fn(f"将打开 {action.url}  确认？[Y/n] › ")
        if not _confirmed(answer):
            return False
        opened = execute(action, opener, True)
        if opened is False:
            return False
        print_fn("已打开。")
        return True
    if action.kind == "brief":
        print_fn(action.text)
        return False
    return False


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
            remember(config.taste_path, text)
        except TasteError:
            print("没有可记住的文字。", file=sys.stderr)
            return 2
        print(f"记住了：{' '.join(text.split())} （写入 taste.md）")
        return 0

    idea = " ".join(argv).strip()
    if not idea:
        print(USAGE, end="", file=sys.stderr)
        return 2
    if not config.api_key:
        print(MISSING_KEY)
        return 2
    if not config.model:
        print("缺少 BUBBLE_MODEL，请参考 .env.example 配置")
        return 2

    client = make_client(config)
    with httpx.Client(timeout=httpx.Timeout(5.0), follow_redirects=True) as http:
        return run_session(idea, config=config, client=client, probe=_bind_probe(http))


def _bind_probe(http: httpx.Client) -> Callable[[str], bool]:
    def probe(url: str) -> bool:
        return probe_url(url, http)

    return probe
