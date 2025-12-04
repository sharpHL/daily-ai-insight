"""
GitHub Trending Collector

Fetches trending repositories from GitHub Trending API.
Supports optional translation of descriptions to Chinese.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

from .base import BaseCollector


class GitHubTrendingCollector(BaseCollector):
    """Collect trending repositories from GitHub"""

    def __init__(self):
        super().__init__("github_trending")
        self.api_url = os.getenv(
            'GITHUB_TRENDING_API',
            'https://gh-trending-api.com/repositories'
        )
        self.language_filter = os.getenv('GITHUB_TRENDING_LANGUAGE', '')
        self.translate_enabled = os.getenv('TRANSLATE_ENABLED', 'false').lower() == 'true'

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch trending repositories from GitHub"""
        try:
            # Build API URL with optional language filter
            url = self.api_url
            params = {}
            if self.language_filter:
                params['language'] = self.language_filter
                params['spoken_language_code'] = 'en'  # Get English descriptions

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                projects = response.json()

            if not isinstance(projects, list):
                print(f"⚠️  GitHub Trending API returned non-list data: {type(projects)}")
                return []

            if len(projects) == 0:
                print("⚠️  No trending projects found")
                return []

            print(f"✅ Fetched {len(projects)} trending repositories")

            # Optional: Translate descriptions
            if self.translate_enabled:
                projects = await self._translate_descriptions(projects)

            # Transform to unified format
            return self._transform_items(projects)

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error fetching GitHub Trending: {e}")
            return []
        except httpx.RequestError as e:
            print(f"❌ Request error fetching GitHub Trending: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error fetching GitHub Trending: {e}")
            return []

    async def _translate_descriptions(self, projects: List[dict]) -> List[dict]:
        """Translate project descriptions to Chinese using LLM"""
        try:
            # Extract non-empty descriptions
            descriptions = [p.get('description', '') or '' for p in projects]
            non_empty = [d for d in descriptions if d.strip()]

            if not non_empty:
                print("⚠️  No descriptions to translate")
                return projects

            # Build translation prompt
            prompt = f"""Translate the following English project descriptions to Chinese.
Provide the translations as a JSON array of strings, in the exact same order as the input.
Each string in the output array must correspond to the string at the same index in the input array.
If an input description is an empty string, the corresponding translated string in the output array should also be an empty string.

Input Descriptions (JSON array of strings):
{descriptions}

Respond ONLY with the JSON array of Chinese translations. Do not include any other text or explanations.
JSON Array of Chinese Translations:"""

            # Call LLM for translation (you'd need to implement this)
            # For now, we'll skip translation and use original descriptions
            # TODO: Integrate with LLM provider for translation
            print("⚠️  Translation not implemented yet, using original descriptions")

            return projects

        except Exception as e:
            print(f"⚠️  Failed to translate descriptions: {e}")
            return projects

    def _transform_items(self, projects: List[dict]) -> List[Dict[str, Any]]:
        """Transform GitHub Trending data to unified format"""
        items = []
        now = datetime.now(timezone.utc).isoformat()

        for idx, project in enumerate(projects):
            # Extract fields from GitHub Trending API response
            owner = project.get('author', '')
            name = project.get('name', '')
            description = project.get('description', '') or ''
            url = project.get('url', '')
            language = project.get('language', '')
            language_color = project.get('languageColor', '')
            stars = project.get('stars', 0)
            forks = project.get('forks', 0)
            stars_today = project.get('currentPeriodStars', 0)
            built_by = project.get('builtBy', [])

            item = {
                'id': f"github-{idx + 1}",
                'title': f"{owner}/{name}",
                'url': url,
                'content': description,
                'published_date': now,
                'source': 'GitHub Trending',
                'authors': [owner] if owner else [],
                'metadata': {
                    'type': 'github_project',
                    'owner': owner,
                    'name': name,
                    'language': language,
                    'language_color': language_color,
                    'stars': stars,
                    'forks': forks,
                    'stars_today': stars_today,
                    'built_by': built_by,
                }
            }

            items.append(item)

        return items


    def transform(self, raw_data: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
        """Transform is not needed as fetch() already returns unified format."""
        # GitHub Trending fetch() already returns unified format
        return raw_data if isinstance(raw_data, list) else []

    def generate_html(self, item: Dict[str, Any]) -> str:
        """Generate HTML for a GitHub trending item."""
        metadata = item.get('metadata', {})
        stars = metadata.get('stars', 0)
        language = metadata.get('language', 'N/A')
        stars_today = metadata.get('stars_today', 0)

        return f"""
            <strong>{item['title']}</strong><br>
            <small>⭐ {stars} stars (Today: +{stars_today}) | Language: {language}</small><br>
            {item.get('content', 'No description')}<br>
            <a href="{item['url']}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
        """


# Test function
async def test_github_trending():
    """Test GitHub Trending collector"""
    print("Testing GitHub Trending Collector...")
    collector = GitHubTrendingCollector()
    items = await collector.fetch()

    print(f"\n📊 Fetched {len(items)} items")
    if items:
        print("\n🔍 Sample item:")
        print(f"  Title: {items[0]['title']}")
        print(f"  URL: {items[0]['url']}")
        print(f"  Content: {items[0]['content'][:100]}...")
        print(f"  Stars: {items[0]['metadata']['stars']}")
        print(f"  Language: {items[0]['metadata']['language']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_github_trending())
