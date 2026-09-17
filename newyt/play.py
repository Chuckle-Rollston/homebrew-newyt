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


def open_private(url: str) -> None:
    if sys.platform == "darwin":
        if _mac_app_exists("Google Chrome"):
            subprocess.Popen(["open", "-na", "Google Chrome", "--args", "--incognito", url])
            return
        if _mac_app_exists("Brave Browser"):
            subprocess.Popen(["open", "-na", "Brave Browser", "--args", "--incognito", url])
            return
        if _mac_app_exists("Microsoft Edge"):
            subprocess.Popen(["open", "-na", "Microsoft Edge", "--args", "--inprivate", url])
            return
        if _mac_app_exists("Firefox"):
            subprocess.Popen(["open", "-na", "Firefox", "--args", "-private-window", url])
            return
        subprocess.Popen(["open", url])
        return

    for browser_cmd, flag in (
        ("google-chrome", "--incognito"),
        ("chromium", "--incognito"),
        ("chromium-browser", "--incognito"),
        ("brave-browser", "--incognito"),
        ("microsoft-edge", "--inprivate"),
        ("firefox", "-private-window"),
    ):
        if shutil.which(browser_cmd):
            subprocess.Popen([browser_cmd, flag, url])
            return
    subprocess.Popen(["xdg-open", url])
