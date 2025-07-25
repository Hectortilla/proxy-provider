import asyncio
import colorlog
from logging import getLogger
from db.csv_store import CsvStore
from health_check import bulk_health_check
from scrapers import scrape_free_proxy_list, scrape_spys

from utils.logging import configure_logging

configure_logging("INFO")

logger = getLogger(__name__)

async def scrape_and_update_db():
    sources = scrape_spys() | scrape_free_proxy_list()
    logger.info(f"Total number of scraped proxies: {len(sources)}")
    res = await bulk_health_check(sources)
    logger.info(f"Total number of healthy proxies: {len([r for r in res if r[2]])}")
    store = CsvStore()
    store.update_from_health_check(res)


if __name__ == "__main__":
    # This is the standard way to run a top-level async function from a script
    asyncio.run(scrape_and_update_db())
