import re
from datetime import date
from pathlib import Path

from bubble.cli import main
from bubble.config import Config
from bubble.taste import read_taste, remember


def test_remember_appends_a_dated_line(tmp_path):
    path = tmp_path / "taste.md"
    path.write_text("旧偏好\n", encoding="utf-8")
    line = remember(path, "记笔记用 Obsidian", today=date(2026, 9, 28))
    assert line == "2026-09-28 记笔记用 Obsidian"
    text = path.read_text(encoding="utf-8")
    assert text == "旧偏好\n2026-09-28 记笔记用 Obsidian\n"
    remember(path, "IDE = IntelliJ", today=date(2026, 9, 28))
    assert path.read_text(encoding="utf-8").splitlines() == [
        "旧偏好",
        "2026-09-28 记笔记用 Obsidian",
        "2026-09-28 IDE = IntelliJ",
    ]


def test_cli_remember_appends_without_calling_a_model(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "taste.md"
    path.parent.mkdir()
    path.write_text("已有一行\n", encoding="utf-8")
    monkeypatch.setenv("BUBBLE_TASTE_PATH", str(path))
    monkeypatch.setattr(
        "bubble.cli.make_client",
        lambda _config: (_ for _ in ()).throw(AssertionError("model client was created")),
    )
    assert main(["remember", "记笔记用", "Obsidian"]) == 0
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "已有一行"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} 记笔记用 Obsidian", lines[1])
    assert read_taste(Config.from_env().taste_path) == path.read_text(encoding="utf-8")


def test_default_taste_path_is_under_home():
    assert Config.from_env().taste_path == Path.home() / ".bubble" / "taste.md"


def test_missing_taste_file_is_empty(tmp_path):
    assert read_taste(tmp_path / "missing.md") == ""
