"""Machine learning-based data extraction for SPIDER framework."""

import asyncio
import time
import json
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import numpy as np
from collections import defaultdict, deque
import re
import hashlib

from ..core.exceptions import SpiderError, ValidationError
from ..core.logger import get_logger


class ExtractionMethod(Enum):
    """Data extraction methods."""
    RULE_BASED = "rule_based"
    ML_CLASSIFICATION = "ml_classification"
    ML_REGRESSION = "ml_regression"
    ML_CLUSTERING = "ml_clustering"
    ML_NLP = "ml_nlp"
    HYBRID = "hybrid"


class DataType(Enum):
    """Data types for extraction."""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    DATE = "date"
    PRICE = "price"
    ADDRESS = "address"
    NAME = "name"
    CUSTOM = "custom"


@dataclass
class ExtractionRule:
    """Rule for data extraction."""
    name: str
    pattern: str
    data_type: DataType
    confidence: float = 1.0
    required: bool = False
    transform: Optional[Callable] = None
    validation: Optional[Callable] = None


@dataclass
class ExtractionResult:
    """Result of data extraction."""
    field_name: str
    value: Any
    confidence: float
    method: ExtractionMethod
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class MLModel:
    """Machine learning model for extraction."""
    name: str
    model_type: str
    model_data: bytes
    features: List[str]
    accuracy: float
    created_at: float
    version: str = "1.0.0"


