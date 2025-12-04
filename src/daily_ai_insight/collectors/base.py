"""Base classes for data collectors.

This module contains:
- BaseCollector: Abstract base class defining the collector interface
- FollowCollector: Concrete implementation for Follow.is API sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import os
import logging
import asyncio
import aiohttp

from .utils import (
    get_follow_headers,
    sleep_random,
    is_date_within_last_days,
    strip_html,
    escape_html,
    format_date_to_chinese
)

logger = logging.getLogger(__name__)


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


class FollowCollector(BaseCollector):
    """Base collector for Follow.is API data sources.

    This class provides complete implementation for Follow.is data collection.
    Subclasses only need to provide configuration in __init__.

    Example:
        class MyCollector(FollowCollector):
            def __init__(self):
                super().__init__(
                    name="my_collector",
                    feed_id_env="MY_FEED_ID",  # or list_id_env
                    source_name="My Source",
                    item_type="article"
                )
    """

    def __init__(
        self,
        name: str,
        feed_id_env: Optional[str] = None,
        list_id_env: Optional[str] = None,
        source_name: Optional[str] = None,
        home_url: str = "https://follow.is",
        read_more_text: str = "阅读更多...",
        item_type: str = "article",
        custom_source_format: Optional[callable] = None,
        transform_callback: Optional[callable] = None
    ):
        """Initialize Follow.is collector.

        Args:
            name: Collector name
            feed_id_env: Environment variable name for feed ID
            list_id_env: Environment variable name for list ID
            source_name: Display name for the source
            home_url: Home page URL for this source
            read_more_text: Text for "read more" link in HTML
            item_type: Type identifier for items (paper, tweet, news, etc.)
            custom_source_format: Optional function to format source field
            transform_callback: Optional function to transform entries.
                Should have signature: (entries: Dict, feeds: Dict, ...) -> Dict
                If not provided, uses default _transform_entry method.
        """
        super().__init__(name)

        # Configuration
        self.feed_id = os.getenv(feed_id_env) if feed_id_env else None
        self.list_id = os.getenv(list_id_env) if list_id_env else None
        self.source_name = source_name or name
        self.home_url = home_url
        self.read_more_text = read_more_text
        self.item_type = item_type
        self.custom_source_format = custom_source_format
        self.transform_callback = transform_callback

        # Global Follow.is configuration
        self.fetch_pages = int(os.getenv("FOLO_FETCH_PAGES", "3"))
        self.filter_days = int(os.getenv("FOLO_FILTER_DAYS", "3"))
        self.cookie = os.getenv("FOLO_COOKIE", "")
        self.api_url = os.getenv("FOLO_DATA_API", "https://api.follow.is/entries")

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from Follow.is API.

        Returns:
            Dictionary with JSFeed structure containing items
        """
        all_items = []
        published_after = None

        # Check if required ID is configured
        feed_or_list_id = self.feed_id or self.list_id
        if not feed_or_list_id:
            logger.warning(f"{self.name}: No feed_id or list_id configured")
            return self._empty_response()

        async with aiohttp.ClientSession() as session:
            for page in range(self.fetch_pages):
                try:
                    headers = get_follow_headers(self.cookie)
                    body = self._build_request_body(published_after)

                    logger.info(f"{self.name}: Fetching page {page + 1}/{self.fetch_pages}")

                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status != 200:
                            logger.error(
                                f"{self.name}: Failed to fetch page {page + 1}: "
                                f"HTTP {resp.status}"
                            )
                            break

                        data = await resp.json()

                        if not data or not data.get("data"):
                            logger.info(f"{self.name}: No more data at page {page + 1}")
                            break

                        # Process and filter items
                        for entry in data["data"]:
                            if not entry.get("entries"):
                                continue

                            entries = entry["entries"]
                            feeds = entry.get("feeds", {})

                            # Filter by date
                            if not is_date_within_last_days(
                                entries.get("publishedAt", ""),
                                self.filter_days
                            ):
                                continue

                            # Transform to unified format
                            item = self._transform_entry(entries, feeds)
                            all_items.append(item)

                        # Update cursor for next page
                        if data["data"]:
                            published_after = data["data"][-1]["entries"]["publishedAt"]

                except Exception as e:
                    logger.error(f"{self.name}: Error fetching page {page + 1}: {e}")
                    break

                # Random delay between pages
                if page < self.fetch_pages - 1:
                    await sleep_random()

        logger.info(f"{self.name}: Collected {len(all_items)} items")

        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"{self.source_name} Feeds",
            "home_page_url": self.home_url,
            "description": f"Aggregated {self.source_name} feeds",
            "language": "zh-cn",
            "items": all_items
        }

    def _build_request_body(self, published_after: Optional[str] = None) -> Dict[str, Any]:
        """Build request body for Follow.is API."""
        body: Dict[str, Any] = {
            "view": 1,
            "withContent": True,
        }

        # Use feedId or listId based on configuration
        if self.feed_id:
            body["feedId"] = self.feed_id
        elif self.list_id:
            body["listId"] = self.list_id

        if published_after:
            body["publishedAfter"] = published_after

        return body

    def _transform_entry(self, entries: Dict, feeds: Dict) -> Dict[str, Any]:
        """Transform Follow.is entry to standard format.

        Can be overridden by subclasses or provided via transform_callback.

        Args:
            entries: Entry data from API
            feeds: Feed metadata from API

        Returns:
            Standardized item dictionary
        """
        # Use callback if provided
        if self.transform_callback:
            return self.transform_callback(
                entries,
                feeds,
                source_name=self.source_name,
                item_type=self.item_type,
                custom_source_format=self.custom_source_format
            )

        # Default transformation
        # Extract basic fields
        title = entries.get("title", "")
        url = entries.get("url", "")
        content_html = entries.get("content", "")
        published_at = entries.get("publishedAt", "")
        author = entries.get("author", "")

        # Format source field (can be customized)
        if self.custom_source_format:
            source = self.custom_source_format(author, feeds)
        else:
            source = feeds.get("title", self.source_name)

        # Extract authors
        authors = author if author else "Unknown"

        return {
            "id": entries.get("id", ""),
            "url": url,
            "title": title,
            "content_html": content_html,
            "content_text": strip_html(content_html),
            "date_published": published_at,
            "authors": [{"name": authors}] if authors != "Unknown" else [],
            "source": source,
            "_metadata": {
                "type": self.item_type,
                "feed_title": feeds.get("title", "")
            }
        }

    def transform(self, raw_data: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
        """Transform raw data to unified format.

        Args:
            raw_data: Raw data from fetch()
            source_type: Type identifier for this source

        Returns:
            List of unified items
        """
        unified_items = []

        if not raw_data or not raw_data.get("items"):
            return unified_items

        for item in raw_data["items"]:
            # Create unified item using base class helper
            unified_item = self.standardize_item(
                item_id=item.get("id", ""),
                title=item.get("title", ""),
                description=item.get("content_text", ""),
                url=item.get("url", ""),
                published_date=item.get("date_published", ""),
                authors=self._format_authors(item.get("authors", [])),
                source=item.get("source", self.source_name),
                item_type=source_type,
                details={
                    "content_html": item.get("content_html", ""),
                    "metadata": item.get("_metadata", {})
                }
            )

            unified_items.append(unified_item)

        return unified_items

    def generate_html(self, item: Dict[str, Any]) -> str:
        """Generate HTML representation of an item.

        Can be overridden by subclasses for custom HTML generation.

        Args:
            item: Unified item dictionary

        Returns:
            HTML string
        """
        # Format date
        pub_date = item.get("published_date", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = pub_date[:19] if len(pub_date) > 19 else pub_date
        else:
            date_str = "未知日期"

        # Get content preview
        content = item.get("description", "")
        if not content and item.get("details", {}).get("content_html"):
            content = strip_html(item["details"]["content_html"])

        content_preview = content[:200] + "..." if len(content) > 200 else content

        return f"""
            <strong>{escape_html(item.get('title', '无标题'))}</strong><br>
            <small>来源: {escape_html(item.get('source', self.source_name))} |
                   发布时间: {escape_html(date_str)}</small><br>
            <p>{escape_html(content_preview)}</p>
            <a href="{escape_html(item.get('url', '#'))}"
               target="_blank" rel="noopener noreferrer">{self.read_more_text}</a>
        """

    def _format_authors(self, authors: List[Dict]) -> str:
        """Format authors list to string."""
        if not authors:
            return "Unknown"

        if isinstance(authors, list):
            names = [a.get("name", "") for a in authors if a.get("name")]
            return ", ".join(names) if names else "Unknown"

        return str(authors)

    def _empty_response(self) -> Dict[str, Any]:
        """Return empty response structure."""
        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"{self.source_name} Feeds",
            "home_page_url": self.home_url,
            "description": f"Aggregated {self.source_name} feeds",
            "language": "zh-cn",
            "items": []
        }