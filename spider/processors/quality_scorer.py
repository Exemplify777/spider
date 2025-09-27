"""Data quality scoring system for SPIDER framework."""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime, timedelta
import re

from ..core.exceptions import SpiderError, ValidationError
from ..core.logger import get_logger


class QualityDimension(Enum):
    """Data quality dimensions."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"
    RELEVANCE = "relevance"
    PRECISION = "precision"


class QualityLevel(Enum):
    """Quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """Quality metric definition."""
    name: str
    dimension: QualityDimension
    weight: float = 1.0
    threshold_excellent: float = 0.9
    threshold_good: float = 0.7
    threshold_fair: float = 0.5
    threshold_poor: float = 0.3
    enabled: bool = True


@dataclass
class QualityScore:
    """Quality score for a dimension."""
    dimension: QualityDimension
    score: float
    level: QualityLevel
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class OverallQualityScore:
    """Overall quality score."""
    total_score: float
    level: QualityLevel
    dimension_scores: Dict[QualityDimension, QualityScore]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class CompletenessScorer:
    """Scores data completeness."""
    
    def __init__(self):
        """Initialize completeness scorer."""
        self.logger = get_logger(self.__class__.__name__)
    
    def calculate_completeness(self, data: List[Dict[str, Any]], required_fields: List[str]) -> QualityScore:
        """Calculate completeness score.
        
        Args:
            data: Input data
            required_fields: List of required fields
            
        Returns:
            Completeness quality score
        """
        if not data:
            return QualityScore(
                dimension=QualityDimension.COMPLETENESS,
                score=0.0,
                level=QualityLevel.CRITICAL,
                details={"error": "No data provided"}
            )
        
        total_records = len(data)
        total_fields = len(required_fields)
        total_possible_values = total_records * total_fields
        
        # Count missing values
        missing_values = 0
        field_completeness = {}
        
        for field in required_fields:
            field_missing = 0
            for record in data:
                if field not in record or record[field] is None or record[field] == "":
                    field_missing += 1
                    missing_values += 1
            
            field_completeness[field] = 1.0 - (field_missing / total_records)
        
        # Calculate overall completeness
        completeness_score = 1.0 - (missing_values / total_possible_values)
        
        # Determine quality level
        level = self._get_quality_level(completeness_score)
        
        # Generate recommendations
        recommendations = self._get_completeness_recommendations(field_completeness, completeness_score)
        
        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            level=level,
            details={
                "total_records": total_records,
                "total_fields": total_fields,
                "missing_values": missing_values,
                "field_completeness": field_completeness,
                "completeness_percentage": completeness_score * 100
            },
            recommendations=recommendations
        )
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level from score.
        
        Args:
            score: Quality score
            
        Returns:
            Quality level
        """
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _get_completeness_recommendations(self, field_completeness: Dict[str, float], overall_score: float) -> List[str]:
        """Get completeness recommendations.
        
        Args:
            field_completeness: Field completeness scores
            overall_score: Overall completeness score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if overall_score < 0.9:
            recommendations.append("Improve data collection processes to reduce missing values")
        
        # Check individual fields
        for field, score in field_completeness.items():
            if score < 0.5:
                recommendations.append(f"Field '{field}' has low completeness ({score:.1%}) - consider making it required")
            elif score < 0.8:
                recommendations.append(f"Field '{field}' has moderate completeness ({score:.1%}) - review data sources")
        
        return recommendations


