"""
Engine Plugin Interface

This module defines the interface for engine plugins that can provide
different scraping engines and execution backends.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class EnginePlugin(Plugin):
    """Base class for engine plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Engine plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.ENGINE,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate engine configuration."""
        try:
            return self._validate_engine_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a scraping task.
        
        Args:
            task: Task configuration and parameters
            context: Additional execution context
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Get list of supported engine features."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get engine capabilities and limitations."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this engine."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "timeout": {"type": "number", "default": 300},
                "max_concurrent_tasks": {"type": "integer", "default": 10},
                "retry_attempts": {"type": "integer", "default": 3},
                "resource_limits": {"type": "object"}
            }
        }
    
    def _validate_engine_config(self, config: Dict[str, Any]) -> bool:
        """Validate engine-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)


class WebScrapingEnginePlugin(EnginePlugin):
    """Base class for web scraping engine plugins."""
    
    def get_supported_features(self) -> List[str]:
        """Get supported web scraping features."""
        return [
            "http_requests", "javascript_rendering", "form_interaction",
            "file_downloads", "image_extraction", "link_following",
            "session_management", "cookie_handling", "proxy_support"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get web scraping capabilities."""
        return {
            "max_pages_per_minute": 100,
            "max_concurrent_requests": 10,
            "javascript_support": True,
            "file_download_support": True,
            "proxy_rotation": True,
            "user_agent_rotation": True
        }
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get web scraping engine configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "user_agent": {"type": "string"},
            "headers": {"type": "object"},
            "cookies": {"type": "object"},
            "proxy_config": {"type": "object"},
            "javascript_enabled": {"type": "boolean", "default": True},
            "follow_redirects": {"type": "boolean", "default": True},
            "max_redirects": {"type": "integer", "default": 10},
            "request_delay": {"type": "number", "default": 1.0}
        })
        return schema


class APIScrapingEnginePlugin(EnginePlugin):
    """Base class for API scraping engine plugins."""
    
    def get_supported_features(self) -> List[str]:
        """Get supported API scraping features."""
        return [
            "rest_api", "graphql", "soap", "rpc", "authentication",
            "rate_limiting", "pagination", "data_validation"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get API scraping capabilities."""
        return {
            "max_requests_per_minute": 1000,
            "authentication_methods": ["bearer", "api_key", "oauth2"],
            "rate_limit_handling": True,
            "pagination_support": True,
            "data_validation": True
        }
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get API scraping engine configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "base_url": {"type": "string"},
            "authentication": {"type": "object"},
            "rate_limit": {"type": "object"},
            "pagination_config": {"type": "object"},
            "request_headers": {"type": "object"},
            "response_format": {"type": "string", "default": "json"}
        })
        return schema


class DatabaseScrapingEnginePlugin(EnginePlugin):
    """Base class for database scraping engine plugins."""
    
    def get_supported_features(self) -> List[str]:
        """Get supported database scraping features."""
        return [
            "sql_queries", "connection_pooling", "transaction_support",
            "data_export", "schema_discovery", "incremental_updates"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get database scraping capabilities."""
        return {
            "max_connections": 20,
            "query_timeout": 300,
            "transaction_support": True,
            "schema_discovery": True,
            "incremental_updates": True
        }
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get database scraping engine configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "connection_string": {"type": "string"},
            "connection_pool_size": {"type": "integer", "default": 5},
            "query_timeout": {"type": "number", "default": 30},
            "transaction_isolation": {"type": "string", "default": "read_committed"},
            "batch_size": {"type": "integer", "default": 1000}
        })
        return schema


class FileScrapingEnginePlugin(EnginePlugin):
    """Base class for file scraping engine plugins."""
    
    def get_supported_features(self) -> List[str]:
        """Get supported file scraping features."""
        return [
            "file_reading", "format_detection", "encoding_detection",
            "chunked_processing", "parallel_processing", "file_watching"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get file scraping capabilities."""
        return {
            "max_file_size": "1GB",
            "supported_formats": ["txt", "csv", "json", "xml", "html"],
            "encoding_detection": True,
            "chunked_processing": True,
            "file_watching": True
        }
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get file scraping engine configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "file_paths": {"type": "array", "items": {"type": "string"}},
            "recursive": {"type": "boolean", "default": False},
            "file_patterns": {"type": "array", "items": {"type": "string"}},
            "encoding": {"type": "string", "default": "utf-8"},
            "chunk_size": {"type": "integer", "default": 8192},
            "watch_directory": {"type": "boolean", "default": False}
        })
        return schema
