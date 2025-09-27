"""
Compliance Plugin Interface

This module defines the interface for compliance plugins that can ensure
data processing compliance with various regulations and standards.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class CompliancePlugin(Plugin):
    """Base class for compliance plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Compliance plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.COMPLIANCE,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate compliance configuration."""
        try:
            return self._validate_compliance_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def check_compliance(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check data compliance with regulations.
        
        Args:
            data: Data to check for compliance
            context: Additional context for compliance checking
            
        Returns:
            Compliance check result
        """
        pass
    
    @abstractmethod
    def get_supported_regulations(self) -> List[str]:
        """Get list of supported regulations."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this compliance plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "regulations": {"type": "array", "items": {"type": "string"}},
                "strict_mode": {"type": "boolean", "default": False},
                "audit_logging": {"type": "boolean", "default": True}
            }
        }
    
    def _validate_compliance_config(self, config: Dict[str, Any]) -> bool:
        """Validate compliance-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
