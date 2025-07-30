from proxy_provider.db.csv_store import _Row, _utcnow
from tests.conftest import PROXY_1, PROXY_2


class TestCSVStore:
    """Tests for the CsvStore class."""

    def test_csv_store_delete(self, csv_file, csv_store):
        """Test that CsvStore.delete properly removes proxies."""
        # Add proxies
        csv_store.upsert(PROXY_1, healthy=True)
        csv_store.upsert(PROXY_2, healthy=True)

        # Verify both proxies exist
        proxies = csv_store.all()
        assert len(proxies) == 2, "Expected 2 proxies before deletion"

        # Delete one proxy
        result = csv_store.delete(PROXY_1)
        assert result is True, "Delete should return True when a proxy is deleted"

        # Verify only one proxy remains
        proxies = csv_store.all()
        assert len(proxies) == 1, "Expected 1 proxy after deletion"
        assert proxies[0].ip_port == PROXY_2, "Expected PROXY_2 to remain"

        # Try to delete a non-existent proxy
        result = csv_store.delete("nonexistent:8080")
        assert result is False, "Delete should return False when no proxy is deleted"

    def test_update_from_health_check(self, csv_file, csv_store):
        """Test that update_from_health_check properly updates proxies."""
        # Add proxies
        csv_store.upsert(PROXY_1, healthy=True, latency_ms=100)
        csv_store.upsert(PROXY_2, healthy=True, latency_ms=200)

        # Create health check results
        health_check_results = [
            (PROXY_1, 150, False),  # IP:port, latency, healthy
            (PROXY_2, 100, True),
        ]

        # Update from health check
        csv_store.update_from_health_check(health_check_results)

        # Verify updates
        proxies = {p.ip_port: p for p in csv_store.all()}

        assert proxies[PROXY_1].healthy is False, "PROXY_1 should be marked unhealthy"
        assert proxies[PROXY_1].latency_ms == 150, "PROXY_1 latency should be updated"
        assert (
            proxies[PROXY_1].last_checked is not None
        ), "PROXY_1 last_checked should be updated"

        assert proxies[PROXY_2].healthy is True, "PROXY_2 should remain healthy"
        assert proxies[PROXY_2].latency_ms == 100, "PROXY_2 latency should be updated"
        assert (
            proxies[PROXY_2].last_checked is not None
        ), "PROXY_2 last_checked should be updated"

    def test_row_to_proxy_url(self):
        """Test that _Row.to_proxy_url correctly formats proxy URLs."""
        # Test with different schemes
        row1 = _Row(scheme="http", ip="192.168.1.1", port=8080)
        assert (
            row1.to_proxy_url() == "http://192.168.1.1:8080"
        ), "HTTP URL should be formatted correctly"

        row2 = _Row(scheme="https", ip="192.168.1.2", port=443)
        assert (
            row2.to_proxy_url() == "https://192.168.1.2:443"
        ), "HTTPS URL should be formatted correctly"

        row3 = _Row(scheme="socks5", ip="192.168.1.3", port=1080)
        assert (
            row3.to_proxy_url() == "socks5://192.168.1.3:1080"
        ), "SOCKS5 URL should be formatted correctly"

    def test_malformed_proxy_data(self, csv_store):
        """Test handling of malformed proxy data in the CSV file."""
        # Create a CSV file with malformed data
        csv_store.upsert(
            PROXY_1, scheme="http", healthy=True, latency_ms=100, last_used=_utcnow()
        )
        csv_store.upsert(
            PROXY_2,
            scheme="http",
            healthy=True,
            latency_ms="invalid",
            last_used=_utcnow(),
        )

        # This should not raise an exception, but should skip the malformed rows
        try:
            proxies = csv_store.all()
            assert len(proxies) == 1, "Only the valid row should be loaded"
            assert (
                proxies[0].ip_port == "192.168.1.1:8080"
            ), "Expected valid proxy to be loaded"
        except Exception as e:
            assert (
                False
            ), f"Loading malformed data should not raise an exception, but got: {e}"
