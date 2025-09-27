"""
Authentication Plugin Interface

This module defines the interface for authentication plugins that can handle
various authentication methods and security protocols.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class AuthPlugin(Plugin):
    """Base class for authentication plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Authentication plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.AUTH,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate authentication configuration."""
        try:
            return self._validate_auth_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Authenticate using provided credentials.
        
        Args:
            credentials: Authentication credentials
            context: Additional context for authentication
            
        Returns:
            Authentication result with token/session info
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, token: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Refresh an authentication token.
        
        Args:
            token: Current token to refresh
            context: Additional context for token refresh
            
        Returns:
            New token information
        """
        pass
    
    @abstractmethod
    def get_auth_methods(self) -> List[str]:
        """Get list of supported authentication methods."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this auth plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "auth_method": {"type": "string"},
                "token_expiry": {"type": "number", "default": 3600},
                "auto_refresh": {"type": "boolean", "default": True},
                "secure_storage": {"type": "boolean", "default": True}
            }
        }
    
    def _validate_auth_config(self, config: Dict[str, Any]) -> bool:
        """Validate auth-specific configuration."""
        required_fields = ["enabled", "auth_method"]
        return all(field in config for field in required_fields)
