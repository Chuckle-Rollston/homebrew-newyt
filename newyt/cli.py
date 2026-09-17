import argparse
import shutil
import sys

from . import browser
from .config import profile_dir
from .tui import main as tui_main


def main() -> None:
    parser = argparse.ArgumentParser(prog="newyt", description="A terminal YouTube client")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("login", help="Log into YouTube in a browser window (stored only on this machine)")
    sub.add_parser("logout", help="Forget the saved YouTube login")
    args = parser.parse_args()

    if args.command == "login":
        try:
            browser.login()
        except browser.BrowserNotInstalled as e:
            print(e)
            sys.exit(1)
        return

    if args.command == "logout":
        shutil.rmtree(profile_dir(), ignore_errors=True)
        print("Logged out.")
        return

    if not browser.is_logged_in():
        print("You're not logged in yet. Run `newyt login` first.")
        print("Your login is stored only in a local browser profile on this machine,")
        print("and is only used to read your home feed, watch later, and history.")
        print("Videos always play in a separate private/incognito window, signed out.")
        sys.exit(1)

    tui_main()


if __name__ == "__main__":
    main()
