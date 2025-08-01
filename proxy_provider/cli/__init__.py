import argparse
import asyncio

from proxy_provider.db import scrape_and_update
from proxy_provider.health_check import TARGET_URL, CONCURRENCY, TIMEOUT_S

def cli() -> None:
    parser = argparse.ArgumentParser(prog="proxy-provider")
    sub = parser.add_subparsers(dest="command", required=True)

    sub_parser = sub.add_parser("scrape-and-update", help="Refresh proxy database")
    sub_parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help=f"Number of concurrent requests for health check (default: {CONCURRENCY})",
    )
    sub_parser.add_argument(
        "--target-url",
        type=str,
        default=TARGET_URL,
        help=f"Target URL for health check (default: {TARGET_URL})",
    )
    sub_parser.add_argument(
        "--timeout",
        type=float,
        default=TIMEOUT_S,
        help=f"Timeout for health check requests in seconds (default: {TIMEOUT_S})",
    )

    args = parser.parse_args()
    if args.command == "scrape-and-update":
        asyncio.run(scrape_and_update(args.concurrency, args.target_url, args.timeout))


if __name__ == "__main__":
    cli()