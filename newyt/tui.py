import curses
import hashlib
import json

from . import browser, downloaded, play, saved
from .ascii_art import fetch_thumbnail_ascii, fetch_thumbnail_color_cells
from .cache import load_cache, save_cache
from .config import cache_dir, download_progress_file

TABS = [
    ("Home", "home", browser.fetch_home),
    ("Watch Later", "watch_later", browser.fetch_watch_later),
    ("History", "history", browser.fetch_history),
    ("Saved", "saved", saved.load),
    ("Downloaded", "downloaded", downloaded.load),
]
LOCAL_TABS = {"saved", "downloaded"}


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

        # Thumbnails: use real color (xterm-256 half-block cells) when the
        # terminal supports it, falling back to the old grayscale ASCII
        # shading otherwise. Color pairs are allocated lazily and cached,
        # since curses needs one pair per distinct (fg, bg) combination.
        self.use_color = curses.COLORS >= 256
        self.color_pairs: dict[tuple[int, int], int] = {}
        self.next_pair = 10

    def _pair_for(self, fg: int, bg: int) -> int:
        key = (fg, bg)
        pid = self.color_pairs.get(key)
        if pid is not None:
            return pid
        if self.next_pair >= curses.COLOR_PAIRS:
            return 0
        pid = self.next_pair
        try:
            curses.init_pair(pid, fg, bg)
        except curses.error:
            return 0
        self.color_pairs[key] = pid
        self.next_pair += 1
        return pid

    def current_tab(self):
        return TABS[self.tab_index]

    def _read_progress(self) -> "dict | None":
        f = download_progress_file()
        if not f.exists():
            return None
        try:
            return json.loads(f.read_text())
        except Exception:
            return None

    def _format_progress(self, progress: dict, width: int = 30) -> str:
        title = (progress.get("title") or "")[:40]
        status = progress.get("status")
        if status == "downloading":
            pct = progress.get("percent")
            if pct is None:
                return f"Downloading: {title} (size unknown)..."
            filled = max(0, min(width, int(width * pct / 100)))
            bar = "#" * filled + "-" * (width - filled)
            return f"Downloading: {title} [{bar}] {pct:.0f}%"
        if status == "merging":
            return f"Merging: {title}..."
        if status == "finished":
            return f"Downloaded: {title} -- opening..."
        return f"{title}: {status}"

    def load_tab(self, force: bool = False, clear_status: bool = True) -> None:
        name, key, fetcher = self.current_tab()
        if key in LOCAL_TABS:
            # Purely local data (Saved/Downloaded) -- always cheap, always
            # fresh, no network fetch or disk cache needed.
            self.videos_by_tab[key] = fetcher()
            if clear_status:
                self.status = ""
            return
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
        except browser.SessionExpired:
            self.status = "Session expired. Quit and run `newyt login` again."
            videos = []
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
        # Give the thumbnail pane most of the width -- the list only needs
        # enough room for a readable title.
        list_w = max(20, min(w // 3, 50))
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
            avail_w = max(10, w - dx - 2)
            avail_h = max(4, h - 8)
            cache_path = cache_dir() / (hashlib.sha1(v.thumbnail_url.encode()).hexdigest() + ".jpg")
            row = 2

            cells = fetch_thumbnail_color_cells(
                v.thumbnail_url, cache_path, width=min(90, avail_w), height=min(35, avail_h)
            ) if self.use_color else None

            if cells:
                for cell_row in cells:
                    if row >= h - 6:
                        break
                    col = dx
                    for char, fg in cell_row:
                        if col >= w - 1:
                            break
                        try:
                            stdscr.addstr(row, col, char, curses.color_pair(self._pair_for(fg, -1)))
                        except curses.error:
                            pass
                        col += 1
                    row += 1
            else:
                lines = fetch_thumbnail_ascii(
                    v.thumbnail_url, cache_path, width=min(70, avail_w), height=min(30, avail_h)
                )
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

        progress = self._read_progress()
        if progress:
            status = self._format_progress(progress, width=max(10, min(40, w - 30)))
            status_attr = curses.color_pair(2)
        else:
            status = self.status or "up/down navigate  left/right tabs  enter play  w save to watch later  r refresh  q quit"
            status_attr = curses.A_NORMAL
        try:
            stdscr.addstr(h - 1, 1, status[: max(0, w - 2)], status_attr)
        except curses.error:
            pass
        stdscr.refresh()

    def run(self) -> None:
        # A short timeout (rather than blocking indefinitely) lets the loop
        # keep redrawing -- and so polling the download-progress file --
        # even while the user isn't pressing anything.
        self.stdscr.timeout(300)
        self.load_tab()
        while True:
            # Keep local tabs (Saved/Downloaded) live: cheap local reads, so
            # just re-read on every idle tick rather than tracking when a
            # background download finished.
            if self.current_tab()[1] in LOCAL_TABS:
                self.load_tab(clear_status=False)
            self.draw()
            key = self.stdscr.getch()
            if key == -1:
                continue
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
                    v = videos[self.sel]
                    if v.local_path:
                        # Already downloaded (the Downloaded tab) -- open
                        # the file directly instead of re-downloading.
                        play.open_local_file(v.local_path)
                        self.status = f"Playing (downloaded): {v.title[:50]}"
                    else:
                        play.open_private(v.url)
                        self.status = f"Downloading & playing: {v.title[:50]}"
            elif key == ord("w"):
                if videos and 0 <= self.sel < len(videos):
                    v = videos[self.sel]
                    added = saved.add(v)
                    self.videos_by_tab.pop("saved", None)
                    self.status = (f"Saved: {v.title[:50]}" if added else f"Already saved: {v.title[:50]}")
            elif key == ord("r"):
                self.load_tab(force=True)
            elif key == ord("q"):
                break


def main() -> None:
    curses.wrapper(lambda stdscr: App(stdscr).run())
