"""Intelligent data validation system for SPIDER framework."""

import asyncio
import time
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime, date
import email_validator
import phonenumbers
from urllib.parse import urlparse

from ..core.exceptions import SpiderError, ValidationError
from ..core.logger import get_logger


class ValidationLevel(Enum):
    """Validation levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class ValidationType(Enum):
    """Validation types."""
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    CUSTOM = "custom"
    ML_BASED = "ml_based"
    STATISTICAL = "statistical"


class ValidationResult(Enum):
    """Validation results."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class ValidationRule:
    """Validation rule definition."""
    name: str
    validation_type: ValidationType
    rule: Union[str, Callable, Dict[str, Any]]
    level: ValidationLevel = ValidationLevel.MODERATE
    required: bool = False
    error_message: str = ""
    warning_message: str = ""
    weight: float = 1.0
    enabled: bool = True


@dataclass
class ValidationReport:
    """Validation report for a data item."""
    field_name: str
    value: Any
    is_valid: bool
    validation_level: ValidationLevel
    results: List[ValidationResult]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class DataQualityMetrics:
    """Data quality metrics."""
    total_fields: int = 0
    valid_fields: int = 0
    invalid_fields: int = 0
    warning_fields: int = 0
    quality_score: float = 0.0
    completeness: float = 0.0
    accuracy: float = 0.0
    consistency: float = 0.0
    timeliness: float = 0.0


