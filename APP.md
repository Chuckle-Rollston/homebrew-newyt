# newyt — agent reference

Terminal YouTube client (curses TUI). Reads a real signed-in YouTube feed via
cookie import (never drives Google's login flow), plays videos by downloading
them with yt-dlp (never loads youtube.com for playback), and keeps two local
lists (Saved, Downloaded) alongside three YouTube-backed tabs (Home, Watch
Later, History).

This file is a map for agents editing this codebase, not user docs — see
`README.md` for that. When you change behavior described here, update this
file in the same commit.

## Module map

```
newyt/
  cli.py              entry point (argparse: login/logout/default-run)
  tui.py               curses UI: tabs, thumbnails, key handling, progress bar
  browser.py           reads Home/Watch Later/History via Playwright + cookies
  cookies.py            imports session cookies from a real browser (browser_cookie3)
  extract.py            parses YouTube's component JSON into Video objects
  models.py             Video dataclass
  cache.py               10-min TTL disk cache for the three YouTube-backed tabs
  saved.py                local "Saved" list (press w)
  downloaded.py            registry backing the "Downloaded" tab
  play.py                spawns _playback_worker detached; open_local_file()
  _playback_worker.py     yt-dlp + ffmpeg download, progress reporting, opens file
  ascii_art.py            thumbnail -> colored ASCII (or grayscale fallback)
  config.py               all on-disk paths (single source of truth)
  __main__.py              `python -m newyt`
```

## Data flow

**Reading a tab** (Home/Watch Later/History):
`tui.App.load_tab()` → `cache.load_cache()` (10 min TTL) → on miss,
`browser.fetch_home/watch_later/history()` → `browser._fetch()` launches a
**headless** Playwright Chromium, injects cookies from `cookies.load()`,
navigates, reads `document.querySelector('ytd-app').data` (NOT
`window.ytInitialData` — that's a skeleton-only snapshot on Home/History; real
content hydrates into the live component tree) → `extract.extract_videos()`
parses it into `list[Video]` → cached to disk.

**Playing a video** (Enter key): `tui.py` → `play.open_private(url)` spawns
`python -m newyt._playback_worker <url>` as a **fully detached** subprocess
(`start_new_session=True`, stdio → DEVNULL — required, since yt-dlp prints
progress even with `quiet: True` and would otherwise corrupt the curses
screen). The worker extracts info, downloads+merges via yt-dlp/ffmpeg to
`~/Desktop/youtube videos`, writes progress to a shared JSON file the whole
time, registers the result in `downloaded.py`, then opens the file with the
OS default app. The TUI never talks to the worker directly — it's pure
filesystem polling (see below).

**Cross-process progress bar**: the worker and the TUI are separate OS
processes with no shared memory. `tui.App.run()` sets
`stdscr.timeout(300)` so the main loop redraws every 300ms even with no
keypress (`getch()` returns -1 → `continue`), and `draw()` reads
`config.download_progress_file()` each frame. The worker writes
`{"id", "title", "status", "percent"}` to that file via yt-dlp's
`progress_hooks`/`postprocessor_hooks`, and deletes it ~1.5s after finishing
(the delay lets the TUI render "finished" before it vanishes).

**Saved / Downloaded tabs**: both are `LOCAL_TABS` in `tui.py` — no network,
no disk-cache TTL, just a local JSON file re-read fresh on every idle tick
(`load_tab(clear_status=False)` in the run loop) so they update live as
downloads finish or `w` is pressed, without needing explicit cache
invalidation. Downloaded videos carry `Video.local_path`; Enter on that tab
calls `play.open_local_file()` directly instead of re-downloading.

## Key design decisions (read before "fixing" these)

- **No automated login.** Google detects Playwright/Selenium-controlled
  browsers and blocks the interactive sign-in form outright ("this browser or
  app may not be secure"/"Couldn't sign you in") — confirmed by testing, not
  a theoretical concern. `newyt login` imports existing session cookies from
  a real browser instead (`cookies.py`, via `browser_cookie3`), the same
  approach as `yt-dlp --cookies-from-browser`.

- **Read `ytd-app.data`, not `window.ytInitialData`.** On Home and History,
  the static initial payload only has skeleton/loading placeholders; real
  content hydrates client-side afterward, in a schema that also varies —
  `extract.py` handles both the classic `videoRenderer`/`playlistVideoRenderer`
  and the newer `lockupViewModel` (YouTube's current rollout for Home/History
  cards; Watch Later still uses the classic schema). If a tab starts
  returning 0 results again, check for a *third* schema variant before
  assuming the cookie/session logic broke.

- **`wait_until="domcontentloaded"`, never `"networkidle"`.** YouTube keeps
  background connections open indefinitely (websockets, analytics, autoplay
  preview loads), so `networkidle` just times out.

- **Session-expiry detection is explicit.** Stale/invalid cookies don't
  error — YouTube just renders its normal signed-out page with 0 results.
  `browser._fetch()` checks for `#avatar-btn` (present only when signed in)
  and raises `SessionExpired` (a `NotLoggedIn` subclass) instead of silently
  returning an empty list, so the TUI can tell the user to re-run
  `newyt login` rather than showing a blank tab.

- **Playback never touches youtube.com, in any form.** This went through
  three iterations, in order, each replaced for a concrete reason:
  1. Opening the real watch page in an incognito OS browser window — broke
     because YouTube's own responsive JS re-shows the related-videos sidebar
     on *any* window resize, so no static window size stays sidebar-free.
  2. A Playwright-controlled Chromium window with the sidebar hidden via
     injected/re-applying CSS — worked, but Google's bot detection would
     intermittently kill playback mid-video ("There's a problem with
     playback") since that's exactly the kind of automation-controlled
     browser it's built to catch.
  3. **Current**: `yt-dlp` downloads the video directly (no browser, no
     youtube.com page load at all), `ffmpeg` merges video+audio (modern
     YouTube rarely offers a single muxed/"progressive" format — confirmed
     empirically: 0 of 48 formats on a test video), preferring H.264/AAC
     over VP9/AV1+Opus for broad QuickTime Player compatibility, then opens
     the finished file with the OS default player.
  If you're asked to fix a playback issue, don't reach back into browser
  automation — that's the failure mode already ruled out twice.

- **Downloaded files are never auto-deleted.** `~/Desktop/youtube videos` is
  user-visible and backs the Downloaded tab — treat it as a permanent
  library, not a cache. (An earlier version cached to
  `~/Library/Application Support/newyt/downloads` with 7-day pruning; that
  was removed when the Downloaded tab was added.)

- **Colored ASCII thumbnails, not solid blocks.** `ascii_art.py` picks a
  glyph from the brightness ramp `" .:-=+*#%@"` (same as the grayscale
  fallback) and colors *that glyph* with the pixel's real color (quantized
  to xterm-256), rather than rendering solid half-block (▀) cells — the
  latter was tried first and looked like a colored bitmap, not ASCII art,
  per explicit user feedback.

- **Homebrew formula quirks** (`Formula/newyt.rb`) — several dead ends worth
  not repeating:
  - `virtualenv_install_with_resources` / `pip_install_and_link` force
    `--no-binary=:all:` and expect sdist `resource` blocks; wheel resources
    fail ("not installable"). Also, `virtualenv_create` makes a venv
    `--without-pip`, so there's no `libexec/bin/pip` to call directly.
  - Fix in place: `install` calls the outer `python@3.12`'s pip pointed at
    the venv (`pip -m ... --python=<venv>/bin/python install --only-binary=:all: <buildpath>`),
    which resolves all dependencies straight from PyPI. PyPI network access
    *is* allowed inside Homebrew's build sandbox (confirmed); arbitrary CDNs
    are not (that's why `playwright install chromium` can't run during
    `brew install` — Chromium downloads from Google's CDN, so that install
    step happens at first real use instead, via `browser._install_chromium()`).
  - `depends_on "ffmpeg"` is required (playback needs it to merge streams).
  - The repo is named `homebrew-newyt` (not `newyt`) so `brew tap
    Chuckle-Rollston/newyt` resolves without a full URL — Homebrew's naming
    convention for personal taps.
  - **The formula's `sha256` must be updated on every commit that changes
    tracked files**, even doc-only changes: it's the checksum of the
    `v0.1.0` tag's tarball, and that tag gets force-moved to the latest
    commit on every change (see repo history) rather than cutting new
    version tags per change, since this is a pre-1.0 personal tap.

## Known fragility / things that can silently break

- `browser.py`/`extract.py` scrape YouTube's internal page data structures,
  not a stable public API — a YouTube redesign can break extraction with no
  warning beyond tabs returning 0 results (which `SessionExpired` detection
  won't catch, since that's specifically about auth state, not schema
  drift).
- `_playback_worker.py` runs fully detached with **no visible stdout/stderr**
  by design (see "no automated login" — actually see the sidebar-hiding
  history above for *why* redirection matters: yt-dlp prints progress even
  with `quiet: True`). Any bug in that process is invisible unless you check
  `~/Library/Application Support/newyt/playback_worker.log`
  (`_playback_worker._log_error`/`_log_message`) — always check that file
  first when debugging a playback report, before adding print statements
  that will never be seen.
- `cookies.py` depends on `browser_cookie3` successfully decrypting the
  target browser's cookie store (macOS Keychain access for Chrome, etc.) —
  this can break with browser updates that change encryption schemes; it's
  a known-fragile dependency, not actively maintained by this project.

## Local state (all under `~/Library/Application Support/newyt/` unless noted)

| Path | Written by | Purpose |
|---|---|---|
| `cookies.json` | `cookies.save()` | imported session cookies |
| `cache/*.json` | `cache.save_cache()` | 10-min TTL cache for Home/Watch Later/History |
| `cache/thumbs/*.jpg` | `ascii_art._fetch_bytes()` | thumbnail image cache (no TTL) |
| `saved.json` | `saved.add()` | local Saved list |
| `downloaded.json` | `downloaded.add()` | Downloaded tab registry (id/title/channel/duration/thumbnail/local_path) |
| `download_progress.json` | `_playback_worker._write_progress()` | live progress, polled by the TUI, self-deletes when done |
| `playback_worker.log` | `_playback_worker._log_error/_log_message()` | only place a playback failure is visible |
| `~/Desktop/youtube videos/` | `_playback_worker.py` (not under config_dir — intentionally user-visible) | downloaded video files, named `Title [id].mp4` |

## Testing notes

No automated test suite exists. Everything so far has been verified by
direct execution (real yt-dlp downloads, real Playwright fetches against a
real logged-in cookie jar, real curses rendering via `script -q` in a pty).
One caveat found during development: fully scripting real `getch()` keyboard
input through a *nested* `pty.fork()` in an already-sandboxed harness was
flaky at the harness level (inconsistent child process lifecycle across
runs) — unrelated to `tui.py` itself. Prefer direct component calls
(`app.draw()`, calling handler logic inline) or `script -q ... python3 -c
"..."` for pty-backed curses tests; if you need genuine keystroke-through-
getch() coverage, expect to verify manually in a real terminal.
