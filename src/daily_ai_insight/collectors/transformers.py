"""Transform functions for different data sources.

This module provides pure functions for transforming entries from different
platforms. These can be used as callbacks with FollowCollector, eliminating
the need to create subclasses for each source type.

Usage:
    from daily_ai_insight.collectors import FollowCollector
    from daily_ai_insight.collectors.transformers import twitter_transform

    collector = FollowCollector(
        name="twitter",
        list_id_env="TWITTER_LIST_ID",
        transform_callback=twitter_transform
    )
"""

import re
from typing import Dict, Any, Optional
from .utils import strip_html


# ============================================================================
# Common Helper
# ============================================================================

def extract_common_fields(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Unknown",
    item_type: str = "article",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Extract common fields that all sources share.

    This is the base transformation that all platform-specific
    transformers build upon.

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Default source name
        item_type: Type identifier (article, tweet, etc.)
        custom_source_format: Optional custom formatter for source field

    Returns:
        Base item dictionary
    """
    # Extract basic fields
    title = entries.get("title", "")
    url = entries.get("url", "")
    content_html = entries.get("content", "")
    published_at = entries.get("publishedAt", "")
    author = entries.get("author", "")

    # Format source
    if custom_source_format:
        source = custom_source_format(author, feeds)
    else:
        source = feeds.get("title", source_name)

    return {
        "id": entries.get("id", ""),
        "url": url,
        "title": title,
        "content_html": content_html,
        "content_text": strip_html(content_html),
        "date_published": published_at,
        "authors": [{"name": author}] if author else [],
        "source": source,
        "_metadata": {
            "type": item_type,
            "feed_title": feeds.get("title", ""),
            "feed_url": feeds.get("url", ""),
        }
    }


# ============================================================================
# Twitter Transformers
# ============================================================================

def twitter_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Twitter",
    item_type: str = "tweet",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Transform Twitter-specific data.

    Extracts:
    - Retweet information
    - Hashtags
    - Mentions
    - Media detection
    - Thread detection

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Source name for display
        item_type: Type identifier
        custom_source_format: Optional custom source formatter

    Returns:
        Transformed Twitter item
    """
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)

    # Twitter-specific processing
    content_html = entries.get("content", "")
    content_text = item["content_text"]
    metadata = item["_metadata"]
    metadata["platform"] = "twitter"

    # Check if it's a retweet
    if content_html.startswith("RT @") or "RT @" in content_html[:50]:
        metadata["is_retweet"] = True
        # Extract original author
        match = re.search(r'RT @(\w+):', content_html)
        if match:
            metadata["original_author"] = match.group(1)
    else:
        metadata["is_retweet"] = False

    # Detect media
    if "<img" in content_html or "<video" in content_html:
        metadata["has_media"] = True
        metadata["image_count"] = content_html.count("<img")
    else:
        metadata["has_media"] = False

    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', content_text)
    if hashtags:
        metadata["hashtags"] = hashtags[:5]

    # Extract mentions
    mentions = re.findall(r'@(\w+)', content_text)
    if mentions:
        metadata["mentions"] = mentions[:5]

    # Detect thread
    if "1/" in item["title"] or "/🧵" in content_text or "Thread:" in content_text:
        metadata["is_thread"] = True

    return item


def twitter_simple_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Twitter",
    item_type: str = "tweet",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Simple Twitter transform (only basic retweet detection).

    Use this for better performance when you don't need detailed metadata.
    """
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)
    metadata = item["_metadata"]
    metadata["platform"] = "twitter"

    # Only detect retweets
    content = entries.get("content", "")
    metadata["is_retweet"] = content.startswith("RT @") or "RT @" in content[:50]

    return item


# ============================================================================
# Weibo Transformers
# ============================================================================

def weibo_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Weibo",
    item_type: str = "weibo",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Transform Weibo-specific data.

    Extracts:
    - Forward (转发) information
    - Topics (话题)
    - Media detection

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Source name for display
        item_type: Type identifier
        custom_source_format: Optional custom source formatter

    Returns:
        Transformed Weibo item
    """
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)

    content_html = entries.get("content", "")
    content_text = item["content_text"]
    metadata = item["_metadata"]
    metadata["platform"] = "weibo"

    # Check if it's a forward
    if "转发微博" in content_html or "//@" in content_html:
        metadata["is_forward"] = True
    else:
        metadata["is_forward"] = False

    # Extract topics
    topics = re.findall(r'#([^#]+)#', content_text)
    if topics:
        metadata["topics"] = topics[:5]

    # Detect media
    if "<img" in content_html or "<video" in content_html:
        metadata["has_media"] = True

    return item


# ============================================================================
# Reddit Transformers
# ============================================================================

