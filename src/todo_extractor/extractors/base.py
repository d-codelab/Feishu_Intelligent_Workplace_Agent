"""Base extractor class for all data sources."""

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    """Abstract base class for todo extractors.

    All data source extractors (doc, IM, etc.) should inherit from this class
    and implement the extract() method.
    """

    @abstractmethod
    def extract(self, **kwargs) -> list[dict[str, Any]]:
        """Extract todo items from the data source.

        Args:
            **kwargs: Extractor-specific parameters (e.g., doc_token, chat_id)

        Returns:
            List of standardized todo dictionaries with fields:
                - title: str
                - description: str
                - owner_open_id: str (optional)
                - deadline: str (YYYY-MM-DD format, optional)
                - priority: str (P0/P1/P2, optional)
                - status: str (待处理/进行中/已完成/阻塞, optional)
                - source_type: str
                - source_link: str
                - evidence: str (optional)
        """
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the data source type (e.g., '飞书文档', '群消息')."""
        pass
