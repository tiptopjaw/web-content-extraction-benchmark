"""
BeautifulSoup-based custom extractor
"""
from typing import Dict, Optional
from .base_extractor import BaseExtractor
from bs4 import BeautifulSoup
import re

class BeautifulSoupExtractor(BaseExtractor):
    """Simple BeautifulSoup-based extractor with heuristics"""

    @property
    def name(self) -> str:
        return "BeautifulSoup-Custom"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using BeautifulSoup with simple heuristics"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                        'aside', 'iframe', 'noscript']):
            tag.decompose()

        # Extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Try to find article element or main content
        main_content = ''

        # Look for article tag
        article = soup.find('article')
        if article:
            main_content = self._extract_text(article)
        else:
            # Look for main tag
            main = soup.find('main')
            if main:
                main_content = self._extract_text(main)
            else:
                # Fall back to finding largest text block
                # Find all divs and pick the one with most text
                divs = soup.find_all(['div', 'section'])
                if divs:
                    largest_div = max(divs, key=lambda d: len(d.get_text(strip=True)))
                    main_content = self._extract_text(largest_div)
                else:
                    # Last resort: get all body text
                    body = soup.find('body')
                    if body:
                        main_content = self._extract_text(body)

        # Extract author from meta tags
        author = None
        author_meta = soup.find('meta', {'name': re.compile(r'author', re.I)})
        if author_meta:
            author = author_meta.get('content')

        # Extract publish date from meta tags
        publish_date = None
        date_meta = soup.find('meta', {'property': re.compile(r'published.*time', re.I)}) or \
                    soup.find('meta', {'name': re.compile(r'date|published', re.I)})
        if date_meta:
            publish_date = date_meta.get('content')

        return {
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'main_content': main_content
        }

    def _extract_text(self, element) -> str:
        """Extract clean text from element"""
        # Get text with line breaks preserved
        texts = []
        for p in element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = p.get_text(strip=True)
            if text:
                texts.append(text)

        if texts:
            return '\n\n'.join(texts)

        # Fallback to all text
        return element.get_text(separator='\n', strip=True)
