"""Tests for advanced caching module."""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock

from spider.infrastructure.advanced_caching import (
    CacheType, EvictionPolicy, CacheConfig, CacheStats, CacheEntry,
    BaseCacheBackend, RedisCacheBackend, RedisClusterCacheBackend,
    MemcacheBackend, MemoryCacheBackend, HybridCacheBackend,
    AdvancedCacheManager, get_cache_manager, cleanup_cache_resources
)


class TestCacheConfig:
    """Test cache configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CacheConfig()
        assert config.cache_type == CacheType.REDIS
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.eviction_policy == EvictionPolicy.LRU
        assert config.default_ttl == 3600
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CacheConfig(
            cache_type=CacheType.MEMCACHE,
            host="test-host",
            port=11211,
            eviction_policy=EvictionPolicy.LFU,
            default_ttl=7200
        )
        assert config.cache_type == CacheType.MEMCACHE
        assert config.host == "test-host"
        assert config.port == 11211
        assert config.eviction_policy == EvictionPolicy.LFU
        assert config.default_ttl == 7200


class TestCacheStats:
    """Test cache statistics."""
    
    def test_stats_creation(self):
        """Test cache stats creation."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.evictions == 0
        assert stats.hit_rate == 0.0
        assert stats.miss_rate == 0.0
    
    def test_stats_update(self):
        """Test stats update."""
        stats = CacheStats()
        stats.hits = 10
        stats.misses = 5
        stats.sets = 15
        stats.deletes = 2
        stats.evictions = 1
        
        # Calculate rates
        total = stats.hits + stats.misses
        stats.hit_rate = stats.hits / total if total > 0 else 0.0
        stats.miss_rate = stats.misses / total if total > 0 else 0.0
        
        assert stats.hit_rate == 10 / 15
        assert stats.miss_rate == 5 / 15


class TestCacheEntry:
    """Test cache entry."""
    
    def test_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl=3600,
            created_at=time.time(),
            accessed_at=time.time()
        )
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 3600
        assert entry.access_count == 0
        assert entry.size == 0


class TestMemoryCacheBackend:
    """Test memory cache backend."""
    
    def test_initialization(self):
        """Test memory cache initialization."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        assert backend.config.cache_type == CacheType.MEMORY
        assert len(backend._cache) == 0
    
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test set and get operations."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set value
        result = await backend.set("test_key", "test_value", 3600)
        assert result is True
        
        # Get value
        value = await backend.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        value = await backend.get("nonexistent_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set value
        await backend.set("test_key", "test_value")
        
        # Delete value
        result = await backend.delete("test_key")
        assert result is True
        
        # Verify deletion
        value = await backend.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test exists operation."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Key doesn't exist
        assert await backend.exists("test_key") is False
        
        # Set key
        await backend.set("test_key", "test_value")
        
        # Key exists
        assert await backend.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set some values
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        
        # Clear cache
        result = await backend.clear()
        assert result is True
        
        # Verify cache is empty
        assert len(backend._cache) == 0
    
    @pytest.mark.asyncio
    async def test_keys(self):
        """Test keys operation."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set some values
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.set("test_key", "test_value")
        
        # Get all keys
        keys = await backend.keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "test_key" in keys
        
        # Get keys with pattern
        test_keys = await backend.keys("test*")
        assert len(test_keys) == 1
        assert "test_key" in test_keys
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set value with short TTL
        await backend.set("test_key", "test_value", 1)
        
        # Value should exist
        value = await backend.get("test_key")
        assert value == "test_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Value should be expired
        value = await backend.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction policy."""
        config = CacheConfig(
            cache_type=CacheType.MEMORY,
            eviction_policy=EvictionPolicy.LRU
        )
        backend = MemoryCacheBackend(config)
        backend._max_size = 2  # Set small max size for testing
        
        # Fill cache
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        
        # Access key1 to make it more recent
        await backend.get("key1")
        
        # Add new key to trigger eviction
        await backend.set("key3", "value3")
        
        # key2 should be evicted (least recently used)
        assert await backend.get("key1") == "value1"
        assert await backend.get("key2") is None
        assert await backend.get("key3") == "value3"
    
    @pytest.mark.asyncio
    async def test_stats_update(self):
        """Test statistics update."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        backend = MemoryCacheBackend(config)
        
        # Set value
        await backend.set("test_key", "test_value")
        
        # Get value (hit)
        await backend.get("test_key")
        
        # Get nonexistent value (miss)
        await backend.get("nonexistent")
        
        # Delete value
        await backend.delete("test_key")
        
        # Check stats
        stats = backend.get_stats()
        assert stats.sets == 1
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.deletes == 1


