from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

DEFAULT_SCHEME = "http"


def scrape_spys() -> set[str]:
    SPYS_URL = "https://spys.me/proxy.txt"
    with httpx.Client(timeout=10) as client:
        r = client.get(SPYS_URL)
        r.raise_for_status()
        _ = r.text
        return set(re.findall(r"\d+(?:\.\d+){3}:\d+", r.text))


def scrape_free_proxy_list() -> set[str]:
    FREE_PROXY_LIST = "https://free-proxy-list.net/"
    with httpx.Client(timeout=10) as client:
        r = client.get(FREE_PROXY_LIST)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cells = soup.select(".fpl-list .table tbody tr td")
        return {
            f"{cells[i].text.strip()}:{cells[i+1].text.strip()}"
            for i in range(0, len(cells), 8)
        }
