"""Imports YouTube session cookies from a real, already-logged-in browser.

Google actively blocks the interactive sign-in flow when it detects an
automation-controlled browser (Playwright/Selenium), so newyt never tries to
drive that flow itself. Instead it reads your existing session cookies out of
a browser you're already signed into -- the same approach tools like
yt-dlp's --cookies-from-browser use -- and hands those cookies to the
headless Playwright context that reads your feed/watch-later/history.
"""
import json

import browser_cookie3

from .config import config_dir

BROWSERS = {
    "chrome": browser_cookie3.chrome,
    "brave": browser_cookie3.brave,
    "edge": browser_cookie3.edge,
    "firefox": browser_cookie3.firefox,
    "safari": browser_cookie3.safari,
    "opera": browser_cookie3.opera,
}


def cookie_file():
    return config_dir() / "cookies.json"


def extract(browser_name: str) -> list[dict]:
    fn = BROWSERS.get(browser_name)
    if fn is None:
        raise ValueError(f"Unsupported browser '{browser_name}'. Choose from: {', '.join(BROWSERS)}")
    jar = fn(domain_name="youtube.com")
    cookies = []
    for c in jar:
        cookies.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path or "/",
                "expires": c.expires if c.expires else -1,
                "secure": bool(c.secure),
            }
        )
    return cookies


def save(cookies: list[dict]) -> None:
    cookie_file().write_text(json.dumps(cookies))


def load() -> "list[dict] | None":
    f = cookie_file()
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
    except Exception:
        return None
    return data or None


def clear() -> None:
    f = cookie_file()
    if f.exists():
        f.unlink()