class TestRedisCacheBackend:
    """Test Redis cache backend."""
    
    @pytest.mark.asyncio
    async def test_initialization_without_redis(self):
        """Test initialization without Redis available."""
        with patch('spider.infrastructure.advanced_caching.REDIS_AVAILABLE', False):
            config = CacheConfig(cache_type=CacheType.REDIS)
            with pytest.raises(Exception):
                RedisCacheBackend(config)
    
    @pytest.mark.asyncio
    async def test_operations_with_mock(self):
        """Test operations with mocked Redis client."""
        with patch('spider.infrastructure.advanced_caching.REDIS_AVAILABLE', True):
            with patch('spider.infrastructure.advanced_caching.redis') as mock_redis:
                # Mock Redis client
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_client.get.return_value = None
                mock_client.setex.return_value = True
                mock_client.delete.return_value = 1
                mock_client.exists.return_value = True
                mock_client.flushdb.return_value = True
                mock_client.keys.return_value = ["key1", "key2"]
                
                mock_redis.Redis.return_value = mock_client
                
                config = CacheConfig(cache_type=CacheType.REDIS)
                backend = RedisCacheBackend(config)
                
                # Test operations
                await backend.set("test_key", "test_value")
                value = await backend.get("test_key")
                exists = await backend.exists("test_key")
                keys = await backend.keys()
                
                # Verify calls
                mock_client.setex.assert_called()
                mock_client.get.assert_called()
                mock_client.exists.assert_called()
                mock_client.keys.assert_called()


class TestMemcacheBackend:
    """Test Memcached cache backend."""
    
    @pytest.mark.asyncio
    async def test_initialization_without_memcache(self):
        """Test initialization without Memcached available."""
        with patch('spider.infrastructure.advanced_caching.MEMCACHE_AVAILABLE', False):
            config = CacheConfig(cache_type=CacheType.MEMCACHE)
            with pytest.raises(Exception):
                MemcacheBackend(config)
    
    @pytest.mark.asyncio
    async def test_operations_with_mock(self):
        """Test operations with mocked Memcached client."""
        with patch('spider.infrastructure.advanced_caching.MEMCACHE_AVAILABLE', True):
            with patch('spider.infrastructure.advanced_caching.memcache') as mock_memcache:
                # Mock Memcached client
                mock_client = Mock()
                mock_client.get_stats.return_value = []
                mock_client.get.return_value = None
                mock_client.set.return_value = True
                mock_client.delete.return_value = True
                mock_client.flush_all.return_value = True
                
                mock_memcache.Client.return_value = mock_client
                
                config = CacheConfig(cache_type=CacheType.MEMCACHE)
                backend = MemcacheBackend(config)
                
                # Test operations
                await backend.set("test_key", "test_value")
                value = await backend.get("test_key")
                exists = await backend.exists("test_key")
                
                # Verify calls
                mock_client.set.assert_called()
                mock_client.get.assert_called()


class TestHybridCacheBackend:
    """Test hybrid cache backend."""
    
    @pytest.mark.asyncio
    async def test_hybrid_operations(self):
        """Test hybrid cache operations."""
        # Create mock backends
        backend1 = Mock(spec=BaseCacheBackend)
        backend2 = Mock(spec=BaseCacheBackend)
        
        # Configure mock responses
        backend1.get.return_value = None
        backend2.get.return_value = "test_value"
        backend1.set.return_value = True
        backend2.set.return_value = True
        backend1.delete.return_value = True
        backend2.delete.return_value = True
        backend1.exists.return_value = False
        backend2.exists.return_value = True
        backend1.clear.return_value = True
        backend2.clear.return_value = True
        backend1.keys.return_value = ["key1"]
        backend2.keys.return_value = ["key2"]
        
        config = CacheConfig(cache_type=CacheType.HYBRID)
        hybrid_backend = HybridCacheBackend(config, [backend1, backend2])
        
        # Test get (should try primary, then fallback)
        value = await hybrid_backend.get("test_key")
        assert value == "test_value"
        backend1.get.assert_called_with("test_key")
        backend2.get.assert_called_with("test_key")
        
        # Test set (should set in both)
        result = await hybrid_backend.set("test_key", "test_value")
        assert result is True
        backend1.set.assert_called_with("test_key", "test_value", None)
        backend2.set.assert_called_with("test_key", "test_value", None)
        
        # Test delete (should delete from both)
        result = await hybrid_backend.delete("test_key")
        assert result is True
        backend1.delete.assert_called_with("test_key")
        backend2.delete.assert_called_with("test_key")


