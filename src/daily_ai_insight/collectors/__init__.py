"""Data collectors for various sources."""

from .base import BaseCollector, FollowCollector
from .github_trending import GitHubTrendingCollector

# Factory functions (recommended approach)
from . import factory
from .factory import (
    create_twitter_collector,
    create_reddit_collector,
    create_papers_collector,
    create_mixed_collector,
    create_collector,
    create_from_preset,
)

__all__ = [
    # Base classes
    "BaseCollector",
    "FollowCollector",
    # Specialized collectors
    "GitHubTrendingCollector",
    # Factory module and functions (recommended)
    "factory",
    "create_twitter_collector",
    "create_reddit_collector",
    "create_papers_collector",
    "create_mixed_collector",
    "create_collector",
    "create_from_preset",
]