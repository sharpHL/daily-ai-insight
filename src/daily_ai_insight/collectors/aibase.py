"""
AI Base Collector (via FOLO)

Fetches AI news from AI Base (www.aibase.com) via FOLO API.
"""

import os
from typing import List, Dict, Any

from .folo_base import FOLOBaseCollector


class AIBaseCollector(FOLOBaseCollector):
    """Collect AI Base news via FOLO"""

    def __init__(self):
        feed_id = os.getenv('AIBASE_FEED_ID', '')
        fetch_pages = int(os.getenv('AIBASE_FETCH_PAGES', '3'))

        super().__init__(
            feed_id=feed_id,
            name='aibase',
            source_name='AI Base',
            fetch_pages=fetch_pages,
            use_feed_id=True,  # Use feedId instead of listId
        )

    def _transform_item(self, entry: dict, feed: dict) -> Dict[str, Any]:
        """Transform FOLO AI Base entry to unified format"""
        entries_data = entry.get('entries', {})
        feed_data = feed

        title = entries_data.get('title', 'Untitled')
        url = entries_data.get('url', '')
        content_html = entries_data.get('content', '')
        published_at = entries_data.get('publishedAt', '')
        author = entries_data.get('author', 'Unknown')
        feed_title = feed_data.get('title', 'AI Base')

        # Clean HTML content
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
                'type': 'news',
                'content_html': content_html,
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
async def test_aibase_collector():
    """Test AI Base collector"""
    print("Testing AI Base Collector...")

    feed_id = os.getenv('AIBASE_FEED_ID')
    if not feed_id:
        print("⚠️  AIBASE_FEED_ID not set, skipping test")
        return

    collector = AIBaseCollector()
    items = await collector.fetch()

    print(f"\n📊 Fetched {len(items)} items")
    if items:
        print("\n🔍 Sample item:")
        print(f"  Title: {items[0]['title']}")
        print(f"  URL: {items[0]['url']}")
        print(f"  Content: {items[0]['content'][:100]}...")
        print(f"  Source: {items[0]['source']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_aibase_collector())
