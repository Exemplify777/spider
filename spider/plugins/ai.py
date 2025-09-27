"""
AI Plugin Interface

This module defines the interface for AI plugins that can provide
artificial intelligence and machine learning capabilities.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class AIPlugin(Plugin):
    """Base class for AI plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"AI plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.AI,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate AI configuration."""
        try:
            return self._validate_ai_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def process_with_ai(self, data: Any, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process data using AI capabilities.
        
        Args:
            data: Data to process
            task: AI task to perform
            context: Additional context for AI processing
            
        Returns:
            AI processing result
        """
        pass
    
    @abstractmethod
    def get_ai_capabilities(self) -> List[str]:
        """Get list of supported AI capabilities."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this AI plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "model_name": {"type": "string"},
                "api_key": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 1000},
                "temperature": {"type": "number", "default": 0.7}
            }
        }
    
    def _validate_ai_config(self, config: Dict[str, Any]) -> bool:
        """Validate AI-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
