#!/usr/bin/env python3
"""Extract Twitter accounts from a Folo list."""

import asyncio
import os
import re
import aiohttp
from dotenv import load_dotenv

load_dotenv()


def get_headers() -> dict:
    """Get Folo API headers."""
    cookie = os.getenv("FOLO_COOKIE", "")
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'accept-language': 'zh-CN,zh;q=0.9',
        'origin': 'https://app.follow.is',
        'x-app-name': 'Folo Web',
        'x-app-version': '0.4.9',
        'Cookie': cookie,
    }


async def extract_accounts_from_list(list_id: str) -> dict:
    """Extract all Twitter accounts from a Folo list by fetching entries."""
    print(f"\n🔍 Extracting accounts from list: {list_id}")
    print("=" * 60)

    all_feeds = {}
    published_after = None

    async with aiohttp.ClientSession() as session:
        for page in range(15):  # Fetch more pages to get all feeds
            body = {
                "view": 1,
                "withContent": True,
                "listId": list_id,
            }
            if published_after:
                body["publishedAfter"] = published_after

            print(f"📥 Fetching page {page + 1}...", end=" ")

            try:
                async with session.post(
                    "https://api.follow.is/entries",
                    headers=get_headers(),
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ HTTP {resp.status}")
                        break

                    data = await resp.json()
                    if not data or not data.get("data"):
                        print("No more data")
                        break

                    new_feeds = 0
                    for entry in data["data"]:
                        feeds = entry.get("feeds", {})
                        feed_id = feeds.get("id", "")
                        if feed_id and feed_id not in all_feeds:
                            new_feeds += 1
                            all_feeds[feed_id] = {
                                "id": feed_id,
                                "title": feeds.get("title", ""),
                                "url": feeds.get("url", ""),
                                "siteUrl": feeds.get("siteUrl", ""),
                                "description": feeds.get("description", ""),
                                "image": feeds.get("image", ""),
                            }

                    print(f"Found {new_feeds} new feeds (total: {len(all_feeds)})")

                    # Update cursor
                    if data["data"]:
                        published_after = data["data"][-1]["entries"]["publishedAt"]

                    if len(data["data"]) < 20:  # Less than full page
                        break

                    await asyncio.sleep(0.5)  # Rate limit

            except Exception as e:
                print(f"❌ Error: {e}")
                break

    return all_feeds


def extract_handle(url: str) -> str:
    """Extract Twitter handle from URL."""
    if not url:
        return ""

    # Match twitter.com or x.com URLs
    patterns = [
        r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
        r'rsshub[^/]*/twitter/user/([a-zA-Z0-9_]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            handle = match.group(1)
            # Filter out common non-user paths
            if handle.lower() not in ['home', 'search', 'explore', 'notifications', 'messages', 'i']:
                return f"@{handle}"

    return ""


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        list_id = sys.argv[1]
    else:
        list_id = "153028784690326528"  # AI自媒体 list

    print("\n🐦 Folo List Twitter Account Extractor")
    print("=" * 60)

    if not os.getenv("FOLO_COOKIE"):
        print("\n⚠️  Warning: FOLO_COOKIE not set")
        print("   Add your Folo cookie to .env file")
        print("   Otherwise API calls may fail\n")

    feeds = await extract_accounts_from_list(list_id)

    if not feeds:
        print("\n❌ No feeds found. Check your FOLO_COOKIE.")
        return

    # Process and display results
    print("\n" + "=" * 60)
    print(f"✅ Found {len(feeds)} unique accounts:")
    print("=" * 60 + "\n")

    accounts = []
    for feed_id, feed in feeds.items():
        title = feed['title']
        url = feed.get('url', '')
        site_url = feed.get('siteUrl', '')
        description = feed.get('description', '')

        handle = extract_handle(site_url) or extract_handle(url)

        accounts.append({
            "title": title,
            "handle": handle,
            "site_url": site_url,
            "description": description[:100] if description else "",
        })

    # Sort by title
    accounts.sort(key=lambda x: x['title'].lower())

    # Display
    for i, acc in enumerate(accounts, 1):
        print(f"{i:2d}. {acc['title']}")
        if acc['handle']:
            print(f"    Handle: {acc['handle']}")
        if acc['site_url']:
            print(f"    URL: {acc['site_url']}")
        if acc['description']:
            print(f"    Bio: {acc['description'][:80]}...")
        print()

    # Summary
    print("=" * 60)
    print("📊 Summary:")
    print(f"   Total accounts: {len(accounts)}")
    with_handle = sum(1 for a in accounts if a['handle'])
    print(f"   With Twitter handle: {with_handle}")
    print()

    # Export handles
    handles = [a['handle'] for a in accounts if a['handle']]
    if handles:
        print("📋 All handles (copy-paste friendly):")
        print(", ".join(handles))


if __name__ == "__main__":
    asyncio.run(main())
