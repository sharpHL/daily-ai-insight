"""Deduplication logic for content."""

import os
import json
import hashlib
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Deduplicator:
    """Remove duplicate content based on various strategies."""

    def __init__(self, storage_path: str = "storage/data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_path / "dedup_history.json"
        self.history_retention_days = 7
        self._load_history()

    def _load_history(self):
        """Load deduplication history from file."""
        self.seen_hashes = set()
        self.history_data = {}

        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history_data = data

                    # Clean old entries
                    cutoff_date = datetime.now() - timedelta(days=self.history_retention_days)

                    cleaned_data = {}
                    for hash_id, item_data in data.items():
                        seen_date = datetime.fromisoformat(item_data.get("seen_at", ""))
                        if seen_date > cutoff_date:
                            cleaned_data[hash_id] = item_data
                            self.seen_hashes.add(hash_id)

                    self.history_data = cleaned_data
                    logger.info(f"Loaded {len(self.seen_hashes)} items from dedup history")

            except Exception as e:
                logger.warning(f"Error loading dedup history: {e}")
                self.history_data = {}

    def _save_history(self):
        """Save deduplication history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2, default=str)
            logger.debug(f"Saved {len(self.history_data)} items to dedup history")
        except Exception as e:
            logger.error(f"Error saving dedup history: {e}")

    def deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate items using multiple strategies.

        Args:
            items: List of data items

        Returns:
            List of unique items
        """
        unique_items = []
        session_seen = set()  # Track duplicates within this batch

        for item in items:
            # Generate various hashes for deduplication
            content_hash = item.get("hash") or self._generate_content_hash(item)
            url_hash = self._generate_url_hash(item.get("url", ""))
            title_hash = self._generate_title_hash(item.get("title", ""))

            # Check if we've seen this exact content before
            if content_hash in self.seen_hashes or content_hash in session_seen:
                logger.debug(f"Duplicate content found: {item.get('title', '')[:50]}")
                continue

            # Check if we've seen this URL recently (allow updates after 24 hours)
            if url_hash in self.history_data:
                last_seen = datetime.fromisoformat(self.history_data[url_hash]["seen_at"])
                if (datetime.now() - last_seen).total_seconds() < 86400:  # 24 hours
                    logger.debug(f"Recent URL found: {item.get('url', '')}")
                    continue

            # Check for similar titles (fuzzy matching)
            if self._is_similar_title_exists(item.get("title", ""), session_seen):
                logger.debug(f"Similar title found: {item.get('title', '')[:50]}")
                continue

            # Item is unique, add it
            unique_items.append(item)

            # Update tracking
            session_seen.add(content_hash)
            session_seen.add(title_hash)
            self.seen_hashes.add(content_hash)

            # Update history
            self.history_data[content_hash] = {
                "title": item.get("title", "")[:100],
                "url": item.get("url", ""),
                "seen_at": datetime.now().isoformat()
            }

            if url_hash:
                self.history_data[url_hash] = {
                    "title": item.get("title", "")[:100],
                    "seen_at": datetime.now().isoformat()
                }

        # Save updated history
        self._save_history()

        logger.info(f"Deduplicated {len(items)} items to {len(unique_items)} unique items")
        return unique_items

    def _generate_content_hash(self, item: Dict[str, Any]) -> str:
        """Generate hash based on content.

        Args:
            item: Data item

        Returns:
            SHA256 hash
        """
        content = f"{item.get('title', '')}{item.get('content', '')}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_url_hash(self, url: str) -> str:
        """Generate hash based on URL.

        Args:
            url: URL string

        Returns:
            SHA256 hash
        """
        if not url:
            return ""

        # Normalize URL before hashing
        url = url.lower().rstrip('/')

        # Remove common tracking parameters
        for param in ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']:
            url = url.split(f'?{param}=')[0].split(f'&{param}=')[0]

        return hashlib.sha256(url.encode()).hexdigest()

    def _generate_title_hash(self, title: str) -> str:
        """Generate hash based on title.

        Args:
            title: Title string

        Returns:
            SHA256 hash
        """
        if not title:
            return ""

        # Normalize title
        title = title.lower().strip()
        # Remove common variations
        title = title.replace(' - ', ' ').replace(' | ', ' ')

        return hashlib.sha256(title.encode()).hexdigest()

    def _is_similar_title_exists(self, title: str, seen_hashes: Set[str]) -> bool:
        """Check if a similar title already exists.

        Args:
            title: Title to check
            seen_hashes: Set of seen title hashes

        Returns:
            True if similar title exists
        """
        if not title:
            return False

        # Simple similarity check based on key words
        title_words = set(title.lower().split())

        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        title_words = title_words - stop_words

        if len(title_words) < 3:
            return False

        # Check against history (simplified - in production, use better similarity metrics)
        for hash_id, data in self.history_data.items():
            if hash_id not in seen_hashes:
                continue

            existing_title = data.get("title", "").lower()
            existing_words = set(existing_title.split()) - stop_words

            # If 70% of words match, consider it similar
            if len(title_words & existing_words) / len(title_words) > 0.7:
                return True

        return False

    def clear_old_history(self):
        """Clear history older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.history_retention_days)

        cleaned_data = {}
        for hash_id, item_data in self.history_data.items():
            try:
                seen_date = datetime.fromisoformat(item_data.get("seen_at", ""))
                if seen_date > cutoff_date:
                    cleaned_data[hash_id] = item_data
            except:
                continue

        removed_count = len(self.history_data) - len(cleaned_data)
        self.history_data = cleaned_data
        self._save_history()

        logger.info(f"Cleared {removed_count} old entries from dedup history")