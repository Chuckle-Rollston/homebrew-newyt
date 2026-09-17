"""A local "Saved" list, separate from the real YouTube Watch Later
playlist. Pressing `w` on a selected video adds it here instantly --
no network call or write to the real account needed, since this is just
a locally-stored compilation of links.
"""
import json

from .config import config_dir
from .models import Video


def _file():
    return config_dir() / "saved.json"


def load() -> list[Video]:
    f = _file()
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text())
        return [Video(**v) for v in data]
    except Exception:
        return []


def _write(videos: list[Video]) -> None:
    _file().write_text(json.dumps([v.__dict__ for v in videos]))


def add(video: Video) -> bool:
    """Returns False if the video was already saved."""
    videos = load()
    if any(v.id == video.id for v in videos):
        return False
    videos.insert(0, video)
    _write(videos)
    return True


def remove(video_id: str) -> bool:
    videos = load()
    kept = [v for v in videos if v.id != video_id]
    if len(kept) == len(videos):
        return False
    _write(kept)
    return True
