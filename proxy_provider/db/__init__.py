import asyncio
from logging import getLogger

from proxy_provider.db.csv_store import CsvStore
from proxy_provider.health_check import bulk_health_check, TARGET_URL, CONCURRENCY, TIMEOUT_S
from proxy_provider.scrapers import scrape_free_proxy_list, scrape_spys
from proxy_provider.utils.logging import configure_logging

configure_logging("INFO")

logger = getLogger(__name__)

async def scrape_and_update(concurrency: int = CONCURRENCY, target_url: str = TARGET_URL, timeout: float = TIMEOUT_S):
    """Scrape proxies from multiple sources and perform a health check on them."""

    sources = scrape_spys() | scrape_free_proxy_list()
    logger.info(f"Total number of scraped proxies: {len(sources)}")
    res = await bulk_health_check(sources, concurrency, target_url, timeout)
    logger.info(f"Total number of healthy proxies: {len([r for r in res if r[2]])}")
    store = CsvStore()
    store.update_from_health_check(res)


if __name__ == "__main__":
    # This is the standard way to run a top-level async function from a script
    asyncio.run(scrape_and_update())
