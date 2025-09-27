"""
Storage Plugin Interface

This module defines the interface for storage plugins that can store
and retrieve data from various storage backends.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class StoragePlugin(Plugin):
    """Base class for storage plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Storage plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.STORAGE,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate storage configuration."""
        try:
            return self._validate_storage_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def store(self, data: Any, key: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store data with the given key.
        
        Args:
            data: Data to store
            key: Storage key
            context: Additional context for storage
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Retrieve data by key.
        
        Args:
            key: Storage key
            context: Additional context for retrieval
            
        Returns:
            Retrieved data
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete data by key.
        
        Args:
            key: Storage key
            context: Additional context for deletion
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def get_storage_capabilities(self) -> Dict[str, Any]:
        """Get storage capabilities and features."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this storage."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "connection_string": {"type": "string"},
                "max_connections": {"type": "integer", "default": 10},
                "timeout": {"type": "number", "default": 30},
                "compression": {"type": "boolean", "default": False}
            }
        }
    
    def _validate_storage_config(self, config: Dict[str, Any]) -> bool:
        """Validate storage-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
