"""Plays a video without ever loading youtube.com in a browser.

Spawns newyt._playback_worker as a separate detached process (so closing
or quitting the newyt TUI doesn't stop the download/playback). That
worker uses yt-dlp to download the video to ~/Desktop/youtube videos
(merging via ffmpeg) and opens it with the system's default player once
done, reporting progress back to the TUI via a shared file since it's a
separate process. This never touches the cookies used to read the
feed/watch-later/history (so it's still "signed out"), and sidesteps
YouTube's own web player entirely: no ads, no related-videos sidebar,
and no exposure to the intermittent "There's a problem with playback"
errors that can hit an automated Chromium mid-video.
"""
import subprocess
import sys


def open_private(url: str) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "newyt._playback_worker", url],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


def open_local_file(path: str) -> None:
    """Opens an already-downloaded file directly, no yt-dlp/network involved."""
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
