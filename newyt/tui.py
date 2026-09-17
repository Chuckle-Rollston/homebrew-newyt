import curses
import hashlib

from . import browser, play
from .ascii_art import fetch_thumbnail_ascii
from .cache import load_cache, save_cache
from .config import cache_dir

TABS = [
    ("Home", "home", browser.fetch_home),
    ("Watch Later", "watch_later", browser.fetch_watch_later),
    ("History", "history", browser.fetch_history),
]


class App:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.tab_index = 0
        self.sel = 0
        self.scroll = 0
        self.videos_by_tab: dict[str, list] = {}
        self.status = ""

        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_CYAN, -1)

    def current_tab(self):
        return TABS[self.tab_index]

    def load_tab(self, force: bool = False) -> None:
        name, key, fetcher = self.current_tab()
        if not force and key in self.videos_by_tab:
            return
        cached = None if force else load_cache(key)
        if cached is not None:
            self.videos_by_tab[key] = cached
            return
        self.status = f"Loading {name} (this opens a background browser, may take a few seconds)..."
        self.draw()
        try:
            videos = fetcher()
        except browser.NotLoggedIn:
            self.status = "Not logged in. Quit and run `newyt login` first."
            videos = []
        except browser.BrowserNotInstalled as e:
            self.status = str(e)
            videos = []
        except Exception as e:
            self.status = f"Error loading {name}: {e}"
            videos = []
        else:
            self.status = ""
        self.videos_by_tab[key] = videos
        if videos:
            save_cache(key, videos)

    def draw(self) -> None:
        stdscr = self.stdscr
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        x = 1
        for i, (name, _key, _f) in enumerate(TABS):
            attr = (curses.color_pair(2) | curses.A_BOLD) if i == self.tab_index else curses.A_NORMAL
            label = f" {name} "
            if x + len(label) < w:
                stdscr.addstr(0, x, label, attr)
            x += len(label) + 1
        stdscr.hline(1, 0, curses.ACS_HLINE, w)

        _name, key, _f = self.current_tab()
        videos = self.videos_by_tab.get(key, [])
        list_w = max(10, w // 2 - 1)
        list_h = h - 4

        if not videos and not self.status:
            stdscr.addstr(3, 2, "No videos found.")

        for i in range(list_h):
            idx = self.scroll + i
            if idx >= len(videos):
                break
            v = videos[idx]
            line = v.title[: max(1, list_w - 2)]
            attr = curses.color_pair(1) if idx == self.sel else curses.A_NORMAL
            try:
                stdscr.addstr(3 + i, 1, line.ljust(list_w - 1), attr)
            except curses.error:
                pass

        if w > list_w + 1:
            stdscr.vline(2, list_w + 1, curses.ACS_VLINE, max(0, h - 3))

        if videos and 0 <= self.sel < len(videos) and w > list_w + 5:
            v = videos[self.sel]
            dx = list_w + 3
            ascii_w = max(10, min(40, w - dx - 2))
            cache_path = cache_dir() / (hashlib.sha1(v.thumbnail_url.encode()).hexdigest() + ".jpg")
            lines = fetch_thumbnail_ascii(v.thumbnail_url, cache_path, width=ascii_w, height=14)
            row = 2
            for l in lines:
                if row >= h - 6:
                    break
                try:
                    stdscr.addstr(row, dx, l)
                except curses.error:
                    pass
                row += 1
            info_y = row + 1
            for j, text in enumerate((v.title, v.channel, v.duration)):
                try:
                    stdscr.addstr(info_y + j, dx, text[: max(0, w - dx - 1)], curses.A_BOLD if j == 0 else curses.A_NORMAL)
                except curses.error:
                    pass

        status = self.status or "up/down navigate  left/right tabs  enter play (private)  r refresh  q quit"
        try:
            stdscr.addstr(h - 1, 1, status[: max(0, w - 2)])
        except curses.error:
            pass
        stdscr.refresh()

    def run(self) -> None:
        self.load_tab()
        while True:
            self.draw()
            key = self.stdscr.getch()
            videos = self.videos_by_tab.get(self.current_tab()[1], [])

            if key in (curses.KEY_UP, ord("k")):
                if self.sel > 0:
                    self.sel -= 1
                    if self.sel < self.scroll:
                        self.scroll = self.sel
            elif key in (curses.KEY_DOWN, ord("j")):
                if self.sel < len(videos) - 1:
                    self.sel += 1
                    h, _w = self.stdscr.getmaxyx()
                    list_h = h - 4
                    if self.sel >= self.scroll + list_h:
                        self.scroll = self.sel - list_h + 1
            elif key == curses.KEY_LEFT:
                self.tab_index = (self.tab_index - 1) % len(TABS)
                self.sel = 0
                self.scroll = 0
                self.load_tab()
            elif key == curses.KEY_RIGHT:
                self.tab_index = (self.tab_index + 1) % len(TABS)
                self.sel = 0
                self.scroll = 0
                self.load_tab()
            elif key in (curses.KEY_ENTER, 10, 13):
                if videos and 0 <= self.sel < len(videos):
                    play.open_private(videos[self.sel].url)
                    self.status = f"Opened privately: {videos[self.sel].title[:50]}"
            elif key == ord("r"):
                self.load_tab(force=True)
            elif key == ord("q"):
                break


def main() -> None:
    curses.wrapper(lambda stdscr: App(stdscr).run())
