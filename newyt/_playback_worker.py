"""Standalone process that opens one video in a fresh, cookie-free browser
window (nothing carried over from the session used to read your feed --
genuinely signed out) with the related-videos sidebar permanently hidden.

Run as `python -m newyt._playback_worker <url>`, detached from the TUI
process so closing/quitting newyt doesn't close the video window.

A plain "hide it with CSS at page load" doesn't survive: YouTube's own
SPA bootstrap wipes early-injected styles, and its responsive layout
re-shows the sidebar on every window resize. So this hides the sidebar
after the page has settled, then keeps re-hiding it via a MutationObserver
and a resize listener.
"""
import sys

from .browser import _install_chromium

HIDE_SIDEBAR_JS = """
() => {
  function hide() {
    const sec = document.querySelector('#secondary');
    if (sec) sec.style.setProperty('display', 'none', 'important');
    const primary = document.querySelector('#primary.ytd-watch-flexy') || document.querySelector('#columns.ytd-watch-flexy');
    if (primary) {
      primary.style.setProperty('max-width', '100%', 'important');
      primary.style.setProperty('width', '100%', 'important');
    }
  }
  hide();
  window.addEventListener('resize', hide);
  new MutationObserver(hide).observe(document.body, {
    childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'hidden'],
  });
  setInterval(hide, 1000);
}
"""


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

    with sync_playwright() as p:
        chromium = _launch(p)
        ctx = chromium.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        try:
            page.evaluate(HIDE_SIDEBAR_JS)
        except Exception:
            pass
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            chromium.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
