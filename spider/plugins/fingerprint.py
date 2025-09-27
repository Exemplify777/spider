"""
Fingerprint Plugin Interface

This module defines the interface for fingerprint plugins that can manage
browser fingerprints and device identification.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class FingerprintPlugin(Plugin):
    """Base class for fingerprint plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Fingerprint plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.FINGERPRINT,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate fingerprint configuration."""
        try:
            return self._validate_fingerprint_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def generate_fingerprint(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a browser/device fingerprint.
        
        Args:
            context: Additional context for fingerprint generation
            
        Returns:
            Generated fingerprint data
        """
        pass
    
    @abstractmethod
    async def randomize_fingerprint(self, fingerprint: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Randomize an existing fingerprint.
        
        Args:
            fingerprint: Original fingerprint to randomize
            context: Additional context for randomization
            
        Returns:
            Randomized fingerprint data
        """
        pass
    
    @abstractmethod
    def get_fingerprint_components(self) -> List[str]:
        """Get list of fingerprint components managed."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this fingerprint plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "randomization_level": {"type": "string", "default": "medium"},
                "preserve_consistency": {"type": "boolean", "default": True},
                "update_interval": {"type": "number", "default": 3600}
            }
        }
    
    def _validate_fingerprint_config(self, config: Dict[str, Any]) -> bool:
        """Validate fingerprint-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
