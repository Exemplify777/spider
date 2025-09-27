"""
SPIDER Framework - Error Utilities

Utility functions for error handling and management.
"""

import traceback
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class SPIDERError(Exception):
    """Base exception class for SPIDER framework."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SPIDER_ERROR"
        self.details = details or {}

class ValidationError(SPIDERError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})

class AuthenticationError(SPIDERError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(SPIDERError):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")

class ScrapingError(SPIDERError):
    """Exception raised for scraping errors."""
    
    def __init__(self, message: str, url: str = None, selector: str = None):
        super().__init__(message, "SCRAPING_ERROR", {"url": url, "selector": selector})

class ConfigurationError(SPIDERError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})

class DatabaseError(SPIDERError):
    """Exception raised for database errors."""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation, "table": table})

class NetworkError(SPIDERError):
    """Exception raised for network errors."""
    
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message, "NETWORK_ERROR", {"url": url, "status_code": status_code})

class RateLimitError(SPIDERError):
    """Exception raised for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_ERROR", {"retry_after": retry_after})

class AIError(SPIDERError):
    """Exception raised for AI-related errors."""
    
    def __init__(self, message: str, model: str = None, operation: str = None):
        super().__init__(message, "AI_ERROR", {"model": model, "operation": operation})

def handle_exception(exc: Exception, context: str = None) -> Dict[str, Any]:
    """
    Handle exception and return error information.
    
    Args:
        exc: Exception to handle
        context: Additional context information
    
    Returns:
        Error information dictionary
    """
    try:
        error_info = {
            'error_type': type(exc).__name__,
            'error_message': str(exc),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        if isinstance(exc, SPIDERError):
            error_info.update({
                'error_code': exc.error_code,
                'details': exc.details
            })
        
        logger.error(f"Exception in {context}: {str(exc)}", exc_info=True)
        return error_info
    
    except Exception as e:
        logger.error(f"Error handling exception: {str(e)}")
        return {
            'error_type': 'UnknownError',
            'error_message': 'An unknown error occurred',
            'context': context,
            'traceback': traceback.format_exc()
        }

def create_error_response(error_info: Dict[str, Any], status_code: int = 500) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        error_info: Error information dictionary
        status_code: HTTP status code
    
    Returns:
        Error response dictionary
    """
    try:
        return {
            'success': False,
            'error': {
                'code': error_info.get('error_code', 'UNKNOWN_ERROR'),
                'message': error_info.get('error_message', 'An unknown error occurred'),
                'type': error_info.get('error_type', 'UnknownError'),
                'details': error_info.get('details', {}),
                'context': error_info.get('context'),
                'timestamp': error_info.get('timestamp')
            },
            'status_code': status_code
        }
    
    except Exception as e:
        logger.error(f"Error creating error response: {str(e)}")
        return {
            'success': False,
            'error': {
                'code': 'ERROR_RESPONSE_ERROR',
                'message': 'Failed to create error response',
                'type': 'ErrorResponseError',
                'details': {},
                'context': None,
                'timestamp': None
            },
            'status_code': 500
        }

def log_error(error_info: Dict[str, Any], level: str = 'ERROR') -> None:
    """
    Log error information.
    
    Args:
        error_info: Error information dictionary
        level: Log level
    """
    try:
        log_level = getattr(logging, level.upper(), logging.ERROR)
        
        if 'traceback' in error_info:
            logger.log(log_level, f"Error: {error_info['error_message']}", exc_info=True)
        else:
            logger.log(log_level, f"Error: {error_info['error_message']}")
    
    except Exception as e:
        logger.error(f"Error logging error: {str(e)}")

def format_error_message(error_info: Dict[str, Any]) -> str:
    """
    Format error message for display.
    
    Args:
        error_info: Error information dictionary
    
    Returns:
        Formatted error message
    """
    try:
        message = error_info.get('error_message', 'An unknown error occurred')
        
        if 'context' in error_info and error_info['context']:
            message = f"{message} (Context: {error_info['context']})"
        
        if 'details' in error_info and error_info['details']:
            details = ', '.join([f"{k}: {v}" for k, v in error_info['details'].items()])
            message = f"{message} (Details: {details})"
        
        return message
    
    except Exception as e:
        logger.error(f"Error formatting error message: {str(e)}")
        return "An error occurred while formatting the error message"

def get_error_code(error_info: Dict[str, Any]) -> str:
    """
    Get error code from error information.
    
    Args:
        error_info: Error information dictionary
    
    Returns:
        Error code
    """
    try:
        return error_info.get('error_code', 'UNKNOWN_ERROR')
    
    except Exception as e:
        logger.error(f"Error getting error code: {str(e)}")
        return 'UNKNOWN_ERROR'

def is_retryable_error(error_info: Dict[str, Any]) -> bool:
    """
    Check if error is retryable.
    
    Args:
        error_info: Error information dictionary
    
    Returns:
        True if retryable, False otherwise
    """
    try:
        error_code = error_info.get('error_code', '')
        error_type = error_info.get('error_type', '')
        
        retryable_codes = [
            'NETWORK_ERROR',
            'RATE_LIMIT_ERROR',
            'DATABASE_ERROR'
        ]
        
        retryable_types = [
            'NetworkError',
            'RateLimitError',
            'DatabaseError'
        ]
        
        return error_code in retryable_codes or error_type in retryable_types
    
    except Exception as e:
        logger.error(f"Error checking if error is retryable: {str(e)}")
        return False

def get_retry_delay(error_info: Dict[str, Any], base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Get retry delay for error.
    
    Args:
        error_info: Error information dictionary
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Retry delay in seconds
    """
    try:
        error_code = error_info.get('error_code', '')
        details = error_info.get('details', {})
        
        if error_code == 'RATE_LIMIT_ERROR':
            retry_after = details.get('retry_after')
            if retry_after:
                return min(float(retry_after), max_delay)
        
        if error_code == 'NETWORK_ERROR':
            return min(base_delay * 2, max_delay)
        
        return base_delay
    
    except Exception as e:
        logger.error(f"Error getting retry delay: {str(e)}")
        return base_delay

def should_log_error(error_info: Dict[str, Any]) -> bool:
    """
    Check if error should be logged.
    
    Args:
        error_info: Error information dictionary
    
    Returns:
        True if should log, False otherwise
    """
    try:
        error_code = error_info.get('error_code', '')
        error_type = error_info.get('error_type', '')
        
        # Don't log certain types of errors
        no_log_codes = [
            'VALIDATION_ERROR',
            'AUTHENTICATION_ERROR',
            'AUTHORIZATION_ERROR'
        ]
        
        no_log_types = [
            'ValidationError',
            'AuthenticationError',
            'AuthorizationError'
        ]
        
        return error_code not in no_log_codes and error_type not in no_log_types
    
    except Exception as e:
        logger.error(f"Error checking if should log error: {str(e)}")
        return True

def create_error_summary(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create error summary from list of errors.
    
    Args:
        errors: List of error information dictionaries
    
    Returns:
        Error summary dictionary
    """
    try:
        if not errors:
            return {
                'total_errors': 0,
                'error_types': {},
                'error_codes': {},
                'most_common_error': None
            }
        
        error_types = {}
        error_codes = {}
        
        for error in errors:
            error_type = error.get('error_type', 'Unknown')
            error_code = error.get('error_code', 'UNKNOWN_ERROR')
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            error_codes[error_code] = error_codes.get(error_code, 0) + 1
        
        most_common_error = max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        
        return {
            'total_errors': len(errors),
            'error_types': error_types,
            'error_codes': error_codes,
            'most_common_error': most_common_error
        }
    
    except Exception as e:
        logger.error(f"Error creating error summary: {str(e)}")
        return {
            'total_errors': 0,
            'error_types': {},
            'error_codes': {},
            'most_common_error': None
        }
