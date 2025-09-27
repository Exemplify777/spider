"""
Notification Plugin Interface

This module defines the interface for notification plugins that can send
notifications and alerts through various channels.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class NotificationPlugin(Plugin):
    """Base class for notification plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Notification plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.NOTIFICATION,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate notification configuration."""
        try:
            return self._validate_notification_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def send_notification(self, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a notification message.
        
        Args:
            message: Notification message
            context: Additional context for notification
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def get_notification_channels(self) -> List[str]:
        """Get list of supported notification channels."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this notification plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "channels": {"type": "array", "items": {"type": "string"}},
                "priority": {"type": "string", "default": "normal"},
                "retry_attempts": {"type": "integer", "default": 3}
            }
        }
    
    def _validate_notification_config(self, config: Dict[str, Any]) -> bool:
        """Validate notification-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
