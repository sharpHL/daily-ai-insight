"""
Simplified FOLO Base Collector

A more streamlined base class for FOLO-based collectors.
"""

import os
import re
import asyncio
import random
from typing import Dict, Any, List, Optional
import aiohttp

from .base import BaseCollector


class FOLOBaseCollector(BaseCollector):
    """Simplified base collector for FOLO API"""

    def __init__(
        self,
        feed_id: Optional[str] = None,
        list_id: Optional[str] = None,
        name: str = 'folo',
        source_name: str = 'FOLO',
        fetch_pages: int = 3,
        use_feed_id: bool = False,
    ):
        """
        Initialize FOLO base collector

        Args:
            feed_id: FOLO feed ID (for feedId-based sources)
            list_id: FOLO list ID (for listId-based sources)
            name: Collector name
            source_name: Display name for the source
            fetch_pages: Number of pages to fetch
            use_feed_id: If True, use feedId; otherwise use listId
        """
        super().__init__(name)

        self.feed_id = feed_id
        self.list_id = list_id
        self.source_name = source_name
        self.fetch_pages = fetch_pages
        self.use_feed_id = use_feed_id

        # Global FOLO configuration
        self.cookie = os.getenv('FOLO_COOKIE', '')
        self.api_url = os.getenv('FOLO_DATA_API', 'https://api.follow.is/wallets/transactions')
        self.filter_days = int(os.getenv('FOLO_FILTER_DAYS', '3'))

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from FOLO API"""
        # Check if required ID is configured
        if self.use_feed_id and not self.feed_id:
            print(f"⚠️  {self.name}: FEED_ID not configured, skipping")
            return []
        elif not self.use_feed_id and not self.list_id:
            print(f"⚠️  {self.name}: LIST_ID not configured, skipping")
            return []

        all_items = []
        published_after = None

        async with aiohttp.ClientSession() as session:
            for page in range(self.fetch_pages):
                try:
                    headers = self._get_headers()
                    body = self._build_request_body(published_after)

                    print(f"⏳ {self.name}: Fetching page {page + 1}/{self.fetch_pages}...")

                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            print(f"❌ {self.name}: HTTP {response.status}")
                            break

                        data = await response.json()

                        if not data or not data.get('data'):
                            print(f"ℹ️  {self.name}: No more data at page {page + 1}")
                            break

                        # Filter by date and transform
                        for entry in data['data']:
                            if self._is_within_filter_days(entry):
                                item = self._transform_item(entry, entry.get('feeds', {}))
                                if item:
                                    all_items.append(item)

                        # Update cursor for pagination
                        if data['data']:
                            last_entry = data['data'][-1]
                            published_after = last_entry['entries']['publishedAt']

                except Exception as e:
                    print(f"❌ {self.name}: Error on page {page + 1}: {e}")
                    break

                # Random delay to avoid rate limiting
                if page < self.fetch_pages - 1:
                    await asyncio.sleep(random.uniform(1.0, 5.0))

        print(f"✅ {self.name}: Fetched {len(all_items)} items")
        return all_items

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://app.follow.is',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }

        if self.cookie:
            headers['Cookie'] = self.cookie

        return headers

    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        return random.choice(user_agents)

    def _build_request_body(self, published_after: Optional[str] = None) -> Dict[str, Any]:
        """Build request body"""
        body: Dict[str, Any] = {
            'view': 1,
            'withContent': True,
        }

        # Use feedId or listId
        if self.use_feed_id and self.feed_id:
            body['feedId'] = self.feed_id
        elif self.list_id:
            body['listId'] = self.list_id

        if published_after:
            body['publishedAfter'] = published_after

        return body

    def _is_within_filter_days(self, entry: dict) -> bool:
        """Check if entry is within filter days"""
        from datetime import datetime, timedelta, timezone

        entries_data = entry.get('entries', {})
        published_at = entries_data.get('publishedAt', '')

        if not published_at:
            return False

        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.filter_days)
            return pub_date >= cutoff_date
        except:
            return False

    def _transform_item(self, entry: dict, feed: dict) -> Dict[str, Any]:
        """
        Transform FOLO entry to unified format.
        Subclasses should override this method.
        """
        entries_data = entry.get('entries', {})

        title = entries_data.get('title', 'Untitled')
        url = entries_data.get('url', '')
        content_html = entries_data.get('content', '')
        published_at = entries_data.get('publishedAt', '')
        author = entries_data.get('author', 'Unknown')
        feed_title = feed.get('title', self.source_name)

        # Clean HTML
        content = self._strip_html(content_html)

        return {
            'id': entries_data.get('id', ''),
            'title': title,
            'url': url,
            'content': content,
            'published_date': published_at,
            'source': feed_title,
            'authors': [author] if author and author != 'Unknown' else [],
            'metadata': {
                'type': self.name,
                'content_html': content_html,
            }
        }

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags from content"""
        if not html:
            return ''

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&quot;', '"')
        # Remove extra whitespace
        clean = ' '.join(clean.split())

        return clean
