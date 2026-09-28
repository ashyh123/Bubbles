"""Runtime configuration, read only from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_TIMEOUT = 45.0


def _timeout_from_env() -> float:
    raw = os.environ.get("BUBBLE_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT
    if value <= 0:
        return DEFAULT_TIMEOUT
    return value


@dataclass(frozen=True)
class Config:
    api_key: str
    base_url: str
    model: str
    reasoning_effort: str
    taste_path: Path
    timeout: float = DEFAULT_TIMEOUT
    log_path: Path | None = None

    def resolved_log_path(self) -> Path:
        if self.log_path is not None:
            return self.log_path
        return self.taste_path.parent / "log"

    @classmethod
    def from_env(cls) -> Config:
        base_url = os.environ.get("BUBBLE_BASE_URL", "").strip() or DEFAULT_BASE_URL
        effort = os.environ.get("BUBBLE_REASONING_EFFORT", "").strip() or DEFAULT_REASONING_EFFORT
        taste_raw = os.environ.get("BUBBLE_TASTE_PATH", "").strip()
        if taste_raw:
            taste_path = Path(taste_raw).expanduser()
        else:
            taste_path = Path.home() / ".bubble" / "taste.md"
        bubble_key = os.environ.get("BUBBLE_API_KEY", "").strip()
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        log_raw = os.environ.get("BUBBLE_LOG_PATH", "").strip()
        if log_raw:
            log_path = Path(log_raw).expanduser()
        else:
            log_path = taste_path.parent / "log"
        model = os.environ.get("BUBBLE_MODEL", "").strip() or DEFAULT_MODEL
        return cls(
            api_key=bubble_key or deepseek_key,
            base_url=base_url,
            model=model,
            reasoning_effort=effort,
            taste_path=taste_path,
            timeout=_timeout_from_env(),
            log_path=log_path,
        )
