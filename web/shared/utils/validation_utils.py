"""
SPIDER Framework - Validation Utilities

Utility functions for data validation.
"""

import re
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    except Exception as e:
        logger.error(f"Error validating email {email}: {str(e)}")
        return False

def validate_password(password: str, min_length: int = 8, require_special: bool = True) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        require_special: Whether to require special characters
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        if len(password) < min_length:
            result['valid'] = False
            result['errors'].append(f"Password must be at least {min_length} characters long")
        
        if not re.search(r'[A-Z]', password):
            result['valid'] = False
            result['errors'].append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            result['valid'] = False
            result['errors'].append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            result['valid'] = False
            result['errors'].append("Password must contain at least one number")
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['valid'] = False
            result['errors'].append("Password must contain at least one special character")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating password: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))
    
    except Exception as e:
        logger.error(f"Error validating URL {url}: {str(e)}")
        return False

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits) <= 15
    
    except Exception as e:
        logger.error(f"Error validating phone {phone}: {str(e)}")
        return False

def validate_username(username: str, min_length: int = 3, max_length: int = 20) -> Dict[str, Any]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        min_length: Minimum username length
        max_length: Maximum username length
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        if len(username) < min_length:
            result['valid'] = False
            result['errors'].append(f"Username must be at least {min_length} characters long")
        
        if len(username) > max_length:
            result['valid'] = False
            result['errors'].append(f"Username must be no more than {max_length} characters long")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            result['valid'] = False
            result['errors'].append("Username can only contain letters, numbers, underscores, and hyphens")
        
        if not re.match(r'^[a-zA-Z]', username):
            result['valid'] = False
            result['errors'].append("Username must start with a letter")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating username {username}: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_json(data: str) -> Dict[str, Any]:
    """
    Validate JSON string.
    
    Args:
        data: JSON string to validate
    
    Returns:
        Validation result dictionary
    """
    try:
        import json
        json.loads(data)
        return {
            'valid': True,
            'errors': []
        }
    
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'errors': [f"Invalid JSON: {str(e)}"]
        }
    except Exception as e:
        logger.error(f"Error validating JSON: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                result['valid'] = False
                result['errors'].append(f"Required field '{field}' is missing or empty")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating required fields: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_data_types(data: Dict[str, Any], field_types: Dict[str, type]) -> Dict[str, Any]:
    """
    Validate data types for fields.
    
    Args:
        data: Data dictionary to validate
        field_types: Dictionary mapping field names to expected types
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        for field, expected_type in field_types.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    result['valid'] = False
                    result['errors'].append(f"Field '{field}' must be of type {expected_type.__name__}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating data types: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_string_length(value: str, min_length: int = 0, max_length: int = None) -> Dict[str, Any]:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length
        max_length: Maximum length (optional)
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        if len(value) < min_length:
            result['valid'] = False
            result['errors'].append(f"String must be at least {min_length} characters long")
        
        if max_length is not None and len(value) > max_length:
            result['valid'] = False
            result['errors'].append(f"String must be no more than {max_length} characters long")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating string length: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_numeric_range(value: Union[int, float], min_value: float = None, max_value: float = None) -> Dict[str, Any]:
    """
    Validate numeric range.
    
    Args:
        value: Numeric value to validate
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        if min_value is not None and value < min_value:
            result['valid'] = False
            result['errors'].append(f"Value must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            result['valid'] = False
            result['errors'].append(f"Value must be no more than {max_value}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating numeric range: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def validate_list_length(value: List[Any], min_length: int = 0, max_length: int = None) -> Dict[str, Any]:
    """
    Validate list length.
    
    Args:
        value: List to validate
        min_length: Minimum length
        max_length: Maximum length (optional)
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        if len(value) < min_length:
            result['valid'] = False
            result['errors'].append(f"List must have at least {min_length} items")
        
        if max_length is not None and len(value) > max_length:
            result['valid'] = False
            result['errors'].append(f"List must have no more than {max_length} items")
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating list length: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }

def sanitize_input(value: str, max_length: int = None) -> str:
    """
    Sanitize user input.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum length (optional)
    
    Returns:
        Sanitized string
    """
    try:
        # Remove leading/trailing whitespace
        sanitized = value.strip()
        
        # Limit length if specified
        if max_length is not None:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    except Exception as e:
        logger.error(f"Error sanitizing input: {str(e)}")
        return ""

def validate_scraper_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate scraper configuration.
    
    Args:
        config: Scraper configuration dictionary
    
    Returns:
        Validation result dictionary
    """
    try:
        result = {
            'valid': True,
            'errors': []
        }
        
        # Check required fields
        required_fields = ['name', 'url', 'selectors']
        required_result = validate_required_fields(config, required_fields)
        if not required_result['valid']:
            result['valid'] = False
            result['errors'].extend(required_result['errors'])
        
        # Validate URL
        if 'url' in config and not validate_url(config['url']):
            result['valid'] = False
            result['errors'].append("Invalid URL format")
        
        # Validate selectors
        if 'selectors' in config:
            if not isinstance(config['selectors'], dict):
                result['valid'] = False
                result['errors'].append("Selectors must be a dictionary")
            elif not config['selectors']:
                result['valid'] = False
                result['errors'].append("At least one selector must be defined")
        
        # Validate delay
        if 'delay' in config:
            delay_result = validate_numeric_range(config['delay'], min_value=0, max_value=60)
            if not delay_result['valid']:
                result['valid'] = False
                result['errors'].extend(delay_result['errors'])
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating scraper config: {str(e)}")
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }
