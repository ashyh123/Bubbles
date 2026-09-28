"""URL checks for open_url and the fixed Bilibili search link.

No function in this module runs a shell command. Model text is data.
"""

from __future__ import annotations

import ipaddress
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx

_SHELL_CHARS = set("`$|\\")
_SEARCH_HOST = "search.bilibili.com"
_SEARCH_PATH = "/all"


def log_discard(message: str) -> None:
    """Record a dropped action. Prefer ~/.bubble/log; fall back to stderr."""
    stamped = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    line = f"{stamped} {message}\n"
    path = Path.home() / ".bubble" / "log"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        sys.stderr.write(line)


def is_ip_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    return host.isdigit()


def is_safe_https_url(url: str) -> bool:
    """https only, no userinfo, no IP host, no whitespace or shell metacharacters."""
    if not isinstance(url, str) or not url or len(url) > 2000:
        return False
    if "@" in url:
        return False
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url):
        return False
    if any(char in _SHELL_CHARS for char in url):
        return False
    parts = urlsplit(url)
    if parts.scheme != "https":
        return False
    if parts.username is not None or parts.password is not None:
        return False
    host = parts.hostname
    return bool(host) and not is_ip_host(host)


def build_bilibili_url(keyword: str) -> str:
    """Build the only video URL Bubble will open. The model's URL is never used."""
    query = urlencode({"keyword": keyword.strip()})
    return f"https://{_SEARCH_HOST}{_SEARCH_PATH}?{query}"


def build_video_search_url(keyword: str) -> str:
    return build_bilibili_url(keyword)


def is_official_video_search(url: str) -> bool:
    """Accept only https://search.bilibili.com/all?keyword=... built by this program."""
    if not isinstance(url, str) or not url or "@" in url:
        return False
    parts = urlsplit(url)
    if parts.scheme != "https":
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if parts.hostname != _SEARCH_HOST:
        return False
    if parts.port not in (None, 443):
        return False
    if parts.path != _SEARCH_PATH:
        return False
    if parts.fragment:
        return False
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    if len(pairs) != 1 or pairs[0][0] != "keyword" or pairs[0][1] == "":
        return False
    return url == build_video_search_url(pairs[0][1])


def _response_ok(response: httpx.Response) -> bool:
    final = response.url
    return response.status_code < 400 and getattr(final, "scheme", "") == "https"


def probe_url(url: str, client: httpx.Client) -> bool:
    """Request the page once before showing it. HEAD, then GET if HEAD fails.

    Redirects are followed. The final URL must still be https. Timeout is 5 seconds.
    """
    timeout = 5.0
    head_ok = False
    try:
        response = client.request("HEAD", url, timeout=timeout, follow_redirects=True)
        head_ok = _response_ok(response)
    except httpx.HTTPError:
        head_ok = False
    if head_ok:
        return True
    try:
        response = client.request("GET", url, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError:
        return False
    return _response_ok(response)
