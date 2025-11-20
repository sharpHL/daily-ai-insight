"""Data cleaning and normalization."""

import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and normalize collected data."""

    def __init__(self):
        # Keywords to filter out promotional content
        self.spam_keywords = [
            "sponsored", "advertisement", "promo", "discount",
            "limited offer", "buy now", "click here"
        ]

        # Minimum content length
        self.min_content_length = 50

        # Maximum age for content (in days)
        self.max_age_days = 7

    def clean(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and filter data items.

        Args:
            items: List of raw data items

        Returns:
            List of cleaned and filtered items
        """
        cleaned_items = []

        for item in items:
            # Skip if item doesn't meet basic requirements
            if not self._is_valid_item(item):
                continue

            # Clean the item
            cleaned_item = self._clean_item(item)

            # Apply filters
            if self._should_keep_item(cleaned_item):
                cleaned_items.append(cleaned_item)

        logger.info(f"Cleaned {len(items)} items, kept {len(cleaned_items)}")
        return cleaned_items

    def _is_valid_item(self, item: Dict[str, Any]) -> bool:
        """Check if item has required fields.

        Args:
            item: Data item

        Returns:
            True if item is valid
        """
        required_fields = ["title", "content", "url"]
        return all(field in item and item[field] for field in required_fields)

    def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean individual item.

        Args:
            item: Raw data item

        Returns:
            Cleaned item
        """
        cleaned = item.copy()

        # Clean title
        cleaned["title"] = self._clean_text(cleaned["title"])

        # Clean content
        cleaned["content"] = self._clean_text(cleaned["content"])

        # Remove duplicate whitespace
        cleaned["title"] = re.sub(r'\s+', ' ', cleaned["title"]).strip()
        cleaned["content"] = re.sub(r'\s+', ' ', cleaned["content"]).strip()

        # Truncate very long content
        if len(cleaned["content"]) > 2000:
            cleaned["content"] = cleaned["content"][:1997] + "..."

        # Normalize URL
        cleaned["url"] = self._normalize_url(cleaned["url"])

        # Ensure datetime objects are properly formatted
        if "published_at" in cleaned and isinstance(cleaned["published_at"], str):
            try:
                cleaned["published_at"] = datetime.fromisoformat(cleaned["published_at"])
            except:
                cleaned["published_at"] = datetime.now()

        return cleaned

    def _clean_text(self, text: str) -> str:
        """Clean text content.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', '', text)

        # Remove URLs from content (keep them in the url field)
        text = re.sub(r'https?://\S+', '', text)

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\'\"]+', ' ', text)

        # Fix encoding issues
        text = text.encode('ascii', 'ignore').decode('ascii')

        return text

    def _normalize_url(self, url: str) -> str:
        """Normalize URL format.

        Args:
            url: Raw URL

        Returns:
            Normalized URL
        """
        if not url:
            return ""

        # Remove tracking parameters
        url = re.sub(r'[\?\&](utm_|ref=|source=)[^&]*', '', url)

        # Remove trailing slashes
        url = url.rstrip('/')

        # Ensure https
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)

        return url

    def _should_keep_item(self, item: Dict[str, Any]) -> bool:
        """Determine if item should be kept after filtering.

        Args:
            item: Cleaned data item

        Returns:
            True if item should be kept
        """
        # Check content length
        if len(item.get("content", "")) < self.min_content_length:
            logger.debug(f"Filtered out item with short content: {item.get('title', '')}")
            return False

        # Check for spam keywords
        content_lower = (item.get("content", "") + item.get("title", "")).lower()
        for keyword in self.spam_keywords:
            if keyword in content_lower:
                logger.debug(f"Filtered out spam item: {item.get('title', '')}")
                return False

        # Check age
        if "published_at" in item:
            age = datetime.now() - item["published_at"]
            if age.days > self.max_age_days:
                logger.debug(f"Filtered out old item: {item.get('title', '')}")
                return False

        # Check for duplicate title/content (exact match)
        if item.get("title", "").strip() == item.get("content", "").strip():
            logger.debug(f"Filtered out duplicate title/content: {item.get('title', '')}")
            return False

        return True

    def group_by_category(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by category/tags.

        Args:
            items: List of cleaned items

        Returns:
            Dictionary of categorized items
        """
        categories = {}

        for item in items:
            # Get tags or use source as category
            tags = item.get("tags", [])
            if not tags:
                tags = [item.get("source", "uncategorized")]

            # Add to each relevant category
            for tag in tags:
                if tag not in categories:
                    categories[tag] = []
                categories[tag].append(item)

        return categories