class AccuracyScorer:
    """Scores data accuracy."""
    
    def __init__(self):
        """Initialize accuracy scorer."""
        self.logger = get_logger(self.__class__.__name__)
        self.validation_rules: Dict[str, Callable] = {}
        self._setup_default_validation_rules()
    
    def _setup_default_validation_rules(self) -> None:
        """Setup default validation rules."""
        self.validation_rules = {
            "email": self._validate_email,
            "phone": self._validate_phone,
            "url": self._validate_url,
            "date": self._validate_date,
            "number": self._validate_number
        }
    
    def calculate_accuracy(self, data: List[Dict[str, Any]], validation_rules: Dict[str, str]) -> QualityScore:
        """Calculate accuracy score.
        
        Args:
            data: Input data
            validation_rules: Field validation rules
            
        Returns:
            Accuracy quality score
        """
        if not data:
            return QualityScore(
                dimension=QualityDimension.ACCURACY,
                score=0.0,
                level=QualityLevel.CRITICAL,
                details={"error": "No data provided"}
            )
        
        total_records = len(data)
        total_validations = 0
        total_valid = 0
        field_accuracy = {}
        
        for field, rule_type in validation_rules.items():
            if rule_type not in self.validation_rules:
                continue
            
            validator = self.validation_rules[rule_type]
            field_valid = 0
            
            for record in data:
                if field in record and record[field] is not None:
                    total_validations += 1
                    if validator(record[field]):
                        field_valid += 1
                        total_valid += 1
            
            if total_validations > 0:
                field_accuracy[field] = field_valid / total_validations
            else:
                field_accuracy[field] = 0.0
        
        # Calculate overall accuracy
        accuracy_score = total_valid / total_validations if total_validations > 0 else 0.0
        
        # Determine quality level
        level = self._get_quality_level(accuracy_score)
        
        # Generate recommendations
        recommendations = self._get_accuracy_recommendations(field_accuracy, accuracy_score)
        
        return QualityScore(
            dimension=QualityDimension.ACCURACY,
            score=accuracy_score,
            level=level,
            details={
                "total_records": total_records,
                "total_validations": total_validations,
                "valid_values": total_valid,
                "field_accuracy": field_accuracy,
                "accuracy_percentage": accuracy_score * 100
            },
            recommendations=recommendations
        )
    
    def _validate_email(self, value: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _validate_phone(self, value: str) -> bool:
        """Validate phone format."""
        pattern = r'^\+?[\d\s\-\(\)]{10,}$'
        return bool(re.match(pattern, value))
    
    def _validate_url(self, value: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, value))
    
    def _validate_date(self, value: str) -> bool:
        """Validate date format."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            try:
                datetime.strptime(value, "%d/%m/%Y")
                return True
            except ValueError:
                return False
    
    def _validate_number(self, value: Union[str, int, float]) -> bool:
        """Validate number format."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _get_accuracy_recommendations(self, field_accuracy: Dict[str, float], overall_score: float) -> List[str]:
        """Get accuracy recommendations."""
        recommendations = []
        
        if overall_score < 0.9:
            recommendations.append("Implement data validation at the source")
        
        for field, score in field_accuracy.items():
            if score < 0.5:
                recommendations.append(f"Field '{field}' has low accuracy ({score:.1%}) - review data entry processes")
            elif score < 0.8:
                recommendations.append(f"Field '{field}' has moderate accuracy ({score:.1%}) - consider additional validation")
        
        return recommendations


