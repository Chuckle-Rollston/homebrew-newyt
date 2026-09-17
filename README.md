# newyt

A terminal YouTube client:

- **Home** — your own recommended videos (reads your real, logged-in YouTube feed)
- **Watch Later** — your actual Watch Later playlist
- **History** — your actual watch history
- ASCII-art thumbnails, arrow-key navigation
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

When you press Enter on a video, `newyt` does **not** reuse that session. It launches
your real installed browser (Chrome/Brave/Edge/Firefox) in a fresh incognito/private
window pointed at the video, so watching never uses or affects your signed-in session.

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

This repo includes `Formula/newyt.rb` for distributing via a personal Homebrew tap.
To use it:

1. Cut a release tag, e.g. `v0.1.0`, on [Chuckle-Rollston/newyt](https://github.com/Chuckle-Rollston/newyt).
2. Update `Formula/newyt.rb`'s `sha256` to the checksum of that release tarball
   (`shasum -a 256 <tarball>`).
3. Others can then install with:

```bash
brew tap Chuckle-Rollston/newyt https://github.com/Chuckle-Rollston/newyt
brew install newyt
```

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
selected video privately, `r` refreshes the current tab, `q` quits.

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
