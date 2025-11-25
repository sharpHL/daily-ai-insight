"""Collector factory functions.

This module provides convenient factory functions for creating collectors
without the need for subclasses. Use these functions for a more functional
approach to collector creation.

Example:
    from daily_ai_insight.collectors.factory import create_twitter_collector

    collector = create_twitter_collector()
    data = await collector.fetch()
"""

from typing import Optional, Callable
from .base import FollowCollector
from .transformers import (
    twitter_transform,
    weibo_transform,
    reddit_transform,
    github_transform,
    auto_detect_transform,
)


# ============================================================================
# Convenience Factory Functions
# ============================================================================

def create_twitter_collector() -> FollowCollector:
    """
    Create a Twitter collector with optimized settings.

    Returns:
        Configured FollowCollector for Twitter data

    Example:
        collector = create_twitter_collector()
        data = await collector.fetch()
    """
    def format_twitter_source(author, feeds):
        """Format Twitter source field."""
        feed_title = feeds.get("title", "Twitter")
        if feed_title.startswith("Twitter"):
            return f"twitter-{author}" if author else "twitter"
        return f"{feed_title} - {author}" if author else feed_title

    return FollowCollector(
        name="twitter",
        list_id_env="TWITTER_LIST_ID",
        source_name="Twitter/X",
        home_url="https://twitter.com",
        item_type="tweet",
        custom_source_format=format_twitter_source,
        transform_callback=twitter_transform
    )


def create_reddit_collector() -> FollowCollector:
    """
    Create a Reddit collector.

    Returns:
        Configured FollowCollector for Reddit data
    """
    return FollowCollector(
        name="reddit",
        list_id_env="REDDIT_LIST_ID",
        source_name="Reddit",
        home_url="https://www.reddit.com",
        item_type="post",
        transform_callback=reddit_transform
    )


def create_papers_collector() -> FollowCollector:
    """
    Create an academic papers collector.

    Returns:
        Configured FollowCollector for academic papers
    """
    return FollowCollector(
        name="papers",
        list_id_env="PAPERS_LIST_ID",
        source_name="Academic Papers",
        home_url="https://arxiv.org",
        item_type="paper"
    )


def create_mixed_collector(
    list_id_env: str = "MIXED_LIST_ID",
    name: str = "mixed"
) -> FollowCollector:
    """
    Create a mixed-source collector with automatic platform detection.

    This collector automatically detects the platform (Twitter, Weibo, Reddit, etc.)
    for each item and applies the appropriate transformation.

    Args:
        list_id_env: Environment variable name for the List ID
        name: Collector name

    Returns:
        Configured FollowCollector with auto-detection

    Example:
        # Create collector for a list containing Twitter + Weibo + Reddit
        collector = create_mixed_collector(list_id_env="AI_NEWS_LIST_ID")
        data = await collector.fetch()

        # Results automatically include platform-specific metadata
        for item in data["items"]:
            platform = item["_metadata"].get("platform")
            if platform == "twitter":
                print(f"Twitter: {item['_metadata'].get('hashtags')}")
    """
    return FollowCollector(
        name=name,
        list_id_env=list_id_env,
        source_name="Mixed Sources",
        home_url="https://follow.is",
        transform_callback=auto_detect_transform
    )


# ============================================================================
# Generic Factory Function
# ============================================================================

