"""Advanced caching strategies for SPIDER framework."""

import asyncio
import time
import hashlib
import json
import pickle
import os
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import OrderedDict, defaultdict
import weakref

from ..core.exceptions import SpiderError, StorageError
from ..core.logger import get_logger


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based
    RANDOM = "random"  # Random eviction


class CacheLevel(Enum):
    """Cache levels."""
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    DISTRIBUTED = "distributed"


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size: int = 1000
    ttl: int = 3600  # seconds
    strategy: CacheStrategy = CacheStrategy.LRU
    level: CacheLevel = CacheLevel.MEMORY
    compression: bool = False
    serialization: str = "pickle"  # "pickle", "json"
    namespace: str = "default"
    enable_stats: bool = True


@dataclass
class CacheEntry:
    """Cache entry."""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    size: int = 0
    ttl: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    memory_usage: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0


class BaseCache:
    """Base cache implementation."""
    
    def __init__(self, config: CacheConfig):
        """Initialize base cache.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self._entries: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._access_counts: Dict[str, int] = defaultdict(int)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        with self._lock:
            if key not in self._entries:
                self._stats.misses += 1
                return None
            
            entry = self._entries[key]
            
            # Check TTL
            if entry.ttl and time.time() - entry.created_at > entry.ttl:
                await self._evict(key)
                self._stats.misses += 1
                return None
            
            # Update access info
            entry.accessed_at = time.time()
            entry.access_count += 1
            self._access_counts[key] += 1
            
            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.hits += 1
            self._update_hit_rate()
            
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Optional tags
            metadata: Optional metadata
        """
        with self._lock:
            # Check if we need to evict
            if len(self._entries) >= self.config.max_size:
                await self._evict_entries()
            
            # Calculate size
            size = self._calculate_size(value)
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                size=size,
                ttl=ttl or self.config.ttl,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self._entries[key] = entry
            self._access_order.append(key)
            self._access_counts[key] = 0
            self._stats.size = len(self._entries)
            self._stats.memory_usage += size
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key not in self._entries:
                return False
            
            await self._evict(key)
            return True
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._entries.clear()
            self._access_order.clear()
            self._access_counts.clear()
            self._stats.size = 0
            self._stats.memory_usage = 0
    
    async def _evict(self, key: str) -> None:
        """Evict a specific key.
        
        Args:
            key: Key to evict
        """
        if key in self._entries:
            entry = self._entries[key]
            self._stats.memory_usage -= entry.size
            del self._entries[key]
            
            if key in self._access_order:
                self._access_order.remove(key)
            
            if key in self._access_counts:
                del self._access_counts[key]
            
            self._stats.evictions += 1
            self._stats.size = len(self._entries)
    
    async def _evict_entries(self) -> None:
        """Evict entries based on strategy."""
        if not self._entries:
            return
        
        if self.config.strategy == CacheStrategy.LRU:
            await self._evict_lru()
        elif self.config.strategy == CacheStrategy.LFU:
            await self._evict_lfu()
        elif self.config.strategy == CacheStrategy.TTL:
            await self._evict_ttl()
        elif self.config.strategy == CacheStrategy.SIZE:
            await self._evict_size()
        elif self.config.strategy == CacheStrategy.RANDOM:
            await self._evict_random()
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        # Remove oldest entries until we have space
        while len(self._entries) >= self.config.max_size and self._access_order:
            oldest_key = self._access_order[0]
            await self._evict(oldest_key)
    
    async def _evict_lfu(self) -> None:
        """Evict least frequently used entries."""
        # Sort by access count and remove least frequent
        sorted_keys = sorted(
            self._access_counts.items(),
            key=lambda x: x[1]
        )
        
        for key, _ in sorted_keys:
            if len(self._entries) < self.config.max_size:
                break
            await self._evict(key)
    
    async def _evict_ttl(self) -> None:
        """Evict expired entries."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._entries.items():
            if entry.ttl and current_time - entry.created_at > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self._evict(key)
    
    async def _evict_size(self) -> None:
        """Evict largest entries."""
        # Sort by size and remove largest
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].size,
            reverse=True
        )
        
        for key, _ in sorted_entries:
            if len(self._entries) < self.config.max_size:
                break
            await self._evict(key)
    
    async def _evict_random(self) -> None:
        """Evict random entries."""
        import random
        
        while len(self._entries) >= self.config.max_size and self._entries:
            key = random.choice(list(self._entries.keys()))
            await self._evict(key)
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate size of value in bytes."""
        try:
            if self.config.serialization == "pickle":
                return len(pickle.dumps(value))
            elif self.config.serialization == "json":
                return len(json.dumps(value).encode('utf-8'))
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 0
    
    def _update_hit_rate(self) -> None:
        """Update hit rate statistics."""
        total = self._stats.hits + self._stats.misses
        if total > 0:
            self._stats.hit_rate = self._stats.hits / total
            self._stats.miss_rate = self._stats.misses / total
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=self._stats.size,
                memory_usage=self._stats.memory_usage,
                hit_rate=self._stats.hit_rate,
                miss_rate=self._stats.miss_rate
            )
    
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get cache keys.
        
        Args:
            pattern: Optional pattern to filter keys
            
        Returns:
            List of keys
        """
        with self._lock:
            keys = list(self._entries.keys())
            
            if pattern:
                import fnmatch
                keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
            
            return keys
    
    def get_entries_by_tag(self, tag: str) -> List[str]:
        """Get keys by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of keys with the tag
        """
        with self._lock:
            return [
                key for key, entry in self._entries.items()
                if tag in entry.tags
            ]


class MemoryCache(BaseCache):
    """In-memory cache implementation."""
    
    def __init__(self, config: CacheConfig):
        """Initialize memory cache.
        
        Args:
            config: Cache configuration
        """
        super().__init__(config)
        self.logger.info(f"Initialized memory cache with {config.max_size} max entries")


class DiskCache(BaseCache):
    """Disk-based cache implementation."""
    
    def __init__(self, config: CacheConfig, cache_dir: str = "cache"):
        """Initialize disk cache.
        
        Args:
            config: Cache configuration
            cache_dir: Cache directory path
        """
        super().__init__(config)
        self.cache_dir = cache_dir
        self.logger.info(f"Initialized disk cache in {cache_dir}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        try:
            file_path = self._get_file_path(key)
            if not os.path.exists(file_path):
                self._stats.misses += 1
                return None
            
            with open(file_path, 'rb') as f:
                if self.config.serialization == "pickle":
                    value = pickle.load(f)
                else:
                    value = json.load(f)
            
            # Update access info
            self._access_counts[key] += 1
            self._stats.hits += 1
            self._update_hit_rate()
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error reading from disk cache: {e}")
            self._stats.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value in disk cache."""
        try:
            file_path = self._get_file_path(key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                if self.config.serialization == "pickle":
                    pickle.dump(value, f)
                else:
                    f.write(json.dumps(value).encode('utf-8'))
            
            # Update stats
            self._stats.size += 1
            
        except Exception as e:
            self.logger.error(f"Error writing to disk cache: {e}")
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for key."""
        # Create a safe filename from key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")


class RedisCache(BaseCache):
    """Redis-based cache implementation."""
    
    def __init__(self, config: CacheConfig, redis_client=None):
        """Initialize Redis cache.
        
        Args:
            config: Cache configuration
            redis_client: Redis client instance
        """
        super().__init__(config)
        self.redis_client = redis_client
        self.logger.info("Initialized Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            if not self.redis_client:
                return None
            
            full_key = f"{self.config.namespace}:{key}"
            value = await self.redis_client.get(full_key)
            
            if value is None:
                self._stats.misses += 1
                return None
            
            # Deserialize
            if self.config.serialization == "pickle":
                return pickle.loads(value)
            else:
                return json.loads(value)
                
        except Exception as e:
            self.logger.error(f"Error reading from Redis cache: {e}")
            self._stats.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value in Redis cache."""
        try:
            if not self.redis_client:
                return
            
            full_key = f"{self.config.namespace}:{key}"
            
            # Serialize
            if self.config.serialization == "pickle":
                serialized = pickle.dumps(value)
            else:
                serialized = json.dumps(value).encode('utf-8')
            
            # Set with TTL
            ttl = ttl or self.config.ttl
            await self.redis_client.setex(full_key, ttl, serialized)
            
            self._stats.size += 1
            
        except Exception as e:
            self.logger.error(f"Error writing to Redis cache: {e}")


class CacheManager:
    """Manages multiple cache levels and strategies."""
    
    def __init__(self):
        """Initialize cache manager."""
        self.logger = get_logger(self.__class__.__name__)
        self._caches: Dict[str, BaseCache] = {}
        self._default_cache: Optional[str] = None
    
    def add_cache(self, name: str, cache: BaseCache, set_default: bool = False) -> None:
        """Add a cache instance.
        
        Args:
            name: Cache name
            cache: Cache instance
            set_default: Whether to set as default cache
        """
        self._caches[name] = cache
        if set_default or not self._default_cache:
            self._default_cache = name
        self.logger.info(f"Added cache: {name}")
    
    def get_cache(self, name: str) -> Optional[BaseCache]:
        """Get cache instance.
        
        Args:
            name: Cache name
            
        Returns:
            Cache instance or None
        """
        return self._caches.get(name)
    
    async def get(
        self, 
        key: str, 
        cache_name: Optional[str] = None
    ) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            cache_name: Specific cache name (uses default if None)
            
        Returns:
            Cached value or None
        """
        cache_name = cache_name or self._default_cache
        if not cache_name or cache_name not in self._caches:
            return None
        
        cache = self._caches[cache_name]
        return await cache.get(key)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        cache_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_name: Specific cache name (uses default if None)
            **kwargs: Additional cache parameters
        """
        cache_name = cache_name or self._default_cache
        if not cache_name or cache_name not in self._caches:
            return
        
        cache = self._caches[cache_name]
        await cache.set(key, value, **kwargs)
    
    async def delete(
        self, 
        key: str, 
        cache_name: Optional[str] = None
    ) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            cache_name: Specific cache name (uses default if None)
            
        Returns:
            True if deleted
        """
        cache_name = cache_name or self._default_cache
        if not cache_name or cache_name not in self._caches:
            return False
        
        cache = self._caches[cache_name]
        return await cache.delete(key)
    
    async def clear(self, cache_name: Optional[str] = None) -> None:
        """Clear cache.
        
        Args:
            cache_name: Specific cache name (clears all if None)
        """
        if cache_name:
            if cache_name in self._caches:
                await self._caches[cache_name].clear()
        else:
            for cache in self._caches.values():
                await cache.clear()
    
    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all caches.
        
        Returns:
            Cache statistics
        """
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }
    
    def cleanup(self) -> None:
        """Cleanup cache manager."""
        for cache in self._caches.values():
            if hasattr(cache, 'cleanup'):
                cache.cleanup()
        self._caches.clear()
        self.logger.info("Cache manager cleaned up")


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    cache_name: Optional[str] = None,
    ttl: Optional[int] = None,
    tags: Optional[List[str]] = None
):
    """Decorator for caching function results.
    
    Args:
        cache_name: Cache name to use
        ttl: Time to live in seconds
        tags: Optional tags
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            # This would need access to a global cache manager
            # For now, we'll just call the function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
