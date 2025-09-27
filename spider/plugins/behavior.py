"""
Behavior Plugin Interface

This module defines the interface for behavior plugins that can simulate
human-like behavior patterns and interactions.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class BehaviorPlugin(Plugin):
    """Base class for behavior plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Behavior plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.BEHAVIOR,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate behavior configuration."""
        try:
            return self._validate_behavior_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def simulate_behavior(self, action: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate human-like behavior for a given action.
        
        Args:
            action: Action to simulate
            context: Additional context for behavior simulation
            
        Returns:
            Behavior simulation result
        """
        pass
    
    @abstractmethod
    def get_behavior_types(self) -> List[str]:
        """Get list of supported behavior types."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this behavior plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "realism_level": {"type": "string", "default": "medium"},
                "delay_range": {"type": "array", "items": {"type": "number"}},
                "randomization": {"type": "boolean", "default": True}
            }
        }
    
    def _validate_behavior_config(self, config: Dict[str, Any]) -> bool:
        """Validate behavior-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
