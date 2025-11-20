"""HuggingFace Papers collector."""

from .follow_base import FollowBaseCollector


class HuggingFacePapersCollector(FollowBaseCollector):
    """Collector for HuggingFace Daily Papers."""

    def __init__(self):
        """Initialize HuggingFace Papers collector."""
        super().__init__(
            name="HuggingFace Papers",
            feed_id_env="HGPAPERS_FEED_ID",
            home_url="https://huggingface.co/papers",
            read_more_text="在 ArXiv/来源 阅读"
        )
