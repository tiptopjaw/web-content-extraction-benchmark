"""
Boilerpy3 extractor wrapper
"""
from typing import Dict, Optional
from .base_extractor import BaseExtractor

try:
    from boilerpy3 import extractors
    BOILERPY3_AVAILABLE = True
except ImportError:
    BOILERPY3_AVAILABLE = False

class Boilerpy3Extractor(BaseExtractor):
    """Wrapper for Boilerpy3 content extractor"""

    def __init__(self, extractor_type='ArticleExtractor'):
        """
        Initialize Boilerpy3 extractor

        Args:
            extractor_type: One of 'ArticleExtractor', 'DefaultExtractor',
                           'LargestContentExtractor', 'KeepEverythingExtractor'
        """
        self.extractor_type = extractor_type
        if BOILERPY3_AVAILABLE:
            extractor_class = getattr(extractors, extractor_type)
            self.extractor = extractor_class()

    @property
    def name(self) -> str:
        return f"Boilerpy3-{self.extractor_type}"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using Boilerpy3"""
        if not BOILERPY3_AVAILABLE:
            raise ImportError("Boilerpy3 is not installed. Install with: pip install boilerpy3")

        # Boilerpy3 only extracts text, no metadata
        try:
            main_content = self.extractor.get_content(html)
        except Exception:
            main_content = ''

        return {
            'title': None,
            'author': None,
            'publish_date': None,
            'main_content': main_content or ''
        }
