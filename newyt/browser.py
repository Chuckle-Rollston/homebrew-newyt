"""Reads the signed-in user's own YouTube pages via a persistent, local
Playwright browser profile. This profile is only ever used to READ pages
(home feed, watch later, history) -- actual video playback always happens
in a separate private/incognito window via newyt.play, so watching is
signed out and doesn't touch this profile or its recommendations.
"""
import subprocess
import sys

from .config import profile_dir
from .extract import extract_videos
from .models import Video

HOME_URL = "https://www.youtube.com/"
WATCH_LATER_URL = "https://www.youtube.com/playlist?list=WL"
HISTORY_URL = "https://www.youtube.com/feed/history"


class NotLoggedIn(Exception):
    pass


class BrowserNotInstalled(Exception):
    pass


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "playwright is not installed. Run: pip install playwright"
        ) from e
    return sync_playwright


def is_logged_in() -> bool:
    d = profile_dir()
    return d.exists() and any(d.iterdir())


def _install_chromium() -> None:
    print("Downloading Chromium for Playwright (one-time, ~150-200MB)...")
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if result.returncode != 0:
        raise BrowserNotInstalled(
            "Couldn't download Chromium automatically. Try running:\n"
            f"  {sys.executable} -m playwright install chromium"
        )


def _launch_persistent(p, headless: bool):
    try:
        return p.chromium.launch_persistent_context(
            str(profile_dir()), headless=headless, viewport={"width": 1280, "height": 900}
        )
    except Exception:
        _install_chromium()
        return p.chromium.launch_persistent_context(
            str(profile_dir()), headless=headless, viewport={"width": 1280, "height": 900}
        )


def login() -> None:
    sync_playwright = _import_playwright()
    with sync_playwright() as p:
        ctx = _launch_persistent(p, headless=False)
        page = ctx.new_page()
        page.goto("https://accounts.google.com/ServiceLogin?service=youtube&continue=https://www.youtube.com/")
        print("A browser window opened. Log in to your YouTube account there.")
        input("Press Enter here once you're logged in (this closes the window)... ")
        ctx.close()


def _fetch(url: str, keys) -> list[Video]:
    if not is_logged_in():
        raise NotLoggedIn("Not logged in. Run `newyt login` first.")
    sync_playwright = _import_playwright()
    with sync_playwright() as p:
        ctx = _launch_persistent(p, headless=True)
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1200)
        try:
            data = page.evaluate("() => window.ytInitialData")
        except Exception:
            data = None
        ctx.close()
    if not data:
        return []
    return extract_videos(data, keys)


def fetch_home() -> list[Video]:
    return _fetch(HOME_URL, ("videoRenderer",))


def fetch_watch_later() -> list[Video]:
    return _fetch(WATCH_LATER_URL, ("playlistVideoRenderer",))


def fetch_history() -> list[Video]:
    return _fetch(HISTORY_URL, ("videoRenderer",))
