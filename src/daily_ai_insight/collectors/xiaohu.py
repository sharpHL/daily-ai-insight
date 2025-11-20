"""Xiaohu.AI collector."""

from .follow_base import FollowBaseCollector


class XiaohuCollector(FollowBaseCollector):
    """Collector for Xiaohu.AI Daily feeds."""

    def __init__(self):
        """Initialize Xiaohu collector."""
        super().__init__(
            name="Xiaohu.AI",
            feed_id_env="XIAOHU_FEED_ID",
            home_url="https://www.xiaohu.ai"
        )
