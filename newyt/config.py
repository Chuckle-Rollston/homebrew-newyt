import os
import sys
from pathlib import Path


def config_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "newyt"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "newyt"
    base.mkdir(parents=True, exist_ok=True)
    return base


def profile_dir() -> Path:
    d = config_dir() / "browser-profile"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    d = config_dir() / "cache" / "thumbs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_cache_file(name: str) -> Path:
    d = config_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}.json"
