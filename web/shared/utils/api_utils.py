"""
SPIDER Framework - API Utilities

Utility functions for API communication and response handling.
"""

import requests
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message: str, status_code: int = None, response_data: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

def make_api_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an API request with error handling.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: API endpoint URL
        headers: Request headers
        data: Request body data
        params: Query parameters
        timeout: Request timeout in seconds
    
    Returns:
        API response data
    
    Raises:
        APIError: If the API request fails
    """
    try:
        # Prepare request
        request_kwargs = {
            'headers': headers or {},
            'timeout': timeout
        }
        
        if data:
            request_kwargs['json'] = data
        
        if params:
            request_kwargs['params'] = params
        
        # Make request
        response = requests.request(method, url, **request_kwargs)
        
        # Handle response
        if response.status_code >= 400:
            raise APIError(
                message=f"API request failed with status {response.status_code}",
                status_code=response.status_code,
                response_data=response.json() if response.content else None
            )
        
        # Parse response
        try:
            return response.json()
        except json.JSONDecodeError:
            return {'data': response.text}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise APIError(f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        raise APIError(f"Unexpected error: {str(e)}")

def handle_api_error(error: Exception) -> Dict[str, Any]:
    """
    Handle API errors and return formatted error response.
    
    Args:
        error: Exception to handle
    
    Returns:
        Formatted error response
    """
    if isinstance(error, APIError):
        return {
            'error': True,
            'message': error.message,
            'status_code': error.status_code,
            'data': error.response_data,
            'timestamp': datetime.utcnow().isoformat()
        }
    else:
        return {
            'error': True,
            'message': str(error),
            'status_code': 500,
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }

def format_api_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format API response data for consistent structure.
    
    Args:
        response_data: Raw API response data
    
    Returns:
        Formatted response data
    """
    if 'error' in response_data and response_data['error']:
        return {
            'success': False,
            'data': None,
            'error': response_data.get('message', 'Unknown error'),
            'status_code': response_data.get('status_code', 500),
            'timestamp': response_data.get('timestamp', datetime.utcnow().isoformat())
        }
    else:
        return {
            'success': True,
            'data': response_data.get('data', response_data),
            'error': None,
            'status_code': 200,
            'timestamp': response_data.get('timestamp', datetime.utcnow().isoformat())
        }

def validate_api_response(response_data: Dict[str, Any], required_fields: list = None) -> bool:
    """
    Validate API response data structure.
    
    Args:
        response_data: API response data to validate
        required_fields: List of required fields
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if response has required structure
        if not isinstance(response_data, dict):
            return False
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in response_data:
                    return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating API response: {str(e)}")
        return False

def get_api_base_url() -> str:
    """
    Get the base API URL from configuration.
    
    Returns:
        Base API URL
    """
    # This would typically come from environment variables or config
    import os
    return os.getenv('API_BASE_URL', 'http://localhost:8000')

def build_api_url(endpoint: str, base_url: str = None) -> str:
    """
    Build full API URL from endpoint.
    
    Args:
        endpoint: API endpoint path
        base_url: Base API URL (optional)
    
    Returns:
        Full API URL
    """
    if base_url is None:
        base_url = get_api_base_url()
    
    # Ensure endpoint starts with /
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    # Ensure base_url doesn't end with /
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    return f"{base_url}{endpoint}"

def make_authenticated_request(
    method: str,
    endpoint: str,
    token: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make an authenticated API request.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        token: Authentication token
        data: Request body data
        params: Query parameters
    
    Returns:
        API response data
    """
    url = build_api_url(endpoint)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    return make_api_request(method, url, headers, data, params)

def paginate_api_request(
    endpoint: str,
    token: str,
    page: int = 1,
    limit: int = 20,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make a paginated API request.
    
    Args:
        endpoint: API endpoint
        token: Authentication token
        page: Page number
        limit: Items per page
        params: Additional query parameters
    
    Returns:
        Paginated API response data
    """
    if params is None:
        params = {}
    
    params.update({
        'page': page,
        'limit': limit
    })
    
    return make_authenticated_request('GET', endpoint, token, params=params)

def retry_api_request(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Retry an API request function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        backoff_factor: Backoff multiplier
    
    Returns:
        Function result
    
    Raises:
        APIError: If all retries fail
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except APIError as e:
            last_exception = e
            
            # Don't retry on client errors (4xx)
            if e.status_code and 400 <= e.status_code < 500:
                raise e
            
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(f"API request failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait_time)
            else:
                logger.error(f"API request failed after {max_retries + 1} attempts")
                raise e
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(f"API request failed, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait_time)
            else:
                logger.error(f"API request failed after {max_retries + 1} attempts")
                raise APIError(f"API request failed after {max_retries + 1} attempts: {str(e)}")
    
    if last_exception:
        raise last_exception
