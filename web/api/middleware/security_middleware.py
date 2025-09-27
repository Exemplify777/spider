"""
SPIDER Framework - Security Middleware

Handles security-related middleware including input validation, 
threat detection, and security headers.
"""

from typing import Dict, Any, List, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import hmac

from ...core.config import get_settings
from ...core.logger import get_logger

logger = get_logger(__name__)

class SecurityMiddleware:
    """Main security middleware for threat detection and prevention."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Security patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # XSS
            r'vbscript:',  # XSS
            r'onload\s*=',  # XSS
            r'onerror\s*=',  # XSS
            r'<iframe[^>]*>',  # XSS
            r'<object[^>]*>',  # XSS
            r'<embed[^>]*>',  # XSS
            r'<link[^>]*>',  # XSS
            r'<meta[^>]*>',  # XSS
            r'union\s+select',  # SQL Injection
            r'drop\s+table',  # SQL Injection
            r'delete\s+from',  # SQL Injection
            r'insert\s+into',  # SQL Injection
            r'update\s+set',  # SQL Injection
            r'exec\s*\(',  # SQL Injection
            r'sp_executesql',  # SQL Injection
            r'\.\./',  # Path Traversal
            r'\.\.\\',  # Path Traversal
            r'%2e%2e%2f',  # URL Encoded Path Traversal
            r'%2e%2e%5c',  # URL Encoded Path Traversal
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        
        # Rate limiting for security events
        self.security_events = defaultdict(lambda: deque())
        self.max_security_events = 10
        self.security_window = 300  # 5 minutes
    
    async def __call__(self, request: Request, call_next):
        """Process security checks for each request."""
        try:
            # Check for malicious patterns in request
            if not await self._check_malicious_patterns(request):
                return self._create_security_error_response(request, "Malicious pattern detected")
            
            # Check for suspicious headers
            if not await self._check_suspicious_headers(request):
                return self._create_security_error_response(request, "Suspicious headers detected")
            
            # Check for brute force attempts
            if not await self._check_brute_force(request):
                return self._create_security_error_response(request, "Brute force attempt detected")
            
            # Check for suspicious user agent
            if not await self._check_user_agent(request):
                return self._create_security_error_response(request, "Suspicious user agent detected")
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            return await call_next(request)
    
    async def _check_malicious_patterns(self, request: Request) -> bool:
        """Check for malicious patterns in request."""
        try:
            # Check URL path
            if self._contains_malicious_pattern(request.url.path):
                await self._log_security_event(request, "malicious_pattern", "path")
                return False
            
            # Check query parameters
            for param, value in request.query_params.items():
                if self._contains_malicious_pattern(str(value)):
                    await self._log_security_event(request, "malicious_pattern", f"query_param:{param}")
                    return False
            
            # Check headers
            for header, value in request.headers.items():
                if self._contains_malicious_pattern(str(value)):
                    await self._log_security_event(request, "malicious_pattern", f"header:{header}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking malicious patterns: {str(e)}")
            return True
    
    def _contains_malicious_pattern(self, text: str) -> bool:
        """Check if text contains malicious patterns."""
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    async def _check_suspicious_headers(self, request: Request) -> bool:
        """Check for suspicious headers."""
        try:
            suspicious_headers = [
                "X-Forwarded-Host",
                "X-Forwarded-Server",
                "X-Forwarded-Proto",
                "X-Original-URL",
                "X-Rewrite-URL"
            ]
            
            for header in suspicious_headers:
                if header in request.headers:
                    value = request.headers[header]
                    if self._is_suspicious_header_value(value):
                        await self._log_security_event(request, "suspicious_header", header)
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking suspicious headers: {str(e)}")
            return True
    
    def _is_suspicious_header_value(self, value: str) -> bool:
        """Check if header value is suspicious."""
        suspicious_values = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "http://",
            "https://",
            "ftp://",
            "file://"
        ]
        
        return any(suspicious in value.lower() for suspicious in suspicious_values)
    
    async def _check_brute_force(self, request: Request) -> bool:
        """Check for brute force attempts."""
        try:
            client_ip = self._get_client_ip(request)
            current_time = time.time()
            
            # Get security events for this IP
            events = self.security_events[client_ip]
            
            # Remove old events
            while events and events[0] < current_time - self.security_window:
                events.popleft()
            
            # Check if too many security events
            if len(events) >= self.max_security_events:
                await self._log_security_event(request, "brute_force", "too_many_events")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking brute force: {str(e)}")
            return True
    
    async def _check_user_agent(self, request: Request) -> bool:
        """Check for suspicious user agents."""
        try:
            user_agent = request.headers.get("user-agent", "")
            
            if not user_agent:
                await self._log_security_event(request, "suspicious_user_agent", "empty")
                return False
            
            # Check for suspicious patterns in user agent
            suspicious_patterns = [
                r'bot',
                r'crawler',
                r'spider',
                r'scanner',
                r'exploit',
                r'hack',
                r'attack'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, user_agent, re.IGNORECASE):
                    await self._log_security_event(request, "suspicious_user_agent", pattern)
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking user agent: {str(e)}")
            return True
    
    async def _log_security_event(self, request: Request, event_type: str, details: str) -> None:
        """Log security event."""
        try:
            client_ip = self._get_client_ip(request)
            current_time = time.time()
            
            # Add event to tracking
            self.security_events[client_ip].append(current_time)
            
            # Log security event
            self.logger.warning(
                f"Security event: {event_type} - {details}",
                extra={
                    "event_type": "security_event",
                    "security_event_type": event_type,
                    "details": details,
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error logging security event: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _create_security_error_response(self, request: Request, message: str) -> JSONResponse:
        """Create security error response."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "SECURITY_VIOLATION",
                    "message": message,
                    "status_code": 403,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            }
        )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "X-Permitted-Cross-Domain-Policies": "none"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value

