"""
Twitter Collector (via FOLO)

Fetches Twitter/X posts via FOLO API.
"""

import os
from typing import List, Dict, Any

from .folo_base import FOLOBaseCollector


class TwitterCollector(FOLOBaseCollector):
    """Collect Twitter/X posts via FOLO"""

    def __init__(self):
        list_id = os.getenv('TWITTER_LIST_ID', '')
        fetch_pages = int(os.getenv('TWITTER_FETCH_PAGES', '3'))

        super().__init__(
            list_id=list_id,
            name='twitter',
            source_name='Twitter/X',
            fetch_pages=fetch_pages,
        )

    def _transform_item(self, entry: dict, feed: dict) -> Dict[str, Any]:
        """Transform FOLO Twitter entry to unified format"""
        entries_data = entry.get('entries', {})
        feed_data = feed

        # Extract tweet details
        title = entries_data.get('title', 'Untitled Tweet')
        url = entries_data.get('url', '')
        content_html = entries_data.get('content', '')
        published_at = entries_data.get('publishedAt', '')
        author = entries_data.get('author', 'Unknown')
        feed_title = feed_data.get('title', 'Twitter')

        # Handle Twitter-specific source naming
        # Original format: "twitter-{author}" or "{feed_title} - {author}"
        if feed_title.startswith('Twitter'):
            source = f"twitter-{author}"
        else:
            source = f"{feed_title} - {author}"

        # Clean HTML content
        content = self._strip_html(content_html)

        return {
            'id': entries_data.get('id', ''),
            'title': title,
            'url': url,
            'content': content,
            'published_date': published_at,
            'source': source,
            'authors': [author] if author and author != 'Unknown' else [],
            'metadata': {
                'type': 'tweet',
                'content_html': content_html,
                'feed_title': feed_title,
            }
        }


    def transform(self, raw_data: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
        """Transform is not needed as fetch() already returns unified format."""
        # FOLO collectors fetch() already returns unified format
        return raw_data if isinstance(raw_data, list) else []

    def generate_html(self, item: Dict[str, Any]) -> str:
        """Generate HTML for a FOLO item."""
        from datetime import datetime
        
        pub_date = item.get('published_date', '')
        try:
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        except:
            date_str = pub_date

        return f"""
            <strong>{item.get('title', 'Untitled')}</strong><br>
            <small>Source: {item.get('source', 'Unknown')} | Date: {date_str}</small><br>
            {item.get('content', 'No content')[:200]}...<br>
            <a href="{item.get('url', '#')}" target="_blank" rel="noopener noreferrer">Read more</a>
        """


# Test function
async def test_twitter_collector():
    """Test Twitter collector"""
    print("Testing Twitter Collector...")

    # Check if required env vars are set
    list_id = os.getenv('TWITTER_LIST_ID')
    if not list_id:
        print("⚠️  TWITTER_LIST_ID not set, skipping test")
        return

    collector = TwitterCollector()
    items = await collector.fetch()

    print(f"\n📊 Fetched {len(items)} tweets")
    if items:
        print("\n🔍 Sample tweet:")
        print(f"  Title: {items[0]['title']}")
        print(f"  URL: {items[0]['url']}")
        print(f"  Content: {items[0]['content'][:100]}...")
        print(f"  Author: {items[0]['authors']}")
        print(f"  Source: {items[0]['source']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_twitter_collector())
