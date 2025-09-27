"""
SPIDER Plugin System

This module provides a comprehensive plugin system for extending SPIDER functionality.
Plugins can add custom extractors, processors, engines, and monitoring capabilities.
"""

from .base import (
    Plugin,
    PluginManager,
    PluginRegistry,
    PluginError,
    PluginValidationError,
    PluginLoadError,
    PluginExecutionError,
)
from .extractor import ExtractorPlugin
from .processor import ProcessorPlugin
from .engine import EnginePlugin
from .monitor import MonitorPlugin
from .middleware import MiddlewarePlugin
from .validator import ValidatorPlugin
from .storage import StoragePlugin
from .auth import AuthPlugin
from .rate_limiter import RateLimiterPlugin
from .proxy import ProxyPlugin
from .captcha import CaptchaPlugin
from .behavior import BehaviorPlugin
from .fingerprint import FingerprintPlugin
from .cache import CachePlugin
from .notification import NotificationPlugin
from .reporting import ReportingPlugin
from .compliance import CompliancePlugin
from .security import SecurityPlugin
from .analytics import AnalyticsPlugin
from .ai import AIPlugin

__all__ = [
    # Base plugin system
    "Plugin",
    "PluginManager", 
    "PluginRegistry",
    "PluginError",
    "PluginValidationError",
    "PluginLoadError",
    "PluginExecutionError",
    
    # Plugin types
    "ExtractorPlugin",
    "ProcessorPlugin", 
    "EnginePlugin",
    "MonitorPlugin",
    "MiddlewarePlugin",
    "ValidatorPlugin",
    "StoragePlugin",
    "AuthPlugin",
    "RateLimiterPlugin",
    "ProxyPlugin",
    "CaptchaPlugin",
    "BehaviorPlugin",
    "FingerprintPlugin",
    "CachePlugin",
    "NotificationPlugin",
    "ReportingPlugin",
    "CompliancePlugin",
    "SecurityPlugin",
    "AnalyticsPlugin",
    "AIPlugin",
]