class InputValidationMiddleware:
    """Middleware for input validation and sanitization."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.max_input_length = 10000  # 10KB
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def __call__(self, request: Request, call_next):
        """Process input validation for each request."""
        try:
            # Check content length
            if not await self._check_content_length(request):
                return self._create_validation_error_response(request, "Content too large")
            
            # Validate request body
            if not await self._validate_request_body(request):
                return self._create_validation_error_response(request, "Invalid request body")
            
            return await call_next(request)
            
        except Exception as e:
            self.logger.error(f"Input validation error: {str(e)}")
            return await call_next(request)
    
    async def _check_content_length(self, request: Request) -> bool:
        """Check if content length is within limits."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_file_size:
                    return False
            except ValueError:
                return False
        
        return True
    
    async def _validate_request_body(self, request: Request) -> bool:
        """Validate request body."""
        try:
            # Only validate for POST, PUT, PATCH requests
            if request.method not in ["POST", "PUT", "PATCH"]:
                return True
            
            # Check if body is too large
            body = await request.body()
            if len(body) > self.max_input_length:
                return False
            
            # Check for null bytes
            if b'\x00' in body:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating request body: {str(e)}")
            return True
    
    def _create_validation_error_response(self, request: Request, message: str) -> JSONResponse:
        """Create validation error response."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": message,
                    "status_code": 400,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            }
        )

class CSRFMiddleware:
    """Middleware for CSRF protection."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.secret_key = "your-secret-key"  # Should be from settings
    
    async def __call__(self, request: Request, call_next):
        """Process CSRF protection for each request."""
        try:
            # Skip CSRF check for safe methods
            if request.method in ["GET", "HEAD", "OPTIONS"]:
                return await call_next(request)
            
            # Check CSRF token
            if not await self._check_csrf_token(request):
                return self._create_csrf_error_response(request)
            
            return await call_next(request)
            
        except Exception as e:
            self.logger.error(f"CSRF middleware error: {str(e)}")
            return await call_next(request)
    
    async def _check_csrf_token(self, request: Request) -> bool:
        """Check CSRF token."""
        try:
            # Get CSRF token from header
            csrf_token = request.headers.get("X-CSRF-Token")
            if not csrf_token:
                return False
            
            # Get session token (would be stored in session)
            session_token = request.headers.get("X-Session-Token")
            if not session_token:
                return False
            
            # Verify CSRF token
            expected_token = self._generate_csrf_token(session_token)
            return hmac.compare_digest(csrf_token, expected_token)
            
        except Exception as e:
            self.logger.error(f"Error checking CSRF token: {str(e)}")
            return False
    
    def _generate_csrf_token(self, session_token: str) -> str:
        """Generate CSRF token."""
        return hmac.new(
            self.secret_key.encode(),
            session_token.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _create_csrf_error_response(self, request: Request) -> JSONResponse:
        """Create CSRF error response."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "CSRF_ERROR",
                    "message": "CSRF token validation failed",
                    "status_code": 403,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            }
        )
