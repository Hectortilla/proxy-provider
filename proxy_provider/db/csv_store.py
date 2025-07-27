"""CSV‑backed proxy store
~~~~~~~~~~~~~~~~~~~~~~~~
A tiny, dependency‑free drop‑in for persisting proxy metadata when you don't
want a full database. Not safe for concurrent writers, but perfect for single
process scripts, notebooks, or small crawlers.

Each row in the CSV maps 1‑to‑1 to a proxy and follows the schema:
``scheme,ip,port,healthy,latency_ms,last_checked,last_used,created_at``
Timestamps are stored in ISO‑8601 (UTC) format.

Example
-------
>>> from proxy_utils.stores.csv_store import CsvStore
>>> store = CsvStore("proxies.csv")
>>> store.upsert("203.0.113.7:8080") # insert a new proxy
>>> store.upsert("203.0.113.7:8080", healthy=False) # update existing proxy
>>> store.delete("203.0.113.7:8080") # delete a proxy
>>> store.all() # get all proxies as a list of _Row objects
"""

from __future__ import annotations
import os

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

dir_path = os.path.dirname(os.path.realpath(__file__))

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"  # always UTC
FIELDNAMES = [
    "scheme",
    "ip",
    "port",
    "healthy",
    "latency_ms",
    "last_checked",
    "last_used",
    "created_at",
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


@dataclass
class _Row:
    scheme: str
    ip: str
    port: int
    healthy: bool = None
    latency_ms: Optional[float] = None
    last_checked: Optional[str] = None
    last_used: Optional[str] = None
    created_at: str = _utcnow()

    @property
    def ip_port(self) -> str:
        return f"{self.ip}:{self.port}"

    def to_proxy_url(self) -> str:
        return f"{self.scheme}://{self.ip}:{self.port}"


class CsvStore:
    """Lightweight proxy store backed by a single CSV file."""

    def __init__(
        self, path: str | Path = f"{dir_path}/proxies.csv", default_scheme: str = "http"
    ) -> None:
        self.path = Path(path)
        self.default_scheme = default_scheme
        if not self.path.exists():
            # create file with header row
            self.path.write_text(",".join(FIELDNAMES) + "\n", encoding="utf‑8")

    # ------------------------------------------------------------------ helpers
    def _write_all(self, rows: List[_Row]):
        with self.path.open("w", newline="", encoding="utf‑8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow(asdict(row))

    # ---------------------------------------------------------------- public API
    def all(self) -> List[_Row]:
        with self.path.open(newline="", encoding="utf‑8") as f:
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            next(reader)  # skip header
            rows = []
            for rec in reader:
                # convert types
                rows.append(
                    _Row(
                        scheme=rec["scheme"],
                        ip=rec["ip"],
                        port=int(rec["port"]),
                        healthy=rec["healthy"] == "True",
                        latency_ms=(
                            float(rec["latency_ms"]) if rec["latency_ms"] else None
                        ),
                        last_checked=rec["last_checked"] or None,
                        last_used=rec["last_used"] or None,
                        created_at=rec["created_at"],
                    )
                )
            return rows

    def upsert(
        self,
        ip_port: str,
        scheme: Optional[str] = None,
        healthy: Optional[bool] = None,
        latency_ms: Optional[float] = None,
        last_checked: Optional[str] = None,
        last_used: Optional[str] = None,
    ):
        """Insert or upsert a proxy row. *scheme* defaults to `default_scheme`."""
        scheme = scheme or self.default_scheme
        ip, port = ip_port.split(":", 1)
        port = int(port)
        rows = self.all()
        found = False
        for row in rows:
            if row.ip == ip and row.port == port and row.scheme == scheme:
                # already exists – make sure it's flagged healthy
                if healthy is not None:
                    row.healthy = healthy
                if latency_ms is not None:
                    row.latency_ms = latency_ms
                if last_checked is not None:
                    row.last_checked = last_checked
                if last_used is not None:
                    row.last_used = last_used
                found = True
                break
        if not found:
            upsert_fields = {
                "healthy": healthy,
                "latency_ms": latency_ms,
                "last_checked": last_checked,
                "last_used": last_used,
            }
            upsert_fields = {k: v for k, v in upsert_fields.items() if v is not None}

            rows.append(
                _Row(
                    scheme=scheme,
                    ip=ip,
                    port=port,
                    created_at=_utcnow(),  # Use the helper for created_at
                    **upsert_fields,
                )
            )
        self._write_all(rows)
        return rows

    def delete(self, ip_port: str, scheme: Optional[str] = None) -> bool:
        scheme = scheme or self.default_scheme
        ip, port_str = ip_port.split(":", 1)
        port = int(port_str)

        rows = self.all()
        original_row_count = len(rows)
        # Filter out the row to be deleted
        updated_rows = [
            row
            for row in rows
            if not (row.ip == ip and row.port == port and row.scheme == scheme)
        ]

        if len(updated_rows) < original_row_count:
            self._write_all(updated_rows)
            return True
        return False

    def update_from_health_check(self, results):
        for res in results:
            self.upsert(
                res[0],
                latency_ms=res[1],
                healthy=res[2],
                last_checked=_utcnow(),
            )
