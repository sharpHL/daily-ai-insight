"""News Aggregator collector."""

from .follow_base import FollowBaseCollector


class NewsAggregatorCollector(FollowBaseCollector):
    """Collector for aggregated news from various sources."""

    def __init__(self):
        """Initialize News Aggregator collector."""
        super().__init__(
            name="News Aggregator",
            list_id_env="NEWS_AGGREGATOR_LIST_ID",
            home_url="https://example.com/news"
        )
