"""
SPIDER Framework - Security Utilities

Utility functions for security operations.
"""

import hashlib
import hmac
import secrets
import string
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def generate_random_string(length: int = 32, include_symbols: bool = True) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string
        include_symbols: Whether to include special symbols
    
    Returns:
        Random string
    """
    try:
        characters = string.ascii_letters + string.digits
        if include_symbols:
            characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    except Exception as e:
        logger.error(f"Error generating random string: {str(e)}")
        return ""

def generate_api_key(prefix: str = "spider") -> str:
    """
    Generate a secure API key.
    
    Args:
        prefix: Prefix for the API key
    
    Returns:
        API key
    """
    try:
        random_part = generate_random_string(32, include_symbols=False)
        return f"{prefix}_{random_part}"
    
    except Exception as e:
        logger.error(f"Error generating API key: {str(e)}")
        return ""

def hash_password(password: str, salt: str = None) -> Dict[str, str]:
    """
    Hash a password using PBKDF2.
    
    Args:
        password: Password to hash
        salt: Salt for hashing (optional)
    
    Returns:
        Dictionary with hashed password and salt
    """
    try:
        if salt is None:
            salt = generate_random_string(32, include_symbols=False)
        
        # Use PBKDF2 with SHA-256
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        hashed_hex = hashed.hex()
        
        return {
            'password_hash': hashed_hex,
            'salt': salt
        }
    
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        return {
            'password_hash': '',
            'salt': ''
        }

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Password to verify
        hashed_password: Stored password hash
        salt: Salt used for hashing
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Hash the provided password with the same salt
        password_hash = hash_password(password, salt)
        
        # Compare the hashes
        return hmac.compare_digest(password_hash['password_hash'], hashed_password)
    
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def generate_hmac_signature(data: str, secret: str, algorithm: str = 'sha256') -> str:
    """
    Generate HMAC signature for data.
    
    Args:
        data: Data to sign
        secret: Secret key for signing
        algorithm: Hash algorithm to use
    
    Returns:
        HMAC signature
    """
    try:
        return hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            algorithm
        ).hexdigest()
    
    except Exception as e:
        logger.error(f"Error generating HMAC signature: {str(e)}")
        return ""

def verify_hmac_signature(data: str, signature: str, secret: str, algorithm: str = 'sha256') -> bool:
    """
    Verify HMAC signature for data.
    
    Args:
        data: Data to verify
        signature: Signature to verify against
        secret: Secret key for verification
        algorithm: Hash algorithm to use
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = generate_hmac_signature(data, secret, algorithm)
        return hmac.compare_digest(expected_signature, signature)
    
    except Exception as e:
        logger.error(f"Error verifying HMAC signature: {str(e)}")
        return False

def sanitize_input(input_string: str, max_length: int = None) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_string: Input string to sanitize
        max_length: Maximum length (optional)
    
    Returns:
        Sanitized string
    """
    try:
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
        
        # Limit length if specified
        if max_length is not None:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    except Exception as e:
        logger.error(f"Error sanitizing input: {str(e)}")
        return ""

def validate_input(input_string: str, allowed_chars: str = None, min_length: int = 0, max_length: int = None) -> bool:
    """
    Validate user input.
    
    Args:
        input_string: Input string to validate
        allowed_chars: Allowed characters (optional)
        min_length: Minimum length
        max_length: Maximum length (optional)
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check length
        if len(input_string) < min_length:
            return False
        
        if max_length is not None and len(input_string) > max_length:
            return False
        
        # Check allowed characters
        if allowed_chars is not None:
            for char in input_string:
                if char not in allowed_chars:
                    return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating input: {str(e)}")
        return False

def escape_html(text: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    """
    try:
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)
    
    except Exception as e:
        logger.error(f"Error escaping HTML: {str(e)}")
        return ""

def unescape_html(text: str) -> str:
    """
    Unescape HTML special characters.
    
    Args:
        text: Text to unescape
    
    Returns:
        Unescaped text
    """
    try:
        html_unescape_table = {
            "&amp;": "&",
            "&quot;": '"',
            "&#x27;": "'",
            "&gt;": ">",
            "&lt;": "<",
        }
        
        for entity, char in html_unescape_table.items():
            text = text.replace(entity, char)
        
        return text
    
    except Exception as e:
        logger.error(f"Error unescaping HTML: {str(e)}")
        return ""

def generate_csrf_token() -> str:
    """
    Generate a CSRF token.
    
    Returns:
        CSRF token
    """
    try:
        return generate_random_string(32, include_symbols=False)
    
    except Exception as e:
        logger.error(f"Error generating CSRF token: {str(e)}")
        return ""

def validate_csrf_token(token: str, session_token: str) -> bool:
    """
    Validate a CSRF token.
    
    Args:
        token: Token to validate
        session_token: Session token to validate against
    
    Returns:
        True if valid, False otherwise
    """
    try:
        return hmac.compare_digest(token, session_token)
    
    except Exception as e:
        logger.error(f"Error validating CSRF token: {str(e)}")
        return False

def generate_secure_filename(filename: str) -> str:
    """
    Generate a secure filename.
    
    Args:
        filename: Original filename
    
    Returns:
        Secure filename
    """
    try:
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return filename
    
    except Exception as e:
        logger.error(f"Error generating secure filename: {str(e)}")
        return "secure_file"

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions
    
    Returns:
        True if valid, False otherwise
    """
    try:
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]
    
    except Exception as e:
        logger.error(f"Error validating file extension: {str(e)}")
        return False

def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength.
    
    Args:
        password: Password to check
    
    Returns:
        Password strength information
    """
    try:
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        # Uppercase check
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one uppercase letter")
        
        # Lowercase check
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one lowercase letter")
        
        # Digit check
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one number")
        
        # Special character check
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one special character")
        
        # Common password check
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        
        if password.lower() in common_passwords:
            score -= 2
            feedback.append("Password is too common")
        
        # Determine strength level
        if score <= 2:
            strength = "weak"
        elif score <= 4:
            strength = "medium"
        else:
            strength = "strong"
        
        return {
            'score': score,
            'strength': strength,
            'feedback': feedback,
            'is_strong': score >= 4
        }
    
    except Exception as e:
        logger.error(f"Error checking password strength: {str(e)}")
        return {
            'score': 0,
            'strength': 'weak',
            'feedback': ['Error checking password strength'],
            'is_strong': False
        }