def create_collector(
    name: str,
    list_id_env: Optional[str] = None,
    feed_id_env: Optional[str] = None,
    source_name: Optional[str] = None,
    home_url: str = "https://follow.is",
    item_type: str = "article",
    transform_callback: Optional[Callable] = None,
    custom_source_format: Optional[Callable] = None
) -> FollowCollector:
    """
    Generic factory function for creating any collector.

    This is the most flexible option, allowing full customization.

    Args:
        name: Collector name
        list_id_env: Environment variable name for List ID
        feed_id_env: Environment variable name for Feed ID
        source_name: Display name for the source
        home_url: Home page URL
        item_type: Type identifier (article, tweet, post, etc.)
        transform_callback: Optional transform function
        custom_source_format: Optional source formatter

    Returns:
        Configured FollowCollector

    Example:
        # Create a custom collector
        collector = create_collector(
            name="my_custom",
            list_id_env="MY_LIST_ID",
            source_name="My Custom Source",
            transform_callback=my_custom_transform
        )
    """
    return FollowCollector(
        name=name,
        list_id_env=list_id_env,
        feed_id_env=feed_id_env,
        source_name=source_name,
        home_url=home_url,
        item_type=item_type,
        transform_callback=transform_callback,
        custom_source_format=custom_source_format
    )


# ============================================================================
# Preset Configurations
# ============================================================================

PRESET_CONFIGS = {
    "twitter": {
        "name": "twitter",
        "list_id_env": "TWITTER_LIST_ID",
        "source_name": "Twitter/X",
        "home_url": "https://twitter.com",
        "item_type": "tweet",
        "transform_callback": twitter_transform,
    },
    "reddit": {
        "name": "reddit",
        "list_id_env": "REDDIT_LIST_ID",
        "source_name": "Reddit",
        "home_url": "https://www.reddit.com",
        "item_type": "post",
        "transform_callback": reddit_transform,
    },
    "papers": {
        "name": "papers",
        "list_id_env": "PAPERS_LIST_ID",
        "source_name": "Academic Papers",
        "home_url": "https://arxiv.org",
        "item_type": "paper",
    },
    "mixed": {
        "name": "mixed",
        "list_id_env": "MIXED_LIST_ID",
        "source_name": "Mixed Sources",
        "home_url": "https://follow.is",
        "transform_callback": auto_detect_transform,
    },
    "aibase": {
        "name": "aibase",
        "feed_id_env": "AIBASE_FEED_ID",
        "source_name": "AI Base",
        "home_url": "https://www.aibase.com",
        "item_type": "news",
    },
    "jiqizhixin": {
        "name": "jiqizhixin",
        "feed_id_env": "JIQIZHIXIN_FEED_ID",
        "source_name": "机器之心",
        "home_url": "https://www.jiqizhixin.com",
        "item_type": "news",
    },
    "qbit": {
        "name": "qbit",
        "feed_id_env": "QBIT_FEED_ID",
        "source_name": "量子位",
        "home_url": "https://www.qbitai.com",
        "item_type": "news",
    },
    "xinzhiyuan": {
        "name": "xinzhiyuan",
        "feed_id_env": "XINZHIYUAN_FEED_ID",
        "source_name": "新智元",
        "home_url": "https://www.xinzhiyuan.com",
        "item_type": "news",
    },
    "xiaohu": {
        "name": "xiaohu",
        "feed_id_env": "XIAOHU_FEED_ID",
        "source_name": "Xiaohu.AI",
        "home_url": "https://www.xiaohu.ai",
        "item_type": "article",
    },
    "news_aggregator": {
        "name": "news_aggregator",
        "list_id_env": "NEWS_AGGREGATOR_LIST_ID",
        "source_name": "News Aggregator",
        "home_url": "https://follow.is",
        "item_type": "news",
    },
}


def create_from_preset(preset: str, **overrides) -> FollowCollector:
    """
    Create a collector from a preset configuration.

    Args:
        preset: Preset name (twitter, reddit, papers, mixed)
        **overrides: Override any preset configuration

    Returns:
        Configured FollowCollector

    Raises:
        KeyError: If preset name is not found

    Example:
        # Use preset with custom List ID
        collector = create_from_preset(
            "twitter",
            list_id_env="MY_CUSTOM_TWITTER_LIST"
        )
    """
    if preset not in PRESET_CONFIGS:
        available = ", ".join(PRESET_CONFIGS.keys())
        raise KeyError(f"Unknown preset '{preset}'. Available: {available}")

    config = {**PRESET_CONFIGS[preset], **overrides}
    return create_collector(**config)
