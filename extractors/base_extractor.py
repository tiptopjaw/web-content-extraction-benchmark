"""
Base class for content extractors
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseExtractor(ABC):
    """Base class that all extractors must implement"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the extractor"""
        pass

    @abstractmethod
    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """
        Extract content from HTML

        Args:
            html: Raw HTML content
            url: Original URL (some extractors use this)

        Returns:
            Dictionary with keys:
                - title: Extracted title
                - author: Extracted author (if available)
                - publish_date: Extracted date (if available)
                - main_content: Extracted main content text
        """
        pass

    def extract_safe(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """
        Safe wrapper that catches exceptions and returns empty result
        """
        try:
            return self.extract(html, url)
        except Exception as e:
            return {
                'title': None,
                'author': None,
                'publish_date': None,
                'main_content': '',
                'error': str(e)
            }
