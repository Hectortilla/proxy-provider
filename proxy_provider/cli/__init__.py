import argparse
import asyncio

from proxy_provider.db import scrape_and_update


def _scrape_and_update(_args):
    scrape_and_update()


def cli() -> None:
    parser = argparse.ArgumentParser(prog="proxy-provider")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scrape-and-update", help="Refresh proxy database")

    args = parser.parse_args()
    if args.command == "scrape-and-update":
        asyncio.run(scrape_and_update())


if __name__ == "__main__":
    cli()
