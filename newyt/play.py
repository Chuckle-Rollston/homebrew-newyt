"""Opens a video in a private/incognito browser window, signed out.

Deliberately does NOT reuse the Playwright profile from browser.py -- this
always launches the user's real installed browser in a fresh, ephemeral
private window with no YouTube session, so playback never carries the
account used to read recommendations/watch-later/history.
"""
import shutil
import subprocess
import sys


def _mac_app_exists(app_name: str) -> bool:
    import os

    return os.path.isdir(f"/Applications/{app_name}.app")


# A narrow window makes YouTube's own responsive layout drop the
# related-videos rail entirely (single column, nothing beside the player)
# instead of showing it alongside -- more reliable than URL tricks like the
# embed player, which throws errors on many videos when opened directly.
NARROW_WINDOW_ARGS = ["--window-size=560,900", "--new-window"]


def open_private(url: str) -> None:
    if sys.platform == "darwin":
        if _mac_app_exists("Google Chrome"):
            subprocess.Popen(["open", "-na", "Google Chrome", "--args", "--incognito", *NARROW_WINDOW_ARGS, url])
            return
        if _mac_app_exists("Brave Browser"):
            subprocess.Popen(["open", "-na", "Brave Browser", "--args", "--incognito", *NARROW_WINDOW_ARGS, url])
            return
        if _mac_app_exists("Microsoft Edge"):
            subprocess.Popen(["open", "-na", "Microsoft Edge", "--args", "--inprivate", *NARROW_WINDOW_ARGS, url])
            return
        if _mac_app_exists("Firefox"):
            subprocess.Popen(
                ["open", "-na", "Firefox", "--args", "-private-window", "-width", "560", "-height", "900", url]
            )
            return
        subprocess.Popen(["open", url])
        return

    for browser_cmd, extra_args in (
        ("google-chrome", ["--incognito", *NARROW_WINDOW_ARGS]),
        ("chromium", ["--incognito", *NARROW_WINDOW_ARGS]),
        ("chromium-browser", ["--incognito", *NARROW_WINDOW_ARGS]),
        ("brave-browser", ["--incognito", *NARROW_WINDOW_ARGS]),
        ("microsoft-edge", ["--inprivate", *NARROW_WINDOW_ARGS]),
        ("firefox", ["-private-window", "-width", "560", "-height", "900"]),
    ):
        if shutil.which(browser_cmd):
            subprocess.Popen([browser_cmd, *extra_args, url])
            return
    subprocess.Popen(["xdg-open", url])
