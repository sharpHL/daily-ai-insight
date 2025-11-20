"""Data collectors for various sources."""

from .base import BaseCollector
from .follow_base import FollowBaseCollector
from .folo_base import FOLOBaseCollector
from .huggingface_papers import HuggingFacePapersCollector
from .reddit import RedditCollector
from .xiaohu import XiaohuCollector
from .news_aggregator import NewsAggregatorCollector

# New collectors
from .github_trending import GitHubTrendingCollector
from .papers import PapersCollector
from .twitter import TwitterCollector
from .aibase import AIBaseCollector
from .jiqizhixin import JiqizhixinCollector
from .qbit import QBitCollector
from .xinzhiyuan import XinZhiYuanCollector

__all__ = [
    "BaseCollector",
    "FollowBaseCollector",
    "FOLOBaseCollector",
    "HuggingFacePapersCollector",
    "RedditCollector",
    "XiaohuCollector",
    "NewsAggregatorCollector",
    # New collectors
    "GitHubTrendingCollector",
    "PapersCollector",
    "TwitterCollector",
    "AIBaseCollector",
    "JiqizhixinCollector",
    "QBitCollector",
    "XinZhiYuanCollector",
]
