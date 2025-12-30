"""
Content extractor wrappers for benchmarking
"""
from .trafilatura_extractor import TrafilaturaExtractor
from .readability_extractor import ReadabilityExtractor
from .boilerpy3_extractor import Boilerpy3Extractor
from .beautifulsoup_extractor import BeautifulSoupExtractor

__all__ = [
    'TrafilaturaExtractor',
    'ReadabilityExtractor',
    'Boilerpy3Extractor',
    'BeautifulSoupExtractor',
]
