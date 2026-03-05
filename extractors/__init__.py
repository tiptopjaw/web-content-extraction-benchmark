"""
Content extractor wrappers for benchmarking
"""
from .trafilatura_extractor import TrafilaturaExtractor
from .readability_extractor import ReadabilityExtractor
from .boilerpy3_extractor import Boilerpy3Extractor
from .beautifulsoup_extractor import BeautifulSoupExtractor
from .rs_trafilatura_extractor import RsTrafilaturaExtractor
from .dom_content_extraction_extractor import DomContentExtractionExtractor
from .dom_smoothie_extractor import DomSmoothieExtractor
from .nanohtml2text_extractor import Nanohtml2textExtractor
from .fast_html2md_extractor import FastHtml2mdExtractor
from .magic_html_extractor import MagicHtmlExtractor
from .mineru_html_extractor import MineruHtmlExtractor
from .readerlm_extractor import ReaderLmExtractor

__all__ = [
    'TrafilaturaExtractor',
    'ReadabilityExtractor',
    'Boilerpy3Extractor',
    'BeautifulSoupExtractor',
    'RsTrafilaturaExtractor',
    'DomContentExtractionExtractor',
    'DomSmoothieExtractor',
    'Nanohtml2textExtractor',
    'FastHtml2mdExtractor',
    'MagicHtmlExtractor',
    'MineruHtmlExtractor',
    'ReaderLmExtractor',
]
