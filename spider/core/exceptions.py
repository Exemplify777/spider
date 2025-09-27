"""Custom exceptions for SPIDER framework."""


class SpiderError(Exception):
    """Base exception for all SPIDER-related errors."""
    pass


class ConfigurationError(SpiderError):
    """Raised when there's a configuration error."""
    pass


class ScrapingError(SpiderError):
    """Raised when scraping fails."""
    pass


class EngineError(SpiderError):
    """Raised when engine operations fail."""
    pass


class ProxyError(SpiderError):
    """Raised when proxy operations fail."""
    pass


class CAPTCHAError(SpiderError):
    """Raised when CAPTCHA solving fails."""
    pass


class ValidationError(SpiderError):
    """Raised when data validation fails."""
    pass


class StorageError(SpiderError):
    """Raised when storage operations fail."""
    pass


class ProcessingError(SpiderError):
    """Raised when data processing fails."""
    pass


class SecurityError(SpiderError):
    """Raised when security operations fail."""
    pass


class ComplianceError(SpiderError):
    """Raised when compliance operations fail."""
    pass


class MonitoringError(SpiderError):
    """Raised when monitoring operations fail."""
    pass
