"""Common helper functions to check whether a proxy is alive and how fast it is.

We expose **one synchronous** and **one asynchronous** function
"""

from __future__ import annotations

import asyncio
import time
from typing import Iterable, Optional

import httpx
from tqdm import tqdm

TEST_URL = "https://httpbin.org/ip"
TIMEOUT_S = 5.0
MAX_PARALLEL = 100
DEFAULT_SCHEME = "http"


def _build_proxy_url(ip_port: str, scheme: str = "http") -> str:
    """Return fully qualified proxy URL (adds the scheme prefix)."""
    return f"{scheme}://{ip_port}"


# ---------------------------- asynchronous helper ---------------------------


async def _proxy_health_check(
    ip_port: str, scheme: str = "http"
) -> tuple[bool, Optional[float]]:
    """Non‑blocking health probe suitable for `asyncio.gather`."""
    proxy_url = _build_proxy_url(ip_port, scheme)
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=TIMEOUT_S) as client:
            r = await client.get(TEST_URL)
            r.raise_for_status()
            _ = r.json()
        latency = (time.perf_counter() - t0) * 1000
        return True, latency
    except Exception:
        return False, None


async def _probe(ip_port: str, sem: asyncio.Semaphore) -> (str, float, bool):
    async with sem:
        healthy, latency = await _proxy_health_check(ip_port, DEFAULT_SCHEME)
        return ip_port, latency, healthy


async def bulk_health_check(
    candidates: Iterable[str], max_parallel: int = MAX_PARALLEL
):
    sem = asyncio.Semaphore(max_parallel)
    tasks = [_probe(ip_port, sem) for ip_port in candidates]
    res = []
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Probing"):
        result = await coro
        if result:
            res.append(result)
    return res


def proxy_health_check(
    ip_port: str, scheme: str = "http"
) -> tuple[bool, Optional[float]]:
    return asyncio.run(_proxy_health_check(ip_port, scheme))
