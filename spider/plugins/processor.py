"""
Processor Plugin Interface

This module defines the interface for processor plugins that can transform,
clean, and process data in various ways.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..plugins.base import Plugin, PluginMetadata, PluginType


class ProcessorPlugin(Plugin):
    """Base class for processor plugins."""
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            description=f"Processor plugin: {self.__class__.__name__}",
            author="SPIDER Framework",
            plugin_type=PluginType.PROCESSOR,
            config_schema=self._get_config_schema()
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate processor configuration."""
        try:
            return self._validate_processor_config(config)
        except Exception:
            return False
    
    @abstractmethod
    async def process(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Process the input data.
        
        Args:
            data: Input data to process
            context: Additional context for processing
            
        Returns:
            Processed data
        """
        pass
    
    @abstractmethod
    def get_input_types(self) -> List[str]:
        """Get list of supported input data types."""
        pass
    
    @abstractmethod
    def get_output_types(self) -> List[str]:
        """Get list of supported output data types."""
        pass
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this processor."""
        return {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "timeout": {"type": "number", "default": 30},
                "retry_attempts": {"type": "integer", "default": 3},
                "parallel_processing": {"type": "boolean", "default": False},
                "batch_size": {"type": "integer", "default": 100}
            }
        }
    
    def _validate_processor_config(self, config: Dict[str, Any]) -> bool:
        """Validate processor-specific configuration."""
        required_fields = ["enabled"]
        return all(field in config for field in required_fields)


class DataCleanerPlugin(ProcessorPlugin):
    """Base class for data cleaning plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["text", "html", "json", "csv"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["text", "html", "json", "csv"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data cleaner configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "remove_duplicates": {"type": "boolean", "default": True},
            "normalize_whitespace": {"type": "boolean", "default": True},
            "remove_html_tags": {"type": "boolean", "default": False},
            "normalize_encoding": {"type": "boolean", "default": True},
            "remove_special_chars": {"type": "boolean", "default": False},
            "trim_strings": {"type": "boolean", "default": True}
        })
        return schema


class DataTransformerPlugin(ProcessorPlugin):
    """Base class for data transformation plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "xml", "html"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "csv", "xml", "html"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data transformer configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "transformation_rules": {"type": "array", "items": {"type": "object"}},
            "field_mapping": {"type": "object"},
            "data_type_conversion": {"type": "boolean", "default": True},
            "flatten_nested": {"type": "boolean", "default": False},
            "aggregate_functions": {"type": "array", "items": {"type": "string"}}
        })
        return schema


class DataValidatorPlugin(ProcessorPlugin):
    """Base class for data validation plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "xml", "html", "text"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "validation_report"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data validator configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "validation_schema": {"type": "object"},
            "strict_validation": {"type": "boolean", "default": False},
            "custom_rules": {"type": "array", "items": {"type": "object"}},
            "error_threshold": {"type": "number", "default": 0.1},
            "generate_report": {"type": "boolean", "default": True}
        })
        return schema


class DataEnricherPlugin(ProcessorPlugin):
    """Base class for data enrichment plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "text"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "csv"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data enricher configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "enrichment_sources": {"type": "array", "items": {"type": "string"}},
            "api_endpoints": {"type": "array", "items": {"type": "string"}},
            "cache_enrichments": {"type": "boolean", "default": True},
            "max_retries": {"type": "integer", "default": 3},
            "rate_limit": {"type": "number", "default": 1.0}
        })
        return schema


class DataAggregatorPlugin(ProcessorPlugin):
    """Base class for data aggregation plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "text"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "csv", "summary"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data aggregator configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "aggregation_functions": {"type": "array", "items": {"type": "string"}},
            "group_by_fields": {"type": "array", "items": {"type": "string"}},
            "time_windows": {"type": "array", "items": {"type": "string"}},
            "statistical_measures": {"type": "array", "items": {"type": "string"}},
            "output_format": {"type": "string", "default": "json"}
        })
        return schema


class DataNormalizerPlugin(ProcessorPlugin):
    """Base class for data normalization plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "text"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "csv", "normalized"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data normalizer configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "normalization_rules": {"type": "array", "items": {"type": "object"}},
            "standardize_formats": {"type": "boolean", "default": True},
            "handle_missing_values": {"type": "boolean", "default": True},
            "outlier_detection": {"type": "boolean", "default": False},
            "scaling_method": {"type": "string", "default": "minmax"}
        })
        return schema


class DataFilterPlugin(ProcessorPlugin):
    """Base class for data filtering plugins."""
    
    def get_input_types(self) -> List[str]:
        """Get supported input types."""
        return ["json", "csv", "text", "html"]
    
    def get_output_types(self) -> List[str]:
        """Get supported output types."""
        return ["json", "csv", "text", "html"]
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get data filter configuration schema."""
        schema = super()._get_config_schema()
        schema["properties"].update({
            "filter_rules": {"type": "array", "items": {"type": "object"}},
            "regex_patterns": {"type": "array", "items": {"type": "string"}},
            "field_filters": {"type": "object"},
            "value_ranges": {"type": "object"},
            "exclude_patterns": {"type": "array", "items": {"type": "string"}}
        })
        return schema
