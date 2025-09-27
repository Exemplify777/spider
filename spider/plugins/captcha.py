"""
CAPTCHA Plugin Interface

This module defines the interface for CAPTCHA plugins that can detect
and solve various types of CAPTCHAs.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class CaptchaPlugin(Plugin):
    """Base class for CAPTCHA plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"CAPTCHA plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.CAPTCHA,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate CAPTCHA configuration."""
        try:
            return self._validate_captcha_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def detect_captcha(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect CAPTCHA in the provided data.
        
        Args:
            data: Data to analyze for CAPTCHA presence
            context: Additional context for detection
            
        Returns:
            CAPTCHA detection result with type and confidence
        """
        pass
    
    @abstractmethod
    async def solve_captcha(self, captcha_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Solve the detected CAPTCHA.
        
        Args:
            captcha_data: CAPTCHA data to solve
            context: Additional context for solving
            
        Returns:
            CAPTCHA solution result
        """
        pass
    
    @abstractmethod
    def get_supported_captcha_types(self) -> List[str]:
        """Get list of supported CAPTCHA types."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this CAPTCHA plugin."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "detection_threshold": {"type": "number", "default": 0.8},
                "solving_service": {"type": "string"},
                "api_key": {"type": "string"},
                "timeout": {"type": "number", "default": 30}
            }
        }
    
    def _validate_captcha_config(self, config: Dict[str, Any]) -> bool:
        """Validate CAPTCHA-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
