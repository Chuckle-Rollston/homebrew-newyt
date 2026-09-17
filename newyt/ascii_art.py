import io
from pathlib import Path

import requests
from PIL import Image

CHARS = " .:-=+*#%@"

# The upper-half-block character lets one terminal cell show two image
# pixels (foreground color = top pixel, background color = bottom pixel),
# doubling vertical resolution for the same number of rows -- the same
# trick terminal image viewers like chafa/viu use.
HALF_BLOCK = "▀"


def _fetch_bytes(url: str, cache_path: Path) -> "bytes | None":
    if not url:
        return None
    if cache_path.exists():
        return cache_path.read_bytes()
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.content
        cache_path.write_bytes(data)
        return data
    except Exception:
        return None


def rgb_to_xterm256(r: int, g: int, b: int) -> int:
    if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
        gray = (r + g + b) / 3
        if gray < 8:
            return 16
        if gray > 248:
            return 231
        return 232 + max(0, min(23, round((gray - 8) / 247 * 24)))
    r6 = min(5, r * 6 // 256)
    g6 = min(5, g * 6 // 256)
    b6 = min(5, b * 6 // 256)
    return 16 + 36 * r6 + 6 * g6 + b6


def image_to_ascii(img_bytes: bytes, width: int = 40, height: int = 18) -> list[str]:
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    img = img.resize((width, height))
    pixels = list(img.getdata())
    lines = []
    for row_start in range(0, len(pixels), width):
        row = pixels[row_start:row_start + width]
        lines.append("".join(CHARS[p * (len(CHARS) - 1) // 255] for p in row))
    return lines


def image_to_color_cells(img_bytes: bytes, width: int = 60, height: int = 24) -> list[list[tuple[int, int]]]:
    """Returns `height` rows of `width` (fg_xterm256, bg_xterm256) pairs, each
    cell meant to be rendered as HALF_BLOCK. Samples at double the row count
    (2 image pixels per cell) for the half-block trick.
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((width, height * 2))
    px = img.load()
    rows = []
    for j in range(height):
        row = []
        for i in range(width):
            top = px[i, j * 2]
            bottom = px[i, j * 2 + 1]
            row.append((rgb_to_xterm256(*top), rgb_to_xterm256(*bottom)))
        rows.append(row)
    return rows


def fetch_thumbnail_ascii(url: str, cache_path: Path, width: int = 40, height: int = 18) -> list[str]:
    data = _fetch_bytes(url, cache_path)
    if data is None:
        return ["[no thumbnail]"] if url else []
    try:
        return image_to_ascii(data, width, height)
    except Exception:
        return ["[thumbnail error]"]


def fetch_thumbnail_color_cells(
    url: str, cache_path: Path, width: int = 60, height: int = 24
) -> "list[list[tuple[int, int]]] | None":
    data = _fetch_bytes(url, cache_path)
    if data is None:
        return None
    try:
        return image_to_color_cells(data, width, height)
    except Exception:
        return None
