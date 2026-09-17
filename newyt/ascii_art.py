import io
from pathlib import Path

import requests
from PIL import Image

CHARS = " .:-=+*#%@"


def image_to_ascii(img_bytes: bytes, width: int = 40, height: int = 18) -> list[str]:
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    img = img.resize((width, height))
    pixels = list(img.getdata())
    lines = []
    for row_start in range(0, len(pixels), width):
        row = pixels[row_start:row_start + width]
        lines.append("".join(CHARS[p * (len(CHARS) - 1) // 255] for p in row))
    return lines


def fetch_thumbnail_ascii(url: str, cache_path: Path, width: int = 40, height: int = 18) -> list[str]:
    if not url:
        return []
    if cache_path.exists():
        data = cache_path.read_bytes()
    else:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.content
            cache_path.write_bytes(data)
        except Exception:
            return ["[no thumbnail]"]
    try:
        return image_to_ascii(data, width, height)
    except Exception:
        return ["[thumbnail error]"]
