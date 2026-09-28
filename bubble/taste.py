"""Read and append the local taste file."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path


class TasteError(ValueError):
    """The remember text cannot be stored as a single line."""


def read_taste(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def remember(path: Path, text: str, *, today: date | None = None) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        raise TasteError("empty preference")
    day = today or datetime.now(timezone.utc).astimezone().date()
    line = f"{day.isoformat()} {cleaned}"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8")
    return line
