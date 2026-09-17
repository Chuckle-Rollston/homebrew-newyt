# newyt

A terminal YouTube client:

- **Home** — your own recommended videos (reads your real, logged-in YouTube feed)
- **Watch Later** — your actual Watch Later playlist
- **History** — your actual watch history
- **Saved** — a local list you build yourself by pressing `w` on any video (see below)
- Colored ASCII-art thumbnails, arrow-key navigation
- Pressing Enter opens the video in a **separate private/incognito browser window, signed out** — playback never touches the YouTube account used to read your feed

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

When you press Enter on a video, `newyt` does **not** reuse that session. It opens a
brand-new, cookie-free Playwright browser window pointed at the video (in a separate
process, so it stays open after you quit the TUI), so watching never uses or affects
your signed-in session. That window also has YouTube's related-videos sidebar
permanently hidden — plain URL tricks (a narrow window, the embed player) don't hold
up, since YouTube's own JS re-shows the sidebar on resize and its embed player errors
out on many videos when opened directly, so `newyt` hides it with injected CSS that
keeps re-applying itself.

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

**Keys:** Up/Down move the selection, Left/Right switch tabs, Enter plays the
selected video privately, `w` saves it to the local Saved tab, `r` refreshes the
current tab, `q` quits.

## Privacy notes

- Your browser's cookie store is protected by the OS (e.g. macOS Keychain for
  Chrome); the first `newyt login` may prompt you to allow access.
- Imported cookies are stored locally at `~/Library/Application Support/newyt/cookies.json`
  (macOS) and never leave your machine or get sent anywhere but youtube.com.
- Fetched video lists are cached locally for 10 minutes (`~/Library/Application
  Support/newyt/cache`) to keep tab-switching fast; press `r` to force a refresh.
- Scraping YouTube's own pages instead of using the official Data API means there's
  no API key or quota, but it also means this can break if YouTube changes its page
  structure, and it's against YouTube's Terms of Service to automate a personal
  account this way — use at your own risk, on your own account.
