"""
Extractor Plugin Interface

This module defines the interface for extractor plugins that can extract data
from various sources and formats.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class ExtractorPlugin(Plugin):
    """Base class for extractor plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Extractor plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.EXTRACTOR,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate extractor configuration."""
        try:
            return self._validate_extractor_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def extract(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Extract data from the input.
        
        Args:
            data: Input data to extract from
            context: Additional context for extraction
            
        Returns:
            Extracted data
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported data formats."""
        pass
    
    @abstractmethod
    def get_extraction_fields(self) -> List[str]:
        """Get list of fields that can be extracted."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this extractor."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "timeout": {"type": "number", "default": 30},
                "retry_attempts": {"type": "integer", "default": 3},
                "parallel_processing": {"type": "boolean", "default": False}
            }
        }
    
    def _validate_extractor_config(self, config: Dict[str, Any]) -> bool:
        """Validate extractor-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)


class HTMLExtractorPlugin(ExtractorPlugin):
    """Base class for HTML extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported HTML formats."""
        return ["html", "xhtml", "xml"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get HTML extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "css_selectors": {"type": "array", "items": {"type": "string"}},
            "xpath_selectors": {"type": "array", "items": {"type": "string"}},
            "text_extraction": {"type": "boolean", "default": True},
            "attribute_extraction": {"type": "boolean", "default": True},
            "nested_extraction": {"type": "boolean", "default": False}
        })
        return schema


class JSONExtractorPlugin(ExtractorPlugin):
    """Base class for JSON extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported JSON formats."""
        return ["json", "jsonl", "ndjson"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get JSON extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "json_paths": {"type": "array", "items": {"type": "string"}},
            "flatten_nested": {"type": "boolean", "default": False},
            "handle_arrays": {"type": "boolean", "default": True},
            "type_conversion": {"type": "boolean", "default": True}
        })
        return schema


class TextExtractorPlugin(ExtractorPlugin):
    """Base class for text extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported text formats."""
        return ["txt", "csv", "tsv", "log", "plain"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get text extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "encoding": {"type": "string", "default": "utf-8"},
            "line_delimiter": {"type": "string", "default": "\\n"},
            "field_delimiter": {"type": "string", "default": ","},
            "regex_patterns": {"type": "array", "items": {"type": "string"}},
            "strip_whitespace": {"type": "boolean", "default": True}
        })
        return schema


class ImageExtractorPlugin(ExtractorPlugin):
    """Base class for image extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats."""
        return ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get image extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "extract_metadata": {"type": "boolean", "default": True},
            "extract_text": {"type": "boolean", "default": False},
            "resize_images": {"type": "boolean", "default": False},
            "max_width": {"type": "integer", "default": 1920},
            "max_height": {"type": "integer", "default": 1080},
            "quality": {"type": "integer", "default": 85}
        })
        return schema


class VideoExtractorPlugin(ExtractorPlugin):
    """Base class for video extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported video formats."""
        return ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get video extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "extract_frames": {"type": "boolean", "default": False},
            "frame_interval": {"type": "number", "default": 1.0},
            "extract_audio": {"type": "boolean", "default": False},
            "extract_metadata": {"type": "boolean", "default": True},
            "thumbnail_generation": {"type": "boolean", "default": True}
        })
        return schema


class DatabaseExtractorPlugin(ExtractorPlugin):
    """Base class for database extractor plugins."""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported database formats."""
        return ["sqlite", "mysql", "postgresql", "mongodb", "redis"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get database extractor configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "connection_string": {"type": "string"},
            "query": {"type": "string"},
            "batch_size": {"type": "integer", "default": 1000},
            "timeout": {"type": "number", "default": 30},
            "connection_pool_size": {"type": "integer", "default": 5}
        })
        return schema
