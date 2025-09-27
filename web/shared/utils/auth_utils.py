"""
SPIDER Framework - Authentication Utilities

Utility functions for authentication and authorization.
"""

import jwt
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def get_auth_headers(token: str) -> Dict[str, str]:
    """
    Get authentication headers for API requests.
    
    Args:
        token: JWT token
    
    Returns:
        Headers dictionary
    """
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

def is_token_expired(token: str) -> bool:
    """
    Check if JWT token is expired.
    
    Args:
        token: JWT token to check
    
    Returns:
        True if expired, False otherwise
    """
    try:
        # Decode token without verification to check expiration
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check expiration
        exp = payload.get('exp')
        if exp:
            return datetime.utcnow().timestamp() > exp
        
        return False
    
    except jwt.InvalidTokenError:
        return True
    except Exception as e:
        logger.error(f"Error checking token expiration: {str(e)}")
        return True

def decode_token(token: str, secret_key: str = None) -> Dict[str, Any]:
    """
    Decode JWT token.
    
    Args:
        token: JWT token to decode
        secret_key: Secret key for verification (optional)
    
    Returns:
        Token payload
    
    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        if secret_key:
            return jwt.decode(token, secret_key, algorithms=['HS256'])
        else:
            # Decode without verification
            return jwt.decode(token, options={"verify_signature": False})
    
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

def get_token_payload(token: str) -> Dict[str, Any]:
    """
    Get token payload without verification.
    
    Args:
        token: JWT token
    
    Returns:
        Token payload
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return {}

def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        User ID or None
    """
    try:
        payload = get_token_payload(token)
        return payload.get('user_id')
    except Exception as e:
        logger.error(f"Error extracting user ID from token: {str(e)}")
        return None

def get_tenant_id_from_token(token: str) -> Optional[str]:
    """
    Extract tenant ID from JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        Tenant ID or None
    """
    try:
        payload = get_token_payload(token)
        return payload.get('tenant_id')
    except Exception as e:
        logger.error(f"Error extracting tenant ID from token: {str(e)}")
        return None

def get_user_role_from_token(token: str) -> Optional[str]:
    """
    Extract user role from JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        User role or None
    """
    try:
        payload = get_token_payload(token)
        return payload.get('role')
    except Exception as e:
        logger.error(f"Error extracting user role from token: {str(e)}")
        return None

def refresh_token(refresh_token: str, api_base_url: str = None) -> Dict[str, Any]:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token
        api_base_url: API base URL
    
    Returns:
        New token data
    
    Raises:
        APIError: If refresh fails
    """
    from .api_utils import make_api_request, APIError
    
    if api_base_url is None:
        from .api_utils import get_api_base_url
        api_base_url = get_api_base_url()
    
    try:
        url = f"{api_base_url}/auth/refresh"
        data = {"refresh_token": refresh_token}
        
        response = make_api_request('POST', url, data=data)
        
        if 'error' in response:
            raise APIError(f"Token refresh failed: {response.get('message', 'Unknown error')}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise APIError(f"Token refresh failed: {str(e)}")

def logout_user(token: str, api_base_url: str = None) -> bool:
    """
    Logout user and invalidate token.
    
    Args:
        token: JWT token
        api_base_url: API base URL
    
    Returns:
        True if successful, False otherwise
    """
    from .api_utils import make_api_request, APIError
    
    if api_base_url is None:
        from .api_utils import get_api_base_url
        api_base_url = get_api_base_url()
    
    try:
        url = f"{api_base_url}/auth/logout"
        headers = get_auth_headers(token)
        
        response = make_api_request('POST', url, headers=headers)
        
        return 'error' not in response
    
    except Exception as e:
        logger.error(f"Error logging out user: {str(e)}")
        return False

def validate_token_permissions(token: str, required_permissions: list) -> bool:
    """
    Validate if token has required permissions.
    
    Args:
        token: JWT token
        required_permissions: List of required permissions
    
    Returns:
        True if has permissions, False otherwise
    """
    try:
        payload = get_token_payload(token)
        user_permissions = payload.get('permissions', [])
        
        # Check if user has all required permissions
        return all(perm in user_permissions for perm in required_permissions)
    
    except Exception as e:
        logger.error(f"Error validating token permissions: {str(e)}")
        return False

def get_token_expiration_time(token: str) -> Optional[datetime]:
    """
    Get token expiration time.
    
    Args:
        token: JWT token
    
    Returns:
        Expiration datetime or None
    """
    try:
        payload = get_token_payload(token)
        exp = payload.get('exp')
        
        if exp:
            return datetime.fromtimestamp(exp)
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting token expiration time: {str(e)}")
        return None

def is_token_valid(token: str, secret_key: str = None) -> bool:
    """
    Check if token is valid (not expired and properly signed).
    
    Args:
        token: JWT token
        secret_key: Secret key for verification (optional)
    
    Returns:
        True if valid, False otherwise
    """
    try:
        if secret_key:
            jwt.decode(token, secret_key, algorithms=['HS256'])
        else:
            # Just check if it's not expired
            return not is_token_expired(token)
        
        return True
    
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return False

def create_token_payload(
    user_id: str,
    username: str,
    email: str,
    role: str,
    tenant_id: str,
    permissions: list = None,
    expires_in: int = 3600
) -> Dict[str, Any]:
    """
    Create token payload for JWT.
    
    Args:
        user_id: User ID
        username: Username
        email: Email address
        role: User role
        tenant_id: Tenant ID
        permissions: List of permissions
        expires_in: Token expiration in seconds
    
    Returns:
        Token payload
    """
    now = datetime.utcnow()
    
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'role': role,
        'tenant_id': tenant_id,
        'permissions': permissions or [],
        'iat': now,
        'exp': now + timedelta(seconds=expires_in),
        'iss': 'spider',
        'aud': 'spider-users'
    }
    
    return payload

def generate_token(payload: Dict[str, Any], secret_key: str) -> str:
    """
    Generate JWT token from payload.
    
    Args:
        payload: Token payload
        secret_key: Secret key for signing
    
    Returns:
        JWT token
    """
    try:
        return jwt.encode(payload, secret_key, algorithm='HS256')
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise ValueError(f"Failed to generate token: {str(e)}")
