"""Unit tests for data collectors."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from daily_ai_insight.collectors import (
    HuggingFacePapersCollector,
    RedditCollector,
    XiaohuCollector,
    NewsAggregatorCollector
)
from daily_ai_insight.collectors.utils import (
    get_random_user_agent,
    is_date_within_last_days,
    strip_html,
    escape_html,
    format_date_to_chinese
)


class TestUtils:
    """Test utility functions."""

    def test_get_random_user_agent(self):
        """Test random user agent generation."""
        agent = get_random_user_agent()
        assert isinstance(agent, str)
        assert len(agent) > 0
        assert "Mozilla" in agent

    def test_is_date_within_last_days(self):
        """Test date filtering."""
        # Test recent date
        today = datetime.now().isoformat()
        assert is_date_within_last_days(today, 3) is True

        # Test old date
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        assert is_date_within_last_days(old_date, 3) is False

        # Test invalid date
        assert is_date_within_last_days("invalid", 3) is False
        assert is_date_within_last_days("", 3) is False

    def test_strip_html(self):
        """Test HTML stripping."""
        html = "<p>Hello <strong>World</strong></p><script>alert('test')</script>"
        text = strip_html(html)
        assert "Hello" in text
        assert "World" in text
        assert "<p>" not in text
        assert "<strong>" not in text
        assert "alert" not in text

    def test_escape_html(self):
        """Test HTML escaping."""
        text = '<script>alert("test")</script>'
        escaped = escape_html(text)
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "<script>" not in escaped

    def test_format_date_to_chinese(self):
        """Test date formatting."""
        date_str = "2024-01-15T10:30:00Z"
        formatted = format_date_to_chinese(date_str)
        assert "2024" in formatted
        assert "01" in formatted
        assert "15" in formatted


class TestFollowBaseCollector:
    """Test Follow.is base collector."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("FOLO_COOKIE", "test_cookie")
        monkeypatch.setenv("FOLO_DATA_API", "https://api.follow.is/entries")
        monkeypatch.setenv("HGPAPERS_FEED_ID", "test_feed_id")
        monkeypatch.setenv("REDDIT_LIST_ID", "test_list_id")
        monkeypatch.setenv("XIAOHU_FEED_ID", "test_feed_id")
        monkeypatch.setenv("NEWS_AGGREGATOR_LIST_ID", "test_list_id")

    @pytest.fixture
    def mock_api_response(self):
        """Mock API response."""
        return {
            "data": [
                {
                    "entries": {
                        "id": "test_id_1",
                        "url": "https://example.com/1",
                        "title": "Test Item 1",
                        "content": "<p>Test content 1</p>",
                        "publishedAt": datetime.now().isoformat(),
                        "author": "Test Author"
                    },
                    "feeds": {
                        "title": "Test Feed"
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_huggingface_papers_fetch(self, mock_env, mock_api_response):
        """Test HuggingFace Papers fetch."""
        collector = HuggingFacePapersCollector()

        # Create proper mock objects
        class MockResponse:
            status = 200

            async def json(self):
                return mock_api_response

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

        class MockSession:
            def post(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

        with patch('aiohttp.ClientSession', return_value=MockSession()):
            result = await collector.fetch()

            assert result is not None
            assert "items" in result
            assert len(result["items"]) > 0
            assert result["items"][0]["title"] == "Test Item 1"

    @pytest.mark.asyncio
    async def test_reddit_fetch(self, mock_env, mock_api_response):
        """Test Reddit fetch."""
        collector = RedditCollector()
        assert collector.list_id == "test_list_id"

    def test_transform(self, mock_env):
        """Test data transformation."""
        collector = HuggingFacePapersCollector()

        raw_data = {
            "items": [
                {
                    "id": "test_id",
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content_html": "<p>Test content</p>",
                    "date_published": "2024-01-15T10:30:00Z",
                    "authors": [{"name": "Author 1"}],
                    "source": "Test Source"
                }
            ]
        }

        result = collector.transform(raw_data, "papers")

        assert len(result) == 1
        assert result[0]["id"] == "test_id"
        assert result[0]["title"] == "Test Title"
        assert result[0]["type"] == "papers"
        assert result[0]["authors"] == "Author 1"
        assert "content_html" in result[0]["details"]

    def test_generate_html(self, mock_env):
        """Test HTML generation."""
        collector = HuggingFacePapersCollector()

        item = {
            "title": "Test Title",
            "url": "https://example.com",
            "source": "Test Source",
            "published_date": "2024-01-15T10:30:00Z",
            "details": {
                "content_html": "<p>Test content</p>"
            }
        }

        html = collector.generate_html(item)

        assert "Test Title" in html
        assert "https://example.com" in html
        assert "Test Source" in html
        assert "<p>Test content</p>" in html


class TestCollectorIntegration:
    """Integration tests for collectors."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("FOLO_COOKIE", "test_cookie")
        monkeypatch.setenv("FOLO_DATA_API", "https://api.follow.is/entries")
        monkeypatch.setenv("HGPAPERS_FEED_ID", "test_feed_id")
        monkeypatch.setenv("REDDIT_LIST_ID", "test_list_id")
        monkeypatch.setenv("XIAOHU_FEED_ID", "test_feed_id")
        monkeypatch.setenv("FOLO_FETCH_PAGES", "1")
        monkeypatch.setenv("FOLO_FILTER_DAYS", "3")

    def test_all_collectors_instantiate(self, mock_env):
        """Test that all collectors can be instantiated."""
        collectors = [
            HuggingFacePapersCollector(),
            RedditCollector(),
            XiaohuCollector(),
            NewsAggregatorCollector()
        ]

        for collector in collectors:
            assert collector.name is not None
            assert hasattr(collector, 'fetch')
            assert hasattr(collector, 'transform')
            assert hasattr(collector, 'generate_html')

    @pytest.mark.asyncio
    async def test_fetch_transform_pipeline(self, mock_env):
        """Test complete fetch -> transform pipeline."""
        collector = HuggingFacePapersCollector()

        # Mock fetch response
        mock_response = {
            "version": "1.1",
            "title": "Test",
            "items": [
                {
                    "id": "test_id",
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content_html": "<p>Test</p>",
                    "date_published": datetime.now().isoformat(),
                    "authors": [{"name": "Author"}],
                    "source": "Test Source"
                }
            ]
        }

        with patch.object(collector, 'fetch', return_value=mock_response):
            raw_data = await collector.fetch()
            transformed = collector.transform(raw_data, "papers")
            html = collector.generate_html(transformed[0])

            assert len(transformed) == 1
            assert transformed[0]["type"] == "papers"
            assert "Test Title" in html
