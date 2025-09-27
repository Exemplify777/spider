"""
Middleware Plugin Interface

This module defines the interface for middleware plugins that can intercept
and modify requests/responses in the processing pipeline.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from ..plugins.base import Plugin, PluginMetadata, PluginType


class MiddlewarePlugin(Plugin):
    """Base class for middleware plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Middleware plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.MIDDLEWARE,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate middleware configuration."""
        try:
            return self._validate_middleware_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an incoming request.
        
        Args:
            request: Request data to process
            context: Additional context for processing
            
        Returns:
            Modified request data
        """
        pass
    
    @abstractmethod
    async def process_response(self, response: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an outgoing response.
        
        Args:
            response: Response data to process
            context: Additional context for processing
            
        Returns:
            Modified response data
        """
        pass
    
    @abstractmethod
    def get_middleware_type(self) -> str:
        """Get the type of middleware (e.g., 'request', 'response', 'both')."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this middleware."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "default": 0},
                "async_processing": {"type": "boolean", "default": False},
                "error_handling": {"type": "string", "default": "continue"}
            }
        }
    
    def _validate_middleware_config(self, config: Dict[str, Any]) -> bool:
        """Validate middleware-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