class TestAdvancedCacheManager:
    """Test advanced cache manager."""
    
    def test_initialization_memory(self):
        """Test initialization with memory cache."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        assert isinstance(manager.backend, MemoryCacheBackend)
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        # Set value
        result = await manager.set("test_key", "test_value")
        assert result is True
        
        # Get value
        value = await manager.get("test_key")
        assert value == "test_value"
        
        # Check existence
        exists = await manager.exists("test_key")
        assert exists is True
        
        # Delete value
        result = await manager.delete("test_key")
        assert result is True
        
        # Verify deletion
        value = await manager.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_warmup_tasks(self):
        """Test cache warmup tasks."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        # Add warmup task
        warmup_called = False
        
        async def warmup_task():
            nonlocal warmup_called
            warmup_called = True
            await manager.set("warmup_key", "warmup_value")
        
        manager.add_warmup_task(warmup_task)
        
        # Execute warmup
        await manager.warmup()
        
        # Verify warmup executed
        assert warmup_called is True
        value = await manager.get("warmup_key")
        assert value == "warmup_value"
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        stats = manager.get_stats()
        assert isinstance(stats, CacheStats)


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_get_cache_manager(self):
        """Test getting cache manager."""
        manager = get_cache_manager()
        assert isinstance(manager, AdvancedCacheManager)
    
    def test_cleanup_cache_resources(self):
        """Test cleanup cache resources."""
        # Should not raise exception
        cleanup_cache_resources()


class TestCacheIntegration:
    """Test cache integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_memory_cache_integration(self):
        """Test memory cache integration."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        # Test multiple operations
        await manager.set("key1", "value1", 60)
        await manager.set("key2", "value2", 60)
        await manager.set("key3", "value3", 60)
        
        # Test retrieval
        assert await manager.get("key1") == "value1"
        assert await manager.get("key2") == "value2"
        assert await manager.get("key3") == "value3"
        
        # Test pattern matching
        keys = await manager.keys("key*")
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
        
        # Test statistics
        stats = manager.get_stats()
        assert stats.sets >= 3
        assert stats.hits >= 3
    
    @pytest.mark.asyncio
    async def test_ttl_behavior(self):
        """Test TTL behavior."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        # Set value with short TTL
        await manager.set("ttl_key", "ttl_value", 1)
        
        # Should exist immediately
        assert await manager.get("ttl_key") == "ttl_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await manager.get("ttl_key") is None
    
    @pytest.mark.asyncio
    async def test_eviction_policy(self):
        """Test eviction policy."""
        config = CacheConfig(
            cache_type=CacheType.MEMORY,
            eviction_policy=EvictionPolicy.LRU
        )
        manager = AdvancedCacheManager(config)
        
        # Set max size to 2 for testing
        manager.backend._max_size = 2
        
        # Fill cache
        await manager.set("key1", "value1")
        await manager.set("key2", "value2")
        
        # Access key1 to make it more recent
        await manager.get("key1")
        
        # Add new key to trigger eviction
        await manager.set("key3", "value3")
        
        # key2 should be evicted
        assert await manager.get("key1") == "value1"
        assert await manager.get("key2") is None
        assert await manager.get("key3") == "value3"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent cache operations."""
        config = CacheConfig(cache_type=CacheType.MEMORY)
        manager = AdvancedCacheManager(config)
        
        async def set_value(i):
            await manager.set(f"key{i}", f"value{i}")
        
        async def get_value(i):
            return await manager.get(f"key{i}")
        
        # Concurrent sets
        tasks = [set_value(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Concurrent gets
        tasks = [get_value(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all values were set and retrieved
        for i, result in enumerate(results):
            assert result == f"value{i}"
