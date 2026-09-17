"""Reads the signed-in user's own YouTube pages using cookies imported from
a real, already-logged-in browser (see newyt.cookies). Google blocks the
interactive sign-in flow inside an automation-controlled browser, so newyt
never drives that flow itself -- it only ever reuses an existing session.
Actual video playback always happens separately in a fresh private/
incognito window via newyt.play, so watching is always signed out.
"""
import subprocess
import sys

from . import cookies as cookies_mod
from .extract import extract_videos
from .models import Video

HOME_URL = "https://www.youtube.com/"
WATCH_LATER_URL = "https://www.youtube.com/playlist?list=WL"
HISTORY_URL = "https://www.youtube.com/feed/history"


class NotLoggedIn(Exception):
    pass


class SessionExpired(NotLoggedIn):
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
    return cookies_mod.load() is not None


def _install_chromium() -> None:
    print("Downloading Chromium for Playwright (one-time, ~150-200MB)...")
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if result.returncode != 0:
        raise BrowserNotInstalled(
            "Couldn't download Chromium automatically. Try running:\n"
            f"  {sys.executable} -m playwright install chromium"
        )


def _launch(p, headless: bool):
    try:
        return p.chromium.launch(headless=headless)
    except Exception:
        _install_chromium()
        return p.chromium.launch(headless=headless)


def login(browser_name: str = "chrome") -> int:
    """Imports YouTube cookies from the given browser. Returns the cookie count."""
    imported = cookies_mod.extract(browser_name)
    if not imported:
        raise NotLoggedIn(
            f"No YouTube cookies found in {browser_name}. Make sure you're signed "
            f"into youtube.com there, then try again."
        )
    cookies_mod.save(imported)
    return len(imported)


def _fetch(url: str, keys=None) -> list[Video]:
    saved = cookies_mod.load()
    if not saved:
        raise NotLoggedIn("Not logged in. Run `newyt login` first.")
    sync_playwright = _import_playwright()
    with sync_playwright() as p:
        browser = _launch(p, headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(saved)
        page = ctx.new_page()
        # YouTube keeps background connections open indefinitely (websockets,
        # analytics, autoplay previews), so it never reaches "networkidle" --
        # wait for the DOM instead.
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        try:
            # window.ytInitialData is a static snapshot that on several pages
            # (home, history) only has skeleton placeholders until the client
            # hydrates real content into the <ytd-app> component tree -- read
            # that live component state instead.
            data = page.evaluate("() => { const app = document.querySelector('ytd-app'); return app ? app.data : null; }")
        except Exception:
            data = None
        try:
            # The imported cookies can go stale (short-lived token rotation,
            # or Google invalidating the session over repeated automated
            # access) -- when that happens the page just silently renders
            # signed out instead of erroring, so check for it explicitly
            # rather than showing an empty tab with no explanation.
            signed_in = page.evaluate("() => !!document.querySelector('#avatar-btn')")
        except Exception:
            signed_in = True
        ctx.close()
        browser.close()
    if not signed_in:
        raise SessionExpired(
            "Your imported YouTube session looks expired or invalid. Run `newyt login` again."
        )
    if not data:
        return []
    return extract_videos(data, keys)


def fetch_home() -> list[Video]:
    return _fetch(HOME_URL)


def fetch_watch_later() -> list[Video]:
    return _fetch(WATCH_LATER_URL)


def fetch_history() -> list[Video]:
    return _fetch(HISTORY_URL)
