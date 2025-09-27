"""
SPIDER Framework - Logging Middleware

Handles request/response logging, structured logging, and audit trails.
"""

from typing import Dict, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import time
import json
import uuid
from datetime import datetime
from contextvars import ContextVar

from ...core.logger import get_logger

logger = get_logger(__name__)

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id')
user_id_var: ContextVar[str] = ContextVar('user_id')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id')

class LoggingMiddleware:
    """Middleware for comprehensive request/response logging."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process logging for each request."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Set context variables
        user = getattr(request.state, 'user', None)
        if user:
            user_id_var.set(user.id)
            tenant_id_var.set(user.tenant_id)
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        await self._log_response(request, response, process_time, request_id)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request."""
        try:
            # Extract request information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Get user information
            user = getattr(request.state, 'user', None)
            user_id = user.id if user else None
            tenant_id = user.tenant_id if user else None
            
            # Log request
            self.logger.info(
                "HTTP request",
                extra={
                    "event_type": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log request: {str(e)}")
    
    async def _log_response(self, request: Request, response: Response, process_time: float, request_id: str) -> None:
        """Log outgoing response."""
        try:
            # Get user information
            user = getattr(request.state, 'user', None)
            user_id = user.id if user else None
            tenant_id = user.tenant_id if user else None
            
            # Log response
            self.logger.info(
                "HTTP response",
                extra={
                    "event_type": "http_response",
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log response: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host

class AuditMiddleware:
    """Middleware for audit logging of sensitive operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.audit_endpoints = [
            "/api/v1/users",
            "/api/v1/scrapers",
            "/api/v1/system",
            "/api/v1/ai"
        ]
    
    async def __call__(self, request: Request, call_next):
        """Process audit logging for each request."""
        # Check if endpoint requires audit logging
        if not self._requires_audit(request.url.path):
            return await call_next(request)
        
        # Get user information
        user = getattr(request.state, 'user', None)
        if not user:
            return await call_next(request)
        
        # Log audit event
        await self._log_audit_event(request, user)
        
        return await call_next(request)
    
    def _requires_audit(self, path: str) -> bool:
        """Check if endpoint requires audit logging."""
        return any(path.startswith(endpoint) for endpoint in self.audit_endpoints)
    
    async def _log_audit_event(self, request: Request, user) -> None:
        """Log audit event."""
        try:
            # Extract request body for audit
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        body = body.decode("utf-8")
                except Exception:
                    body = "Unable to read body"
            
            # Log audit event
            self.logger.info(
                "Audit event",
                extra={
                    "event_type": "audit",
                    "action": f"{request.method} {request.url.path}",
                    "user_id": user.id,
                    "username": user.username,
                    "tenant_id": user.tenant_id,
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent", ""),
                    "request_body": body,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host

class PerformanceMiddleware:
    """Middleware for performance monitoring and logging."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.slow_request_threshold = 5.0  # 5 seconds
    
    async def __call__(self, request: Request, call_next):
        """Process performance monitoring for each request."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log performance metrics
        await self._log_performance_metrics(request, response, process_time)
        
        return response
    
    async def _log_performance_metrics(self, request: Request, response: Response, process_time: float) -> None:
        """Log performance metrics."""
        try:
            # Get user information
            user = getattr(request.state, 'user', None)
            user_id = user.id if user else None
            tenant_id = user.tenant_id if user else None
            
            # Determine if request is slow
            is_slow = process_time > self.slow_request_threshold
            
            # Log performance metrics
            self.logger.info(
                "Performance metrics",
                extra={
                    "event_type": "performance",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "is_slow": is_slow,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Log slow requests as warnings
            if is_slow:
                self.logger.warning(
                    "Slow request detected",
                    extra={
                        "event_type": "slow_request",
                        "method": request.method,
                        "path": request.url.path,
                        "process_time": process_time,
                        "threshold": self.slow_request_threshold,
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metrics: {str(e)}")

class ErrorLoggingMiddleware:
    """Middleware for comprehensive error logging."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process error logging for each request."""
        try:
            return await call_next(request)
        except Exception as e:
            # Log error
            await self._log_error(request, e)
            raise
    
    async def _log_error(self, request: Request, error: Exception) -> None:
        """Log error details."""
        try:
            # Get user information
            user = getattr(request.state, 'user', None)
            user_id = user.id if user else None
            tenant_id = user.tenant_id if user else None
            
            # Log error
            self.logger.error(
                "Request error",
                extra={
                    "event_type": "error",
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent", ""),
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
            
        except Exception as log_error:
            self.logger.error(f"Failed to log error: {str(log_error)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
