"""Data validators for SPIDER framework."""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaError

from ..core.exceptions import ValidationError
from ..core.logger import get_logger


class ValidationRule(Enum):
    """Validation rule enumeration."""
    REQUIRED = "required"
    TYPE = "type"
    FORMAT = "format"
    PATTERN = "pattern"
    RANGE = "range"
    LENGTH = "length"
    CUSTOM = "custom"


@dataclass
class ValidationResult:
    """Validation result container."""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with configuration.
        
        Args:
            config: Validator-specific configuration
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """Validate data.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            Validation result
        """
        pass


class DataValidator(BaseValidator):
    """General data validator with multiple validation rules."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data validator."""
        super().__init__(config)
        self.rules = self.config.get('rules', [])
        self.strict_mode = self.config.get('strict_mode', False)
    
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """Validate data against configured rules.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        for rule in self.rules:
            try:
                rule_result = self._apply_rule(data, rule, **kwargs)
                if not rule_result.is_valid:
                    errors.extend(rule_result.errors)
                warnings.extend(rule_result.warnings)
            except Exception as e:
                error_msg = f"Validation rule failed: {e}"
                if self.strict_mode:
                    errors.append(error_msg)
                else:
                    warnings.append(error_msg)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _apply_rule(self, data: Any, rule: Dict[str, Any], **kwargs) -> ValidationResult:
        """Apply a single validation rule.
        
        Args:
            data: Data to validate
            rule: Rule configuration
            **kwargs: Additional parameters
            
        Returns:
            Validation result
        """
        rule_type = rule.get('type')
        field = rule.get('field')
        value = self._get_field_value(data, field) if field else data
        
        if rule_type == ValidationRule.REQUIRED.value:
            return self._validate_required(value, rule)
        elif rule_type == ValidationRule.TYPE.value:
            return self._validate_type(value, rule)
        elif rule_type == ValidationRule.FORMAT.value:
            return self._validate_format(value, rule)
        elif rule_type == ValidationRule.PATTERN.value:
            return self._validate_pattern(value, rule)
        elif rule_type == ValidationRule.RANGE.value:
            return self._validate_range(value, rule)
        elif rule_type == ValidationRule.LENGTH.value:
            return self._validate_length(value, rule)
        elif rule_type == ValidationRule.CUSTOM.value:
            return self._validate_custom(value, rule, **kwargs)
        else:
            return ValidationResult(True, [], [f"Unknown rule type: {rule_type}"])
    
    def _get_field_value(self, data: Any, field: str) -> Any:
        """Get field value from data.
        
        Args:
            data: Data to extract field from
            field: Field path (e.g., 'user.name', 'items[0].id')
            
        Returns:
            Field value
        """
        if not isinstance(data, dict):
            return None
        
        parts = field.split('.')
        current = data
        
        for part in parts:
            if '[' in part and ']' in part:
                # Handle array access like 'items[0]'
                field_name = part[:part.index('[')]
                index = int(part[part.index('[') + 1:part.index(']')])
                
                if isinstance(current, dict) and field_name in current:
                    current = current[field_name]
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    return None
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current
    
    def _validate_required(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate required field."""
        if value is None or value == "":
            return ValidationResult(False, [f"Field is required"])
        return ValidationResult(True, [])
    
    def _validate_type(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate data type."""
        expected_type = rule.get('expected_type')
        if expected_type is None:
            return ValidationResult(True, [])
        
        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return ValidationResult(True, [], [f"Unknown type: {expected_type}"])
        
        if not isinstance(value, expected_python_type):
            return ValidationResult(False, [f"Expected {expected_type}, got {type(value).__name__}"])
        
        return ValidationResult(True, [])
    
    def _validate_format(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate format."""
        if not isinstance(value, str):
            return ValidationResult(True, [])
        
        format_type = rule.get('format')
        if format_type is None:
            return ValidationResult(True, [])
        
        format_validators = {
            'email': self._validate_email,
            'url': self._validate_url,
            'date': self._validate_date,
            'datetime': self._validate_datetime,
            'ip': self._validate_ip,
            'uuid': self._validate_uuid
        }
        
        validator = format_validators.get(format_type)
        if validator is None:
            return ValidationResult(True, [], [f"Unknown format: {format_type}"])
        
        if not validator(value):
            return ValidationResult(False, [f"Invalid {format_type} format"])
        
        return ValidationResult(True, [])
    
    def _validate_pattern(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate regex pattern."""
        if not isinstance(value, str):
            return ValidationResult(True, [])
        
        pattern = rule.get('pattern')
        if pattern is None:
            return ValidationResult(True, [])
        
        try:
            if not re.match(pattern, value):
                return ValidationResult(False, [f"Value does not match pattern: {pattern}"])
        except re.error as e:
            return ValidationResult(False, [f"Invalid regex pattern: {e}"])
        
        return ValidationResult(True, [])
    
    def _validate_range(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate numeric range."""
        if not isinstance(value, (int, float)):
            return ValidationResult(True, [])
        
        min_val = rule.get('min')
        max_val = rule.get('max')
        
        if min_val is not None and value < min_val:
            return ValidationResult(False, [f"Value {value} is less than minimum {min_val}"])
        
        if max_val is not None and value > max_val:
            return ValidationResult(False, [f"Value {value} is greater than maximum {max_val}"])
        
        return ValidationResult(True, [])
    
    def _validate_length(self, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate length."""
        if not hasattr(value, '__len__'):
            return ValidationResult(True, [])
        
        length = len(value)
        min_length = rule.get('min_length')
        max_length = rule.get('max_length')
        
        if min_length is not None and length < min_length:
            return ValidationResult(False, [f"Length {length} is less than minimum {min_length}"])
        
        if max_length is not None and length > max_length:
            return ValidationResult(False, [f"Length {length} is greater than maximum {max_length}"])
        
        return ValidationResult(True, [])
    
    def _validate_custom(self, value: Any, rule: Dict[str, Any], **kwargs) -> ValidationResult:
        """Validate using custom function."""
        custom_function = rule.get('function')
        if custom_function is None:
            return ValidationResult(True, [], ["No custom function provided"])
        
        try:
            if callable(custom_function):
                result = custom_function(value, **kwargs)
                if isinstance(result, bool):
                    return ValidationResult(result, [] if result else ["Custom validation failed"])
                elif isinstance(result, ValidationResult):
                    return result
                else:
                    return ValidationResult(True, [], ["Custom function returned unexpected result"])
            else:
                return ValidationResult(True, [], ["Custom function is not callable"])
        except Exception as e:
            return ValidationResult(False, [f"Custom validation error: {e}"])
    
    def _validate_email(self, value: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _validate_url(self, value: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, value))
    
    def _validate_date(self, value: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, value):
            return False
        
        try:
            from datetime import datetime
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _validate_datetime(self, value: str) -> bool:
        """Validate datetime format (ISO 8601)."""
        try:
            from datetime import datetime
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def _validate_ip(self, value: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, value))
    
    def _validate_uuid(self, value: str) -> bool:
        """Validate UUID format."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, value, re.IGNORECASE))


class SchemaValidator(BaseValidator):
    """JSON Schema validator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize schema validator."""
        super().__init__(config)
        self.schema = self.config.get('schema')
        self.strict_mode = self.config.get('strict_mode', True)
    
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """Validate data against JSON schema.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            Validation result
        """
        if self.schema is None:
            return ValidationResult(True, [], ["No schema provided"])
        
        try:
            validate(instance=data, schema=self.schema)
            return ValidationResult(True, [])
        except JsonSchemaError as e:
            error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            error_msg = f"Schema validation failed at {error_path}: {e.message}"
            return ValidationResult(False, [error_msg])
        except Exception as e:
            return ValidationResult(False, [f"Schema validation error: {e}"])
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate data from file against schema.
        
        Args:
            file_path: Path to file containing JSON data
            
        Returns:
            Validation result
        """
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            return self.validate(data)
        except FileNotFoundError:
            return ValidationResult(False, [f"File not found: {file_path}"])
        except json.JSONDecodeError as e:
            return ValidationResult(False, [f"Invalid JSON in file: {e}"])
        except Exception as e:
            return ValidationResult(False, [f"File validation error: {e}"])
    
    def load_schema_from_file(self, schema_path: str) -> None:
        """Load schema from file.
        
        Args:
            schema_path: Path to schema file
        """
        try:
            import json
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            raise ValidationError(f"Schema file not found: {schema_path}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON schema: {e}")
        except Exception as e:
            raise ValidationError(f"Schema loading error: {e}")


class DataQualityValidator(BaseValidator):
    """Data quality validator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data quality validator."""
        super().__init__(config)
        self.quality_thresholds = self.config.get('quality_thresholds', {})
        self.required_fields = self.config.get('required_fields', [])
        self.duplicate_check = self.config.get('duplicate_check', False)
        self.null_check = self.config.get('null_check', True)
    
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """Validate data quality.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        if isinstance(data, list):
            return self._validate_list(data, errors, warnings)
        elif isinstance(data, dict):
            return self._validate_dict(data, errors, warnings)
        else:
            return ValidationResult(True, [], ["Data quality validation only supports lists and dicts"])
    
    def _validate_list(self, data: List[Any], errors: List[str], warnings: List[str]) -> ValidationResult:
        """Validate list data quality."""
        if not data:
            return ValidationResult(True, [], ["Empty list"])
        
        # Check for duplicates
        if self.duplicate_check:
            seen = set()
            duplicates = []
            for i, item in enumerate(data):
                item_str = str(item)
                if item_str in seen:
                    duplicates.append(i)
                else:
                    seen.add(item_str)
            
            if duplicates:
                warnings.append(f"Found {len(duplicates)} duplicate items at indices: {duplicates}")
        
        # Check null values
        if self.null_check:
            null_count = sum(1 for item in data if item is None)
            if null_count > 0:
                null_percentage = (null_count / len(data)) * 100
                if null_percentage > self.quality_thresholds.get('max_null_percentage', 10):
                    errors.append(f"Too many null values: {null_percentage:.1f}%")
                else:
                    warnings.append(f"Found {null_count} null values ({null_percentage:.1f}%)")
        
        # Validate each item
        for i, item in enumerate(data):
            if isinstance(item, dict):
                item_result = self._validate_dict(item, [], [])
                if not item_result.is_valid:
                    errors.extend([f"Item {i}: {error}" for error in item_result.errors])
                warnings.extend([f"Item {i}: {warning}" for warning in item_result.warnings])
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _validate_dict(self, data: Dict[str, Any], errors: List[str], warnings: List[str]) -> ValidationResult:
        """Validate dict data quality."""
        # Check required fields
        missing_fields = [field for field in self.required_fields if field not in data]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Check null values
        if self.null_check:
            null_fields = [field for field, value in data.items() if value is None]
            if null_fields:
                null_percentage = (len(null_fields) / len(data)) * 100
                if null_percentage > self.quality_thresholds.get('max_null_percentage', 10):
                    errors.append(f"Too many null fields: {null_percentage:.1f}%")
                else:
                    warnings.append(f"Found {len(null_fields)} null fields ({null_percentage:.1f}%)")
        
        # Check data completeness
        completeness = self._calculate_completeness(data)
        min_completeness = self.quality_thresholds.get('min_completeness', 80)
        if completeness < min_completeness:
            errors.append(f"Data completeness {completeness:.1f}% below threshold {min_completeness}%")
        elif completeness < 100:
            warnings.append(f"Data completeness: {completeness:.1f}%")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness percentage."""
        if not data:
            return 0.0
        
        non_null_count = sum(1 for value in data.values() if value is not None and value != "")
        return (non_null_count / len(data)) * 100


class ValidationPipeline:
    """Validation pipeline for multiple validators."""
    
    def __init__(self, validators: List[BaseValidator]):
        """Initialize validation pipeline.
        
        Args:
            validators: List of validators to run
        """
        self.validators = validators
        self.logger = get_logger(self.__class__.__name__)
    
    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """Run data through validation pipeline.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation parameters
            
        Returns:
            Combined validation result
        """
        all_errors = []
        all_warnings = []
        
        for validator in self.validators:
            try:
                result = validator.validate(data, **kwargs)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
            except Exception as e:
                all_errors.append(f"Validator {validator.__class__.__name__} failed: {e}")
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Add validator to pipeline.
        
        Args:
            validator: Validator to add
        """
        self.validators.append(validator)
    
    def remove_validator(self, validator: BaseValidator) -> None:
        """Remove validator from pipeline.
        
        Args:
            validator: Validator to remove
        """
        if validator in self.validators:
            self.validators.remove(validator)
