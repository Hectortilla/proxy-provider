from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from proxy_provider import ProxyRotator
from proxy_provider.db.csv_store import FIELDNAMES, ISO_FMT, CsvStore, _utcnow
from tests.conftest import PROXY_1, PROXY_2, PROXY_3, UNHEALTHY_PROXY


class TestProxyRotator:
    """Tests for the ProxyRotator class."""

    def test_get_proxy_rotator_policy(self, varied_csv_store):
        """Test that ProxyRotator returns different proxies in consecutive calls."""
        # Patch the CsvStore to use our test CSV file
        with patch("proxy_provider.CsvStore", return_value=varied_csv_store):
            rotator = ProxyRotator()

            proxy1, latency1 = rotator.get_proxy()
            proxy2, latency2 = rotator.get_proxy()
            # Verify that different proxies are returned
            assert (
                proxy1 != proxy2
            ), f"Expected different proxies, but got {proxy1} twice"
            # Get the third proxy
            proxy3, latency3 = rotator.get_proxy()

            # Verify that all three proxies are different
            assert (
                proxy1 != proxy3
            ), f"Expected different proxies, but got {proxy1} and {proxy3}"
            assert (
                proxy2 != proxy3
            ), f"Expected different proxies, but got {proxy2} and {proxy3}"
            assert UNHEALTHY_PROXY not in (
                proxy1,
                proxy2,
                proxy3,
            ), f"Unhealthy proxy {UNHEALTHY_PROXY} should not be returned"

    def test_store_properly_upsert(self, varied_csv_store):
        """Test that CsvStore properly"""
        # Patch the CsvStore to use our test CSV file
        with patch("proxy_provider.CsvStore", return_value=varied_csv_store):
            rotator = ProxyRotator()
            proxies = rotator.store.all()
            assert len(proxies) == 4, f"Expected 4 proxies, but got {len(proxies)}"
            assert set(row.ip_port for row in proxies) == {
                PROXY_1,
                PROXY_2,
                PROXY_3,
                UNHEALTHY_PROXY,
            }, "Proxies in store do not match expected values"

    def test_empty_proxy_list(self, csv_file):
        """Test behavior when no proxies are available."""
        empty_store = CsvStore(path=csv_file)
        with patch("proxy_provider.CsvStore", return_value=empty_store):
            rotator = ProxyRotator()
            result = rotator.get_proxy()
            assert result is None, "Expected None when no proxies are available"

    def test_all_proxies_unhealthy(self, csv_store):
        """Test behavior when all proxies are unhealthy."""
        # Add only unhealthy proxies
        csv_store.upsert(PROXY_1, healthy=False)
        csv_store.upsert(PROXY_2, healthy=False)

        with patch("proxy_provider.CsvStore", return_value=csv_store):
            rotator = ProxyRotator()
            result = rotator.get_proxy()
            assert result is None, "Expected None when all proxies are unhealthy"

    def test_proxy_sorting_by_last_used(self, csv_store):
        """Test that proxies are returned in order of last_used timestamp."""
        # Add proxies with different last_used timestamps
        now = datetime.now(timezone.utc)
        one_hour_ago = (now - timedelta(hours=1)).strftime(ISO_FMT)
        two_hours_ago = (now - timedelta(hours=2)).strftime(ISO_FMT)

        csv_store.upsert(PROXY_1, healthy=True, last_used=one_hour_ago)
        csv_store.upsert(PROXY_2, healthy=True, last_used=two_hours_ago)
        csv_store.upsert(PROXY_3, healthy=True)  # No last_used (should be first)

        with patch("proxy_provider.CsvStore", return_value=csv_store):
            rotator = ProxyRotator()
            proxy1, _ = rotator.get_proxy()
            proxy2, _ = rotator.get_proxy()
            proxy3, _ = rotator.get_proxy()

            # PROXY_3 should be first (no last_used), then PROXY_2 (older), then PROXY_1
            assert PROXY_3 in proxy1, "Proxy with no last_used should be returned first"
            assert (
                PROXY_2 in proxy2
            ), "Proxy with older last_used should be returned second"
            assert (
                PROXY_1 in proxy3
            ), "Proxy with newer last_used should be returned last"

    def test_proxy_sorting_by_latency(self, csv_store):
        """Test that proxies are sorted by latency when last_used timestamps are the same."""
        # Add proxies with same last_used timestamp but different latencies
        now = datetime.now(timezone.utc)
        same_time = now.strftime(ISO_FMT)

        csv_store.upsert(PROXY_1, healthy=True, last_used=same_time, latency_ms=300)
        csv_store.upsert(PROXY_2, healthy=True, last_used=same_time, latency_ms=100)
        csv_store.upsert(PROXY_3, healthy=True, last_used=same_time, latency_ms=200)

        with patch("proxy_provider.CsvStore", return_value=csv_store):
            rotator = ProxyRotator()
            proxy1, _ = rotator.get_proxy()
            proxy2, _ = rotator.get_proxy()
            proxy3, _ = rotator.get_proxy()

            # Should be ordered by latency: PROXY_2 (100ms), PROXY_3 (200ms), PROXY_1 (300ms)
            assert (
                PROXY_2 in proxy1
            ), "Proxy with lowest latency should be returned first"
            assert (
                PROXY_3 in proxy2
            ), "Proxy with medium latency should be returned second"
            assert (
                PROXY_1 in proxy3
            ), "Proxy with highest latency should be returned last"

    def test_last_used_timestamp_update(self, csv_store):
        """Test that last_used timestamp is updated when a proxy is retrieved."""

        # Add a proxy
        def _get_proxy_1(rotator):
            proxies = rotator.store.all()
            return next(p for p in proxies if p.ip_port == PROXY_1)

        csv_store.upsert(PROXY_1, healthy=True)

        with patch("proxy_provider.CsvStore", return_value=csv_store):
            rotator = ProxyRotator()

            proxy_1 = _get_proxy_1(rotator)
            assert (
                proxy_1.last_used is None
            ), "last_used should be None before getting the proxy"

            # Get the proxy
            before_get = datetime.now(timezone.utc)
            proxy, _ = rotator.get_proxy()
            after_get = datetime.now(timezone.utc)

            # Check that the proxy was returned
            assert PROXY_1 in proxy, "Expected PROXY_1 to be returned"

            # Get the updated proxy from the store
            updated_proxy = _get_proxy_1(rotator)
            # Check that last_used was updated
            assert updated_proxy.last_used is not None, "last_used should be updated"

            # Parse the timestamp and check it's between before_get and after_get
            last_used_dt = datetime.strptime(updated_proxy.last_used, ISO_FMT).replace(
                tzinfo=timezone.utc
            )
            assert (
                before_get <= last_used_dt <= after_get
            ), "last_used timestamp should be updated to current time"

    def test_malformed_date_handling(self, varied_csv_store):
        """Test that malformed dates in last_used are handled gracefully."""
        with patch("proxy_provider.CsvStore", return_value=varied_csv_store):
            # This should not raise an exception
            rotator = ProxyRotator()

            proxy, _ = rotator.get_proxy()
            assert (
                PROXY_1 in proxy
            ), "Proxy with lowest latency should be returned first"

            # Corrupt the last_used date for PROXY_1
            rotator.proxies = varied_csv_store.upsert(
                PROXY_1,
                last_used="invalid-date-format",
            )

            proxy, _ = rotator.get_proxy()
            assert (
                PROXY_1 in proxy
            ), "Proxy with malformed date should be treated as having no last_used"
            proxy, _ = rotator.get_proxy()
            assert (
                PROXY_2 in proxy
            ), "Proxy with valid last_used should be returned next"

    def test_proxy_reuse_after_all_used(self, varied_csv_store):
        with patch("proxy_provider.CsvStore", return_value=varied_csv_store):
            rotator = ProxyRotator()

            # First round - should use all proxies
            proxy1, _ = rotator.get_proxy()
            proxy2, _ = rotator.get_proxy()
            proxy3, _ = rotator.get_proxy()

            # Second round - should reuse proxies in the same order as they were first used
            # (since they now all have last_used timestamps, but in the order they were used)
            proxy4, _ = rotator.get_proxy()
            proxy5, _ = rotator.get_proxy()
            proxy6, _ = rotator.get_proxy()

            # The order should be the same in both rounds
            assert proxy1 == proxy4, "First proxy should be reused first"
            assert proxy2 == proxy5, "Second proxy should be reused second"
            assert proxy3 == proxy6, "Third proxy should be reused third"