class ConsistencyScorer:
    """Scores data consistency."""
    
    def __init__(self):
        """Initialize consistency scorer."""
        self.logger = get_logger(self.__class__.__name__)
    
    def calculate_consistency(self, data: List[Dict[str, Any]], consistency_rules: Dict[str, List[str]]) -> QualityScore:
        """Calculate consistency score.
        
        Args:
            data: Input data
            consistency_rules: Field consistency rules
            
        Returns:
            Consistency quality score
        """
        if not data:
            return QualityScore(
                dimension=QualityDimension.CONSISTENCY,
                score=0.0,
                level=QualityLevel.CRITICAL,
                details={"error": "No data provided"}
            )
        
        total_records = len(data)
        total_checks = 0
        total_consistent = 0
        field_consistency = {}
        
        for field, rules in consistency_rules.items():
            if field not in data[0]:
                continue
            
            field_consistent = 0
            field_checks = 0
            
            for record in data:
                if field in record and record[field] is not None:
                    field_checks += 1
                    total_checks += 1
                    
                    if self._check_field_consistency(record[field], rules):
                        field_consistent += 1
                        total_consistent += 1
            
            if field_checks > 0:
                field_consistency[field] = field_consistent / field_checks
            else:
                field_consistency[field] = 0.0
        
        # Calculate overall consistency
        consistency_score = total_consistent / total_checks if total_checks > 0 else 0.0
        
        # Determine quality level
        level = self._get_quality_level(consistency_score)
        
        # Generate recommendations
        recommendations = self._get_consistency_recommendations(field_consistency, consistency_score)
        
        return QualityScore(
            dimension=QualityDimension.CONSISTENCY,
            score=consistency_score,
            level=level,
            details={
                "total_records": total_records,
                "total_checks": total_checks,
                "consistent_values": total_consistent,
                "field_consistency": field_consistency,
                "consistency_percentage": consistency_score * 100
            },
            recommendations=recommendations
        )
    
    def _check_field_consistency(self, value: Any, rules: List[str]) -> bool:
        """Check field consistency against rules.
        
        Args:
            value: Field value
            rules: Consistency rules
            
        Returns:
            True if consistent
        """
        for rule in rules:
            if rule == "case_consistent":
                if not self._check_case_consistency(value):
                    return False
            elif rule == "format_consistent":
                if not self._check_format_consistency(value):
                    return False
            elif rule == "range_consistent":
                if not self._check_range_consistency(value):
                    return False
        
        return True
    
    def _check_case_consistency(self, value: str) -> bool:
        """Check case consistency."""
        if not isinstance(value, str):
            return True
        
        # Check if all letters are same case
        return value.islower() or value.isupper() or value.istitle()
    
    def _check_format_consistency(self, value: str) -> bool:
        """Check format consistency."""
        if not isinstance(value, str):
            return True
        
        # Check for consistent formatting patterns
        return len(set(re.findall(r'[^\w\s]', value))) <= 1
    
    def _check_range_consistency(self, value: Union[int, float]) -> bool:
        """Check range consistency."""
        if not isinstance(value, (int, float)):
            return True
        
        # Check if value is within reasonable range
        return -1000000 <= value <= 1000000
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _get_consistency_recommendations(self, field_consistency: Dict[str, float], overall_score: float) -> List[str]:
        """Get consistency recommendations."""
        recommendations = []
        
        if overall_score < 0.9:
            recommendations.append("Implement data standardization processes")
        
        for field, score in field_consistency.items():
            if score < 0.5:
                recommendations.append(f"Field '{field}' has low consistency ({score:.1%}) - standardize data format")
            elif score < 0.8:
                recommendations.append(f"Field '{field}' has moderate consistency ({score:.1%}) - review data entry guidelines")
        
        return recommendations


