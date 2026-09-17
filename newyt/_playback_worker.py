"""Standalone process that opens one video in a fresh, cookie-free browser
window (nothing carried over from the session used to read your feed --
genuinely signed out) with the related-videos sidebar permanently hidden.

Run as `python -m newyt._playback_worker <url>`, detached from the TUI
process so closing/quitting newyt doesn't close the video window.

Hiding the sidebar isn't a one-shot job:
- A <style> tag injected before YouTube's own SPA bootstrap runs gets wiped
  by that bootstrap, so the hide has to happen after the page settles.
- YouTube's responsive layout re-shows the sidebar on every window resize,
  so the hide has to keep re-applying itself (MutationObserver + resize
  listener), not just run once.
- A fresh, cookie-free session often hits a cookie-consent screen first;
  dismissing it navigates the page, which would otherwise wipe out
  anything injected before that point. So this also re-applies on every
  page load, not just the first one, and best-effort auto-dismisses that
  consent screen so it doesn't block the video at all.

This process runs detached with no visible stdout/stderr, so any failure
is logged to ~/Library/Application Support/newyt/playback_worker.log
(or the platform equivalent) instead of vanishing silently.
"""
import sys
import traceback

from .browser import _install_chromium
from .config import config_dir

HIDE_SIDEBAR_JS = """
() => {
  const SIDEBAR_SELECTORS = [
    '#secondary', '#related',
    'ytd-watch-next-secondary-results-renderer',
    '#panels-full-bleed-container',
  ];
  const WIDEN_SELECTORS = [
    '#primary.ytd-watch-flexy', '#columns.ytd-watch-flexy', '#page-manager',
  ];
  const CONSENT_BUTTON_TEXTS = ['accept all', 'i agree', 'accept the use of cookies'];

  function hide() {
    for (const sel of SIDEBAR_SELECTORS) {
      document.querySelectorAll(sel).forEach((el) => el.style.setProperty('display', 'none', 'important'));
    }
    for (const sel of WIDEN_SELECTORS) {
      const el = document.querySelector(sel);
      if (el) {
        el.style.setProperty('max-width', '100%', 'important');
        el.style.setProperty('width', '100%', 'important');
      }
    }
  }

  function dismissConsent() {
    const candidates = document.querySelectorAll('button, tp-yt-paper-button, yt-button-renderer');
    for (const b of candidates) {
      const text = (b.innerText || b.textContent || '').trim().toLowerCase();
      if (CONSENT_BUTTON_TEXTS.includes(text)) {
        b.click();
        return;
      }
    }
  }

  function tick() {
    dismissConsent();
    hide();
  }

  tick();
  window.addEventListener('resize', tick);
  new MutationObserver(tick).observe(document.documentElement, {
    childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'hidden'],
  });
  setInterval(tick, 1000);
}
"""


def _log_path():
    return config_dir() / "playback_worker.log"


def _log_error(context: str) -> None:
    try:
        with open(_log_path(), "a") as f:
            f.write(f"--- {context} ---\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        pass


def _launch(p):
    try:
        return p.chromium.launch(headless=False)
    except Exception:
        _install_chromium()
        return p.chromium.launch(headless=False)


def main() -> None:
    if len(sys.argv) < 2:
        return
    url = sys.argv[1]

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            chromium = _launch(p)
            ctx = chromium.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()

            def apply_hide():
                try:
                    page.evaluate(HIDE_SIDEBAR_JS)
                except Exception:
                    _log_error("apply_hide")

            # Re-apply on every load, not just the first -- a cookie-consent
            # screen (common on a fresh, cookie-free session) navigates the
            # page when dismissed, which would otherwise wipe this out.
            page.on("load", lambda: apply_hide())

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            apply_hide()

            try:
                page.wait_for_event("close", timeout=0)
            except Exception:
                pass
            try:
                chromium.close()
            except Exception:
                pass
    except Exception:
        _log_error("main")


if __name__ == "__main__":
    main()
