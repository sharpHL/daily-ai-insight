"""Storage manager for data persistence."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StorageManager:
    """Manage data storage and retrieval."""

    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.processed_path = self.base_path / "processed"
        self.archives_path = self.base_path / "archives"

        # Create directories
        for path in [self.data_path, self.processed_path, self.archives_path]:
            path.mkdir(parents=True, exist_ok=True)

    def save_raw_data(self, items: List[Dict[str, Any]], source: str = "folo") -> str:
        """Save raw collected data.

        Args:
            items: List of data items
            source: Data source name

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.json"
        filepath = self.data_path / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "source": source,
                    "collected_at": datetime.now().isoformat(),
                    "count": len(items),
                    "items": items
                }, f, indent=2, default=str)

            logger.info(f"Saved {len(items)} raw items to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving raw data: {e}")
            raise

    def save_processed_data(self, data: Dict[str, Any], report_type: str = "daily") -> str:
        """Save processed/analyzed data.

        Args:
            data: Processed data dictionary
            report_type: Type of report

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{report_type}_{date_str}.json"
        filepath = self.processed_path / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "type": report_type,
                    "processed_at": datetime.now().isoformat(),
                    "data": data
                }, f, indent=2, default=str)

            logger.info(f"Saved processed data to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving processed data: {e}")
            raise

    def save_report(self, report: str, format: str = "markdown") -> str:
        """Save generated report.

        Args:
            report: Report content
            format: Report format (markdown, html, json)

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        extension = "md" if format == "markdown" else format
        filename = f"report_{date_str}.{extension}"
        filepath = self.archives_path / filename

        try:
            mode = 'w' if format in ['markdown', 'html'] else 'wb'
            encoding = 'utf-8' if format in ['markdown', 'html'] else None

            with open(filepath, mode, encoding=encoding) as f:
                if format == 'json':
                    json.dump(report, f, indent=2, default=str)
                else:
                    f.write(report)

            logger.info(f"Saved report to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise

    def load_recent_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Load recent raw data within specified hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of all items from recent files
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        all_items = []

        try:
            for filepath in self.data_path.glob("*.json"):
                # Check file modification time
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_time:
                    continue

                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get("items", [])
                    all_items.extend(items)

            logger.info(f"Loaded {len(all_items)} items from recent files")
            return all_items

        except Exception as e:
            logger.error(f"Error loading recent data: {e}")
            return []

    def load_last_report(self) -> Optional[Dict[str, Any]]:
        """Load the most recent report.

        Returns:
            Last report data or None
        """
        try:
            # Find most recent report file
            report_files = list(self.archives_path.glob("report_*.md"))
            if not report_files:
                return None

            latest_file = max(report_files, key=lambda p: p.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "file": str(latest_file),
                "content": content,
                "created_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
            }

        except Exception as e:
            logger.error(f"Error loading last report: {e}")
            return None

    def get_today_data(self) -> Dict[str, Any]:
        """Get all data collected today.

        Returns:
            Dictionary with today's data
        """
        today_str = datetime.now().strftime("%Y%m%d")
        today_items = []
        sources = set()

        try:
            for filepath in self.data_path.glob(f"*_{today_str}*.json"):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get("items", [])
                    today_items.extend(items)
                    sources.add(data.get("source", "unknown"))

            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sources": list(sources),
                "count": len(today_items),
                "items": today_items
            }

        except Exception as e:
            logger.error(f"Error getting today's data: {e}")
            return {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0, "items": []}

    def cleanup_old_files(self, days: int = 7):
        """Remove files older than specified days.

        Args:
            days: Number of days to retain files
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        try:
            # Clean raw data files
            for filepath in self.data_path.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_date:
                    filepath.unlink()
                    removed_count += 1

            # Clean processed data files (keep longer)
            cutoff_processed = datetime.now() - timedelta(days=days * 2)
            for filepath in self.processed_path.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_processed:
                    filepath.unlink()
                    removed_count += 1

            # Archives are kept indefinitely

            logger.info(f"Removed {removed_count} old files")

        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        try:
            raw_files = list(self.data_path.glob("*.json"))
            processed_files = list(self.processed_path.glob("*.json"))
            report_files = list(self.archives_path.glob("*"))

            # Calculate total size
            total_size = sum(f.stat().st_size for f in raw_files + processed_files + report_files)

            return {
                "raw_files": len(raw_files),
                "processed_files": len(processed_files),
                "report_files": len(report_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file": min(
                    [f.stat().st_mtime for f in raw_files + processed_files + report_files],
                    default=None
                ),
                "newest_file": max(
                    [f.stat().st_mtime for f in raw_files + processed_files + report_files],
                    default=None
                )
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}