class FormatValidator:
    """Validates data format and structure."""
    
    def __init__(self):
        """Initialize format validator."""
        self.logger = get_logger(self.__class__.__name__)
        self._setup_default_validators()
    
    def _setup_default_validators(self) -> None:
        """Setup default format validators."""
        self.validators = {
            "email": self._validate_email,
            "phone": self._validate_phone,
            "url": self._validate_url,
            "date": self._validate_date,
            "number": self._validate_number,
            "text": self._validate_text,
            "json": self._validate_json,
            "csv": self._validate_csv,
            "xml": self._validate_xml
        }
    
    def _validate_email(self, value: str) -> Tuple[bool, str]:
        """Validate email format."""
        try:
            email_validator.validate_email(value)
            return True, ""
        except email_validator.EmailNotValidError as e:
            return False, str(e)
    
    def _validate_phone(self, value: str) -> Tuple[bool, str]:
        """Validate phone number format."""
        try:
            parsed = phonenumbers.parse(value, None)
            if phonenumbers.is_valid_number(parsed):
                return True, ""
            else:
                return False, "Invalid phone number"
        except phonenumbers.NumberParseException as e:
            return False, str(e)
    
    def _validate_url(self, value: str) -> Tuple[bool, str]:
        """Validate URL format."""
        try:
            result = urlparse(value)
            if all([result.scheme, result.netloc]):
                return True, ""
            else:
                return False, "Invalid URL format"
        except Exception as e:
            return False, str(e)
    
    def _validate_date(self, value: str) -> Tuple[bool, str]:
        """Validate date format."""
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y",
            "%m-%d-%Y"
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(value, fmt)
                return True, ""
            except ValueError:
                continue
        
        return False, "Invalid date format"
    
    def _validate_number(self, value: Union[str, int, float]) -> Tuple[bool, str]:
        """Validate number format."""
        try:
            float(value)
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid number format"
    
    def _validate_text(self, value: str) -> Tuple[bool, str]:
        """Validate text format."""
        if not isinstance(value, str):
            return False, "Value must be a string"
        
        if len(value.strip()) == 0:
            return False, "Text cannot be empty"
        
        return True, ""
    
    def _validate_json(self, value: str) -> Tuple[bool, str]:
        """Validate JSON format."""
        try:
            json.loads(value)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    def _validate_csv(self, value: str) -> Tuple[bool, str]:
        """Validate CSV format."""
        lines = value.strip().split('\n')
        if len(lines) < 2:
            return False, "CSV must have at least 2 lines (header + data)"
        
        # Check if all lines have same number of columns
        first_line_columns = len(lines[0].split(','))
        for i, line in enumerate(lines[1:], 1):
            if len(line.split(',')) != first_line_columns:
                return False, f"Line {i+1} has different number of columns"
        
        return True, ""
    
    def _validate_xml(self, value: str) -> Tuple[bool, str]:
        """Validate XML format."""
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(value)
            return True, ""
        except ET.ParseError as e:
            return False, f"Invalid XML: {str(e)}"
    
    def validate(self, value: Any, format_type: str) -> Tuple[bool, str]:
        """Validate value against format type.
        
        Args:
            value: Value to validate
            format_type: Format type to validate against
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if format_type not in self.validators:
            return False, f"Unknown format type: {format_type}"
        
        try:
            return self.validators[format_type](value)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class RangeValidator:
    """Validates data ranges and constraints."""
    
    def __init__(self):
        """Initialize range validator."""
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_range(
        self, 
        value: Union[int, float], 
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> Tuple[bool, str]:
        """Validate value is within range.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                return False, f"Value {num_value} is below minimum {min_value}"
            
            if max_value is not None and num_value > max_value:
                return False, f"Value {num_value} is above maximum {max_value}"
            
            return True, ""
            
        except (ValueError, TypeError):
            return False, "Value must be a number"
    
    def validate_length(
        self, 
        value: str, 
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, "Value must be a string"
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            return False, f"Length {length} is below minimum {min_length}"
        
        if max_length is not None and length > max_length:
            return False, f"Length {length} is above maximum {max_length}"
        
        return True, ""
    
    def validate_list_size(
        self, 
        value: List[Any], 
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Validate list size.
        
        Args:
            value: List to validate
            min_size: Minimum allowed size
            max_size: Maximum allowed size
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, list):
            return False, "Value must be a list"
        
        size = len(value)
        
        if min_size is not None and size < min_size:
            return False, f"List size {size} is below minimum {min_size}"
        
        if max_size is not None and size > max_size:
            return False, f"List size {size} is above maximum {max_size}"
        
        return True, ""


class PatternValidator:
    """Validates data against patterns and regex."""
    
    def __init__(self):
        """Initialize pattern validator."""
        self.logger = get_logger(self.__class__.__name__)
        self._setup_default_patterns()
    
    def _setup_default_patterns(self) -> None:
        """Setup default validation patterns."""
        self.patterns = {
            "alphanumeric": r'^[a-zA-Z0-9]+$',
            "alphabetic": r'^[a-zA-Z]+$',
            "numeric": r'^[0-9]+$',
            "hexadecimal": r'^[0-9a-fA-F]+$',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            "credit_card": r'^[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}$',
            "ssn": r'^\d{3}-\d{2}-\d{4}$',
            "zip_code": r'^\d{5}(-\d{4})?$',
            "ip_address": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            "mac_address": r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        }
    
    def validate_pattern(self, value: str, pattern: str) -> Tuple[bool, str]:
        """Validate value against regex pattern.
        
        Args:
            value: Value to validate
            pattern: Regex pattern
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if re.match(pattern, value):
                return True, ""
            else:
                return False, f"Value does not match pattern: {pattern}"
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"
    
    def validate_named_pattern(self, value: str, pattern_name: str) -> Tuple[bool, str]:
        """Validate value against named pattern.
        
        Args:
            value: Value to validate
            pattern_name: Name of the pattern
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if pattern_name not in self.patterns:
            return False, f"Unknown pattern: {pattern_name}"
        
        return self.validate_pattern(value, self.patterns[pattern_name])
    
    def add_pattern(self, name: str, pattern: str) -> None:
        """Add custom pattern.
        
        Args:
            name: Pattern name
            pattern: Regex pattern
        """
        self.patterns[name] = pattern
        self.logger.info(f"Added pattern: {name}")


class StatisticalValidator:
    """Validates data using statistical methods."""
    
    def __init__(self):
        """Initialize statistical validator."""
        self.logger = get_logger(self.__class__.__name__)
        self.data_distributions: Dict[str, Dict[str, Any]] = {}
        self.outlier_threshold = 3.0  # Z-score threshold for outliers
    
    def add_training_data(self, field_name: str, values: List[Union[int, float]]) -> None:
        """Add training data for statistical validation.
        
        Args:
            field_name: Field name
            values: List of values
        """
        if not values:
            return
        
        numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
        
        if len(numeric_values) < 2:
            return
        
        distribution = {
            "mean": statistics.mean(numeric_values),
            "std": statistics.stdev(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "median": statistics.median(numeric_values),
            "count": len(numeric_values)
        }
        
        self.data_distributions[field_name] = distribution
        self.logger.info(f"Added statistical distribution for {field_name}")
    
    def validate_outlier(
        self, 
        value: Union[int, float], 
        field_name: str
    ) -> Tuple[bool, str]:
        """Validate if value is an outlier.
        
        Args:
            value: Value to validate
            field_name: Field name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if field_name not in self.data_distributions:
            return True, ""  # No training data, assume valid
        
        try:
            num_value = float(value)
            distribution = self.data_distributions[field_name]
            
            # Calculate Z-score
            z_score = abs((num_value - distribution["mean"]) / distribution["std"])
            
            if z_score > self.outlier_threshold:
                return False, f"Value {num_value} is an outlier (Z-score: {z_score:.2f})"
            
            return True, ""
            
        except (ValueError, TypeError):
            return False, "Value must be numeric for outlier detection"
    
    def validate_range_statistical(
        self, 
        value: Union[int, float], 
        field_name: str,
        confidence_level: float = 0.95
    ) -> Tuple[bool, str]:
        """Validate value is within statistical range.
        
        Args:
            value: Value to validate
            field_name: Field name
            confidence_level: Confidence level for range
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if field_name not in self.data_distributions:
            return True, ""  # No training data, assume valid
        
        try:
            num_value = float(value)
            distribution = self.data_distributions[field_name]
            
            # Calculate confidence interval
            z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%
            margin = z_score * distribution["std"]
            
            lower_bound = distribution["mean"] - margin
            upper_bound = distribution["mean"] + margin
            
            if num_value < lower_bound or num_value > upper_bound:
                return False, f"Value {num_value} is outside statistical range [{lower_bound:.2f}, {upper_bound:.2f}]"
            
            return True, ""
            
        except (ValueError, TypeError):
            return False, "Value must be numeric for statistical validation"


class MLBasedValidator:
    """Machine learning-based validation."""
    
    def __init__(self):
        """Initialize ML-based validator."""
        self.logger = get_logger(self.__class__.__name__)
        self.models: Dict[str, Any] = {}
        self.training_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.feature_extractors: Dict[str, Callable] = {}
        self._setup_default_feature_extractors()
    
    def _setup_default_feature_extractors(self) -> None:
        """Setup default feature extractors."""
        self.feature_extractors = {
            "length": lambda x: len(str(x)),
            "word_count": lambda x: len(str(x).split()),
            "has_digits": lambda x: bool(re.search(r'\d', str(x))),
            "has_special_chars": lambda x: bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', str(x))),
            "is_uppercase": lambda x: str(x).isupper(),
            "is_lowercase": lambda x: str(x).islower(),
            "has_spaces": lambda x: ' ' in str(x),
            "is_numeric": lambda x: str(x).replace('.', '').replace('-', '').isdigit(),
            "is_alpha": lambda x: str(x).isalpha(),
            "is_alphanumeric": lambda x: str(x).isalnum()
        }
    
    def add_training_data(self, field_name: str, value: Any, is_valid: bool) -> None:
        """Add training data for ML model.
        
        Args:
            field_name: Field name
            value: Input value
            is_valid: Whether the value is valid
        """
        features = self._extract_features(value)
        
        training_sample = {
            "value": value,
            "is_valid": is_valid,
            "features": features,
            "timestamp": time.time()
        }
        
        self.training_data[field_name].append(training_sample)
        self.logger.debug(f"Added training data for {field_name}: {is_valid}")
    
    def _extract_features(self, value: Any) -> Dict[str, Any]:
        """Extract features from value.
        
        Args:
            value: Input value
            
        Returns:
            Feature dictionary
        """
        features = {}
        
        for feature_name, extractor in self.feature_extractors.items():
            try:
                features[feature_name] = extractor(value)
            except Exception as e:
                self.logger.warning(f"Feature extraction failed for {feature_name}: {e}")
                features[feature_name] = 0
        
        return features
    
    def train_model(self, field_name: str) -> bool:
        """Train ML model for field validation.
        
        Args:
            field_name: Field name
            
        Returns:
            True if training successful
        """
        if field_name not in self.training_data or len(self.training_data[field_name]) < 10:
            self.logger.warning(f"Insufficient training data for {field_name}")
            return False
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            
            # Prepare training data
            X = []
            y = []
            
            for sample in self.training_data[field_name]:
                features = list(sample["features"].values())
                X.append(features)
                y.append(sample["is_valid"])
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Calculate accuracy
            accuracy = model.score(X_test, y_test)
            
            # Save model
            self.models[field_name] = {
                "model": model,
                "accuracy": accuracy,
                "features": list(self.feature_extractors.keys())
            }
            
            self.logger.info(f"Trained ML model for {field_name} with accuracy: {accuracy:.3f}")
            return True
            
        except Exception as e:
            self.logger.error(f"ML model training failed for {field_name}: {e}")
            return False
    
    def validate_ml(self, value: Any, field_name: str) -> Tuple[bool, str, float]:
        """Validate value using ML model.
        
        Args:
            value: Value to validate
            field_name: Field name
            
        Returns:
            Tuple of (is_valid, error_message, confidence)
        """
        if field_name not in self.models:
            return True, "", 0.5  # No model, assume valid with low confidence
        
        try:
            model_info = self.models[field_name]
            model = model_info["model"]
            
            # Extract features
            features = self._extract_features(value)
            feature_vector = np.array([list(features.values())])
            
            # Make prediction
            prediction = model.predict(feature_vector)[0]
            confidence = max(model.predict_proba(feature_vector)[0])
            
            is_valid = bool(prediction)
            error_message = "" if is_valid else "ML model predicts invalid value"
            
            return is_valid, error_message, confidence
            
        except Exception as e:
            self.logger.error(f"ML validation failed for {field_name}: {e}")
            return True, "", 0.0


class IntelligentValidator:
    """Intelligent data validation system."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        """Initialize intelligent validator.
        
        Args:
            validation_level: Default validation level
        """
        self.logger = get_logger(self.__class__.__name__)
        self.validation_level = validation_level
        self.rules: Dict[str, List[ValidationRule]] = defaultdict(list)
        self.format_validator = FormatValidator()
        self.range_validator = RangeValidator()
        self.pattern_validator = PatternValidator()
        self.statistical_validator = StatisticalValidator()
        self.ml_validator = MLBasedValidator()
        self.validation_history: deque = deque(maxlen=10000)
        self.quality_metrics: Dict[str, DataQualityMetrics] = {}
    
    def add_rule(self, field_name: str, rule: ValidationRule) -> None:
        """Add validation rule for field.
        
        Args:
            field_name: Field name
            rule: Validation rule
        """
        self.rules[field_name].append(rule)
        self.logger.info(f"Added validation rule for {field_name}: {rule.name}")
    
    def remove_rule(self, field_name: str, rule_name: str) -> bool:
        """Remove validation rule.
        
        Args:
            field_name: Field name
            rule_name: Rule name
            
        Returns:
            True if removed, False if not found
        """
        for i, rule in enumerate(self.rules[field_name]):
            if rule.name == rule_name:
                del self.rules[field_name][i]
                self.logger.info(f"Removed validation rule: {rule_name}")
                return True
        return False
    
    async def validate_field(
        self, 
        field_name: str, 
        value: Any,
        validation_level: Optional[ValidationLevel] = None
    ) -> ValidationReport:
        """Validate a single field.
        
        Args:
            field_name: Field name
            value: Value to validate
            validation_level: Optional validation level override
            
        Returns:
            Validation report
        """
        level = validation_level or self.validation_level
        start_time = time.time()
        
        errors = []
        warnings = []
        results = []
        total_score = 0.0
        total_weight = 0.0
        
        # Get rules for field
        field_rules = self.rules.get(field_name, [])
        
        # If no rules, use default validation
        if not field_rules:
            field_rules = self._get_default_rules(field_name, value)
        
        for rule in field_rules:
            if not rule.enabled:
                continue
            
            try:
                is_valid, error_msg, warning_msg = await self._validate_rule(rule, value)
                
                if is_valid:
                    results.append(ValidationResult.VALID)
                elif rule.level == ValidationLevel.STRICT:
                    results.append(ValidationResult.INVALID)
                    errors.append(f"{rule.name}: {error_msg or rule.error_message}")
                else:
                    results.append(ValidationResult.WARNING)
                    warnings.append(f"{rule.name}: {warning_msg or rule.warning_message}")
                
                # Calculate weighted score
                rule_score = 1.0 if is_valid else 0.0
                total_score += rule_score * rule.weight
                total_weight += rule.weight
                
            except Exception as e:
                self.logger.error(f"Rule validation failed for {rule.name}: {e}")
                results.append(ValidationResult.INVALID)
                errors.append(f"Rule {rule.name} failed: {str(e)}")
        
        # Calculate overall score
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine overall validity
        is_valid = len(errors) == 0 and (level == ValidationLevel.LENIENT or len(warnings) == 0)
        
        report = ValidationReport(
            field_name=field_name,
            value=value,
            is_valid=is_valid,
            validation_level=level,
            results=results,
            errors=errors,
            warnings=warnings,
            score=final_score,
            metadata={
                "duration": time.time() - start_time,
                "rules_count": len(field_rules),
                "validation_level": level.value
            }
        )
        
        # Record validation history
        self.validation_history.append({
            "timestamp": time.time(),
            "field_name": field_name,
            "is_valid": is_valid,
            "score": final_score,
            "errors_count": len(errors),
            "warnings_count": len(warnings)
        })
        
        return report
    
    async def _validate_rule(self, rule: ValidationRule, value: Any) -> Tuple[bool, str, str]:
        """Validate value against a single rule.
        
        Args:
            rule: Validation rule
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message, warning_message)
        """
        if rule.validation_type == ValidationType.FORMAT:
            is_valid, error_msg = self.format_validator.validate(value, rule.rule)
            return is_valid, error_msg, ""
        
        elif rule.validation_type == ValidationType.RANGE:
            if isinstance(rule.rule, dict):
                is_valid, error_msg = self.range_validator.validate_range(
                    value, 
                    rule.rule.get("min"), 
                    rule.rule.get("max")
                )
            else:
                is_valid, error_msg = True, ""
            return is_valid, error_msg, ""
        
        elif rule.validation_type == ValidationType.PATTERN:
            is_valid, error_msg = self.pattern_validator.validate_pattern(value, rule.rule)
            return is_valid, error_msg, ""
        
        elif rule.validation_type == ValidationType.CUSTOM:
            if callable(rule.rule):
                try:
                    result = rule.rule(value)
                    if isinstance(result, bool):
                        return result, "", ""
                    elif isinstance(result, tuple) and len(result) == 2:
                        return result[0], result[1], ""
                    elif isinstance(result, tuple) and len(result) == 3:
                        return result[0], result[1], result[2]
                except Exception as e:
                    return False, f"Custom validation error: {str(e)}", ""
            return False, "Invalid custom rule", ""
        
        elif rule.validation_type == ValidationType.ML_BASED:
            is_valid, error_msg, confidence = self.ml_validator.validate_ml(value, rule.name)
            return is_valid, error_msg, f"ML confidence: {confidence:.2f}"
        
        elif rule.validation_type == ValidationType.STATISTICAL:
            is_valid, error_msg = self.statistical_validator.validate_outlier(value, rule.name)
            return is_valid, error_msg, ""
        
        return True, "", ""
    
    def _get_default_rules(self, field_name: str, value: Any) -> List[ValidationRule]:
        """Get default validation rules for field.
        
        Args:
            field_name: Field name
            value: Value to validate
            
        Returns:
            List of default rules
        """
        rules = []
        
        # Basic type validation
        if isinstance(value, str):
            rules.append(ValidationRule(
                name="text_format",
                validation_type=ValidationType.FORMAT,
                rule="text",
                level=ValidationLevel.MODERATE
            ))
        elif isinstance(value, (int, float)):
            rules.append(ValidationRule(
                name="number_format",
                validation_type=ValidationType.FORMAT,
                rule="number",
                level=ValidationLevel.MODERATE
            ))
        
        return rules
    
    async def validate_dataset(
        self, 
        data: Dict[str, Any],
        validation_level: Optional[ValidationLevel] = None
    ) -> Dict[str, ValidationReport]:
        """Validate entire dataset.
        
        Args:
            data: Dataset to validate
            validation_level: Optional validation level override
            
        Returns:
            Dictionary of validation reports
        """
        reports = {}
        
        for field_name, value in data.items():
            report = await self.validate_field(field_name, value, validation_level)
            reports[field_name] = report
        
        # Update quality metrics
        self._update_quality_metrics(reports)
        
        return reports
    
    def _update_quality_metrics(self, reports: Dict[str, ValidationReport]) -> None:
        """Update data quality metrics.
        
        Args:
            reports: Validation reports
        """
        total_fields = len(reports)
        valid_fields = sum(1 for r in reports.values() if r.is_valid)
        invalid_fields = sum(1 for r in reports.values() if not r.is_valid and r.errors)
        warning_fields = sum(1 for r in reports.values() if r.warnings and not r.errors)
        
        quality_score = sum(r.score for r in reports.values()) / total_fields if total_fields > 0 else 0.0
        completeness = valid_fields / total_fields if total_fields > 0 else 0.0
        accuracy = valid_fields / total_fields if total_fields > 0 else 0.0
        
        metrics = DataQualityMetrics(
            total_fields=total_fields,
            valid_fields=valid_fields,
            invalid_fields=invalid_fields,
            warning_fields=warning_fields,
            quality_score=quality_score,
            completeness=completeness,
            accuracy=accuracy,
            consistency=1.0 - (warning_fields / total_fields) if total_fields > 0 else 1.0,
            timeliness=1.0  # Placeholder for timeliness
        )
        
        self.quality_metrics["latest"] = metrics
    
    def get_quality_metrics(self) -> Dict[str, DataQualityMetrics]:
        """Get data quality metrics.
        
        Returns:
            Data quality metrics
        """
        return self.quality_metrics
    
    def get_validation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get validation history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of validation records
        """
        return list(self.validation_history)[-limit:]
    
    def add_training_data(self, field_name: str, value: Any, is_valid: bool) -> None:
        """Add training data for ML validation.
        
        Args:
            field_name: Field name
            value: Input value
            is_valid: Whether the value is valid
        """
        self.ml_validator.add_training_data(field_name, value, is_valid)
    
    def train_ml_models(self, field_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Train ML models for validation.
        
        Args:
            field_names: Optional list of field names to train
            
        Returns:
            Dictionary of training results
        """
        return self.ml_validator.train_model(field_names[0]) if field_names else {}
    
    def cleanup(self) -> None:
        """Cleanup validator."""
        self.validation_history.clear()
        self.quality_metrics.clear()
        self.logger.info("Intelligent validator cleaned up")
