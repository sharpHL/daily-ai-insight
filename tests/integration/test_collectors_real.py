"""Real integration tests for data collectors.

These tests make actual API calls to Follow.is and other services.
Requires valid credentials in .env file.

Run with: pytest tests/integration/ -v
Skip with: pytest tests/unit/ -v  (to run only unit tests)
"""

import pytest
import os
from typing import Dict, Any, List

from daily_ai_insight.collectors import create_from_preset


class TestRedditReal:
    """Real API tests for Reddit collector."""

    @pytest.fixture
    def collector(self, check_env_vars):
        """Create collector with real credentials."""
        check_env_vars("FOLO_COOKIE", "REDDIT_LIST_ID")
        return create_from_preset("reddit")

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real data from Reddit."""
        print(f"\n🔍 Fetching from {collector.name}...")

        raw_data = await collector.fetch()

        assert raw_data is not None
        assert "items" in raw_data
        assert isinstance(raw_data["items"], list)

        print(f"✓ Fetched {len(raw_data['items'])} items")

    @pytest.mark.asyncio
    async def test_full_pipeline(self, collector, is_real_test):
        """Test complete fetch -> transform -> HTML pipeline."""
        raw_data = await collector.fetch()

        if not raw_data["items"]:
            pytest.skip("No items fetched")

        # Transform
        transformed = collector.transform(raw_data, "reddit")
        assert len(transformed) > 0
        assert all(item["type"] == "reddit" for item in transformed)

        # Generate HTML for first item
        html = collector.generate_html(transformed[0])
        assert len(html) > 0

        print(f"✓ Pipeline: {len(raw_data['items'])} items → {len(transformed)} transformed → HTML")


class TestXiaohuReal:
    """Real API tests for Xiaohu collector."""

    @pytest.fixture
    def collector(self, check_env_vars):
        """Create collector with real credentials."""
        check_env_vars("FOLO_COOKIE", "XIAOHU_FEED_ID")
        return create_from_preset("xiaohu")

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real data from Xiaohu."""
        print(f"\n🔍 Fetching from {collector.name}...")

        raw_data = await collector.fetch()

        assert raw_data is not None
        assert "items" in raw_data
        print(f"✓ Fetched {len(raw_data['items'])} items")

    @pytest.mark.asyncio
    async def test_data_freshness(self, collector, is_real_test):
        """Test that fetched data is recent (within filter days)."""
        from datetime import datetime, timedelta

        raw_data = await collector.fetch()

        if not raw_data["items"]:
            pytest.skip("No items fetched")

        # Check that items are within the configured filter days
        filter_days = collector.filter_days
        cutoff_date = datetime.now() - timedelta(days=filter_days)

        for item in raw_data["items"]:
            pub_date_str = item.get("date_published", "")
            if pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                assert pub_date >= cutoff_date, f"Item date {pub_date} is older than {filter_days} days"

        print(f"✓ All items are within {filter_days} days")


class TestNewsAggregatorReal:
    """Real API tests for News Aggregator collector."""

    @pytest.fixture
    def collector(self, check_env_vars):
        """Create collector with real credentials."""
        check_env_vars("FOLO_COOKIE", "NEWS_AGGREGATOR_LIST_ID")
        return create_from_preset("news_aggregator")

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real data from News Aggregator."""
        print(f"\n🔍 Fetching from {collector.name}...")

        raw_data = await collector.fetch()

        assert raw_data is not None
        assert "items" in raw_data
        print(f"✓ Fetched {len(raw_data['items'])} items")


class TestAllCollectorsReal:
    """Integration tests for all collectors together."""

    @pytest.fixture
    def all_collectors(self, check_env_vars):
        """Create all collectors."""
        check_env_vars(
            "FOLO_COOKIE",
            "REDDIT_LIST_ID",
            "XIAOHU_FEED_ID",
            "NEWS_AGGREGATOR_LIST_ID"
        )
        return [
            create_from_preset("reddit"),
            create_from_preset("xiaohu"),
            create_from_preset("news_aggregator")
        ]

    @pytest.mark.asyncio
    async def test_all_collectors_fetch(self, all_collectors, is_real_test):
        """Test that all collectors can fetch data."""
        results = {}

        for collector in all_collectors:
            print(f"\n🔍 Testing {collector.name}...")
            raw_data = await collector.fetch()

            assert raw_data is not None
            assert "items" in raw_data

            results[collector.name] = len(raw_data["items"])
            print(f"✓ {collector.name}: {results[collector.name]} items")

        print(f"\n📊 Summary: {sum(results.values())} total items from {len(results)} collectors")

    @pytest.mark.asyncio
    async def test_concurrent_fetch(self, all_collectors, is_real_test):
        """Test fetching from all collectors concurrently."""
        import asyncio

        print("\n🚀 Concurrent fetch from all collectors...")

        # Fetch concurrently
        tasks = [collector.fetch() for collector in all_collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate results
        successful = 0
        for collector, result in zip(all_collectors, results):
            if isinstance(result, Exception):
                print(f"✗ {collector.name} failed: {result}")
            else:
                assert "items" in result
                successful += 1
                print(f"✓ {collector.name}: {len(result['items'])} items")

        assert successful > 0, "At least one collector should succeed"
        print(f"\n✓ {successful}/{len(all_collectors)} collectors succeeded")

    def test_collector_configuration(self, all_collectors, is_real_test):
        """Test that all collectors are properly configured."""
        for collector in all_collectors:
            # Check basic properties
            assert collector.name is not None, f"{collector.__class__.__name__} has no name"
            assert collector.cookie, f"{collector.name} has no cookie"
            assert collector.api_url, f"{collector.name} has no API URL"

            # Check feed/list ID
            assert (
                collector.feed_id or collector.list_id
            ), f"{collector.name} has neither feed_id nor list_id"

            # Check pagination settings
            assert collector.fetch_pages > 0, f"{collector.name} fetch_pages must be > 0"
            assert collector.filter_days > 0, f"{collector.name} filter_days must be > 0"

            print(f"✓ {collector.name} configured correctly")


class TestErrorHandling:
    """Test error handling with real API."""

    @pytest.mark.asyncio
    async def test_invalid_cookie(self, check_env_vars):
        """Test behavior with invalid cookie."""
        import os

        check_env_vars("REDDIT_LIST_ID")

        # Temporarily override cookie
        original_cookie = os.environ.get("FOLO_COOKIE")
        os.environ["FOLO_COOKIE"] = "invalid_cookie_12345"

        try:
            collector = create_from_preset("reddit")
            raw_data = await collector.fetch()

            # Should return empty result gracefully
            assert raw_data is not None
            assert "items" in raw_data
            # May or may not have items depending on API behavior
            print(f"⚠ Invalid cookie test: {len(raw_data['items'])} items (may be 0)")

        finally:
            # Restore original cookie
            if original_cookie:
                os.environ["FOLO_COOKIE"] = original_cookie

    @pytest.mark.asyncio
    async def test_invalid_list_id(self):
        """Test behavior with invalid list ID."""
        os.environ["REDDIT_LIST_ID"] = "invalid_list_id_99999"

        collector = create_from_preset("reddit")
        raw_data = await collector.fetch()

        # Should handle gracefully
        assert raw_data is not None
        assert "items" in raw_data
        print(f"⚠ Invalid list ID test: {len(raw_data['items'])} items (expected 0)")
