"""FOLO RSS aggregator collector."""

import os
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import feedparser
from dotenv import load_dotenv
import logging

from .base import BaseCollector

load_dotenv()
logger = logging.getLogger(__name__)


class FoloCollector(BaseCollector):
    """Collector for FOLO RSS aggregator."""

    def __init__(self):
        super().__init__("FOLO")
        self.cookie = os.getenv("FOLO_COOKIE")
        if not self.cookie:
            raise ValueError("FOLO_COOKIE environment variable is required")

        self.base_url = "https://folo.app"
        self.api_base = "https://api.folo.app"

        # Default FOLO lists to fetch
        self.folo_lists = [
            {
                "name": "AI & Tech News",
                "url": "/api/v1/lists/tech-ai/feeds",
                "category": "technology"
            },
            {
                "name": "Open Source Projects",
                "url": "/api/v1/lists/opensource/feeds",
                "category": "opensource"
            },
            {
                "name": "Research Papers",
                "url": "/api/v1/lists/research/feeds",
                "category": "research"
            }
        ]

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from FOLO RSS aggregator.

        Returns:
            List of standardized data items
        """
        all_items = []

        async with aiohttp.ClientSession() as session:
            # Try different API endpoints
            # First, try to get user's subscribed feeds
            feeds = await self._fetch_user_feeds(session)

            if not feeds:
                # Fallback to public feeds
                feeds = await self._fetch_public_feeds(session)

            # Fetch content from each feed
            tasks = [self._fetch_feed_content(session, feed) for feed in feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching feed: {result}")
                    continue
                if result:
                    all_items.extend(result)

        logger.info(f"Collected {len(all_items)} items from FOLO")
        return all_items

    async def _fetch_user_feeds(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch user's subscribed feeds from FOLO.

        Args:
            session: aiohttp session

        Returns:
            List of feed information
        """
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://folo.app/"
        }

        feeds = []

        try:
            # Try multiple possible API endpoints
            endpoints = [
                "/api/v1/feeds",
                "/api/feeds",
                "/api/user/feeds",
                "/feeds"
            ]

            for endpoint in endpoints:
                url = f"{self.api_base}{endpoint}"
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Handle different response structures
                        if isinstance(data, list):
                            feeds = data
                        elif isinstance(data, dict):
                            feeds = data.get("feeds", data.get("data", []))

                        if feeds:
                            logger.info(f"Found {len(feeds)} feeds from {endpoint}")
                            break
                    else:
                        logger.debug(f"Failed to fetch from {endpoint}: {resp.status}")

        except Exception as e:
            logger.warning(f"Error fetching user feeds: {e}")

        return feeds

    async def _fetch_public_feeds(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch public/default feeds as fallback.

        Args:
            session: aiohttp session

        Returns:
            List of feed information
        """
        # Return some default popular RSS feeds as fallback
        default_feeds = [
            {
                "name": "Hacker News",
                "url": "https://hnrss.org/frontpage",
                "category": "technology"
            },
            {
                "name": "ArXiv AI",
                "url": "http://arxiv.org/rss/cs.AI",
                "category": "research"
            },
            {
                "name": "GitHub Trending",
                "url": "https://rsshub.app/github/trending/daily",
                "category": "opensource"
            }
        ]

        return default_feeds

    async def _fetch_feed_content(
        self, session: aiohttp.ClientSession, feed_info: Dict
    ) -> List[Dict[str, Any]]:
        """Fetch and parse content from a single feed.

        Args:
            session: aiohttp session
            feed_info: Feed information dictionary

        Returns:
            List of standardized items from the feed
        """
        items = []

        try:
            feed_url = feed_info.get("url", feed_info.get("feed_url"))
            if not feed_url:
                return items

            # If it's a relative URL, make it absolute
            if feed_url.startswith("/"):
                feed_url = f"{self.api_base}{feed_url}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            # Add cookie for FOLO API calls
            if "folo" in feed_url.lower():
                headers["Cookie"] = self.cookie

            async with session.get(feed_url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch {feed_url}: {resp.status}")
                    return items

                content = await resp.text()

                # Try to parse as RSS/Atom feed
                feed = feedparser.parse(content)

                if feed.entries:
                    for entry in feed.entries[:20]:  # Limit to 20 items per feed
                        item = self._parse_feed_entry(entry, feed_info)
                        if item:
                            items.append(item)
                else:
                    # Try to parse as JSON (for API responses)
                    try:
                        data = json.loads(content)
                        items = self._parse_json_response(data, feed_info)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse content from {feed_url}")

        except Exception as e:
            logger.error(f"Error fetching feed {feed_info.get('name', 'Unknown')}: {e}")

        return items

    def _parse_feed_entry(self, entry: Any, feed_info: Dict) -> Dict[str, Any]:
        """Parse a single RSS/Atom feed entry.

        Args:
            entry: Feed entry from feedparser
            feed_info: Feed metadata

        Returns:
            Standardized item dictionary
        """
        try:
            # Extract basic information
            title = entry.get("title", "Untitled")
            link = entry.get("link", "")

            # Get content (try different fields)
            content = (
                entry.get("summary", "") or
                entry.get("description", "") or
                entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            )

            # Clean HTML if present
            if content and "<" in content:
                soup = BeautifulSoup(content, "html.parser")
                content = soup.get_text(strip=True)

            # Parse publication date
            published = None
            if hasattr(entry, "published_parsed"):
                published = datetime.fromtimestamp(
                    feedparser._parse_date(entry.published_parsed)
                )
            elif hasattr(entry, "updated_parsed"):
                published = datetime.fromtimestamp(
                    feedparser._parse_date(entry.updated_parsed)
                )

            # Extract author
            author = entry.get("author", None)

            # Extract tags
            tags = []
            if hasattr(entry, "tags"):
                tags = [tag.get("term", "") for tag in entry.tags]

            # Add category from feed info
            category = feed_info.get("category", "general")
            if category not in tags:
                tags.append(category)

            return self.standardize_item(
                title=title,
                content=content[:1000],  # Limit content length
                url=link,
                published_at=published,
                author=author,
                tags=tags,
                raw_data={"feed": feed_info.get("name", "Unknown")}
            )

        except Exception as e:
            logger.error(f"Error parsing feed entry: {e}")
            return None

    def _parse_json_response(self, data: Dict, feed_info: Dict) -> List[Dict[str, Any]]:
        """Parse JSON API response from FOLO.

        Args:
            data: JSON response data
            feed_info: Feed metadata

        Returns:
            List of standardized items
        """
        items = []

        try:
            # Handle different JSON structures
            articles = []

            if isinstance(data, list):
                articles = data
            elif isinstance(data, dict):
                # Try different possible keys
                articles = (
                    data.get("articles", []) or
                    data.get("items", []) or
                    data.get("data", []) or
                    data.get("feeds", [])
                )

            for article in articles[:20]:  # Limit to 20 items
                if not isinstance(article, dict):
                    continue

                item = self.standardize_item(
                    title=article.get("title", "Untitled"),
                    content=article.get("description", article.get("summary", "")),
                    url=article.get("link", article.get("url", "")),
                    published_at=self._parse_date(article.get("published_at", article.get("date"))),
                    author=article.get("author"),
                    tags=[feed_info.get("category", "general")],
                    raw_data={"feed": feed_info.get("name", "Unknown")}
                )

                if item:
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")

        return items

    def _parse_date(self, date_str: Any) -> datetime:
        """Parse various date formats.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object
        """
        if not date_str:
            return datetime.now()

        if isinstance(date_str, datetime):
            return date_str

        # Try common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        return datetime.now()