class RuleBasedExtractor:
    """Rule-based data extraction using regex patterns."""
    
    def __init__(self):
        """Initialize rule-based extractor."""
        self.logger = get_logger(self.__class__.__name__)
        self.rules: Dict[str, ExtractionRule] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default extraction rules."""
        # Email extraction
        self.add_rule(ExtractionRule(
            name="email",
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            data_type=DataType.EMAIL,
            confidence=0.9
        ))
        
        # Phone number extraction
        self.add_rule(ExtractionRule(
            name="phone",
            pattern=r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            data_type=DataType.PHONE,
            confidence=0.8
        ))
        
        # URL extraction
        self.add_rule(ExtractionRule(
            name="url",
            pattern=r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            data_type=DataType.URL,
            confidence=0.9
        ))
        
        # Price extraction
        self.add_rule(ExtractionRule(
            name="price",
            pattern=r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            data_type=DataType.PRICE,
            confidence=0.7,
            transform=lambda x: float(x.replace('$', '').replace(',', ''))
        ))
        
        # Date extraction
        self.add_rule(ExtractionRule(
            name="date",
            pattern=r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            data_type=DataType.DATE,
            confidence=0.6
        ))
    
    def add_rule(self, rule: ExtractionRule) -> None:
        """Add extraction rule.
        
        Args:
            rule: Extraction rule to add
        """
        self.rules[rule.name] = rule
        self.logger.info(f"Added extraction rule: {rule.name}")
    
    def remove_rule(self, name: str) -> bool:
        """Remove extraction rule.
        
        Args:
            name: Rule name
            
        Returns:
            True if removed, False if not found
        """
        if name in self.rules:
            del self.rules[name]
            self.logger.info(f"Removed extraction rule: {name}")
            return True
        return False
    
    async def extract(self, text: str, field_name: str) -> List[ExtractionResult]:
        """Extract data using rules.
        
        Args:
            text: Text to extract from
            field_name: Name of the field being extracted
            
        Returns:
            List of extraction results
        """
        results = []
        
        for rule_name, rule in self.rules.items():
            try:
                matches = re.finditer(rule.pattern, text, re.IGNORECASE)
                
                for match in matches:
                    value = match.group(0)
                    
                    # Apply transformation if defined
                    if rule.transform:
                        try:
                            value = rule.transform(value)
                        except Exception as e:
                            self.logger.warning(f"Transform failed for {rule_name}: {e}")
                            continue
                    
                    # Apply validation if defined
                    if rule.validation and not rule.validation(value):
                        continue
                    
                    result = ExtractionResult(
                        field_name=field_name,
                        value=value,
                        confidence=rule.confidence,
                        method=ExtractionMethod.RULE_BASED,
                        metadata={
                            "rule_name": rule_name,
                            "data_type": rule.data_type.value,
                            "match_start": match.start(),
                            "match_end": match.end()
                        }
                    )
                    results.append(result)
                    
            except Exception as e:
                self.logger.error(f"Error in rule {rule_name}: {e}")
        
        return results


class MLBasedExtractor:
    """Machine learning-based data extraction."""
    
    def __init__(self):
        """Initialize ML-based extractor."""
        self.logger = get_logger(self.__class__.__name__)
        self.models: Dict[str, MLModel] = {}
        self.training_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.feature_extractors: Dict[str, Callable] = {}
        self._setup_default_feature_extractors()
    
    def _setup_default_feature_extractors(self) -> None:
        """Setup default feature extractors."""
        self.feature_extractors["text_length"] = lambda x: len(str(x))
        self.feature_extractors["word_count"] = lambda x: len(str(x).split())
        self.feature_extractors["has_digits"] = lambda x: bool(re.search(r'\d', str(x)))
        self.feature_extractors["has_special_chars"] = lambda x: bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', str(x)))
        self.feature_extractors["is_uppercase"] = lambda x: str(x).isupper()
        self.feature_extractors["is_lowercase"] = lambda x: str(x).islower()
        self.feature_extractors["has_spaces"] = lambda x: ' ' in str(x)
        self.feature_extractors["has_at_symbol"] = lambda x: '@' in str(x)
        self.feature_extractors["has_dollar_sign"] = lambda x: '$' in str(x)
        self.feature_extractors["has_http"] = lambda x: 'http' in str(x).lower()
    
    def add_training_data(self, field_name: str, text: str, label: str, features: Optional[Dict[str, Any]] = None) -> None:
        """Add training data for ML model.
        
        Args:
            field_name: Field name
            text: Input text
            label: Expected label/class
            features: Optional pre-computed features
        """
        if features is None:
            features = self._extract_features(text)
        
        training_sample = {
            "text": text,
            "label": label,
            "features": features,
            "timestamp": time.time()
        }
        
        self.training_data[field_name].append(training_sample)
        self.logger.debug(f"Added training data for {field_name}: {label}")
    
    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extract features from text.
        
        Args:
            text: Input text
            
        Returns:
            Feature dictionary
        """
        features = {}
        
        for feature_name, extractor in self.feature_extractors.items():
            try:
                features[feature_name] = extractor(text)
            except Exception as e:
                self.logger.warning(f"Feature extraction failed for {feature_name}: {e}")
                features[feature_name] = 0
        
        return features
    
    def train_model(self, field_name: str, model_type: str = "classification") -> bool:
        """Train ML model for field extraction.
        
        Args:
            field_name: Field name
            model_type: Type of ML model
            
        Returns:
            True if training successful
        """
        if field_name not in self.training_data or len(self.training_data[field_name]) < 10:
            self.logger.warning(f"Insufficient training data for {field_name}")
            return False
        
        try:
            # Prepare training data
            X = []
            y = []
            
            for sample in self.training_data[field_name]:
                features = list(sample["features"].values())
                X.append(features)
                y.append(sample["label"])
            
            X = np.array(X)
            y = np.array(y)
            
            # Train model based on type
            if model_type == "classification":
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif model_type == "regression":
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            else:
                self.logger.error(f"Unknown model type: {model_type}")
                return False
            
            model.fit(X, y)
            
            # Calculate accuracy
            accuracy = model.score(X, y)
            
            # Save model
            model_data = pickle.dumps(model)
            feature_names = list(self.feature_extractors.keys())
            
            ml_model = MLModel(
                name=f"{field_name}_{model_type}",
                model_type=model_type,
                model_data=model_data,
                features=feature_names,
                accuracy=accuracy,
                created_at=time.time()
            )
            
            self.models[field_name] = ml_model
            
            self.logger.info(f"Trained {model_type} model for {field_name} with accuracy: {accuracy:.3f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Model training failed for {field_name}: {e}")
            return False
    
    async def extract(self, text: str, field_name: str) -> List[ExtractionResult]:
        """Extract data using ML model.
        
        Args:
            text: Text to extract from
            field_name: Name of the field being extracted
            
        Returns:
            List of extraction results
        """
        if field_name not in self.models:
            self.logger.warning(f"No trained model for {field_name}")
            return []
        
        try:
            model = self.models[field_name]
            loaded_model = pickle.loads(model.model_data)
            
            # Extract features
            features = self._extract_features(text)
            feature_vector = np.array([list(features.values())])
            
            # Make prediction
            if model.model_type == "classification":
                prediction = loaded_model.predict(feature_vector)[0]
                confidence = max(loaded_model.predict_proba(feature_vector)[0])
            else:
                prediction = loaded_model.predict(feature_vector)[0]
                confidence = 0.8  # Default confidence for regression
            
            result = ExtractionResult(
                field_name=field_name,
                value=prediction,
                confidence=confidence,
                method=ExtractionMethod.ML_CLASSIFICATION if model.model_type == "classification" else ExtractionMethod.ML_REGRESSION,
                metadata={
                    "model_name": model.name,
                    "model_accuracy": model.accuracy,
                    "features": features
                }
            )
            
            return [result]
            
        except Exception as e:
            self.logger.error(f"ML extraction failed for {field_name}: {e}")
            return []


