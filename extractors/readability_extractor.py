"""
Readability extractor wrapper (using readabilipy)
"""
from typing import Dict, Optional
from .base_extractor import BaseExtractor

try:
    from readabilipy import simple_json_from_html_string
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

class ReadabilityExtractor(BaseExtractor):
    """Wrapper for Readability content extractor"""

    @property
    def name(self) -> str:
        return "Readability"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using Readability"""
        if not READABILITY_AVAILABLE:
            raise ImportError("Readabilipy is not installed. Install with: pip install readabilipy")

        # Extract article
        result = simple_json_from_html_string(html, use_readability=True)

        if result is None or not result.get('plain_content'):
            return {
                'title': None,
                'author': None,
                'publish_date': None,
                'main_content': ''
            }

        # Get plain text content
        plain_content = result.get('plain_content', [])
        if isinstance(plain_content, list):
            main_content = '\n\n'.join(
                item.get('text', '') for item in plain_content
                if item.get('text')
            )
        else:
            main_content = plain_content

        return {
            'title': result.get('title'),
            'author': result.get('byline'),
            'publish_date': result.get('date'),
            'main_content': main_content
        }
