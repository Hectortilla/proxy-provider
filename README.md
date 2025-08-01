<h1 align="center">
Proxy Provider
</h1>
</p>
<p align="center">
  <strong>
    A friction‑free toolkit for discovering, vetting, and rotating free HTTP/SOCKS proxies.
  </strong>
</p>

<p align="center">
  <img
    src="https://github.com/Hectortilla/proxy-provider/actions/workflows/tests.yml/badge.svg"
    alt="Tests"
  />
  <a href="https://pypi.org/project/proxy-provider/"><img
    src="https://img.shields.io/pypi/v/proxy-provider.svg"
    alt="PyPI"
  /></a>
  <a href="https://opensource.org/licenses/MIT"><img
    src="https://img.shields.io/badge/License-MIT-yellow.svg"
    alt="License: MIT"
  /></a>
</p>

---

## Why?

Open‑proxy lists are noisy and short‑lived. **Proxy Provided** automates the grunt work so you can focus on your crawler, data‑gathering script, or pentest without babysitting IPs.

* **Scrape → Validate → Store** – Hundreds of public proxies tested in parallel and persisted locally.
* **Health‑aware rotation** – Always hands you the *least‑recently‑used* proxy that’s alive and low‑latency.

---

## Features

| Capability               | Details                                                                          |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Scraping**             | Built‑in scrapers for *spys.me* and *free‑proxy‑list.net* (easy to extend).      |
| **Health checks**        | Concurrent checks via `httpx`; records RTT and marks dead proxies.               |
| **Rotation policy**      | Least‑recently‑used → lowest latency, with on‑demand re‑probe.           |

---

## Installation

```bash
pip install proxy-provider           # CSV store + rotator
```

---

## Quick Start

```python
from proxy_provider import ProxyRotator
rotator = ProxyRotator()
for _ in range(100):
    proxy_url, latency = rotator.get_proxy()
    print("Using:", proxy_url, "with latency", latency, "ms")

```

As you can see, ProxyRotator returns both the proxy URL and its latency in milliseconds. Since open proxies are often slow, consider adjusting your timeouts based on the reported latency.

### Refreshing the proxy database

`proxy_provider` ships with a ready-made list of proxies and their last-known status, but public proxies go bad quickly.
Although `ProxyRotator` checks a proxy’s health every time it’s selected—and skips to the next one if it’s dead—everything runs faster when the database is already current.

Update all proxy records in a single step:

**From the command line**

```bash
proxy-provider scrape-and-update
```

**From Python**

```python
import asyncio
from proxy_provider.db import scrape_and_update

asyncio.run(scrape_and_update())
```

The command (or function) re-scrapes the proxy sources, tests each proxy, and writes the latest health and latency information back to your local store.

---

## Testing

The project includes a test suite using pytest. To run the tests:

```bash
# Install dev dependencies including pytest
poetry install

# Run the tests
poetry run pytest
```

The tests verify the functionality of the ProxyRotator and the CsvStore:

For more details about the test structure and how to add new tests, see [tests/README.md](tests/README.md).