class NLPBasedExtractor:
    """Natural Language Processing-based extraction."""
    
    def __init__(self):
        """Initialize NLP-based extractor."""
        self.logger = get_logger(self.__class__.__name__)
        self.named_entities = {}
        self._setup_default_entities()
    
    def _setup_default_entities(self) -> None:
        """Setup default named entity patterns."""
        self.named_entities = {
            "person": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "organization": r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Co\.)\b',
            "location": r'\b(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            "url": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            "price": r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            "percentage": r'\b\d+(?:\.\d+)?%\b',
            "number": r'\b\d+(?:\.\d+)?\b'
        }
    
    async def extract_entities(self, text: str) -> List[ExtractionResult]:
        """Extract named entities from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            List of extraction results
        """
        results = []
        
        for entity_type, pattern in self.named_entities.items():
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    value = match.group(0)
                    
                    # Calculate confidence based on pattern complexity
                    confidence = self._calculate_confidence(entity_type, value)
                    
                    result = ExtractionResult(
                        field_name=entity_type,
                        value=value,
                        confidence=confidence,
                        method=ExtractionMethod.ML_NLP,
                        metadata={
                            "entity_type": entity_type,
                            "match_start": match.start(),
                            "match_end": match.end(),
                            "pattern": pattern
                        }
                    )
                    results.append(result)
                    
            except Exception as e:
                self.logger.error(f"Entity extraction failed for {entity_type}: {e}")
        
        return results
    
    def _calculate_confidence(self, entity_type: str, value: str) -> float:
        """Calculate confidence for extracted entity.
        
        Args:
            entity_type: Type of entity
            value: Extracted value
            
        Returns:
            Confidence score
        """
        base_confidence = {
            "email": 0.9,
            "phone": 0.8,
            "url": 0.9,
            "date": 0.7,
            "price": 0.8,
            "percentage": 0.9,
            "number": 0.6,
            "person": 0.5,
            "organization": 0.6,
            "location": 0.4
        }
        
        confidence = base_confidence.get(entity_type, 0.5)
        
        # Adjust based on value characteristics
        if entity_type == "email" and "@" in value and "." in value:
            confidence += 0.1
        elif entity_type == "phone" and len(re.sub(r'\D', '', value)) >= 10:
            confidence += 0.1
        elif entity_type == "url" and value.startswith(('http://', 'https://')):
            confidence += 0.1
        
        return min(1.0, confidence)


class HybridExtractor:
    """Hybrid extractor combining multiple methods."""
    
    def __init__(self):
        """Initialize hybrid extractor."""
        self.logger = get_logger(self.__class__.__name__)
        self.rule_extractor = RuleBasedExtractor()
        self.ml_extractor = MLBasedExtractor()
        self.nlp_extractor = NLPBasedExtractor()
        self.confidence_threshold = 0.5
        self.method_weights = {
            ExtractionMethod.RULE_BASED: 0.3,
            ExtractionMethod.ML_CLASSIFICATION: 0.4,
            ExtractionMethod.ML_REGRESSION: 0.4,
            ExtractionMethod.ML_NLP: 0.3
        }
    
    async def extract(
        self, 
        text: str, 
        field_name: str,
        methods: Optional[List[ExtractionMethod]] = None
    ) -> List[ExtractionResult]:
        """Extract data using hybrid approach.
        
        Args:
            text: Text to extract from
            field_name: Name of the field being extracted
            methods: Optional list of methods to use
            
        Returns:
            List of extraction results
        """
        if methods is None:
            methods = [
                ExtractionMethod.RULE_BASED,
                ExtractionMethod.ML_CLASSIFICATION,
                ExtractionMethod.ML_NLP
            ]
        
        all_results = []
        
        # Run all specified methods
        if ExtractionMethod.RULE_BASED in methods:
            rule_results = await self.rule_extractor.extract(text, field_name)
            all_results.extend(rule_results)
        
        if ExtractionMethod.ML_CLASSIFICATION in methods or ExtractionMethod.ML_REGRESSION in methods:
            ml_results = await self.ml_extractor.extract(text, field_name)
            all_results.extend(ml_results)
        
        if ExtractionMethod.ML_NLP in methods:
            nlp_results = await self.nlp_extractor.extract_entities(text)
            all_results.extend(nlp_results)
        
        # Merge and rank results
        merged_results = self._merge_results(all_results)
        
        # Filter by confidence threshold
        filtered_results = [
            result for result in merged_results
            if result.confidence >= self.confidence_threshold
        ]
        
        return filtered_results
    
    def _merge_results(self, results: List[ExtractionResult]) -> List[ExtractionResult]:
        """Merge and rank extraction results.
        
        Args:
            results: List of extraction results
            
        Returns:
            Merged and ranked results
        """
        # Group by field name and value
        grouped = defaultdict(list)
        
        for result in results:
            key = (result.field_name, str(result.value).lower())
            grouped[key].append(result)
        
        merged_results = []
        
        for (field_name, value), group in grouped.items():
            if len(group) == 1:
                merged_results.append(group[0])
            else:
                # Merge multiple results for same field/value
                merged_result = self._merge_group(group)
                merged_results.append(merged_result)
        
        # Sort by confidence
        merged_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return merged_results
    
    def _merge_group(self, group: List[ExtractionResult]) -> ExtractionResult:
        """Merge a group of results.
        
        Args:
            group: Group of results to merge
            
        Returns:
            Merged result
        """
        # Use the result with highest confidence as base
        base_result = max(group, key=lambda x: x.confidence)
        
        # Calculate weighted average confidence
        total_weight = 0
        weighted_confidence = 0
        
        for result in group:
            weight = self.method_weights.get(result.method, 0.5)
            weighted_confidence += result.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            base_result.confidence = weighted_confidence / total_weight
        
        # Merge metadata
        merged_metadata = base_result.metadata.copy()
        merged_metadata["merged_methods"] = [r.method.value for r in group]
        merged_metadata["original_confidences"] = [r.confidence for r in group]
        
        base_result.metadata = merged_metadata
        base_result.method = ExtractionMethod.HYBRID
        
        return base_result
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """Set confidence threshold for filtering results.
        
        Args:
            threshold: Confidence threshold (0.0 to 1.0)
        """
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"Set confidence threshold to {self.confidence_threshold}")
    
    def set_method_weight(self, method: ExtractionMethod, weight: float) -> None:
        """Set weight for a specific extraction method.
        
        Args:
            method: Extraction method
            weight: Weight (0.0 to 1.0)
        """
        self.method_weights[method] = max(0.0, min(1.0, weight))
        self.logger.info(f"Set weight for {method.value} to {weight}")


