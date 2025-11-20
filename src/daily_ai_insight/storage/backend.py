"""Abstract storage backend interface."""

from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime


class StorageBackend(Protocol):
    """Storage backend protocol (duck-typed interface).

    All storage implementations must follow this interface.
    Supports sync and async methods based on implementation needs.
    """

    async def save_raw(
        self,
        items: List[Dict[str, Any]],
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save raw collected data.

        Args:
            items: List of data items
            source: Data source name (e.g., 'reddit', 'github')
            metadata: Optional metadata to attach

        Returns:
            Identifier (file path, key, URL, etc.)
        """
        ...

    async def save_processed(
        self,
        data: Dict[str, Any],
        report_type: str = "daily"
    ) -> str:
        """Save processed/analyzed data.

        Args:
            data: Processed data dictionary
            report_type: Type of report (e.g., 'daily', 'weekly')

        Returns:
            Identifier of saved data
        """
        ...

    async def save_report(
        self,
        content: str,
        format: str = "markdown"
    ) -> str:
        """Save final report.

        Args:
            content: Report content
            format: Report format ('markdown', 'html', 'json')

        Returns:
            Identifier of saved report
        """
        ...

    async def load_recent(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Load recent raw data within time window.

        Args:
            hours: Number of hours to look back

        Returns:
            List of all items from recent data
        """
        ...

    async def query(
        self,
        pattern: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Query data by pattern and date range.

        Args:
            pattern: Query pattern (glob, key prefix, etc.)
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching data items
        """
        ...

    async def cleanup(self, days: int = 7):
        """Remove old data.

        Args:
            days: Number of days to retain data
        """
        ...

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics (sync operation).

        Returns:
            Dictionary with stats (file count, size, etc.)
        """
        ...
