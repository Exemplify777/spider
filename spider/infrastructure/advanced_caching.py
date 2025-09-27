"""
Advanced Caching Module for SPIDER Framework

This module provides advanced caching capabilities including Redis Cluster,
Memcached integration, distributed caching, and intelligent cache management.

Author: SPIDER Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import random

try:
    import redis
    import redis.cluster
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    import memcache
    MEMCACHE_AVAILABLE = True
except ImportError:
    MEMCACHE_AVAILABLE = False
    memcache = None

from ..core.exceptions import SpiderError
from ..core.logger import get_logger

logger = get_logger(__name__)


class CacheType(Enum):
    """Types of cache backends."""
    REDIS = "redis"
    REDIS_CLUSTER = "redis_cluster"
    MEMCACHE = "memcache"
    MEMORY = "memory"
    HYBRID = "hybrid"


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    RANDOM = "random"
    FIFO = "fifo"  # First In, First Out


@dataclass
class CacheConfig:
    """Configuration for cache backends."""
    cache_type: CacheType = CacheType.REDIS
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 10
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    decode_responses: bool = True
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    default_ttl: int = 3600
    max_memory: Optional[str] = None
    cluster_nodes: List[Dict[str, Any]] = field(default_factory=list)
    memcache_servers: List[str] = field(default_factory=lambda: ["127.0.0.1:11211"])


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    key_count: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    last_updated: float = 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    ttl: int
    created_at: float
    accessed_at: float
    access_count: int = 0
    size: int = 0


class BaseCacheBackend:
    """Base class for cache backends."""
    
    def __init__(self, config: CacheConfig):
        """Initialize cache backend."""
        self.config = config
        self.stats = CacheStats()
        self._lock = threading.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        raise NotImplementedError
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.stats.hits + self.stats.misses
            if total_requests > 0:
                self.stats.hit_rate = self.stats.hits / total_requests
                self.stats.miss_rate = self.stats.misses / total_requests
            self.stats.last_updated = time.time()
            return self.stats
    
    def _update_stats(self, operation: str):
        """Update cache statistics."""
        with self._lock:
            if operation == "hit":
                self.stats.hits += 1
            elif operation == "miss":
                self.stats.misses += 1
            elif operation == "set":
                self.stats.sets += 1
            elif operation == "delete":
                self.stats.deletes += 1
            elif operation == "eviction":
                self.stats.evictions += 1


class RedisCacheBackend(BaseCacheBackend):
    """Redis cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize Redis cache backend."""
        super().__init__(config)
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            if not REDIS_AVAILABLE:
                raise SpiderError("Redis not available. Install redis-py package.")
            
            self.client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise SpiderError(f"Redis connection failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            value = self.client.get(key)
            if value is not None:
                self._update_stats("hit")
                return json.loads(value) if isinstance(value, str) else value
            else:
                self._update_stats("miss")
                return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._update_stats("miss")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis."""
        try:
            ttl = ttl or self.config.default_ttl
            serialized_value = json.dumps(value) if not isinstance(value, (str, int, float)) else value
            
            result = self.client.setex(key, ttl, serialized_value)
            if result:
                self._update_stats("set")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        try:
            result = self.client.delete(key)
            if result:
                self._update_stats("delete")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis entries."""
        try:
            result = self.client.flushdb()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern from Redis."""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []


