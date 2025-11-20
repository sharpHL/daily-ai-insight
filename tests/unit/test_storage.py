"""Unit tests for storage backends."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from daily_ai_insight.storage import create_storage, FileStorage
from daily_ai_insight.storage.backends.kv import KVStorage


class TestStorageFactory:
    """Test storage factory function."""

    def test_create_file_storage_default(self):
        """Test creating default file storage."""
        storage = create_storage()
        assert isinstance(storage, FileStorage)
        assert storage.git_sync is True

    def test_create_file_storage_explicit(self):
        """Test creating file storage with explicit parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = create_storage(
                backend="file",
                base_path=tmpdir,
                git_sync=False
            )
            assert isinstance(storage, FileStorage)
            assert storage.base_path == Path(tmpdir)
            assert storage.git_sync is False

    @patch.dict("os.environ", {
        "STORAGE_BACKEND": "file",
        "STORAGE_PATH": "/tmp/test",
        "STORAGE_GIT_SYNC": "false"
    })
    def test_create_from_env(self):
        """Test creating storage from environment variables."""
        storage = create_storage()
        assert isinstance(storage, FileStorage)
        assert storage.base_path == Path("/tmp/test")
        assert storage.git_sync is False

    def test_create_invalid_backend(self):
        """Test creating storage with invalid backend."""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_storage(backend="invalid")


class TestFileStorage:
    """Test file storage backend."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        tmpdir = tempfile.mkdtemp()
        storage = FileStorage(base_path=tmpdir, git_sync=False)
        yield storage
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_save_raw(self, temp_storage):
        """Test saving raw data."""
        items = [
            {"title": "Item 1", "content": "Content 1"},
            {"title": "Item 2", "content": "Content 2"}
        ]

        filepath = await temp_storage.save_raw(items, source="test")

        assert Path(filepath).exists()
        assert "test_" in filepath
        assert Path(filepath).parent == temp_storage.data_path

    @pytest.mark.asyncio
    async def test_save_processed(self, temp_storage):
        """Test saving processed data."""
        data = {"summary": "Test summary", "count": 10}

        filepath = await temp_storage.save_processed(data, report_type="daily")

        assert Path(filepath).exists()
        assert "daily_" in filepath
        assert Path(filepath).parent == temp_storage.processed_path

    @pytest.mark.asyncio
    async def test_save_report(self, temp_storage):
        """Test saving report."""
        report = "# Test Report\n\nThis is a test."

        filepath = await temp_storage.save_report(report, format="markdown")

        assert Path(filepath).exists()
        assert filepath.endswith(".md")
        assert Path(filepath).parent == temp_storage.archives_path

        # Verify content
        content = Path(filepath).read_text(encoding='utf-8')
        assert content == report

    @pytest.mark.asyncio
    async def test_load_recent(self, temp_storage):
        """Test loading recent data."""
        # Save some data
        items1 = [{"id": 1}, {"id": 2}]
        items2 = [{"id": 3}, {"id": 4}]

        await temp_storage.save_raw(items1, source="test1")
        await temp_storage.save_raw(items2, source="test2")

        # Load recent
        recent = await temp_storage.load_recent(hours=24)

        assert len(recent) == 4
        assert {"id": 1} in recent
        assert {"id": 4} in recent

    @pytest.mark.asyncio
    async def test_query(self, temp_storage):
        """Test querying data."""
        # Save data
        await temp_storage.save_raw([{"test": 1}], source="reddit")
        await temp_storage.save_raw([{"test": 2}], source="github")

        # Query by pattern
        results = await temp_storage.query("reddit_*.json")

        assert len(results) == 1
        assert results[0]["source"] == "reddit"

    @pytest.mark.asyncio
    async def test_cleanup(self, temp_storage):
        """Test cleanup old files."""
        # Create some files
        await temp_storage.save_raw([{"test": 1}], source="old")

        # Modify timestamp to be old
        for filepath in temp_storage.data_path.glob("*.json"):
            import time
            old_time = time.time() - (8 * 24 * 3600)  # 8 days ago
            Path(filepath).touch()
            import os
            os.utime(filepath, (old_time, old_time))

        # Cleanup
        await temp_storage.cleanup(days=7)

        # Verify files removed
        assert len(list(temp_storage.data_path.glob("*.json"))) == 0

    def test_get_statistics(self, temp_storage):
        """Test getting storage statistics."""
        stats = temp_storage.get_statistics()

        assert "raw_files" in stats
        assert "processed_files" in stats
        assert "report_files" in stats
        assert "total_size_mb" in stats

    def test_gitignore_created(self, temp_storage):
        """Test .gitignore is created."""
        gitignore = temp_storage.base_path / ".gitignore"
        assert gitignore.exists()

        content = gitignore.read_text()
        assert "data/" in content
        assert "processed/" in content
        assert "!archives/" in content

    @pytest.mark.asyncio
    async def test_git_commit_disabled(self, temp_storage):
        """Test Git commit is skipped when disabled."""
        report = "# Test"
        filepath = await temp_storage.save_report(report)

        # Should not raise error even if Git is not available
        assert Path(filepath).exists()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_git_commit_enabled(self, mock_run):
        """Test Git commit when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(base_path=tmpdir, git_sync=True)
            report = "# Test Report"

            await storage.save_report(report)

            # Verify git commands were called
            assert mock_run.call_count >= 2  # add + commit
            calls = [str(call) for call in mock_run.call_args_list]
            assert any("git add" in str(call) for call in calls)
            assert any("git commit" in str(call) for call in calls)


class TestKVStorage:
    """Test Cloudflare KV storage backend."""

    def test_kv_requires_credentials(self):
        """Test KV requires credentials."""
        with pytest.raises(ValueError, match="Missing Cloudflare credentials"):
            KVStorage()

    @patch.dict("os.environ", {
        "CF_ACCOUNT_ID": "test_account",
        "CF_KV_NAMESPACE_ID": "test_namespace",
        "CF_API_TOKEN": "test_token"
    })
    def test_kv_initialization(self):
        """Test KV initialization with credentials."""
        kv = KVStorage()
        assert kv.account_id == "test_account"
        assert kv.namespace_id == "test_namespace"
        assert kv.api_token == "test_token"

    @patch.dict("os.environ", {
        "CF_ACCOUNT_ID": "test_account",
        "CF_KV_NAMESPACE_ID": "test_namespace",
        "CF_API_TOKEN": "test_token"
    })
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_kv_save_raw(self, mock_session):
        """Test saving raw data to KV."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_session.return_value.__aenter__.return_value.put.return_value.__aenter__.return_value = mock_response

        kv = KVStorage()
        items = [{"test": 1}]

        key = await kv.save_raw(items, source="test")

        assert "test-raw" in key
        assert datetime.now().strftime("%Y-%m-%d") in key

    @patch.dict("os.environ", {
        "CF_ACCOUNT_ID": "test_account",
        "CF_KV_NAMESPACE_ID": "test_namespace",
        "CF_API_TOKEN": "test_token"
    })
    def test_kv_statistics(self):
        """Test KV statistics."""
        kv = KVStorage()
        stats = kv.get_statistics()

        assert stats["backend"] == "cloudflare_kv"
        assert stats["namespace_id"] == "test_namespace"
        assert "default_ttl_days" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