class MLExtractionManager:
    """Manager for ML-based data extraction."""
    
    def __init__(self):
        """Initialize ML extraction manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.hybrid_extractor = HybridExtractor()
        self.extraction_history: deque = deque(maxlen=10000)
        self.performance_stats = defaultdict(list)
    
    async def extract_data(
        self, 
        text: str, 
        field_name: str,
        methods: Optional[List[ExtractionMethod]] = None
    ) -> List[ExtractionResult]:
        """Extract data from text.
        
        Args:
            text: Text to extract from
            field_name: Name of the field being extracted
            methods: Optional list of methods to use
            
        Returns:
            List of extraction results
        """
        start_time = time.time()
        
        try:
            results = await self.hybrid_extractor.extract(text, field_name, methods)
            
            # Record performance
            duration = time.time() - start_time
            self.performance_stats[field_name].append(duration)
            
            # Record extraction history
            extraction_record = {
                "timestamp": time.time(),
                "field_name": field_name,
                "text_length": len(text),
                "results_count": len(results),
                "duration": duration,
                "methods": [m.value for m in (methods or [])]
            }
            self.extraction_history.append(extraction_record)
            
            self.logger.info(f"Extracted {len(results)} results for {field_name} in {duration:.3f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Data extraction failed for {field_name}: {e}")
            return []
    
    def add_training_data(self, field_name: str, text: str, label: str) -> None:
        """Add training data for ML models.
        
        Args:
            field_name: Field name
            text: Input text
            label: Expected label
        """
        self.hybrid_extractor.ml_extractor.add_training_data(field_name, text, label)
    
    def train_models(self, field_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Train ML models for specified fields.
        
        Args:
            field_names: Optional list of field names to train
            
        Returns:
            Dictionary of training results
        """
        results = {}
        
        if field_names is None:
            field_names = list(self.hybrid_extractor.ml_extractor.training_data.keys())
        
        for field_name in field_names:
            try:
                success = self.hybrid_extractor.ml_extractor.train_model(field_name)
                results[field_name] = success
            except Exception as e:
                self.logger.error(f"Training failed for {field_name}: {e}")
                results[field_name] = False
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics.
        
        Returns:
            Performance statistics
        """
        stats = {}
        
        for field_name, durations in self.performance_stats.items():
            if durations:
                stats[field_name] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations)
                }
        
        return stats
    
    def get_extraction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get extraction history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of extraction records
        """
        return list(self.extraction_history)[-limit:]
    
    def cleanup(self) -> None:
        """Cleanup extraction manager."""
        self.extraction_history.clear()
        self.performance_stats.clear()
        self.logger.info("ML extraction manager cleaned up")
