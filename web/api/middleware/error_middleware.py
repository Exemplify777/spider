"""
SPIDER Framework - Error Middleware

Handles error responses, exception handling, and error formatting.
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from datetime import datetime

from ...core.logger import get_logger

logger = get_logger(__name__)

class ErrorMiddleware:
    """Middleware for comprehensive error handling."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process error handling for each request."""
        try:
            return await call_next(request)
        except HTTPException as e:
            return self._handle_http_exception(request, e)
        except RequestValidationError as e:
            return self._handle_validation_error(request, e)
        except StarletteHTTPException as e:
            return self._handle_starlette_exception(request, e)
        except Exception as e:
            return self._handle_generic_exception(request, e)
    
    def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_response = self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            request=request
        )
        
        self.logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "event_type": "http_exception",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    def _handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        error_response = self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=self._format_validation_errors(exc.errors()),
            request=request
        )
        
        self.logger.warning(
            f"Validation error: {exc.errors()}",
            extra={
                "event_type": "validation_error",
                "errors": exc.errors(),
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response
        )
    
    def _handle_starlette_exception(self, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        error_response = self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            request=request
        )
        
        self.logger.warning(
            f"Starlette exception: {exc.status_code} - {exc.detail}",
            extra={
                "event_type": "starlette_exception",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    def _handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions."""
        error_response = self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message="An internal server error occurred",
            request=request
        )
        
        self.logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "event_type": "unhandled_exception",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
    
    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        error_response = {
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if details:
            error_response["error"]["details"] = details
        
        if request:
            error_response["error"]["request_id"] = getattr(request.state, 'request_id', None)
            error_response["error"]["path"] = request.url.path
            error_response["error"]["method"] = request.method
        
        return error_response
    
    def _format_validation_errors(self, errors: list) -> Dict[str, Any]:
        """Format validation errors for response."""
        formatted_errors = {}
        
        for error in errors:
            field = ".".join(str(loc) for loc in error["loc"])
            if field not in formatted_errors:
                formatted_errors[field] = []
            
            formatted_errors[field].append({
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        return formatted_errors

class SecurityErrorMiddleware:
    """Middleware for security-related error handling."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process security error handling for each request."""
        try:
            return await call_next(request)
        except HTTPException as e:
            if e.status_code in [401, 403]:
                return self._handle_security_error(request, e)
            raise
        except Exception as e:
            # Check if it's a security-related error
            if self._is_security_error(e):
                return self._handle_security_error(request, e)
            raise
    
    def _handle_security_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle security-related errors."""
        error_response = {
            "error": {
                "code": "SECURITY_ERROR",
                "message": "Security violation detected",
                "status_code": 403,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None),
                "path": request.url.path,
                "method": request.method
            }
        }
        
        self.logger.warning(
            f"Security error: {str(exc)}",
            extra={
                "event_type": "security_error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "path": request.url.path,
                "method": request.method,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        return JSONResponse(
            status_code=403,
            content=error_response
        )
    
    def _is_security_error(self, exc: Exception) -> bool:
        """Check if exception is security-related."""
        security_error_types = [
            "AuthenticationError",
            "AuthorizationError",
            "PermissionDenied",
            "SecurityViolation"
        ]
        
        return type(exc).__name__ in security_error_types
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host

class RateLimitErrorMiddleware:
    """Middleware for rate limit error handling."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process rate limit error handling for each request."""
        try:
            return await call_next(request)
        except HTTPException as e:
            if e.status_code == 429:
                return self._handle_rate_limit_error(request, e)
            raise
    
    def _handle_rate_limit_error(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle rate limit errors."""
        error_response = {
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please try again later.",
                "status_code": 429,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_after": 60,
                "request_id": getattr(request.state, 'request_id', None),
                "path": request.url.path,
                "method": request.method
            }
        }
        
        self.logger.warning(
            f"Rate limit exceeded: {request.url.path}",
            extra={
                "event_type": "rate_limit_exceeded",
                "path": request.url.path,
                "method": request.method,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        return JSONResponse(
            status_code=429,
            content=error_response,
            headers={"Retry-After": "60"}
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
