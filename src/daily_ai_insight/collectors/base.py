"""Base class for data collectors."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class BaseCollector(ABC):
    """Abstract base class for data collectors.

    Implements the standard three-method pattern:
    1. fetch() - Fetch raw data from source
    2. transform() - Transform raw data to unified format
    3. generate_html() - Generate HTML representation
    """

    def __init__(self, name: str):
        self.name = name
        self.collected_at = None

    @abstractmethod
    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch raw data from the source.

        Returns:
            Raw data dictionary with structure:
            {
                "version": str,
                "title": str,
                "items": List[Dict] - raw items from source
            }
        """
        pass

    @abstractmethod
    def transform(self, raw_data: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
        """Transform raw data to unified format.

        Args:
            raw_data: Raw data from fetch()
            source_type: Type identifier for this source

        Returns:
            List of unified items with structure:
            {
                "id": str,
                "type": str,
                "url": str,
                "title": str,
                "description": str,
                "published_date": str,
                "authors": str or List[str],
                "source": str,
                "details": dict
            }
        """
        pass

    @abstractmethod
    def generate_html(self, item: Dict[str, Any]) -> str:
        """Generate HTML representation of an item.

        Args:
            item: Unified item dictionary

        Returns:
            HTML string
        """
        pass

    def generate_hash(self, content: Dict[str, Any]) -> str:
        """Generate a unique hash for content deduplication.

        Args:
            content: The content dictionary

        Returns:
            SHA256 hash of title + url
        """
        unique_str = f"{content.get('title', '')}{content.get('url', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()

    def standardize_item(
        self,
        item_id: str,
        title: str,
        description: str,
        url: str,
        published_date: str,
        authors: str,
        source: str,
        item_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Standardize data item structure following JS implementation.

        Args:
            item_id: Unique item ID
            title: Item title
            description: Item description/content
            url: Item URL
            published_date: Publication date (ISO format)
            authors: Author(s) name(s)
            source: Source name
            item_type: Type identifier
            details: Additional details dictionary

        Returns:
            Standardized data dictionary
        """
        return {
            "id": item_id,
            "type": item_type,
            "url": url,
            "title": title,
            "description": description,
            "published_date": published_date,
            "authors": authors,
            "source": source,
            "details": details or {}
        }