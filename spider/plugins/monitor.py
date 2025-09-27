"""
Monitor Plugin Interface

This module defines the interface for monitor plugins that can provide
monitoring and observability capabilities.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class MonitorPlugin(Plugin):
    """Base class for monitor plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Monitor plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.MONITOR,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate monitor configuration."""
        try:
            return self._validate_monitor_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def collect_metrics(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect monitoring metrics.
        
        Args:
            context: Additional context for metric collection
            
        Returns:
            Collected metrics data
        """
        pass
    
    @abstractmethod
    def get_metric_types(self) -> List[str]:
        """Get list of supported metric types."""
        pass
    
    @abstractmethod
    def get_monitoring_capabilities(self) -> Dict[str, Any]:
        """Get monitoring capabilities and features."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this monitor."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "collection_interval": {"type": "number", "default": 60},
                "retention_period": {"type": "number", "default": 86400},
                "alert_thresholds": {"type": "object"},
                "export_formats": {"type": "array", "items": {"type": "string"}}
            }
        }
    
    def _validate_monitor_config(self, config: Dict[str, Any]) -> bool:
        """Validate monitor-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
