"""
Analytics Plugin Interface

This module defines the interface for analytics plugins that can provide
data analytics and insights.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class AnalyticsPlugin(Plugin):
    """Base class for analytics plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Analytics plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.ANALYTICS,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate analytics configuration."""
        try:
            return self._validate_analytics_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def analyze_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze data and generate insights.
        
        Args:
            data: Data to analyze
            context: Additional context for analysis
            
        Returns:
            Analytics results and insights
        """
        pass
    
    @abstractmethod
    def get_analytics_types(self) -> List[str]:
        """Get list of supported analytics types."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this analytics plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "analysis_types": {"type": "array", "items": {"type": "string"}},
                "visualization": {"type": "boolean", "default": True},
                "export_formats": {"type": "array", "items": {"type": "string"}}
            }
        }
    
    def _validate_analytics_config(self, config: Dict[str, Any]) -> bool:
        """Validate analytics-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
