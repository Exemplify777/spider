"""
SPIDER Framework - Rate Limiting Middleware

Handles rate limiting and throttling for API endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import redis
import json

from ...core.config import get_settings
from ...core.logger import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware:
    """Rate limiting middleware using sliding window algorithm."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self.memory_store = defaultdict(lambda: deque())
        
        # Rate limit configurations
        self.rate_limits = {
            "global": {
                "requests_per_minute": 1000,
                "burst_size": 2000
            },
            "per_user": {
                "requests_per_minute": 100,
                "burst_size": 200
            },
            "per_ip": {
                "requests_per_minute": 500,
                "burst_size": 1000
            },
            "endpoints": {
                "/api/v1/ai/sentiment": {
                    "requests_per_minute": 50,
                    "burst_size": 100
                },
                "/api/v1/ai/entities": {
                    "requests_per_minute": 50,
                    "burst_size": 100
                },
                "/api/v1/scrapers/*/run": {
                    "requests_per_minute": 10,
                    "burst_size": 20
                }
            }
        }
    
    async def __call__(self, request: Request, call_next):
        """Process rate limiting for each request."""
        try:
            # Skip rate limiting for health checks
            if self._is_health_endpoint(request.url.path):
                return await call_next(request)
            
            # Get client identifier
            client_id = self._get_client_id(request)
            
            # Check rate limits
            if not await self._check_rate_limit(request, client_id):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self._get_rate_limit(request)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + 60))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            self._add_rate_limit_headers(response, request, client_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return await call_next(request)
    
    def _is_health_endpoint(self, path: str) -> bool:
        """Check if endpoint is a health check."""
        health_paths = [
            "/health",
            "/health/detailed",
            "/ready",
            "/metrics"
        ]
        return any(path.startswith(health_path) for health_path in health_paths)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get user ID first
        user = getattr(request.state, 'user', None)
        if user:
            return f"user:{user.id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, request: Request, client_id: str) -> bool:
        """Check if request is within rate limits."""
        try:
            # Get rate limit configuration for endpoint
            endpoint_config = self._get_endpoint_config(request.url.path)
            
            # Check global rate limit
            if not await self._check_global_rate_limit():
                return False
            
            # Check per-client rate limit
            if not await self._check_client_rate_limit(client_id, endpoint_config):
                return False
            
            # Check per-IP rate limit
            ip = request.client.host
            if not await self._check_ip_rate_limit(ip, endpoint_config):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True  # Allow request on error
    
    def _get_endpoint_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        # Check for specific endpoint configuration
        for endpoint_pattern, config in self.rate_limits["endpoints"].items():
            if self._match_endpoint_pattern(path, endpoint_pattern):
                return config
        
        # Use per-user configuration as default
        return self.rate_limits["per_user"]
    
    def _match_endpoint_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern."""
        if "*" in pattern:
            # Simple wildcard matching
            pattern_parts = pattern.split("*")
            if len(pattern_parts) == 2:
                return path.startswith(pattern_parts[0]) and path.endswith(pattern_parts[1])
        return path == pattern
    
    async def _check_global_rate_limit(self) -> bool:
        """Check global rate limit."""
        config = self.rate_limits["global"]
        return await self._check_rate_limit_window("global", config)
    
    async def _check_client_rate_limit(self, client_id: str, config: Dict[str, int]) -> bool:
        """Check per-client rate limit."""
        return await self._check_rate_limit_window(client_id, config)
    
    async def _check_ip_rate_limit(self, ip: str, config: Dict[str, int]) -> bool:
        """Check per-IP rate limit."""
        ip_key = f"ip:{ip}"
        return await self._check_rate_limit_window(ip_key, config)
    
    async def _check_rate_limit_window(self, key: str, config: Dict[str, int]) -> bool:
        """Check rate limit using sliding window algorithm."""
        try:
            if self.redis_client:
                return await self._check_redis_rate_limit(key, config)
            else:
                return await self._check_memory_rate_limit(key, config)
        except Exception as e:
            logger.error(f"Rate limit window check error for {key}: {str(e)}")
            return True  # Allow request on error
    
    async def _check_redis_rate_limit(self, key: str, config: Dict[str, int]) -> bool:
        """Check rate limit using Redis."""
        try:
            now = time.time()
            window_size = 60  # 1 minute window
            requests_per_minute = config["requests_per_minute"]
            
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window_size)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window_size)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return current_requests < requests_per_minute
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {str(e)}")
            return True
    
    async def _check_memory_rate_limit(self, key: str, config: Dict[str, int]) -> bool:
        """Check rate limit using in-memory storage."""
        try:
            now = time.time()
            window_size = 60  # 1 minute window
            requests_per_minute = config["requests_per_minute"]
            
            # Get request history for this key
            request_history = self.memory_store[key]
            
            # Remove expired entries
            while request_history and request_history[0] < now - window_size:
                request_history.popleft()
            
            # Check if under limit
            if len(request_history) >= requests_per_minute:
                return False
            
            # Add current request
            request_history.append(now)
            
            return True
            
        except Exception as e:
            logger.error(f"Memory rate limit check error: {str(e)}")
            return True
    
    def _get_rate_limit(self, request: Request) -> int:
        """Get rate limit for request."""
        endpoint_config = self._get_endpoint_config(request.url.path)
        return endpoint_config["requests_per_minute"]
    
    def _add_rate_limit_headers(self, response, request: Request, client_id: str) -> None:
        """Add rate limit headers to response."""
        try:
            endpoint_config = self._get_endpoint_config(request.url.path)
            limit = endpoint_config["requests_per_minute"]
            
            # Calculate remaining requests
            remaining = max(0, limit - self._get_current_requests(client_id))
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {str(e)}")
    
    def _get_current_requests(self, client_id: str) -> int:
        """Get current request count for client."""
        try:
            if self.redis_client:
                return self.redis_client.zcard(client_id)
            else:
                now = time.time()
                request_history = self.memory_store[client_id]
                # Remove expired entries
                while request_history and request_history[0] < now - 60:
                    request_history.popleft()
                return len(request_history)
        except Exception as e:
            logger.error(f"Error getting current requests: {str(e)}")
            return 0

class BurstLimitMiddleware:
    """Burst limiting middleware for handling traffic spikes."""
    
    def __init__(self):
        self.settings = get_settings()
        self.burst_limits = {
            "global": 2000,
            "per_user": 200,
            "per_ip": 1000
        }
        self.burst_windows = defaultdict(lambda: deque())
    
    async def __call__(self, request: Request, call_next):
        """Process burst limiting for each request."""
        try:
            # Skip burst limiting for health checks
            if self._is_health_endpoint(request.url.path):
                return await call_next(request)
            
            # Get client identifier
            client_id = self._get_client_id(request)
            
            # Check burst limits
            if not await self._check_burst_limit(client_id):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Burst limit exceeded",
                        "message": "Too many requests in short time. Please slow down.",
                        "retry_after": 10
                    },
                    headers={"Retry-After": "10"}
                )
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Burst limiting error: {str(e)}")
            return await call_next(request)
    
    def _is_health_endpoint(self, path: str) -> bool:
        """Check if endpoint is a health check."""
        health_paths = ["/health", "/health/detailed", "/ready", "/metrics"]
        return any(path.startswith(health_path) for health_path in health_paths)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        user = getattr(request.state, 'user', None)
        if user:
            return f"user:{user.id}"
        
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    async def _check_burst_limit(self, client_id: str) -> bool:
        """Check burst limit for client."""
        try:
            now = time.time()
            burst_window = 10  # 10 seconds
            burst_limit = self.burst_limits["per_user"]  # Default to per-user limit
            
            # Get burst history
            burst_history = self.burst_windows[client_id]
            
            # Remove expired entries
            while burst_history and burst_history[0] < now - burst_window:
                burst_history.popleft()
            
            # Check if under burst limit
            if len(burst_history) >= burst_limit:
                return False
            
            # Add current request
            burst_history.append(now)
            
            return True
            
        except Exception as e:
            logger.error(f"Burst limit check error: {str(e)}")
            return True
