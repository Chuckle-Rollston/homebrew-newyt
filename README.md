# newyt

A terminal YouTube client:

- **Home** — your own recommended videos (reads your real, logged-in YouTube feed)
- **Watch Later** — your actual Watch Later playlist
- **History** — your actual watch history
- ASCII-art thumbnails, arrow-key navigation
- Pressing Enter opens the video in a **separate private/incognito browser window, signed out** — playback never touches the YouTube account used to read your feed

## How it works

`newyt` uses [Playwright](https://playwright.dev/) to drive a small, local, persistent
Chromium profile that only you control. You log in once (`newyt login`); after that,
`newyt` reads `https://www.youtube.com/`, your Watch Later playlist, and your history
page from that profile in the background to build the three tabs.

When you press Enter on a video, `newyt` does **not** reuse that profile. It launches
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

1. Push this repo to GitHub and cut a release tag, e.g. `v0.1.0`.
2. Update `Formula/newyt.rb`: set `homepage`/`url` to your repo, and `sha256` to the
   checksum of the release tarball (`shasum -a 256 <tarball>`).
3. Others can then install with:

```bash
brew tap YOUR_GITHUB_USERNAME/newyt https://github.com/YOUR_GITHUB_USERNAME/newyt
brew install newyt
```

(Installing bundles a Chromium download via Playwright, so first install takes a
minute or two.)

## Usage

```bash
newyt login    # opens a real browser window once, log into YouTube there
newyt          # launches the terminal app
newyt logout   # forgets the saved login
```

**Keys:** Up/Down move the selection, Left/Right switch tabs, Enter plays the
selected video privately, `r` refreshes the current tab, `q` quits.

## Privacy notes

- The browser profile used to read your feed lives at
  `~/Library/Application Support/newyt/browser-profile` (macOS) and never leaves
  your machine.
- Fetched video lists are cached locally for 10 minutes (`~/Library/Application
  Support/newyt/cache`) to keep tab-switching fast; press `r` to force a refresh.
- Scraping YouTube's own pages instead of using the official Data API means there's
  no API key or quota, but it also means this can break if YouTube changes its page
  structure, and it's against YouTube's Terms of Service to automate a personal
  account this way — use at your own risk, on your own account.
