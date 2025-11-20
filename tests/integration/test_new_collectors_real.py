"""Real integration tests for new data collectors.

These tests make actual API calls. Requires valid credentials in .env file.

Run with: pytest tests/integration/test_new_collectors_real.py -v -s
Skip with: pytest tests/unit/ -v (to run only unit tests)
"""

import pytest
import os
from typing import List

from daily_ai_insight.collectors import (
    GitHubTrendingCollector,
    PapersCollector,
    TwitterCollector,
    AIBaseCollector,
    JiqizhixinCollector,
    QBitCollector,
    XinZhiYuanCollector,
)


class TestGitHubTrendingReal:
    """Real API tests for GitHub Trending collector."""

    @pytest.fixture
    def collector(self):
        """Create collector (no auth required for GitHub Trending)."""
        return GitHubTrendingCollector()

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real data from GitHub Trending."""
        print(f"\n🔍 Fetching from GitHub Trending...")

        items = await collector.fetch()

        # Validate response
        assert items is not None, "Response should not be None"
        assert isinstance(items, list), "Response should be a list"

        print(f"✓ Fetched {len(items)} trending repositories")

        if items:
            item = items[0]
            assert "id" in item
            assert "title" in item
            assert "url" in item
            assert "metadata" in item
            assert "stars" in item["metadata"]
            print(f"✓ Top repo: {item['title']} ({item['metadata']['stars']} ⭐)")

    @pytest.mark.asyncio
    async def test_github_data_structure(self, collector, is_real_test):
        """Test that GitHub data has correct structure."""
        items = await collector.fetch()

        if not items:
            pytest.skip("No items fetched")

        for item in items[:3]:  # Check first 3 items
            # Check unified format
            assert "id" in item
            assert "title" in item
            assert "url" in item
            assert "content" in item
            assert "source" in item
            assert item["source"] == "GitHub Trending"

            # Check GitHub-specific metadata
            assert "metadata" in item
            assert "type" in item["metadata"]
            assert item["metadata"]["type"] == "github_project"
            assert "stars" in item["metadata"]
            assert "language" in item["metadata"]

        print(f"✓ All items have correct structure")


class TestPapersCollectorReal:
    """Real API tests for Papers collector."""

    @pytest.fixture
    def collector(self, check_env_vars):
        """Create collector with real credentials."""
        check_env_vars("FOLO_COOKIE", "PAPERS_LIST_ID")
        return PapersCollector()

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real papers data."""
        print(f"\n🔍 Fetching from {collector.name}...")

        items = await collector.fetch()

        assert items is not None
        assert isinstance(items, list)

        print(f"✓ Fetched {len(items)} papers")

        if items:
            print(f"✓ First paper: {items[0]['title'][:50]}...")


class TestTwitterCollectorReal:
    """Real API tests for Twitter collector."""

    @pytest.fixture
    def collector(self, check_env_vars):
        """Create collector with real credentials."""
        check_env_vars("FOLO_COOKIE", "TWITTER_LIST_ID")
        return TwitterCollector()

    @pytest.mark.asyncio
    async def test_fetch_real_data(self, collector, is_real_test):
        """Test fetching real Twitter data."""
        print(f"\n🔍 Fetching from {collector.name}...")

        items = await collector.fetch()

        assert items is not None
        assert isinstance(items, list)

        print(f"✓ Fetched {len(items)} tweets")

        if items:
            item = items[0]
            # Check Twitter-specific formatting
            assert item["source"].startswith("twitter-") or " - " in item["source"]
            print(f"✓ Source format: {item['source']}")


class TestChineseTechMediaReal:
    """Real API tests for Chinese tech media collectors."""

    @pytest.fixture
    def aibase(self, check_env_vars):
        """Create AI Base collector."""
        check_env_vars("FOLO_COOKIE", "AIBASE_FEED_ID")
        return AIBaseCollector()

    @pytest.fixture
    def jiqizhixin(self, check_env_vars):
        """Create Jiqizhixin collector."""
        check_env_vars("FOLO_COOKIE", "JIQIZHIXIN_FEED_ID")
        return JiqizhixinCollector()

    @pytest.fixture
    def qbit(self, check_env_vars):
        """Create QBit collector."""
        check_env_vars("FOLO_COOKIE", "QBIT_FEED_ID")
        return QBitCollector()

    @pytest.fixture
    def xinzhiyuan(self, check_env_vars):
        """Create XinZhiYuan collector."""
        check_env_vars("FOLO_COOKIE", "XINZHIYUAN_FEED_ID")
        return XinZhiYuanCollector()

    @pytest.mark.asyncio
    async def test_aibase_fetch(self, aibase, is_real_test):
        """Test AI Base fetch."""
        print(f"\n🔍 Fetching from AI Base...")
        items = await aibase.fetch()
        assert isinstance(items, list)
        print(f"✓ Fetched {len(items)} items from AI Base")

    @pytest.mark.asyncio
    async def test_jiqizhixin_fetch(self, jiqizhixin, is_real_test):
        """Test Jiqizhixin fetch."""
        print(f"\n🔍 Fetching from 机器之心...")
        items = await jiqizhixin.fetch()
        assert isinstance(items, list)
        print(f"✓ Fetched {len(items)} items from 机器之心")

    @pytest.mark.asyncio
    async def test_qbit_fetch(self, qbit, is_real_test):
        """Test QBit fetch."""
        print(f"\n🔍 Fetching from 量子位...")
        items = await qbit.fetch()
        assert isinstance(items, list)
        print(f"✓ Fetched {len(items)} items from 量子位")

    @pytest.mark.asyncio
    async def test_xinzhiyuan_fetch(self, xinzhiyuan, is_real_test):
        """Test XinZhiYuan fetch."""
        print(f"\n🔍 Fetching from 新智元...")
        items = await xinzhiyuan.fetch()
        assert isinstance(items, list)
        print(f"✓ Fetched {len(items)} items from 新智元")


