"""Data collectors for various sources."""

from .base import BaseCollector
from .follow_base import FollowBaseCollector
from .huggingface_papers import HuggingFacePapersCollector
from .reddit import RedditCollector
from .xiaohu import XiaohuCollector
from .news_aggregator import NewsAggregatorCollector

__all__ = [
    "BaseCollector",
    "FollowBaseCollector",
    "HuggingFacePapersCollector",
    "RedditCollector",
    "XiaohuCollector",
    "NewsAggregatorCollector",
]
