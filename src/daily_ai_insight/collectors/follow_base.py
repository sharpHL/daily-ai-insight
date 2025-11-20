"""Base collector for Follow.is API."""

import os
import logging
from typing import Dict, Any, List, Optional
import aiohttp

from .base import BaseCollector
from .utils import (
    get_follow_headers,
    sleep_random,
    is_date_within_last_days,
    strip_html,
    escape_html,
    format_date_to_chinese
)

logger = logging.getLogger(__name__)


class FollowBaseCollector(BaseCollector):
    """Base collector for Follow.is API data sources.

    This implements the common fetch logic for all Follow.is-based collectors.
    Subclasses only need to implement transform() and generate_html().
    """

    def __init__(
        self,
        name: str,
        feed_id_env: Optional[str] = None,
        list_id_env: Optional[str] = None,
        home_url: str = "https://follow.is",
        read_more_text: str = "阅读更多"
    ):
        """Initialize Follow.is base collector.

        Args:
            name: Collector name
            feed_id_env: Environment variable name for feed ID (optional)
            list_id_env: Environment variable name for list ID (optional)
            home_url: Home page URL for this source
            read_more_text: Text for "read more" link in HTML
        """
        super().__init__(name)
        self.feed_id = os.getenv(feed_id_env) if feed_id_env else None
        self.list_id = os.getenv(list_id_env) if list_id_env else None
        self.home_url = home_url
        self.read_more_text = read_more_text

        # Global configuration (shared by all Follow.is collectors)
        self.fetch_pages = int(os.getenv("FOLO_FETCH_PAGES", "3"))
        self.filter_days = int(os.getenv("FOLO_FILTER_DAYS", "3"))
        self.cookie = os.getenv("FOLO_COOKIE", "")
        self.api_url = os.getenv("FOLO_DATA_API", "https://api.follow.is/entries")

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from Follow.is API.

        Returns:
            Dictionary with structure:
            {
                "version": "https://jsonfeed.org/version/1.1",
                "title": str,
                "home_page_url": str,
                "description": str,
                "language": "zh-cn",
                "items": List[Dict]
            }
        """
        all_items = []
        published_after = None

        # Check if required ID is set
        feed_or_list_id = self.feed_id or self.list_id
        if not feed_or_list_id:
            logger.error(f"{self.name}: No feed_id or list_id configured")
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

                        # Filter and process items
                        filtered_items = self._filter_items(data["data"])
                        all_items.extend(filtered_items)

                        # Update cursor for next page
                        if data["data"]:
                            published_after = data["data"][-1]["entries"]["publishedAt"]

                except Exception as e:
                    logger.error(f"{self.name}: Error fetching page {page + 1}: {e}")
                    break

                # Random delay to avoid rate limiting
                if page < self.fetch_pages - 1:
                    await sleep_random()

        logger.info(f"{self.name}: Collected {len(all_items)} items")

        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"{self.name} Feeds",
            "home_page_url": self._get_home_url(),
            "description": f"Aggregated {self.name} feeds",
            "language": "zh-cn",
            "items": all_items
        }

    def _build_request_body(self, published_after: Optional[str] = None) -> Dict[str, Any]:
        """Build request body for Follow.is API.

        Args:
            published_after: Cursor for pagination

        Returns:
            Request body dictionary
        """
        body: Dict[str, Any] = {
            "view": 1,
            "withContent": True,
        }

        # Use feedId or listId based on what's configured
        if self.feed_id:
            body["feedId"] = self.feed_id
        elif self.list_id:
            body["listId"] = self.list_id

        if published_after:
            body["publishedAfter"] = published_after

        return body

    def _filter_items(self, data: List[Dict]) -> List[Dict]:
        """Filter items by date and transform to standard format.

        Args:
            data: Raw data items from API

        Returns:
            Filtered and transformed items
        """
        filtered = []

        for entry in data:
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

            # Transform to standard format
            item = {
                "id": entries.get("id", ""),
                "url": entries.get("url", ""),
                "title": entries.get("title", ""),
                "content_html": entries.get("content", ""),
                "date_published": entries.get("publishedAt", ""),
                "authors": [{"name": entries.get("author", "")}],
                "source": feeds.get("title", self.name),
            }

            filtered.append(item)

        return filtered

    def _empty_response(self) -> Dict[str, Any]:
        """Return empty response structure.

        Returns:
            Empty response dictionary
        """
        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"{self.name} Feeds",
            "home_page_url": self._get_home_url(),
            "description": f"Aggregated {self.name} feeds",
            "language": "zh-cn",
            "items": []
        }

    def _get_home_url(self) -> str:
        """Get home page URL for this source.

        Returns:
            Home page URL
        """
        return self.home_url

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
            # Extract authors
            authors = item.get("authors", [])
            if isinstance(authors, list):
                author_names = ", ".join(a.get("name", "") for a in authors if a.get("name"))
            else:
                author_names = str(authors)

            # Create unified item
            unified_item = self.standardize_item(
                item_id=item.get("id", ""),
                title=item.get("title", ""),
                description=strip_html(item.get("content_html", "")),
                url=item.get("url", ""),
                published_date=item.get("date_published", ""),
                authors=author_names or "Unknown",
                source=item.get("source", self.name),
                item_type=source_type,
                details={
                    "content_html": item.get("content_html", "")
                }
            )

            unified_items.append(unified_item)

        return unified_items

    def generate_html(self, item: Dict[str, Any]) -> str:
        """Generate HTML representation of an item.

        Args:
            item: Unified item dictionary

        Returns:
            HTML string
        """
        return f"""
            <strong>{escape_html(item['title'])}</strong><br>
            <small>来源: {escape_html(item.get('source', '未知'))} | 发布日期: {format_date_to_chinese(item.get('published_date', ''))}</small>
            <div class="content-html">
                {item.get('details', {}).get('content_html', '无内容。')}
            </div>
            <a href="{escape_html(item['url'])}" target="_blank" rel="noopener noreferrer">{self.read_more_text}</a>
        """
