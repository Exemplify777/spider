"""Core modules for SPIDER framework."""

from .config import Config
from .engine import EngineFactory, BaseEngine, ScrapingRequest, ScrapingResponse, EngineType
from .logger import get_logger, setup_logging
from .exceptions import SpiderError, ConfigurationError, ScrapingError, EngineError, ProxyError, CAPTCHAError, ValidationError, StorageError, MonitoringError

__all__ = [
    "Config",
    "EngineFactory", 
    "BaseEngine",
    "ScrapingRequest",
    "ScrapingResponse",
    "EngineType",
    "get_logger",
    "setup_logging",
    "SpiderError",
    "ConfigurationError", 
    "ScrapingError",
    "EngineError",
    "ProxyError",
    "CAPTCHAError",
    "ValidationError",
    "StorageError",
    "MonitoringError",
]
