"""
magic-html extractor wrapper (https://github.com/opendatalab/magic-html)
"""
from typing import Dict, Optional
from .base_extractor import BaseExtractor

try:
    from magic_html import GeneralExtractor
    from bs4 import BeautifulSoup
    MAGIC_HTML_AVAILABLE = True
except ImportError:
    MAGIC_HTML_AVAILABLE = False


class MagicHtmlExtractor(BaseExtractor):
    """Wrapper for magic-html content extractor"""

    def __init__(self):
        if MAGIC_HTML_AVAILABLE:
            self._extractor = GeneralExtractor()

    @property
    def name(self) -> str:
        return "magic-html"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        if not MAGIC_HTML_AVAILABLE:
            raise ImportError(
                "magic-html is not installed. Install from: "
                "https://github.com/opendatalab/magic-html/releases"
            )

        result = self._extractor.extract(html, base_url=url)

        extracted_html = result.get('html', '')
        title = result.get('title', None)

        # Convert extracted HTML to plain text
        if extracted_html:
            soup = BeautifulSoup(extracted_html, 'html.parser')
            main_content = soup.get_text(separator='\n', strip=True)
        else:
            main_content = ''

        return {
            'title': title or None,
            'author': None,
            'publish_date': None,
            'main_content': main_content,
        }
