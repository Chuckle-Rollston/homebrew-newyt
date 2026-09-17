"""Standalone process that downloads one video to ~/Desktop/youtube videos
and opens it with the system's default player, never loading youtube.com
itself. Run as `python -m newyt._playback_worker <url>`, detached from
the TUI process so quitting newyt doesn't stop the download or playback.

Progress is written to newyt.config.download_progress_file() as it goes
(yt-dlp progress hooks), since this is a separate process from the TUI --
the TUI polls that file to render a live progress bar. On success, the
video is also registered in newyt.downloaded so it shows up in the
Downloaded tab, pointing at the file on disk instead of re-downloading.

This process runs detached with no visible stdout/stderr, so any failure
is logged to ~/Library/Application Support/newyt/playback_worker.log
(or the platform equivalent) instead of vanishing silently.
"""
import json
import os
import subprocess
import sys
import time
import traceback

from . import downloaded
from .config import config_dir, download_progress_file, downloads_dir
from .models import Video

MAX_HEIGHT = 1080


def _log_path():
    return config_dir() / "playback_worker.log"


def _log_error(context: str) -> None:
    try:
        with open(_log_path(), "a") as f:
            f.write(f"--- {context} ---\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        pass


def _open_file(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def _format_duration(seconds) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _write_progress(payload: dict) -> None:
    try:
        download_progress_file().write_text(json.dumps(payload))
    except Exception:
        pass


def _clear_progress() -> None:
    try:
        download_progress_file().unlink(missing_ok=True)
    except Exception:
        pass


def _make_progress_hook(video_id: str, title: str):
    def hook(d: dict) -> None:
        status = d.get("status")
        payload = {"id": video_id, "title": title, "status": status}
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded_bytes = d.get("downloaded_bytes", 0)
            payload["percent"] = round(downloaded_bytes / total * 100, 1) if total else None
        _write_progress(payload)

    return hook


def _postprocessor_hook(video_id: str, title: str):
    def hook(d: dict) -> None:
        if d.get("status") == "started":
            _write_progress({"id": video_id, "title": title, "status": "merging"})

    return hook


def main() -> None:
    if len(sys.argv) < 2:
        return
    url = sys.argv[1]

    try:
        import yt_dlp
    except ImportError:
        _log_error("yt_dlp not installed")
        return

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as ydl:
            preview = ydl.extract_info(url, download=False)
        video_id = preview.get("id") or url
        title = preview.get("title") or url

        _write_progress({"id": video_id, "title": title, "status": "downloading", "percent": 0})

        out_dir = downloads_dir()
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "noprogress": True,
            "progress_hooks": [_make_progress_hook(video_id, title)],
            "postprocessor_hooks": [_postprocessor_hook(video_id, title)],
            # Prefer H.264/AAC first -- QuickTime Player (the default on a
            # fresh Mac) plays that universally; VP9/AV1+Opus (yt-dlp's
            # usual "best") only reliably plays on newer macOS/Apple
            # Silicon, so it's a fallback, not the default.
            "format": (
                f"bestvideo[vcodec^=avc1][height<={MAX_HEIGHT}]+bestaudio[acodec^=mp4a]/"
                f"bestvideo[height<={MAX_HEIGHT}]+bestaudio/best[height<={MAX_HEIGHT}]/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": str(out_dir / "%(title).150s [%(id)s].%(ext)s"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            # merge_output_format can change the extension from what
            # prepare_filename predicted before postprocessing ran.
            mp4_path = os.path.splitext(filepath)[0] + ".mp4"
            if os.path.exists(mp4_path):
                filepath = mp4_path

        downloaded.add(
            Video(
                id=video_id,
                title=title,
                channel=info.get("uploader") or info.get("channel") or "",
                duration=_format_duration(info.get("duration")),
                thumbnail_url=info.get("thumbnail") or "",
                local_path=filepath,
            )
        )
        _write_progress({"id": video_id, "title": title, "status": "finished", "percent": 100})
        _open_file(filepath)
        # Give the TUI's poll loop a chance to render "finished" before the
        # progress file disappears.
        time.sleep(1.5)
    except Exception:
        _log_error("main")
    finally:
        _clear_progress()


if __name__ == "__main__":
    main()
