"""Reddit collector."""

from .follow_base import FollowBaseCollector


class RedditCollector(FollowBaseCollector):
    """Collector for Reddit posts."""

    def __init__(self):
        """Initialize Reddit collector."""
        super().__init__(
            name="Reddit",
            list_id_env="REDDIT_LIST_ID",
            home_url="https://www.reddit.com"
        )
