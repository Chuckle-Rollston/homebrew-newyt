# newyt

A terminal YouTube client:

- **Home** — your own recommended videos (reads your real, logged-in YouTube feed)
- **Watch Later** — your actual Watch Later playlist
- **History** — your actual watch history
- **Saved** — a local list you build yourself by pressing `w` on any video (see below)
- **Downloaded** — every video you've played, saved permanently to `~/Desktop/youtube videos`
- Colored ASCII-art thumbnails, arrow-key navigation
- Pressing Enter downloads and plays the video **without ever loading youtube.com** — no ads, no related-videos sidebar, no exposure to YouTube's web player, and playback never touches the account used to read your feed — with a live progress bar while it downloads

## How it works

Google blocks the interactive sign-in flow inside an automation-controlled browser
(Playwright/Selenium), so `newyt` never tries to log in for you. Instead, `newyt login`
imports your existing YouTube session cookies from a real browser you're already
signed into (Chrome by default; `--browser firefox/brave/edge/safari/opera` for
others) — the same technique tools like `yt-dlp --cookies-from-browser` use.

Those cookies are stored locally and handed to a headless [Playwright](https://playwright.dev/)
Chromium instance, which `newyt` uses to read `https://www.youtube.com/`, your
Watch Later playlist, and your history page in the background to build the three
tabs.

When you press Enter on a video, `newyt` does **not** open youtube.com at all, in any
browser. Earlier versions played back through a browser window, but a signed-out,
automation-controlled browser is exactly what YouTube's bot detection is built to
catch, and it would sometimes error out mid-video ("There's a problem with
playback"). Instead, `newyt` uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) (a
well-maintained YouTube extractor, much more robust than scraping the page yourself)
to download the video to `~/Desktop/youtube videos`, merging the separate video and
audio streams via [ffmpeg](https://ffmpeg.org/) (installed automatically via
Homebrew) -- modern YouTube rarely offers a single muxed file anymore -- then opens
it with your system's default player (QuickTime Player on a stock Mac) once it's
done.

This all happens in a separate detached process (spawned so it keeps running after
you quit the TUI), which reports progress back to the TUI as a live progress bar in
the status line, and never uses the cookies from `newyt login`, so playback is
genuinely signed out. Every video you play gets kept in the **Downloaded** tab
afterward -- pressing Enter there opens the file straight from disk instead of
re-downloading it.

Nothing is sent anywhere except to youtube.com itself — there's no third-party server,
API key, or account involved beyond your own YouTube login.

## Install

### Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m playwright install chromium
```

### Homebrew (personal tap)

This repo is named `homebrew-newyt`, which is Homebrew's naming convention for a
personal tap repo -- it lets `brew tap Chuckle-Rollston/newyt` resolve automatically
without needing the full GitHub URL. Install with:

```bash
brew tap Chuckle-Rollston/newyt
brew install newyt
```

To publish a new release: cut a tag (e.g. `v0.1.1`), then update `Formula/newyt.rb`'s
`url` and `sha256` (`shasum -a 256 <tarball>`) to match.

## Usage

```bash
newyt login                    # imports your YouTube session from Chrome
newyt login --browser firefox  # ...or another browser
newyt                          # launches the terminal app
newyt logout                   # forgets the imported session
```

The first time you read a tab, `newyt` downloads Playwright's Chromium (one-time,
~150-200MB).

**Keys:** Up/Down move the selection, Left/Right switch tabs, Enter downloads and
plays the selected video (or opens it straight from disk on the Downloaded tab),
`w` saves it to the local Saved tab, `r` refreshes the current tab, `q` quits.

## Privacy notes

- Your browser's cookie store is protected by the OS (e.g. macOS Keychain for
  Chrome); the first `newyt login` may prompt you to allow access.
- Imported cookies are stored locally at `~/Library/Application Support/newyt/cookies.json`
  (macOS) and never leave your machine or get sent anywhere but youtube.com.
- Fetched video lists are cached locally for 10 minutes (`~/Library/Application
  Support/newyt/cache`) to keep tab-switching fast; press `r` to force a refresh.
- Every video you play is downloaded and kept permanently at
  `~/Desktop/youtube videos` (visible in the Downloaded tab) -- nothing is
  auto-deleted, so that folder will grow with use; delete files from it yourself
  if you want them gone (they'll drop out of the Downloaded tab automatically).
- Playback failures are logged to `~/Library/Application Support/newyt/playback_worker.log`,
  since that process runs detached with no visible terminal output.
- Scraping YouTube's own pages instead of using the official Data API means there's
  no API key or quota, but it also means this can break if YouTube changes its page
  structure, and it's against YouTube's Terms of Service to automate a personal
  account this way — use at your own risk, on your own account.
