"""Data transformers for SPIDER framework."""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import unicodedata

from ..core.exceptions import ValidationError
from ..core.logger import get_logger


class BaseTransformer(ABC):
    """Base class for all data transformers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize transformer with configuration.
        
        Args:
            config: Transformer-specific configuration
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data.
        
        Args:
            data: Data to transform
            
        Returns:
            Transformed data
        """
        pass


class DataCleaner(BaseTransformer):
    """Data cleaning transformer."""
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data.
        
        Args:
            data: Data to clean
            
        Returns:
            Cleaned data
        """
        cleaned_data = {}
        
        for key, value in data.items():
            if key.startswith('_'):
                # Preserve metadata
                cleaned_data[key] = value
            else:
                cleaned_data[key] = self._clean_value(value)
        
        return cleaned_data
    
    def _clean_value(self, value: Any) -> Any:
        """Clean a single value.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value
        """
        if isinstance(value, str):
            return self._clean_string(value)
        elif isinstance(value, list):
            return [self._clean_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._clean_value(v) for k, v in value.items()}
        else:
            return value
    
    def _clean_string(self, text: str) -> str:
        """Clean a string value.
        
        Args:
            text: String to clean
            
        Returns:
            Cleaned string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove HTML entities
        text = self._decode_html_entities(text)
        
        return text
    
    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities in text.
        
        Args:
            text: Text with HTML entities
            
        Returns:
            Text with decoded entities
        """
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text


class DataNormalizer(BaseTransformer):
    """Data normalization transformer."""
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure and values.
        
        Args:
            data: Data to normalize
            
        Returns:
            Normalized data
        """
        normalized_data = {}
        
        for key, value in data.items():
            if key.startswith('_'):
                # Preserve metadata
                normalized_data[key] = value
            else:
                normalized_key = self._normalize_key(key)
                normalized_value = self._normalize_value(value)
                normalized_data[normalized_key] = normalized_value
        
        return normalized_data
    
    def _normalize_key(self, key: str) -> str:
        """Normalize a key name.
        
        Args:
            key: Key to normalize
            
        Returns:
            Normalized key
        """
        # Convert to lowercase
        key = key.lower()
        
        # Replace spaces and special characters with underscores
        key = re.sub(r'[^a-z0-9_]', '_', key)
        
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        
        # Remove leading/trailing underscores
        key = key.strip('_')
        
        return key
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize a value.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value
        """
        if isinstance(value, str):
            return self._normalize_string(value)
        elif isinstance(value, (int, float)):
            return self._normalize_number(value)
        elif isinstance(value, list):
            return [self._normalize_value(item) for item in value]
        elif isinstance(value, dict):
            return {self._normalize_key(k): self._normalize_value(v) for k, v in value.items()}
        else:
            return value
    
    def _normalize_string(self, text: str) -> str:
        """Normalize a string value.
        
        Args:
            text: String to normalize
            
        Returns:
            Normalized string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _normalize_number(self, number: Union[int, float]) -> Union[int, float]:
        """Normalize a number value.
        
        Args:
            number: Number to normalize
            
        Returns:
            Normalized number
        """
        # Round to specified decimal places if configured
        decimal_places = self.config.get('decimal_places')
        if decimal_places is not None and isinstance(number, float):
            return round(number, decimal_places)
        
        return number


class DataEnricher(BaseTransformer):
    """Data enrichment transformer."""
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional information.
        
        Args:
            data: Data to enrich
            
        Returns:
            Enriched data
        """
        enriched_data = data.copy()
        
        # Add timestamp
        enriched_data['_enriched_at'] = datetime.utcnow().isoformat()
        
        # Add data quality metrics
        enriched_data['_quality_metrics'] = self._calculate_quality_metrics(data)
        
        # Apply enrichment rules
        enrichment_rules = self.config.get('enrichment_rules', {})
        for field, rule in enrichment_rules.items():
            enriched_data[field] = self._apply_enrichment_rule(data, rule)
        
        return enriched_data
    
    def _calculate_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data quality metrics.
        
        Args:
            data: Data to analyze
            
        Returns:
            Quality metrics
        """
        total_fields = len([k for k in data.keys() if not k.startswith('_')])
        empty_fields = len([k for k, v in data.items() 
                           if not k.startswith('_') and (not v or v == '')])
        
        return {
            'total_fields': total_fields,
            'empty_fields': empty_fields,
            'completeness_ratio': (total_fields - empty_fields) / total_fields if total_fields > 0 else 0,
            'field_count': total_fields
        }
    
    def _apply_enrichment_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Any:
        """Apply an enrichment rule.
        
        Args:
            data: Data to enrich
            rule: Enrichment rule configuration
            
        Returns:
            Enriched value
        """
        rule_type = rule.get('type')
        
        if rule_type == 'concat':
            # Concatenate multiple fields
            fields = rule.get('fields', [])
            separator = rule.get('separator', ' ')
            values = [str(data.get(field, '')) for field in fields]
            return separator.join(values)
        
        elif rule_type == 'format':
            # Format string with field values
            template = rule.get('template', '')
            return template.format(**data)
        
        elif rule_type == 'lookup':
            # Lookup value in mapping
            field = rule.get('field')
            mapping = rule.get('mapping', {})
            value = data.get(field)
            return mapping.get(value, value)
        
        elif rule_type == 'default':
            # Set default value if field is empty
            field = rule.get('field')
            default_value = rule.get('default_value')
            return data.get(field) or default_value
        
        else:
            return data.get(rule.get('field', ''))
