"""Standalone process that plays one video via yt-dlp + a native player,
never loading youtube.com itself. Run as
`python -m newyt._playback_worker <url>`, detached from the TUI process
so quitting newyt doesn't stop playback.

Modern YouTube rarely offers a single "progressive" (video+audio already
muxed) format anymore -- almost everything is separate video-only and
audio-only streams that need merging. Two paths handle that:

- VLC installed: stream the video-only URL with the audio-only URL
  attached via VLC's :input-slave option, so playback starts instantly
  with no download or merging step.
- Otherwise: download bestvideo+bestaudio and let yt-dlp merge them via
  ffmpeg (required for this path -- logged clearly if missing), then
  open the finished file with the system's default player.

This process runs detached with no visible stdout/stderr, so any failure
is logged to ~/Library/Application Support/newyt/playback_worker.log
(or the platform equivalent) instead of vanishing silently.
"""
import shutil
import subprocess
import sys
import time
import traceback

from .config import config_dir

MAX_DOWNLOAD_AGE_DAYS = 7
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


def _log_message(context: str, message: str) -> None:
    try:
        with open(_log_path(), "a") as f:
            f.write(f"--- {context} ---\n{message}\n\n")
    except Exception:
        pass


def _vlc_darwin_installed() -> bool:
    import os

    return os.path.isdir("/Applications/VLC.app")


def _vlc_linux_cmd() -> "str | None":
    for cmd in ("vlc", "cvlc"):
        if shutil.which(cmd):
            return cmd
    return None


def _open_file(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def _prune_old_downloads(downloads_dir) -> None:
    cutoff = time.time() - MAX_DOWNLOAD_AGE_DAYS * 86400
    try:
        for f in downloads_dir.glob("*"):
            try:
                if f.is_file() and f.stat().st_mtime < cutoff:
                    f.unlink()
            except Exception:
                pass
    except Exception:
        pass


def _best_stream_urls(info: dict) -> "tuple[str, str | None] | None":
    """Returns (video_url, audio_url_or_None) for the best available
    stream(s), preferring a single progressive format if one exists,
    otherwise the best separate video-only + audio-only pair.
    """
    if info.get("url") and info.get("acodec") not in (None, "none") and info.get("vcodec") not in (None, "none"):
        return info["url"], None

    formats = info.get("formats") or []
    progressive = [
        f for f in formats
        if f.get("url") and f.get("acodec") not in (None, "none") and f.get("vcodec") not in (None, "none")
    ]
    if progressive:
        progressive.sort(key=lambda f: f.get("height") or 0)
        return progressive[-1]["url"], None

    video_only = [
        f for f in formats
        if f.get("url") and f.get("vcodec") not in (None, "none") and f.get("acodec") in (None, "none")
        and (f.get("height") or 0) <= MAX_HEIGHT
    ]
    audio_only = [
        f for f in formats
        if f.get("url") and f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    if not video_only:
        return None
    video_only.sort(key=lambda f: f.get("height") or 0)
    audio_url = None
    if audio_only:
        audio_only.sort(key=lambda f: f.get("abr") or 0)
        audio_url = audio_only[-1]["url"]
    return video_only[-1]["url"], audio_url


def _play_with_vlc(video_url: str, audio_url: "str | None") -> bool:
    if sys.platform == "darwin":
        if not _vlc_darwin_installed():
            return False
        args = ["open", "-na", "VLC", "--args", video_url]
        if audio_url:
            args.append(f":input-slave={audio_url}")
        subprocess.Popen(args)
        return True

    vlc_cmd = _vlc_linux_cmd()
    if not vlc_cmd:
        return False
    args = [vlc_cmd, video_url]
    if audio_url:
        args.append(f":input-slave={audio_url}")
    subprocess.Popen(args)
    return True


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
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        streams = _best_stream_urls(info)
        if streams and _play_with_vlc(*streams):
            return

        if not shutil.which("ffmpeg"):
            _log_message(
                "main",
                "No VLC and no ffmpeg found -- can't merge separate video/audio "
                "streams without one of them. Install VLC or run: brew install ffmpeg",
            )
            return

        downloads_dir = config_dir() / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        _prune_old_downloads(downloads_dir)

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "noprogress": True,
            # Prefer H.264/AAC first -- QuickTime Player (the default on a
            # fresh Mac) plays that universally; VP9/AV1+Opus (yt-dlp's
            # usual "best") only reliably plays on newer macOS/Apple
            # Silicon, so it's a fallback, not the default.
            "format": (
                f"bestvideo[vcodec^=avc1][height<={MAX_HEIGHT}]+bestaudio[acodec^=mp4a]/"
                f"bestvideo[height<={MAX_HEIGHT}]+bestaudio/best[height<={MAX_HEIGHT}]/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": str(downloads_dir / "%(id)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            # merge_output_format can change the extension from what
            # prepare_filename predicted before postprocessing ran.
            import os

            mp4_path = os.path.splitext(filepath)[0] + ".mp4"
            if os.path.exists(mp4_path):
                filepath = mp4_path
        _open_file(filepath)
    except Exception:
        _log_error("main")


if __name__ == "__main__":
    main()
