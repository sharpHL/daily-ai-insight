"""Local filesystem storage backend with Git integration."""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import subprocess

logger = logging.getLogger(__name__)


class FileStorage:
    """Local filesystem storage with automatic Git commits.

    Directory structure:
        storage/
        ├── data/          # Raw data (gitignored)
        ├── processed/     # Processed data (gitignored)
        └── archives/      # Final reports (tracked by Git)
    """

    def __init__(
        self,
        base_path: str = "storage",
        git_sync: bool = True,
        auto_push: bool = False
    ):
        """Initialize file storage.

        Args:
            base_path: Base directory for storage
            git_sync: Enable automatic Git commits for archives
            auto_push: Automatically push to remote after commit
        """
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.processed_path = self.base_path / "processed"
        self.archives_path = self.base_path / "archives"
        self.git_sync = git_sync
        self.auto_push = auto_push

        # Create directories
        for path in [self.data_path, self.processed_path, self.archives_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Setup .gitignore
        self._setup_gitignore()

    def _setup_gitignore(self):
        """Create .gitignore to exclude temporary data."""
        gitignore_path = self.base_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = (
                "# Local temporary data (not committed)\n"
                "data/\n"
                "processed/\n"
                "\n"
                "# Only track archives\n"
                "!archives/\n"
            )
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            logger.info(f"Created {gitignore_path}")

    async def save_raw(
        self,
        items: List[Dict[str, Any]],
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save raw collected data (local temp, not committed).

        Args:
            items: List of data items
            source: Data source name
            metadata: Optional metadata

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.json"
        filepath = self.data_path / filename

        data = {
            "source": source,
            "collected_at": datetime.now().isoformat(),
            "count": len(items),
            "items": items,
            **(metadata or {})
        }

        # Async file write
        await asyncio.to_thread(
            self._write_json,
            filepath,
            data
        )

        logger.info(f"💾 Saved {len(items)} raw items to {filepath.name}")
        return str(filepath)

    async def save_processed(
        self,
        data: Dict[str, Any],
        report_type: str = "daily"
    ) -> str:
        """Save processed data (local temp, not committed).

        Args:
            data: Processed data
            report_type: Type of report

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{report_type}_{date_str}.json"
        filepath = self.processed_path / filename

        payload = {
            "type": report_type,
            "processed_at": datetime.now().isoformat(),
            "data": data
        }

        await asyncio.to_thread(
            self._write_json,
            filepath,
            payload
        )

        logger.info(f"📊 Saved processed data to {filepath.name}")
        return str(filepath)

    async def save_report(
        self,
        content: str,
        format: str = "markdown"
    ) -> str:
        """Save final report (committed to Git).

        Args:
            content: Report content
            format: Report format

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = "md" if format == "markdown" else format
        filename = f"report_{date_str}.{ext}"
        filepath = self.archives_path / filename

        # Write report
        await asyncio.to_thread(
            filepath.write_text,
            content,
            encoding='utf-8'
        )

        logger.info(f"📄 Saved report to {filepath.name}")

        # Auto Git commit
        if self.git_sync:
            await self._git_commit(filepath)

        return str(filepath)

    async def _git_commit(self, filepath: Path):
        """Commit file to Git asynchronously.

        Args:
            filepath: File to commit
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")

            # Try to get relative path, fall back to absolute
            try:
                rel_path = filepath.relative_to(Path.cwd())
            except ValueError:
                # Not in current directory, use absolute path
                rel_path = filepath

            # Git add
            await asyncio.to_thread(
                subprocess.run,
                ["git", "add", str(rel_path)],
                check=True,
                capture_output=True,
                text=True
            )

            # Git commit
            commit_message = (
                f"feat: daily report {date_str}\n\n"
                f"🤖 Generated with daily-ai-insight\n\n"
                f"Co-Authored-By: Claude <noreply@anthropic.com>"
            )

            await asyncio.to_thread(
                subprocess.run,
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"✓ Git committed: {filepath.name}")

            # Auto push if enabled
            if self.auto_push:
                await self._git_push()

        except subprocess.CalledProcessError as e:
            # Git errors don't block main flow
            stderr = e.stderr if hasattr(e, 'stderr') else str(e)
            logger.warning(f"Git commit skipped: {stderr}")
        except Exception as e:
            logger.warning(f"Git commit failed: {e}")

    async def _git_push(self):
        """Push commits to remote."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["git", "push"],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("✓ Git pushed to remote")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git push failed: {e.stderr}")

    async def load_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Load recent raw data.

        Args:
            hours: Time window in hours

        Returns:
            List of all items from recent files
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        def _load():
            items = []
            for filepath in self.data_path.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_time:
                    continue

                try:
                    data = json.loads(filepath.read_text(encoding='utf-8'))
                    items.extend(data.get("items", []))
                except Exception as e:
                    logger.warning(f"Failed to load {filepath.name}: {e}")

            return items

        all_items = await asyncio.to_thread(_load)
        logger.info(f"📥 Loaded {len(all_items)} recent items")
        return all_items

    async def query(
        self,
        pattern: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Query data files by pattern and date range.

        Args:
            pattern: Glob pattern (e.g., 'reddit_*.json')
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of matching data
        """
        def _query():
            results = []
            for filepath in self.data_path.glob(pattern):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)

                # Date filtering
                if start_date and mtime < start_date:
                    continue
                if end_date and mtime > end_date:
                    continue

                try:
                    data = json.loads(filepath.read_text(encoding='utf-8'))
                    results.append(data)
                except Exception as e:
                    logger.warning(f"Failed to load {filepath.name}: {e}")

            return results

        results = await asyncio.to_thread(_query)
        logger.info(f"🔍 Query '{pattern}' found {len(results)} files")
        return results

    async def cleanup(self, days: int = 7):
        """Remove old files.

        Args:
            days: Files older than this are removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        def _cleanup():
            count = 0

            # Clean raw data
            for filepath in self.data_path.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_date:
                    filepath.unlink()
                    count += 1

            # Clean processed data (keep longer)
            cutoff_processed = datetime.now() - timedelta(days=days * 2)
            for filepath in self.processed_path.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_processed:
                    filepath.unlink()
                    count += 1

            # Archives are kept forever (managed by Git)
            return count

        removed = await asyncio.to_thread(_cleanup)
        logger.info(f"🗑️  Removed {removed} old files")

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with stats
        """
        try:
            raw_files = list(self.data_path.glob("*.json"))
            processed_files = list(self.processed_path.glob("*.json"))
            report_files = list(self.archives_path.glob("*"))

            total_size = sum(
                f.stat().st_size
                for f in raw_files + processed_files + report_files
            )

            all_files = raw_files + processed_files + report_files
            mtimes = [f.stat().st_mtime for f in all_files] if all_files else []

            return {
                "raw_files": len(raw_files),
                "processed_files": len(processed_files),
                "report_files": len(report_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file": datetime.fromtimestamp(min(mtimes)).isoformat() if mtimes else None,
                "newest_file": datetime.fromtimestamp(max(mtimes)).isoformat() if mtimes else None
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def _write_json(self, filepath: Path, data: Dict[str, Any]):
        """Write JSON file (sync helper for async operation).

        Args:
            filepath: Target file path
            data: Data to write
        """
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding='utf-8'
        )
