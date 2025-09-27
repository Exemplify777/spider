"""
SPIDER Framework - Data Utilities

Utility functions for data formatting, validation, and manipulation.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def format_date(date_obj: Union[datetime, date, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format date object to string.
    
    Args:
        date_obj: Date object to format
        format_str: Format string
    
    Returns:
        Formatted date string
    """
    try:
        if isinstance(date_obj, str):
            # Try to parse ISO format first
            try:
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            except ValueError:
                # Try other common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return str(date_obj)
        
        if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
            date_obj = datetime.combine(date_obj, datetime.min.time())
        
        return date_obj.strftime(format_str)
    
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return str(date_obj)

def format_number(number: Union[int, float], precision: int = 2) -> str:
    """
    Format number with specified precision.
    
    Args:
        number: Number to format
        precision: Decimal precision
    
    Returns:
        Formatted number string
    """
    try:
        if isinstance(number, int):
            return str(number)
        
        return f"{number:.{precision}f}"
    
    except Exception as e:
        logger.error(f"Error formatting number: {str(e)}")
        return str(number)

def format_bytes(bytes_value: int, precision: int = 2) -> str:
    """
    Format bytes to human readable format.
    
    Args:
        bytes_value: Number of bytes
        precision: Decimal precision
    
    Returns:
        Formatted bytes string
    """
    try:
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.{precision}f} {units[unit_index]}"
    
    except Exception as e:
        logger.error(f"Error formatting bytes: {str(e)}")
        return str(bytes_value)

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
        logger.error(f"Error validating email: {str(e)}")
        return False

def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}")
        return False

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum length
    
    Returns:
        Sanitized string
    """
    try:
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', input_str)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    except Exception as e:
        logger.error(f"Error sanitizing input: {str(e)}")
        return str(input_str)[:max_length]

def parse_json(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON string safely.
    
    Args:
        json_str: JSON string to parse
    
    Returns:
        Parsed JSON data or None
    """
    try:
        return json.loads(json_str)
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {str(e)}")
        return None

def to_json(data: Any, indent: int = 2) -> str:
    """
    Convert data to JSON string.
    
    Args:
        data: Data to convert
        indent: JSON indentation
    
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, indent=indent, default=str)
    
    except Exception as e:
        logger.error(f"Error converting to JSON: {str(e)}")
        return str(data)

def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
    
    Returns:
        Merged dictionary
    """
    try:
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    except Exception as e:
        logger.error(f"Error merging dictionaries: {str(e)}")
        return dict1

def flatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        data: Dictionary to flatten
        separator: Key separator
    
    Returns:
        Flattened dictionary
    """
    try:
        def _flatten(obj, parent_key='', sep=separator):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    items.extend(_flatten(v, new_key, sep=sep).items())
            else:
                items.append((parent_key, obj))
            return dict(items)
        
        return _flatten(data)
    
    except Exception as e:
        logger.error(f"Error flattening dictionary: {str(e)}")
        return data

def filter_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Filter dictionary to include only specified keys.
    
    Args:
        data: Dictionary to filter
        keys: Keys to include
    
    Returns:
        Filtered dictionary
    """
    try:
        return {key: data[key] for key in keys if key in data}
    
    except Exception as e:
        logger.error(f"Error filtering dictionary: {str(e)}")
        return {}

def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dictionary.
    
    Args:
        data: Dictionary to clean
    
    Returns:
        Cleaned dictionary
    """
    try:
        return {key: value for key, value in data.items() if value is not None}
    
    except Exception as e:
        logger.error(f"Error removing None values: {str(e)}")
        return data

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    try:
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    except Exception as e:
        logger.error(f"Error truncating string: {str(e)}")
        return text

def capitalize_first(text: str) -> str:
    """
    Capitalize first letter of text.
    
    Args:
        text: Text to capitalize
    
    Returns:
        Capitalized text
    """
    try:
        if not text:
            return text
        
        return text[0].upper() + text[1:].lower()
    
    except Exception as e:
        logger.error(f"Error capitalizing text: {str(e)}")
        return text

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
    
    Returns:
        Slugified text
    """
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Replace spaces and special characters with hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        
        # Remove leading/trailing hyphens
        text = text.strip('-')
        
        return text
    
    except Exception as e:
        logger.error(f"Error slugifying text: {str(e)}")
        return text

def extract_numbers(text: str) -> List[Union[int, float]]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to extract numbers from
    
    Returns:
        List of numbers
    """
    try:
        pattern = r'-?\d+\.?\d*'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                if '.' in match:
                    numbers.append(float(match))
                else:
                    numbers.append(int(match))
            except ValueError:
                continue
        
        return numbers
    
    except Exception as e:
        logger.error(f"Error extracting numbers: {str(e)}")
        return []

def clean_html(html: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        html: HTML string
    
    Returns:
        Cleaned text
    """
    try:
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        import html
        clean = html.unescape(clean)
        
        # Clean up whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html
