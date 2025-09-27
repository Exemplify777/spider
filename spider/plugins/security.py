"""
Security Plugin Interface

This module defines the interface for security plugins that can provide
security features and threat detection.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class SecurityPlugin(Plugin):
    """Base class for security plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Security plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.SECURITY,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate security configuration."""
        try:
            return self._validate_security_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def scan_for_threats(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scan data for security threats.
        
        Args:
            data: Data to scan
            context: Additional context for security scanning
            
        Returns:
            Security scan result
        """
        pass
    
    @abstractmethod
    def get_security_features(self) -> List[str]:
        """Get list of supported security features."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this security plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "threat_detection": {"type": "boolean", "default": True},
                "encryption": {"type": "boolean", "default": True},
                "access_control": {"type": "boolean", "default": True}
            }
        }
    
    def _validate_security_config(self, config: Dict[str, Any]) -> bool:
        """Validate security-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
