"""Opens a video in a fresh, private browser window, signed out.

Spawns newyt._playback_worker as a separate detached process (so closing
or quitting the newyt TUI doesn't close the video window). That worker
uses its own fresh Playwright browser context -- never the cookies used to
read the feed/watch-later/history -- and permanently hides the
related-videos sidebar (immune to the user resizing the window), which a
plain "open this URL in the OS browser" can't do since YouTube's sidebar
is shown/hidden by its own responsive JS on every resize.
"""
import subprocess
import sys


def open_private(url: str) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "newyt._playback_worker", url],
        start_new_session=True,
    )