class UniquenessScorer:
    """Scores data uniqueness."""
    
    def __init__(self):
        """Initialize uniqueness scorer."""
        self.logger = get_logger(self.__class__.__name__)
    
    def calculate_uniqueness(self, data: List[Dict[str, Any]], unique_fields: List[str]) -> QualityScore:
        """Calculate uniqueness score.
        
        Args:
            data: Input data
            unique_fields: List of fields that should be unique
            
        Returns:
            Uniqueness quality score
        """
        if not data:
            return QualityScore(
                dimension=QualityDimension.UNIQUENESS,
                score=0.0,
                level=QualityLevel.CRITICAL,
                details={"error": "No data provided"}
            )
        
        total_records = len(data)
        total_unique_values = 0
        field_uniqueness = {}
        
        for field in unique_fields:
            if field not in data[0]:
                continue
            
            values = [record.get(field) for record in data if record.get(field) is not None]
            unique_values = len(set(values))
            total_values = len(values)
            
            if total_values > 0:
                uniqueness_ratio = unique_values / total_values
                field_uniqueness[field] = uniqueness_ratio
                total_unique_values += unique_values
            else:
                field_uniqueness[field] = 0.0
        
        # Calculate overall uniqueness
        total_possible_unique = len(unique_fields) * total_records
        uniqueness_score = total_unique_values / total_possible_unique if total_possible_unique > 0 else 0.0
        
        # Determine quality level
        level = self._get_quality_level(uniqueness_score)
        
        # Generate recommendations
        recommendations = self._get_uniqueness_recommendations(field_uniqueness, uniqueness_score)
        
        return QualityScore(
            dimension=QualityDimension.UNIQUENESS,
            score=uniqueness_score,
            level=level,
            details={
                "total_records": total_records,
                "unique_fields": unique_fields,
                "field_uniqueness": field_uniqueness,
                "uniqueness_percentage": uniqueness_score * 100
            },
            recommendations=recommendations
        )
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _get_uniqueness_recommendations(self, field_uniqueness: Dict[str, float], overall_score: float) -> List[str]:
        """Get uniqueness recommendations."""
        recommendations = []
        
        if overall_score < 0.9:
            recommendations.append("Implement duplicate detection and removal processes")
        
        for field, score in field_uniqueness.items():
            if score < 0.5:
                recommendations.append(f"Field '{field}' has low uniqueness ({score:.1%}) - check for duplicates")
            elif score < 0.8:
                recommendations.append(f"Field '{field}' has moderate uniqueness ({score:.1%}) - review data sources")
        
        return recommendations


