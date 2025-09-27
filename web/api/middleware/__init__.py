"""
SPIDER Framework - API Middleware

This module contains middleware components for the API including authentication, 
rate limiting, logging, and error handling.
"""

from .auth_middleware import AuthMiddleware
from .rate_limit_middleware import RateLimitMiddleware
from .logging_middleware import LoggingMiddleware
from .error_middleware import ErrorMiddleware
from .cors_middleware import CORSMiddleware
from .security_middleware import SecurityMiddleware

__all__ = [
    'AuthMiddleware',
    'RateLimitMiddleware',
    'LoggingMiddleware',
    'ErrorMiddleware',
    'CORSMiddleware',
    'SecurityMiddleware'
]

__version__ = '2.0.0'
__author__ = 'SPIDER Framework Team'
__email__ = 'team@example.com'
