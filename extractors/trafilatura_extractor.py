"""
Trafilatura extractor wrapper
"""
from typing import Dict, Optional
from .base_extractor import BaseExtractor

try:
    import trafilatura
    from trafilatura import extract
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

class TrafilaturaExtractor(BaseExtractor):
    """Wrapper for Trafilatura content extractor"""

    @property
    def name(self) -> str:
        return "Trafilatura"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using Trafilatura"""
        if not TRAFILATURA_AVAILABLE:
            raise ImportError("Trafilatura is not installed. Install with: pip install trafilatura")

        # Extract with metadata - returns a dict-like Document object
        result = trafilatura.bare_extraction(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            include_images=False,
            include_links=False,
            output_format='python',
            with_metadata=True
        )

        if result is None:
            return {
                'title': None,
                'author': None,
                'publish_date': None,
                'main_content': ''
            }

        # Access Document attributes directly
        return {
            'title': getattr(result, 'title', None),
            'author': getattr(result, 'author', None),
            'publish_date': getattr(result, 'date', None),
            'main_content': getattr(result, 'text', '') or getattr(result, 'raw_text', '') or ''
        }