class DataQualityScorer:
    """Main data quality scoring system."""
    
    def __init__(self):
        """Initialize data quality scorer."""
        self.logger = get_logger(self.__class__.__name__)
        self.metrics: Dict[QualityDimension, QualityMetric] = {}
        self.scoring_history: deque = deque(maxlen=1000)
        
        # Initialize scorers
        self.completeness_scorer = CompletenessScorer()
        self.accuracy_scorer = AccuracyScorer()
        self.consistency_scorer = ConsistencyScorer()
        self.uniqueness_scorer = UniquenessScorer()
        
        # Setup default metrics
        self._setup_default_metrics()
    
    def _setup_default_metrics(self) -> None:
        """Setup default quality metrics."""
        self.metrics = {
            QualityDimension.COMPLETENESS: QualityMetric(
                name="completeness",
                dimension=QualityDimension.COMPLETENESS,
                weight=1.0
            ),
            QualityDimension.ACCURACY: QualityMetric(
                name="accuracy",
                dimension=QualityDimension.ACCURACY,
                weight=1.0
            ),
            QualityDimension.CONSISTENCY: QualityMetric(
                name="consistency",
                dimension=QualityDimension.CONSISTENCY,
                weight=0.8
            ),
            QualityDimension.UNIQUENESS: QualityMetric(
                name="uniqueness",
                dimension=QualityDimension.UNIQUENESS,
                weight=0.6
            )
        }
    
    def add_metric(self, metric: QualityMetric) -> None:
        """Add quality metric.
        
        Args:
            metric: Quality metric
        """
        self.metrics[metric.dimension] = metric
        self.logger.info(f"Added quality metric: {metric.name}")
    
    def remove_metric(self, dimension: QualityDimension) -> bool:
        """Remove quality metric.
        
        Args:
            dimension: Quality dimension
            
        Returns:
            True if removed, False if not found
        """
        if dimension in self.metrics:
            del self.metrics[dimension]
            self.logger.info(f"Removed quality metric: {dimension.value}")
            return True
        return False
    
    async def calculate_quality_score(
        self,
        data: List[Dict[str, Any]],
        required_fields: List[str],
        validation_rules: Dict[str, str],
        consistency_rules: Dict[str, List[str]],
        unique_fields: List[str]
    ) -> OverallQualityScore:
        """Calculate overall data quality score.
        
        Args:
            data: Input data
            required_fields: List of required fields
            validation_rules: Field validation rules
            consistency_rules: Field consistency rules
            unique_fields: List of unique fields
            
        Returns:
            Overall quality score
        """
        start_time = time.time()
        
        dimension_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Calculate completeness score
        if QualityDimension.COMPLETENESS in self.metrics:
            completeness_score = self.completeness_scorer.calculate_completeness(data, required_fields)
            dimension_scores[QualityDimension.COMPLETENESS] = completeness_score
            
            weight = self.metrics[QualityDimension.COMPLETENESS].weight
            total_weighted_score += completeness_score.score * weight
            total_weight += weight
        
        # Calculate accuracy score
        if QualityDimension.ACCURACY in self.metrics:
            accuracy_score = self.accuracy_scorer.calculate_accuracy(data, validation_rules)
            dimension_scores[QualityDimension.ACCURACY] = accuracy_score
            
            weight = self.metrics[QualityDimension.ACCURACY].weight
            total_weighted_score += accuracy_score.score * weight
            total_weight += weight
        
        # Calculate consistency score
        if QualityDimension.CONSISTENCY in self.metrics:
            consistency_score = self.consistency_scorer.calculate_consistency(data, consistency_rules)
            dimension_scores[QualityDimension.CONSISTENCY] = consistency_score
            
            weight = self.metrics[QualityDimension.CONSISTENCY].weight
            total_weighted_score += consistency_score.score * weight
            total_weight += weight
        
        # Calculate uniqueness score
        if QualityDimension.UNIQUENESS in self.metrics:
            uniqueness_score = self.uniqueness_scorer.calculate_uniqueness(data, unique_fields)
            dimension_scores[QualityDimension.UNIQUENESS] = uniqueness_score
            
            weight = self.metrics[QualityDimension.UNIQUENESS].weight
            total_weighted_score += uniqueness_score.score * weight
            total_weight += weight
        
        # Calculate overall score
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Determine overall quality level
        overall_level = self._get_overall_quality_level(overall_score)
        
        # Generate overall recommendations
        recommendations = self._get_overall_recommendations(dimension_scores, overall_score)
        
        result = OverallQualityScore(
            total_score=overall_score,
            level=overall_level,
            dimension_scores=dimension_scores,
            metadata={
                "total_records": len(data),
                "calculation_time": time.time() - start_time,
                "dimensions_evaluated": len(dimension_scores),
                "total_weight": total_weight
            }
        )
        
        # Record scoring history
        self.scoring_history.append({
            "timestamp": time.time(),
            "total_score": overall_score,
            "level": overall_level.value,
            "records_count": len(data),
            "dimensions_count": len(dimension_scores)
        })
        
        return result
    
    def _get_overall_quality_level(self, score: float) -> QualityLevel:
        """Get overall quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _get_overall_recommendations(self, dimension_scores: Dict[QualityDimension, QualityScore], overall_score: float) -> List[str]:
        """Get overall recommendations."""
        recommendations = []
        
        if overall_score < 0.9:
            recommendations.append("Overall data quality needs improvement")
        
        # Check each dimension
        for dimension, score in dimension_scores.items():
            if score.level in [QualityLevel.POOR, QualityLevel.CRITICAL]:
                recommendations.extend(score.recommendations[:2])  # Top 2 recommendations per dimension
        
        return recommendations
    
    def get_scoring_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get scoring history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of scoring records
        """
        return list(self.scoring_history)[-limit:]
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """Get quality trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Quality trends
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        
        recent_scores = [
            record for record in self.scoring_history
            if record["timestamp"] > cutoff_time
        ]
        
        if not recent_scores:
            return {}
        
        # Group by day
        daily_scores = defaultdict(list)
        
        for record in recent_scores:
            day = datetime.fromtimestamp(record["timestamp"]).strftime("%Y-%m-%d")
            daily_scores[day].append(record["total_score"])
        
        # Calculate daily averages
        trends = {}
        for day, scores in daily_scores.items():
            trends[day] = statistics.mean(scores)
        
        return trends
    
    def cleanup(self) -> None:
        """Cleanup quality scorer."""
        self.scoring_history.clear()
        self.logger.info("Data quality scorer cleaned up")
