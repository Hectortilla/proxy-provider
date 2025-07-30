
import pytest
import os
import tempfile

from proxy_provider.db.csv_store import CsvStore, ISO_FMT

PROXY_1 = "192.168.1.1:8080"
PROXY_2 = "192.168.1.2:8080"
PROXY_3 = "192.168.1.3:8080"
UNHEALTHY_PROXY = "192.168.1.4:8080"

@pytest.fixture
def csv_file():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def csv_store(csv_file):
    """Create a CsvStore instance with the temporary CSV file."""
    return CsvStore(path=csv_file)

@pytest.fixture
def varied_csv_store(csv_store):
    """Set up test proxies in the CSV store."""
    # Add multiple healthy proxies with different last_used timestamps
    csv_store.upsert(PROXY_1, healthy=True, latency_ms=100)
    csv_store.upsert(PROXY_2, healthy=True, latency_ms=200)
    csv_store.upsert(PROXY_3, healthy=True, latency_ms=300)
    # Add an unhealthy proxy that should be ignored
    csv_store.upsert(UNHEALTHY_PROXY, healthy=False, latency_ms=50)
    return csv_store