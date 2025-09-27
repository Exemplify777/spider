"""
Reporting Plugin Interface

This module defines the interface for reporting plugins that can generate
reports and analytics from scraped data.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class ReportingPlugin(Plugin):
    """Base class for reporting plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Reporting plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.REPORTING,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate reporting configuration."""
        try:
            return self._validate_reporting_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def generate_report(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a report from the provided data.
        
        Args:
            data: Data to generate report from
            context: Additional context for report generation
            
        Returns:
            Generated report data
        """
        pass
    
    @abstractmethod
    def get_report_formats(self) -> List[str]:
        """Get list of supported report formats."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this reporting plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "report_format": {"type": "string", "default": "json"},
                "include_charts": {"type": "boolean", "default": True},
                "template": {"type": "string"}
            }
        }
    
    def _validate_reporting_config(self, config: Dict[str, Any]) -> bool:
        """Validate reporting-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