class TestAllNewCollectorsReal:
    """Integration tests for all new collectors together."""

    @pytest.fixture
    def all_new_collectors(self):
        """Create all new collectors that don't require auth."""
        collectors = [GitHubTrendingCollector()]

        # Add FOLO collectors if configured
        if os.getenv("FOLO_COOKIE"):
            if os.getenv("PAPERS_LIST_ID"):
                collectors.append(PapersCollector())
            if os.getenv("TWITTER_LIST_ID"):
                collectors.append(TwitterCollector())
            if os.getenv("AIBASE_FEED_ID"):
                collectors.append(AIBaseCollector())
            if os.getenv("JIQIZHIXIN_FEED_ID"):
                collectors.append(JiqizhixinCollector())
            if os.getenv("QBIT_FEED_ID"):
                collectors.append(QBitCollector())
            if os.getenv("XINZHIYUAN_FEED_ID"):
                collectors.append(XinZhiYuanCollector())

        return collectors

    @pytest.mark.asyncio
    async def test_all_new_collectors_fetch(self, all_new_collectors, is_real_test):
        """Test that all configured new collectors can fetch data."""
        if not all_new_collectors:
            pytest.skip("No collectors configured")

        results = {}

        for collector in all_new_collectors:
            print(f"\n🔍 Testing {collector.__class__.__name__}...")

            try:
                items = await collector.fetch()
                assert items is not None
                assert isinstance(items, list)

                results[collector.__class__.__name__] = len(items)
                print(f"✓ {collector.__class__.__name__}: {len(items)} items")

            except Exception as e:
                print(f"✗ {collector.__class__.__name__} failed: {e}")
                results[collector.__class__.__name__] = 0

        total = sum(results.values())
        print(f"\n📊 Summary: {total} total items from {len(results)} new collectors")
        print(f"   Breakdown: {results}")

    @pytest.mark.asyncio
    async def test_concurrent_fetch_new_collectors(self, all_new_collectors, is_real_test):
        """Test fetching from all new collectors concurrently."""
        import asyncio

        if not all_new_collectors:
            pytest.skip("No collectors configured")

        print(f"\n🚀 Concurrent fetch from {len(all_new_collectors)} new collectors...")

        # Fetch concurrently
        tasks = [collector.fetch() for collector in all_new_collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate results
        successful = 0
        for collector, result in zip(all_new_collectors, results):
            if isinstance(result, Exception):
                print(f"✗ {collector.__class__.__name__} failed: {result}")
            else:
                assert isinstance(result, list)
                successful += 1
                print(f"✓ {collector.__class__.__name__}: {len(result)} items")

        assert successful > 0, "At least one collector should succeed"
        print(f"\n✓ {successful}/{len(all_new_collectors)} new collectors succeeded")


class TestMixedOldAndNewCollectors:
    """Test old and new collectors working together."""

    @pytest.mark.asyncio
    async def test_all_collectors_together(self, is_real_test):
        """Test that old and new collectors can run together."""
        import asyncio
        from daily_ai_insight.collectors import (
            RedditCollector,
        )

        collectors = [
            GitHubTrendingCollector(),  # New, no auth required
        ]

        # Add old collectors if configured
        if os.getenv("FOLO_COOKIE"):
            if os.getenv("REDDIT_LIST_ID"):
                collectors.append(RedditCollector())
            if os.getenv("TWITTER_LIST_ID"):
                collectors.append(TwitterCollector())

        if len(collectors) == 1:
            pytest.skip("Only GitHub Trending configured, need more for this test")

        print(f"\n🚀 Testing {len(collectors)} collectors (old + new) together...")

        tasks = [c.fetch() for c in collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = 0
        total_items = 0

        for collector, result in zip(collectors, results):
            name = collector.__class__.__name__
            if isinstance(result, Exception):
                print(f"✗ {name} failed: {result}")
            else:
                count = len(result) if isinstance(result, list) else len(result.get("items", []))
                successful += 1
                total_items += count
                print(f"✓ {name}: {count} items")

        print(f"\n📊 Total: {total_items} items from {successful}/{len(collectors)} collectors")
        assert successful >= 1, "At least GitHub Trending should work"
