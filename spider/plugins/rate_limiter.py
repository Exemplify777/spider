"""
Rate Limiter Plugin Interface

This module defines the interface for rate limiter plugins that can control
request rates and implement various throttling strategies.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class RateLimiterPlugin(Plugin):
    """Base class for rate limiter plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Rate limiter plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.RATE_LIMITER,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate rate limiter configuration."""
        try:
            return self._validate_rate_limiter_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def check_rate_limit(self, identifier: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check if a request is within rate limits.
        
        Args:
            identifier: Unique identifier for rate limiting
            context: Additional context for rate limiting
            
        Returns:
            Rate limit check result with allowed status and limits
        """
        pass
    
    @abstractmethod
    async def record_request(self, identifier: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a request for rate limiting purposes.
        
        Args:
            identifier: Unique identifier for rate limiting
            context: Additional context for rate limiting
        """
        pass
    
    @abstractmethod
    def get_rate_limit_strategies(self) -> List[str]:
        """Get list of supported rate limiting strategies."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this rate limiter."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "strategy": {"type": "string", "default": "token_bucket"},
                "requests_per_minute": {"type": "integer", "default": 60},
                "burst_capacity": {"type": "integer", "default": 10},
                "window_size": {"type": "number", "default": 60}
            }
        }
    
    def _validate_rate_limiter_config(self, config: Dict[str, Any]) -> bool:
        """Validate rate limiter-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)
