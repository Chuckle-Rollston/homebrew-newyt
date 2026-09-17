import argparse
import sys

from . import browser
from . import cookies as cookies_mod
from .tui import main as tui_main


def main() -> None:
    parser = argparse.ArgumentParser(prog="newyt", description="A terminal YouTube client")
    sub = parser.add_subparsers(dest="command")

    login_parser = sub.add_parser(
        "login",
        help="Import your YouTube session from a browser you're already signed into",
    )
    login_parser.add_argument(
        "--browser",
        default="chrome",
        choices=sorted(cookies_mod.BROWSERS),
        help="Browser to read your YouTube cookies from (default: chrome)",
    )

    sub.add_parser("logout", help="Forget the imported YouTube session")
    args = parser.parse_args()

    if args.command == "login":
        try:
            count = browser.login(args.browser)
        except browser.NotLoggedIn as e:
            print(e)
            sys.exit(1)
        print(f"Imported {count} YouTube cookies from {args.browser}.")
        print("You can now run `newyt`.")
        return

    if args.command == "logout":
        cookies_mod.clear()
        print("Logged out.")
        return

    if not browser.is_logged_in():
        print("You're not logged in yet. Run `newyt login` first")
        print("(add --browser firefox/brave/edge/safari/opera if you don't use Chrome).")
        print("This reads your existing YouTube session cookies from that browser --")
        print("it's only used to read your home feed, watch later, and history.")
        print("Videos always play via yt-dlp + VLC/your default player, never youtube.com itself.")
        sys.exit(1)

    tui_main()


if __name__ == "__main__":
    main()