class RedisClusterCacheBackend(BaseCacheBackend):
    """Redis Cluster cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize Redis Cluster cache backend."""
        super().__init__(config)
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis Cluster."""
        try:
            if not REDIS_AVAILABLE:
                raise SpiderError("Redis not available. Install redis-py package.")
            
            if not self.config.cluster_nodes:
                raise SpiderError("Redis Cluster nodes not configured")
            
            startup_nodes = [
                {"host": node["host"], "port": node["port"]} 
                for node in self.config.cluster_nodes
            ]
            
            self.client = redis.cluster.RedisCluster(
                startup_nodes=startup_nodes,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses,
                skip_full_coverage_check=True
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis Cluster with {len(startup_nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis Cluster: {e}")
            raise SpiderError(f"Redis Cluster connection failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis Cluster."""
        try:
            value = self.client.get(key)
            if value is not None:
                self._update_stats("hit")
                return json.loads(value) if isinstance(value, str) else value
            else:
                self._update_stats("miss")
                return None
        except Exception as e:
            logger.error(f"Redis Cluster get error for key {key}: {e}")
            self._update_stats("miss")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis Cluster."""
        try:
            ttl = ttl or self.config.default_ttl
            serialized_value = json.dumps(value) if not isinstance(value, (str, int, float)) else value
            
            result = self.client.setex(key, ttl, serialized_value)
            if result:
                self._update_stats("set")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis Cluster set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis Cluster."""
        try:
            result = self.client.delete(key)
            if result:
                self._update_stats("delete")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis Cluster delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis Cluster."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis Cluster exists error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis Cluster entries."""
        try:
            result = self.client.flushall()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis Cluster clear error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern from Redis Cluster."""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis Cluster keys error for pattern {pattern}: {e}")
            return []


class MemcacheBackend(BaseCacheBackend):
    """Memcached cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize Memcached cache backend."""
        super().__init__(config)
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Memcached."""
        try:
            if not MEMCACHE_AVAILABLE:
                raise SpiderError("Memcached not available. Install python-memcached package.")
            
            self.client = memcache.Client(
                self.config.memcache_servers,
                debug=0
            )
            
            # Test connection
            self.client.get_stats()
            logger.info(f"Connected to Memcached at {self.config.memcache_servers}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Memcached: {e}")
            raise SpiderError(f"Memcached connection failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Memcached."""
        try:
            value = self.client.get(key)
            if value is not None:
                self._update_stats("hit")
                return value
            else:
                self._update_stats("miss")
                return None
        except Exception as e:
            logger.error(f"Memcached get error for key {key}: {e}")
            self._update_stats("miss")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Memcached."""
        try:
            ttl = ttl or self.config.default_ttl
            result = self.client.set(key, value, time=ttl)
            if result:
                self._update_stats("set")
            return bool(result)
        except Exception as e:
            logger.error(f"Memcached set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Memcached."""
        try:
            result = self.client.delete(key)
            if result:
                self._update_stats("delete")
            return bool(result)
        except Exception as e:
            logger.error(f"Memcached delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Memcached."""
        try:
            return self.client.get(key) is not None
        except Exception as e:
            logger.error(f"Memcached exists error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Memcached entries."""
        try:
            result = self.client.flush_all()
            return bool(result)
        except Exception as e:
            logger.error(f"Memcached clear error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern from Memcached."""
        # Memcached doesn't support pattern matching
        return []


class MemoryCacheBackend(BaseCacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize memory cache backend."""
        super().__init__(config)
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._max_size = 10000  # Default max size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        try:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check TTL
                if time.time() - entry.created_at > entry.ttl:
                    await self.delete(key)
                    self._update_stats("miss")
                    return None
                
                # Update access info
                entry.accessed_at = time.time()
                entry.access_count += 1
                
                # Update access order for LRU
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                
                self._update_stats("hit")
                return entry.value
            else:
                self._update_stats("miss")
                return None
        except Exception as e:
            logger.error(f"Memory cache get error for key {key}: {e}")
            self._update_stats("miss")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        try:
            ttl = ttl or self.config.default_ttl
            
            # Check if we need to evict
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict()
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                size=len(str(value))
            )
            
            self._cache[key] = entry
            self._access_order.append(key)
            
            self._update_stats("set")
            return True
        except Exception as e:
            logger.error(f"Memory cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        try:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._update_stats("delete")
                return True
            return False
        except Exception as e:
            logger.error(f"Memory cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        return key in self._cache
    
    async def clear(self) -> bool:
        """Clear all memory cache entries."""
        try:
            self._cache.clear()
            self._access_order.clear()
            return True
        except Exception as e:
            logger.error(f"Memory cache clear error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern from memory cache."""
        if pattern == "*":
            return list(self._cache.keys())
        
        # Simple pattern matching
        import fnmatch
        return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def _evict(self):
        """Evict entries based on policy."""
        if not self._cache:
            return
        
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used
            if self._access_order:
                key_to_remove = self._access_order[0]
                await self.delete(key_to_remove)
                self._update_stats("eviction")
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            key_to_remove = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            await self.delete(key_to_remove)
            self._update_stats("eviction")
        elif self.config.eviction_policy == EvictionPolicy.RANDOM:
            # Remove random entry
            key_to_remove = random.choice(list(self._cache.keys()))
            await self.delete(key_to_remove)
            self._update_stats("eviction")


class HybridCacheBackend(BaseCacheBackend):
    """Hybrid cache backend combining multiple backends."""
    
    def __init__(self, config: CacheConfig, backends: List[BaseCacheBackend]):
        """Initialize hybrid cache backend."""
        super().__init__(config)
        self.backends = backends
        self.primary_backend = backends[0] if backends else None
        self.fallback_backends = backends[1:] if len(backends) > 1 else []
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from hybrid cache."""
        # Try primary backend first
        if self.primary_backend:
            value = await self.primary_backend.get(key)
            if value is not None:
                self._update_stats("hit")
                return value
        
        # Try fallback backends
        for backend in self.fallback_backends:
            value = await backend.get(key)
            if value is not None:
                # Populate primary backend
                if self.primary_backend:
                    await self.primary_backend.set(key, value)
                self._update_stats("hit")
                return value
        
        self._update_stats("miss")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in hybrid cache."""
        success = True
        
        # Set in all backends
        for backend in self.backends:
            result = await backend.set(key, value, ttl)
            if not result:
                success = False
        
        if success:
            self._update_stats("set")
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete value from hybrid cache."""
        success = True
        
        # Delete from all backends
        for backend in self.backends:
            result = await backend.delete(key)
            if not result:
                success = False
        
        if success:
            self._update_stats("delete")
        return success
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in hybrid cache."""
        # Check primary backend first
        if self.primary_backend and await self.primary_backend.exists(key):
            return True
        
        # Check fallback backends
        for backend in self.fallback_backends:
            if await backend.exists(key):
                return True
        
        return False
    
    async def clear(self) -> bool:
        """Clear all hybrid cache entries."""
        success = True
        
        # Clear all backends
        for backend in self.backends:
            result = await backend.clear()
            if not result:
                success = False
        
        return success
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern from hybrid cache."""
        all_keys = set()
        
        # Collect keys from all backends
        for backend in self.backends:
            keys = await backend.keys(pattern)
            all_keys.update(keys)
        
        return list(all_keys)


class AdvancedCacheManager:
    """Advanced cache manager with multiple backends and intelligent management."""
    
    def __init__(self, config: CacheConfig):
        """Initialize advanced cache manager."""
        self.config = config
        self.backend: BaseCacheBackend = self._create_backend()
        self._warmup_tasks: List[Callable] = []
        self._lock = threading.Lock()
    
    def _create_backend(self) -> BaseCacheBackend:
        """Create cache backend based on configuration."""
        if self.config.cache_type == CacheType.REDIS:
            return RedisCacheBackend(self.config)
        elif self.config.cache_type == CacheType.REDIS_CLUSTER:
            return RedisClusterCacheBackend(self.config)
        elif self.config.cache_type == CacheType.MEMCACHE:
            return MemcacheBackend(self.config)
        elif self.config.cache_type == CacheType.MEMORY:
            return MemoryCacheBackend(self.config)
        elif self.config.cache_type == CacheType.HYBRID:
            # Create hybrid backend with multiple backends
            backends = []
            
            # Add Redis as primary
            redis_config = CacheConfig(
                cache_type=CacheType.REDIS,
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db
            )
            backends.append(RedisCacheBackend(redis_config))
            
            # Add Memcached as fallback
            memcache_config = CacheConfig(
                cache_type=CacheType.MEMCACHE,
                memcache_servers=self.config.memcache_servers
            )
            backends.append(MemcacheBackend(memcache_config))
            
            return HybridCacheBackend(self.config, backends)
        else:
            raise SpiderError(f"Unsupported cache type: {self.config.cache_type}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self.backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        return await self.backend.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self.backend.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self.backend.exists(key)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        return await self.backend.clear()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        return await self.backend.keys(pattern)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.backend.get_stats()
    
    def add_warmup_task(self, task: Callable):
        """Add cache warmup task."""
        self._warmup_tasks.append(task)
    
    async def warmup(self):
        """Execute cache warmup tasks."""
        for task in self._warmup_tasks:
            try:
                await task()
            except Exception as e:
                logger.error(f"Cache warmup task failed: {e}")
    
    async def cleanup(self):
        """Cleanup cache resources."""
        if hasattr(self.backend, 'cleanup'):
            await self.backend.cleanup()


# Global cache manager instance
_cache_manager: Optional[AdvancedCacheManager] = None


def get_cache_manager() -> AdvancedCacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        # Use memory cache by default to avoid Redis dependency
        config = CacheConfig(cache_type=CacheType.MEMORY)
        _cache_manager = AdvancedCacheManager(config)
    return _cache_manager


def cleanup_cache_resources():
    """Cleanup global cache resources."""
    global _cache_manager
    if _cache_manager is not None:
        try:
            # Try to run cleanup in existing event loop
            loop = asyncio.get_running_loop()
            asyncio.create_task(_cache_manager.cleanup())
        except RuntimeError:
            # No running event loop, create a new one
            asyncio.run(_cache_manager.cleanup())
        _cache_manager = None
