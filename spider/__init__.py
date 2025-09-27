"""
SPIDER - Scalable Python Integrated Data Extraction & Retrieval

A comprehensive web scraping framework designed for scalable data extraction
across various web sources with support for static content, dynamic JavaScript,
and complex anti-bot protections.
"""

__version__ = "1.0.0"
__author__ = "SPIDER Team"
__email__ = "team@spider.dev"

from .core.engine import EngineFactory
from .core.config import Config
from .core.logger import get_logger

__all__ = [
    "EngineFactory",
    "Config", 
    "get_logger",
]
