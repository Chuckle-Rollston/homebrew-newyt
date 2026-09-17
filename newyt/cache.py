import json
import time

from .config import data_cache_file
from .models import Video


def save_cache(name: str, videos: list[Video]) -> None:
    data = {"ts": time.time(), "videos": [v.__dict__ for v in videos]}
    data_cache_file(name).write_text(json.dumps(data))


def load_cache(name: str, max_age: float = 600) -> "list[Video] | None":
    f = data_cache_file(name)
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
    except Exception:
        return None
    if time.time() - data.get("ts", 0) > max_age:
        return None
    try:
        return [Video(**v) for v in data["videos"]]
    except Exception:
        return None