def reddit_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Reddit",
    item_type: str = "post",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Transform Reddit-specific data.

    Extracts:
    - Subreddit information
    - Post type (link, text, image)
    - Code detection

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Source name for display
        item_type: Type identifier
        custom_source_format: Optional custom source formatter

    Returns:
        Transformed Reddit item
    """
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)

    content_html = entries.get("content", "")
    content_text = item["content_text"]
    url = entries.get("url", "")
    metadata = item["_metadata"]
    metadata["platform"] = "reddit"

    # Extract subreddit
    subreddit_match = re.search(r'/r/(\w+)/', url)
    if subreddit_match:
        metadata["subreddit"] = subreddit_match.group(1)

    # Determine post type
    if len(content_text) < 100 and url and not url.startswith("https://www.reddit.com"):
        metadata["post_type"] = "link"
    elif "<img" in content_html:
        metadata["post_type"] = "image"
    else:
        metadata["post_type"] = "text"

    # Check for code
    if "<code>" in content_html or "```" in content_text:
        metadata["has_code"] = True

    return item


# ============================================================================
# GitHub Transformers
# ============================================================================

def github_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "GitHub",
    item_type: str = "repository",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Transform GitHub-specific data.

    Extracts:
    - Repository information
    - Programming language
    - Trending status

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Source name for display
        item_type: Type identifier
        custom_source_format: Optional custom source formatter

    Returns:
        Transformed GitHub item
    """
    item = extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)

    content_html = entries.get("content", "")
    content_text = item["content_text"]
    url = entries.get("url", "")
    metadata = item["_metadata"]
    metadata["platform"] = "github"

    # Extract repository info
    repo_match = re.search(r'github\.com/([^/]+)/([^/\?]+)', url)
    if repo_match:
        metadata["repo_owner"] = repo_match.group(1)
        metadata["repo_name"] = repo_match.group(2)
        metadata["repo_full"] = f"{repo_match.group(1)}/{repo_match.group(2)}"

    # Try to extract language
    language_patterns = [
        r'Language:\s*(\w+)',
        r'Written in\s+(\w+)',
        r'(\w+)\s+repository'
    ]
    for pattern in language_patterns:
        lang_match = re.search(pattern, content_text, re.IGNORECASE)
        if lang_match:
            metadata["language"] = lang_match.group(1)
            break

    # Check if trending
    if "trending" in feeds.get("title", "").lower():
        metadata["is_trending"] = True

    return item


# ============================================================================
# Generic/Mixed Transformer
# ============================================================================

def auto_detect_transform(
    entries: Dict,
    feeds: Dict,
    source_name: str = "Mixed",
    item_type: str = "article",
    custom_source_format: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Auto-detect source type and apply appropriate transform.

    This is useful for mixed-source lists where you want automatic
    platform detection without creating a custom transformer.

    Args:
        entries: Entry data from API
        feeds: Feed metadata from API
        source_name: Default source name
        item_type: Default type identifier
        custom_source_format: Optional custom source formatter

    Returns:
        Transformed item with platform-specific metadata
    """
    feed_url = feeds.get("url", "").lower()
    feed_title = feeds.get("title", "").lower()

    # Detect platform and use appropriate transformer
    if "twitter" in feed_url or "twitter" in feed_title:
        return twitter_transform(entries, feeds, source_name, item_type, custom_source_format)
    elif "weibo" in feed_url or "微博" in feed_title:
        return weibo_transform(entries, feeds, source_name, item_type, custom_source_format)
    elif "reddit" in feed_url or "reddit" in feed_title:
        return reddit_transform(entries, feeds, source_name, item_type, custom_source_format)
    elif "github" in feed_url or "github" in feed_title:
        return github_transform(entries, feeds, source_name, item_type, custom_source_format)
    else:
        # Default: just extract common fields
        return extract_common_fields(entries, feeds, source_name, item_type, custom_source_format)


# ============================================================================
# Transformer Registry (for easy discovery)
# ============================================================================

TRANSFORMERS = {
    "twitter": twitter_transform,
    "twitter_simple": twitter_simple_transform,
    "weibo": weibo_transform,
    "reddit": reddit_transform,
    "github": github_transform,
    "auto": auto_detect_transform,
    "default": extract_common_fields,
}


def get_transformer(name: str) -> callable:
    """
    Get a transformer function by name.

    Args:
        name: Transformer name (twitter, weibo, reddit, github, auto, default)

    Returns:
        Transformer function

    Raises:
        KeyError: If transformer name not found
    """
    return TRANSFORMERS[name]


def list_transformers() -> list:
    """List all available transformer names."""
    return list(TRANSFORMERS.keys())
