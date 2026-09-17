"""Parses video info out of YouTube's embedded ytInitialData JSON blob.

This is more stable than scraping DOM/CSS selectors, since it's the same
structured data YouTube's own frontend renders from.
"""
from .models import Video

RENDERER_KEYS = ("videoRenderer", "playlistVideoRenderer")


def iter_renderers(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                yield v
            else:
                yield from iter_renderers(v, keys)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_renderers(item, keys)


def _text(node) -> str:
    if not node:
        return ""
    if "simpleText" in node:
        return node["simpleText"]
    if "runs" in node:
        return "".join(r.get("text", "") for r in node["runs"])
    return ""


def parse_video_renderer(vr: dict) -> "Video | None":
    vid = vr.get("videoId")
    if not vid:
        return None
    title = _text(vr.get("title"))
    if not title:
        return None
    channel = _text(vr.get("ownerText") or vr.get("shortBylineText"))
    duration = _text(vr.get("lengthText"))
    thumbs = (vr.get("thumbnail") or {}).get("thumbnails") or []
    thumb_url = thumbs[0]["url"] if thumbs else ""
    return Video(id=vid, title=title, channel=channel, duration=duration, thumbnail_url=thumb_url)


def extract_videos(data, keys=RENDERER_KEYS) -> list[Video]:
    seen: set[str] = set()
    out: list[Video] = []
    for renderer in iter_renderers(data, keys):
        video = parse_video_renderer(renderer)
        if video and video.id not in seen:
            seen.add(video.id)
            out.append(video)
    return out
