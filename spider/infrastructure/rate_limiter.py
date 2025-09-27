"""Rate limiting infrastructure for SPIDER framework."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..core.exceptions import SpiderError
from ..core.logger import get_logger


class RateLimitStrategy(Enum):
    """Rate limiting strategy enumeration."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    window_size: int = 60  # seconds
    enabled: bool = True


class BaseRateLimiter(ABC):
    """Base class for rate limiters."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission to make a request.
        
        Args:
            key: Rate limiting key (e.g., domain, IP)
            
        Returns:
            True if request is allowed
        """
        pass
    
    @abstractmethod
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time until next request is allowed.
        
        Args:
            key: Rate limiting key
            
        Returns:
            Wait time in seconds
        """
        pass


class TokenBucketRateLimiter(BaseRateLimiter):
    """Token bucket rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize token bucket rate limiter."""
        super().__init__(config)
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.tokens_per_second = config.requests_per_minute / 60.0
        self.max_tokens = config.burst_size
    
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission using token bucket algorithm."""
        if not self.config.enabled:
            return True
        
        current_time = time.time()
        bucket = self._get_bucket(key, current_time)
        
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            bucket['last_update'] = current_time
            return True
        
        return False
    
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time until next token is available."""
        if not self.config.enabled:
            return 0.0
        
        current_time = time.time()
        bucket = self._get_bucket(key, current_time)
        
        if bucket['tokens'] >= 1:
            return 0.0
        
        # Calculate time until next token
        tokens_needed = 1 - bucket['tokens']
        return tokens_needed / self.tokens_per_second
    
    def _get_bucket(self, key: str, current_time: float) -> Dict[str, Any]:
        """Get or create bucket for key."""
        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': self.max_tokens,
                'last_update': current_time
            }
        
        bucket = self.buckets[key]
        
        # Add tokens based on time elapsed
        time_elapsed = current_time - bucket['last_update']
        tokens_to_add = time_elapsed * self.tokens_per_second
        bucket['tokens'] = min(self.max_tokens, bucket['tokens'] + tokens_to_add)
        
        return bucket


class SlidingWindowRateLimiter(BaseRateLimiter):
    """Sliding window rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize sliding window rate limiter."""
        super().__init__(config)
        self.windows: Dict[str, list] = {}
        self.window_size = config.window_size
        self.max_requests = config.requests_per_minute
    
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission using sliding window algorithm."""
        if not self.config.enabled:
            return True
        
        current_time = time.time()
        window = self._get_window(key, current_time)
        
        if len(window) < self.max_requests:
            window.append(current_time)
            return True
        
        return False
    
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time until window slides enough."""
        if not self.config.enabled:
            return 0.0
        
        current_time = time.time()
        window = self._get_window(key, current_time)
        
        if len(window) < self.max_requests:
            return 0.0
        
        # Find oldest request in window
        oldest_request = min(window)
        return (oldest_request + self.window_size) - current_time
    
    def _get_window(self, key: str, current_time: float) -> list:
        """Get or create sliding window for key."""
        if key not in self.windows:
            self.windows[key] = []
        
        window = self.windows[key]
        
        # Remove old requests outside window
        cutoff_time = current_time - self.window_size
        self.windows[key] = [req_time for req_time in window if req_time > cutoff_time]
        
        return self.windows[key]


class FixedWindowRateLimiter(BaseRateLimiter):
    """Fixed window rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize fixed window rate limiter."""
        super().__init__(config)
        self.windows: Dict[str, Dict[str, Any]] = {}
        self.window_size = config.window_size
        self.max_requests = config.requests_per_minute
    
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission using fixed window algorithm."""
        if not self.config.enabled:
            return True
        
        current_time = time.time()
        window_start = int(current_time // self.window_size) * self.window_size
        
        if key not in self.windows:
            self.windows[key] = {
                'window_start': window_start,
                'count': 0
            }
        
        window = self.windows[key]
        
        # Reset window if needed
        if window['window_start'] != window_start:
            window['window_start'] = window_start
            window['count'] = 0
        
        if window['count'] < self.max_requests:
            window['count'] += 1
            return True
        
        return False
    
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time until next window starts."""
        if not self.config.enabled:
            return 0.0
        
        current_time = time.time()
        window_start = int(current_time // self.window_size) * self.window_size
        next_window_start = window_start + self.window_size
        
        return next_window_start - current_time


class AdaptiveRateLimiter(BaseRateLimiter):
    """Adaptive rate limiter that adjusts based on response times and errors."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize adaptive rate limiter."""
        super().__init__(config)
        self.base_limiter = TokenBucketRateLimiter(config)
        self.adaptive_config = config
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.min_rate = 1  # Minimum requests per minute
        self.max_rate = config.requests_per_minute
        self.current_rate = config.requests_per_minute
        self.adaptation_factor = 0.1
    
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission with adaptive rate limiting."""
        if not self.config.enabled:
            return True
        
        # Update rate based on recent performance
        await self._adapt_rate(key)
        
        # Use base limiter with current rate
        return await self.base_limiter.acquire(key)
    
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time with adaptive rate limiting."""
        if not self.config.enabled:
            return 0.0
        
        await self._adapt_rate(key)
        return await self.base_limiter.get_wait_time(key)
    
    async def record_response(self, key: str, response_time: float, success: bool) -> None:
        """Record response metrics for adaptive adjustment.
        
        Args:
            key: Rate limiting key
            response_time: Response time in seconds
            success: Whether request was successful
        """
        if key not in self.metrics:
            self.metrics[key] = {
                'response_times': [],
                'success_rate': 1.0,
                'last_update': time.time()
            }
        
        metrics = self.metrics[key]
        metrics['response_times'].append(response_time)
        metrics['last_update'] = time.time()
        
        # Keep only recent metrics (last 100 requests)
        if len(metrics['response_times']) > 100:
            metrics['response_times'] = metrics['response_times'][-100:]
        
        # Update success rate
        if success:
            metrics['success_rate'] = min(1.0, metrics['success_rate'] + 0.01)
        else:
            metrics['success_rate'] = max(0.0, metrics['success_rate'] - 0.05)
    
    async def _adapt_rate(self, key: str) -> None:
        """Adapt rate based on recent performance."""
        if key not in self.metrics:
            return
        
        metrics = self.metrics[key]
        current_time = time.time()
        
        # Only adapt if we have recent data
        if current_time - metrics['last_update'] > 60:  # 1 minute
            return
        
        # Calculate average response time
        if not metrics['response_times']:
            return
        
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
        success_rate = metrics['success_rate']
        
        # Adjust rate based on performance
        if avg_response_time > 5.0 or success_rate < 0.8:
            # Slow down if response time is high or success rate is low
            self.current_rate = max(self.min_rate, self.current_rate * (1 - self.adaptation_factor))
        elif avg_response_time < 1.0 and success_rate > 0.95:
            # Speed up if response time is low and success rate is high
            self.current_rate = min(self.max_rate, self.current_rate * (1 + self.adaptation_factor))
        
        # Update base limiter rate
        self.base_limiter.tokens_per_second = self.current_rate / 60.0


class RateLimiter:
    """Main rate limiter class."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        
        # Create appropriate limiter based on strategy
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.limiter = TokenBucketRateLimiter(config)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.limiter = SlidingWindowRateLimiter(config)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            self.limiter = FixedWindowRateLimiter(config)
        else:
            self.limiter = TokenBucketRateLimiter(config)
    
    async def acquire(self, key: str = "default") -> bool:
        """Acquire permission to make a request."""
        return await self.limiter.acquire(key)
    
    async def get_wait_time(self, key: str = "default") -> float:
        """Get wait time until next request is allowed."""
        return await self.limiter.get_wait_time(key)
    
    async def record_response(self, key: str, response_time: float, success: bool) -> None:
        """Record response metrics for adaptive adjustment."""
        if hasattr(self.limiter, 'record_response'):
            await self.limiter.record_response(key, response_time, success)
    
    async def wait_if_needed(self, key: str = "default") -> None:
        """Wait if rate limit is exceeded."""
        wait_time = await self.get_wait_time(key)
        if wait_time > 0:
            self.logger.info(f"Rate limit exceeded for {key}, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
    
    def get_stats(self, key: str = "default") -> Dict[str, Any]:
        """Get rate limiting statistics."""
        stats = {
            'strategy': self.config.strategy.value,
            'enabled': self.config.enabled,
            'requests_per_minute': self.config.requests_per_minute,
            'burst_size': self.config.burst_size
        }
        
        # Add limiter-specific stats
        if hasattr(self.limiter, 'buckets') and key in self.limiter.buckets:
            bucket = self.limiter.buckets[key]
            stats['tokens_available'] = bucket['tokens']
            stats['last_update'] = bucket['last_update']
        
        return stats
