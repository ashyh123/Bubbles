import pytest


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Keep tests away from the real home directory and any developer API keys."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    for key in (
        "BUBBLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "BUBBLE_BASE_URL",
        "BUBBLE_MODEL",
        "BUBBLE_REASONING_EFFORT",
        "BUBBLE_TIMEOUT",
        "BUBBLE_TASTE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)
    return home
