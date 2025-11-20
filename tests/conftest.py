"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_rss_item() -> Dict[str, Any]:
    """Sample RSS item for testing."""
    return {
        "title": "Test Article About AI",
        "content": "This is a test article about artificial intelligence and machine learning.",
        "url": "https://example.com/test-article",
        "published_at": "2025-01-20",
        "source": "test",
        "tags": ["ai", "technology"]
    }


@pytest.fixture
def sample_rss_items() -> List[Dict[str, Any]]:
    """Multiple sample RSS items for testing."""
    return [
        {
            "title": "AI Breakthrough in 2025",
            "content": "Major advancement in large language models...",
            "url": "https://example.com/ai-breakthrough",
            "published_at": "2025-01-20",
            "source": "test",
            "tags": ["ai"]
        },
        {
            "title": "New Open Source ML Library",
            "content": "A new open source machine learning library...",
            "url": "https://example.com/ml-library",
            "published_at": "2025-01-20",
            "source": "test",
            "tags": ["opensource", "ml"]
        },
        {
            "title": "Crypto Market Update",
            "content": "Latest cryptocurrency prices and trends...",
            "url": "https://example.com/crypto",
            "published_at": "2025-01-20",
            "source": "test",
            "tags": ["crypto"]
        }
    ]


@pytest.fixture
def test_storage_path(tmp_path: Path) -> Path:
    """Temporary storage path for testing."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    (storage_dir / "data").mkdir()
    (storage_dir / "processed").mkdir()
    (storage_dir / "archives").mkdir()
    return storage_dir
