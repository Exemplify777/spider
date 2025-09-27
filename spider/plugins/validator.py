"""
Validator Plugin Interface

This module defines the interface for validator plugins that can validate
data, configurations, and results.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class ValidatorPlugin(Plugin):
    """Base class for validator plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Validator plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.VALIDATOR,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate validator configuration."""
        try:
            return self._validate_validator_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate input data.
        
        Args:
            data: Data to validate
            context: Additional context for validation
            
        Returns:
            Validation result with success status and details
        """
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> List[str]:
        """Get list of validation rules supported."""
        pass
    
    @abstractmethod
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types for validation."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this validator."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "strict_mode": {"type": "boolean", "default": False},
                "validation_rules": {"type": "array", "items": {"type": "object"}},
                "error_threshold": {"type": "number", "default": 0.1},
                "generate_report": {"type": "boolean", "default": True}
            }
        }
    
    def _validate_validator_config(self, config: Dict[str, Any]) -> bool:
        """Validate validator-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
