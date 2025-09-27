"""
Cache Plugin Interface

This module defines the interface for cache plugins that can provide
caching capabilities for various data types.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class CachePlugin(Plugin):
    """Base class for cache plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Cache plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.CACHE,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate cache configuration."""
        try:
            return self._validate_cache_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def get(self, key: str, context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            context: Additional context for cache retrieval
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            context: Additional context for cache storage
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            context: Additional context for cache deletion
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def get_cache_capabilities(self) -> Dict[str, Any]:
        """Get cache capabilities and features."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this cache plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "max_size": {"type": "integer", "default": 1000},
                "default_ttl": {"type": "number", "default": 3600},
                "eviction_policy": {"type": "string", "default": "lru"},
                "compression": {"type": "boolean", "default": False}
            }
        }
    
    def _validate_cache_config(self, config: Dict[str, Any]) -> bool:
        """Validate cache-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
