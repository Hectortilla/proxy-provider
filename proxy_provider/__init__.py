from datetime import datetime, timezone
from typing import Optional, Tuple

from proxy_provider.db.csv_store import ISO_FMT, CsvStore, _Row, _utcnow
from proxy_provider.utils.logging import configure_logging

configure_logging("INFO")


class ProxyRotator:
    """Simple *least‑recently‑used* proxy rotator with health validation.

    *min_recheck_interval* tells the rotator to trust the recorded `healthy`
    status for that long. Older entries are re‑checked on demand.
    """

    # ---------------------------------------------------------------------
    def __init__(self):
        self.store = CsvStore()
        self.proxies = self.store.all()

    def get_proxy(self) -> Optional[Tuple[str, float]]:
        """
        Implements a smart rotating policy for retrieving proxies:
        1. Filters out unhealthy proxies.
        2. Prioritizes proxies that have not been used recently (oldest last_used).
        3. As a tie-breaker, prefers proxies with lower latency.
        4. If no 'last_used' timestamp exists, treats them as never used (highest priority).
        """
        # 1. Filter out unhealthy proxies
        healthy_proxies = [proxy for proxy in self.proxies if proxy.healthy]

        if not healthy_proxies:
            return None  # No healthy proxies available

        # Define a key for sorting
        # Prioritize:
        # 1. Proxies with no last_used (treat as highly preferred)
        # 2. Then by last_used (oldest first)
        # 3. Then by latency_ms (lowest first), treating None as effectively infinite (least preferred)

        def sort_key(proxy_row: _Row) -> tuple:
            # Parse last_used string to datetime for proper comparison
            last_used_dt = None
            if proxy_row.last_used:
                try:
                    last_used_dt = datetime.strptime(
                        proxy_row.last_used, ISO_FMT
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    # Handle malformed dates gracefully, treat as never used
                    pass

            # For last_used: We want proxies that are None (never used) first,
            # then older dates. A common trick is to use a large future date for None
            # or invert the sorting. Here, let's make None come first naturally.
            # Using (last_used_dt is None, last_used_dt or datetime.min) ensures None comes first.
            # (True, datetime.min) will be before (False, actual_datetime).

            # For latency: We want lowest latency first. None latency should be last.
            # Using (latency_ms is None, latency_ms or float('inf')) puts None (inf) last.

            return (
                last_used_dt is not None,  # False if never used (comes first)
                last_used_dt
                or datetime.min.replace(
                    tzinfo=timezone.utc
                ),  # Actual date, or very old date if None (for consistent comparison)
                proxy_row.latency_ms
                is not None,  # False if latency is None (comes last)
                proxy_row.latency_ms
                or float(
                    "inf"
                ),  # Actual latency, or infinity if None (for consistent comparison)
            )

        # Sort the healthy proxies using the defined key
        sorted_proxies = sorted(healthy_proxies, key=sort_key)

        # Get the "smartest" proxy (the first one after sorting)
        selected_proxy_row = sorted_proxies[0]

        # Update its last_used timestamp immediately to reflect it's being used
        self.proxies = self.store.upsert(
            selected_proxy_row.ip_port,
            scheme=selected_proxy_row.scheme,
            last_used=_utcnow(),
        )

        return selected_proxy_row.to_proxy_url(), selected_proxy_row.latency_ms
