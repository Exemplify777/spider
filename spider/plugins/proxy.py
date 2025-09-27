"""
Proxy Plugin Interface

This module defines the interface for proxy plugins that can manage
proxy connections and rotation strategies.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class ProxyPlugin(Plugin):
    """Base class for proxy plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Proxy plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.PROXY,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate proxy configuration."""
        try:
            return self._validate_proxy_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def get_proxy(self, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a proxy for use in requests.
        
        Args:
            context: Additional context for proxy selection
            
        Returns:
            Proxy configuration or None if no proxy available
        """
        pass
    
    @abstractmethod
    async def release_proxy(self, proxy: Dict[str, Any], success: bool, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Release a proxy after use.
        
        Args:
            proxy: Proxy configuration to release
            success: Whether the proxy was successful
            context: Additional context for proxy release
        """
        pass
    
    @abstractmethod
    def get_proxy_types(self) -> List[str]:
        """Get list of supported proxy types."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this proxy plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "proxy_list": {"type": "array", "items": {"type": "string"}},
                "rotation_strategy": {"type": "string", "default": "round_robin"},
                "health_check_interval": {"type": "number", "default": 300},
                "max_failures": {"type": "integer", "default": 3}
            }
        }
    
    def _validate_proxy_config(self, config: Dict[str, Any]) -> bool:
        """Validate proxy-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
