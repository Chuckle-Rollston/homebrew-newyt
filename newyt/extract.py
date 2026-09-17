"""Parses video info out of YouTube's own component data.

Pages are read from `document.querySelector('ytd-app').data` in a headless
Playwright page (not the static `window.ytInitialData` blob, which on
several pages only holds skeleton/loading placeholders until the client
hydrates real content into the component tree). YouTube uses two schemas
for video entries depending on the page/rollout: the classic
videoRenderer/playlistVideoRenderer, and the newer lockupViewModel. Both
are handled here since either can show up on any given page.
"""
from .models import Video


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


def parse_lockup_view_model(lv: dict) -> "Video | None":
    if lv.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO":
        return None
    vid = lv.get("contentId")
    if not vid:
        return None
    metadata_vm = (lv.get("metadata") or {}).get("lockupMetadataViewModel") or {}
    title = (metadata_vm.get("title") or {}).get("content", "")
    if not title:
        return None

    channel = ""
    rows = ((metadata_vm.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows") or []
    if rows:
        parts = rows[0].get("metadataParts") or []
        if parts:
            channel = (parts[0].get("text") or {}).get("content", "")

    thumbnail_vm = (lv.get("contentImage") or {}).get("thumbnailViewModel") or {}
    sources = (thumbnail_vm.get("image") or {}).get("sources") or []
    thumb_url = sources[0].get("url", "") if sources else ""

    duration = ""
    for overlay in thumbnail_vm.get("overlays") or []:
        badges = ((overlay.get("thumbnailBottomOverlayViewModel") or {}).get("badges")) or []
        for badge in badges:
            text = (badge.get("thumbnailBadgeViewModel") or {}).get("text")
            if text:
                duration = text
                break
        if duration:
            break

    return Video(id=vid, title=title, channel=channel, duration=duration, thumbnail_url=thumb_url)


PARSERS = {
    "videoRenderer": parse_video_renderer,
    "playlistVideoRenderer": parse_video_renderer,
    "lockupViewModel": parse_lockup_view_model,
}

RENDERER_KEYS = tuple(PARSERS)


def iter_renderers(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                yield k, v
            else:
                yield from iter_renderers(v, keys)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_renderers(item, keys)


def extract_videos(data, keys=None) -> list[Video]:
    keys = keys or RENDERER_KEYS
    seen: set[str] = set()
    out: list[Video] = []
    for key, renderer in iter_renderers(data, keys):
        parser = PARSERS.get(key, parse_video_renderer)
        video = parser(renderer)
        if video and video.id not in seen:
            seen.add(video.id)
            out.append(video)
    return out
