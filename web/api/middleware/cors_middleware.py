"""
SPIDER Framework - CORS Middleware

Handles Cross-Origin Resource Sharing (CORS) configuration and headers.
"""

from typing import List, Optional, Union
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...core.config import get_settings
from ...core.logger import get_logger

logger = get_logger(__name__)

class CORSMiddleware:
    """CORS middleware for handling cross-origin requests."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
    
    def get_cors_middleware(self) -> FastAPICORSMiddleware:
        """Get configured CORS middleware."""
        return FastAPICORSMiddleware(
            allow_origins=self._get_allowed_origins(),
            allow_credentials=True,
            allow_methods=self._get_allowed_methods(),
            allow_headers=self._get_allowed_headers(),
            expose_headers=self._get_exposed_headers(),
            max_age=self._get_max_age()
        )
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed origins for CORS."""
        # Get from environment or use defaults
        origins = getattr(self.settings, 'cors_origins', [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://example.com",
            "https://dashboard.example.com"
        ])
        
        # Add development origins if in development mode
        if getattr(self.settings, 'debug', False):
            origins.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ])
        
        return origins
    
    def _get_allowed_methods(self) -> List[str]:
        """Get allowed HTTP methods for CORS."""
        return [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "OPTIONS",
            "HEAD"
        ]
    
    def _get_allowed_headers(self) -> List[str]:
        """Get allowed headers for CORS."""
        return [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-API-Key",
            "X-Tenant-ID",
            "X-Request-ID",
            "X-Forwarded-For",
            "X-Real-IP"
        ]
    
    def _get_exposed_headers(self) -> List[str]:
        """Get exposed headers for CORS."""
        return [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Total-Count",
            "X-Page-Count"
        ]
    
    def _get_max_age(self) -> int:
        """Get max age for preflight requests."""
        return 3600  # 1 hour

class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with additional features."""
    
    def __init__(self, app, allow_origins: List[str] = None, allow_credentials: bool = True):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """Process CORS headers for each request."""
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._handle_preflight_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(request, response)
        
        return response
    
    def _handle_preflight_request(self, request: Request) -> Response:
        """Handle preflight OPTIONS requests."""
        origin = request.headers.get("Origin")
        
        # Check if origin is allowed
        if not self._is_origin_allowed(origin):
            return Response(
                status_code=403,
                content="Origin not allowed",
                headers=self._get_cors_headers(request, origin)
            )
        
        # Return preflight response
        return Response(
            status_code=200,
            content="OK",
            headers=self._get_cors_headers(request, origin)
        )
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        if "*" in self.allow_origins:
            return True
        
        return origin in self.allow_origins
    
    def _add_cors_headers(self, request: Request, response: Response) -> None:
        """Add CORS headers to response."""
        origin = request.headers.get("Origin")
        
        if origin and self._is_origin_allowed(origin):
            headers = self._get_cors_headers(request, origin)
            for key, value in headers.items():
                response.headers[key] = value
    
    def _get_cors_headers(self, request: Request, origin: str) -> dict:
        """Get CORS headers for response."""
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-API-Key, X-Tenant-ID, X-Request-ID",
            "Access-Control-Expose-Headers": "X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-Total-Count, X-Page-Count",
            "Access-Control-Max-Age": "3600"
        }
        
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers

class SecurityHeadersMiddleware:
    """Middleware for adding security headers."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
