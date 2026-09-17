"""Registry of videos downloaded to ~/Desktop/youtube videos (see
newyt.config.downloads_dir). The Downloaded tab reads this to show what's
actually on disk, and pressing Enter on an entry there opens the local
file directly instead of re-downloading.
"""
import json
import os

from .config import config_dir
from .models import Video


def _file():
    return config_dir() / "downloaded.json"


def load() -> list[Video]:
    f = _file()
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text())
        videos = [Video(**v) for v in data]
    except Exception:
        return []
    # Drop entries whose file was moved/deleted outside newyt.
    return [v for v in videos if v.local_path and os.path.exists(v.local_path)]


def _write(videos: list[Video]) -> None:
    _file().write_text(json.dumps([v.__dict__ for v in videos]))


def add(video: Video) -> None:
    videos = [v for v in load() if v.id != video.id]
    videos.insert(0, video)
    _write(videos)
