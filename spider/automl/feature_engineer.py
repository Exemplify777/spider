"""
Feature Engineer

Advanced feature engineering capabilities for automated machine learning.
Includes automated feature generation, selection, and transformation.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_selection import SelectKBest, SelectPercentile, RFE, VarianceThreshold
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression, f_classif, f_regression
from sklearn.decomposition import PCA, FastICA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import PolynomialFeatures
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.base import BaseEstimator, TransformerMixin
import re

logger = logging.getLogger(__name__)


class FeatureType(str, Enum):
    """Feature type enumeration."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    MIXED = "mixed"


class EngineeringMethod(str, Enum):
    """Feature engineering method enumeration."""
    POLYNOMIAL = "polynomial"
    INTERACTION = "interaction"
    BINNING = "binning"
    LOG_TRANSFORM = "log_transform"
    SQUARE_ROOT = "square_root"
    RECIPROCAL = "reciprocal"
    EXPONENTIAL = "exponential"
    TIME_FEATURES = "time_features"
    TEXT_FEATURES = "text_features"
    AGGREGATION = "aggregation"
    RATIO = "ratio"
    DIFFERENCE = "difference"
    LAG = "lag"
    ROLLING = "rolling"


class SelectionMethod(str, Enum):
    """Feature selection method enumeration."""
    VARIANCE_THRESHOLD = "variance_threshold"
    SELECT_K_BEST = "select_k_best"
    SELECT_PERCENTILE = "select_percentile"
    MUTUAL_INFO = "mutual_info"
    RFE = "rfe"
    CORRELATION = "correlation"
    UNIVARIATE = "univariate"


@dataclass
class FeatureConfig:
    """Feature engineering configuration."""
    enable_polynomial_features: bool = True
    enable_interaction_features: bool = True
    enable_binning: bool = True
    enable_log_transform: bool = True
    enable_time_features: bool = True
    enable_text_features: bool = True
    enable_aggregation: bool = True
    enable_ratio_features: bool = True
    max_polynomial_degree: int = 2
    max_interaction_features: int = 10
    n_bins: int = 5
    selection_method: SelectionMethod = SelectionMethod.SELECT_K_BEST
    max_features: int = 100
    correlation_threshold: float = 0.95
    variance_threshold: float = 0.01
    random_state: int = 42


@dataclass
class FeatureResult:
    """Feature engineering result."""
    original_features: List[str]
    engineered_features: List[str]
    selected_features: List[str]
    feature_importance: Dict[str, float]
    feature_scores: Dict[str, float]
    feature_types: Dict[str, FeatureType]
    engineering_summary: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


class FeatureEngineer:
    """
    Advanced feature engineering system.
    
    Features:
    - Automated feature generation and transformation
    - Intelligent feature selection
    - Feature type detection and handling
    - Performance optimization
    - Feature importance analysis
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_types = {}
        self.feature_importance = {}
        self.engineering_history = []
    
    async def engineer_features(self, data: pd.DataFrame, target: pd.Series, 
                              config: FeatureConfig) -> FeatureResult:
        """
        Engineer features for the dataset.
        
        Args:
            data: Input data
            target: Target variable
            config: Feature engineering configuration
            
        Returns:
            Feature engineering result
        """
        try:
            # Detect feature types
            feature_types = self._detect_feature_types(data)
            
            # Create a copy of the data
            engineered_data = data.copy()
            original_features = list(data.columns)
            
            # Apply feature engineering
            engineered_data = await self._apply_feature_engineering(
                engineered_data, feature_types, config
            )
            
            # Get engineered features
            engineered_features = [col for col in engineered_data.columns 
                                 if col not in original_features]
            
            # Apply feature selection
            selected_features, feature_scores = await self._apply_feature_selection(
                engineered_data, target, config
            )
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(
                engineered_data[selected_features], target
            )
            
            # Create engineering summary
            engineering_summary = self._create_engineering_summary(
                original_features, engineered_features, selected_features, config
            )
            
            result = FeatureResult(
                original_features=original_features,
                engineered_features=engineered_features,
                selected_features=selected_features,
                feature_importance=feature_importance,
                feature_scores=feature_scores,
                feature_types=feature_types,
                engineering_summary=engineering_summary
            )
            
            # Store in history
            self.engineering_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "original_features": len(original_features),
                "engineered_features": len(engineered_features),
                "selected_features": len(selected_features),
                "config": config.__dict__
            })
            
            logger.info(f"Feature engineering completed: {len(engineered_features)} new features, {len(selected_features)} selected")
            return result
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            raise
    
    def _detect_feature_types(self, data: pd.DataFrame) -> Dict[str, FeatureType]:
        """Detect feature types in the dataset."""
        feature_types = {}
        
        for column in data.columns:
            if data[column].dtype in ['int64', 'float64']:
                # Check if it's boolean
                if data[column].nunique() == 2:
                    feature_types[column] = FeatureType.BOOLEAN
                else:
                    feature_types[column] = FeatureType.NUMERIC
            elif data[column].dtype == 'object':
                # Check if it's datetime
                if self._is_datetime_column(data[column]):
                    feature_types[column] = FeatureType.DATETIME
                # Check if it's text
                elif self._is_text_column(data[column]):
                    feature_types[column] = FeatureType.TEXT
                else:
                    feature_types[column] = FeatureType.CATEGORICAL
            else:
                feature_types[column] = FeatureType.MIXED
        
        return feature_types
    
    def _is_datetime_column(self, series: pd.Series) -> bool:
        """Check if a column contains datetime data."""
        try:
            pd.to_datetime(series.dropna().iloc[:5])
            return True
        except:
            return False
    
    def _is_text_column(self, series: pd.Series) -> bool:
        """Check if a column contains text data."""
        # Check if average string length is > 10 and contains spaces
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return False
        
        avg_length = non_null_series.astype(str).str.len().mean()
        has_spaces = non_null_series.astype(str).str.contains(' ').any()
        
        return avg_length > 10 and has_spaces
    
    async def _apply_feature_engineering(self, data: pd.DataFrame, 
                                        feature_types: Dict[str, FeatureType],
                                        config: FeatureConfig) -> pd.DataFrame:
        """Apply feature engineering transformations."""
        engineered_data = data.copy()
        
        # Polynomial features for numeric columns
        if config.enable_polynomial_features:
            numeric_columns = [col for col, ftype in feature_types.items() 
                             if ftype == FeatureType.NUMERIC]
            if len(numeric_columns) > 0:
                engineered_data = self._add_polynomial_features(
                    engineered_data, numeric_columns, config
                )
        
        # Interaction features
        if config.enable_interaction_features:
            engineered_data = self._add_interaction_features(
                engineered_data, feature_types, config
            )
        
        # Binning for numeric columns
        if config.enable_binning:
            numeric_columns = [col for col, ftype in feature_types.items() 
                             if ftype == FeatureType.NUMERIC]
            for col in numeric_columns:
                engineered_data = self._add_binning_features(
                    engineered_data, col, config
                )
        
        # Log transform for numeric columns
        if config.enable_log_transform:
            numeric_columns = [col for col, ftype in feature_types.items() 
                             if ftype == FeatureType.NUMERIC]
            for col in numeric_columns:
                if engineered_data[col].min() > 0:  # Only for positive values
                    engineered_data[f"{col}_log"] = np.log1p(engineered_data[col])
        
        # Time features for datetime columns
        if config.enable_time_features:
            datetime_columns = [col for col, ftype in feature_types.items() 
                              if ftype == FeatureType.DATETIME]
            for col in datetime_columns:
                engineered_data = self._add_time_features(engineered_data, col)
        
        # Text features
        if config.enable_text_features:
            text_columns = [col for col, ftype in feature_types.items() 
                          if ftype == FeatureType.TEXT]
            for col in text_columns:
                engineered_data = self._add_text_features(engineered_data, col)
        
        # Ratio features
        if config.enable_ratio_features:
            engineered_data = self._add_ratio_features(engineered_data, feature_types)
        
        return engineered_data
    
    def _add_polynomial_features(self, data: pd.DataFrame, numeric_columns: List[str], 
                                config: FeatureConfig) -> pd.DataFrame:
        """Add polynomial features."""
        if len(numeric_columns) < 2:
            return data
        
        # Limit to avoid too many features
        selected_columns = numeric_columns[:5]  # Limit to 5 columns
        
        poly = PolynomialFeatures(
            degree=config.max_polynomial_degree,
            include_bias=False,
            interaction_only=False
        )
        
        poly_features = poly.fit_transform(data[selected_columns])
        feature_names = poly.get_feature_names_out(selected_columns)
        
        # Add polynomial features to dataframe
        for i, feature_name in enumerate(feature_names):
            if feature_name not in data.columns:
                data[f"poly_{feature_name}"] = poly_features[:, i]
        
        return data
    
    def _add_interaction_features(self, data: pd.DataFrame, 
                                 feature_types: Dict[str, FeatureType],
                                 config: FeatureConfig) -> pd.DataFrame:
        """Add interaction features."""
        numeric_columns = [col for col, ftype in feature_types.items() 
                          if ftype == FeatureType.NUMERIC]
        
        if len(numeric_columns) < 2:
            return data
        
        # Create interaction features
        interaction_count = 0
        for i, col1 in enumerate(numeric_columns):
            for col2 in numeric_columns[i+1:]:
                if interaction_count >= config.max_interaction_features:
                    break
                
                interaction_name = f"{col1}_x_{col2}"
                if interaction_name not in data.columns:
                    data[interaction_name] = data[col1] * data[col2]
                    interaction_count += 1
            
            if interaction_count >= config.max_interaction_features:
                break
        
        return data
    
    def _add_binning_features(self, data: pd.DataFrame, column: str, 
                             config: FeatureConfig) -> pd.DataFrame:
        """Add binning features."""
        try:
            # Create bins
            data[f"{column}_binned"] = pd.cut(
                data[column], 
                bins=config.n_bins, 
                labels=False, 
                include_lowest=True
            )
            
            # Create quantile bins
            data[f"{column}_qbin"] = pd.qcut(
                data[column], 
                q=config.n_bins, 
                labels=False, 
                duplicates='drop'
            )
            
        except Exception as e:
            logger.warning(f"Binning failed for {column}: {e}")
        
        return data
    
    def _add_time_features(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """Add time-based features."""
        try:
            dt_series = pd.to_datetime(data[column])
            
            data[f"{column}_year"] = dt_series.dt.year
            data[f"{column}_month"] = dt_series.dt.month
            data[f"{column}_day"] = dt_series.dt.day
            data[f"{column}_weekday"] = dt_series.dt.weekday
            data[f"{column}_hour"] = dt_series.dt.hour
            data[f"{column}_quarter"] = dt_series.dt.quarter
            
        except Exception as e:
            logger.warning(f"Time feature extraction failed for {column}: {e}")
        
        return data
    
    def _add_text_features(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """Add text-based features."""
        try:
            text_series = data[column].fillna('').astype(str)
            
            # Basic text features
            data[f"{column}_length"] = text_series.str.len()
            data[f"{column}_word_count"] = text_series.str.split().str.len()
            data[f"{column}_char_count"] = text_series.str.replace(' ', '').str.len()
            data[f"{column}_has_numbers"] = text_series.str.contains(r'\d').astype(int)
            data[f"{column}_has_special"] = text_series.str.contains(r'[^a-zA-Z0-9\s]').astype(int)
            
            # TF-IDF features (simplified)
            if len(text_series) > 10:  # Only for datasets with enough text
                tfidf = TfidfVectorizer(max_features=10, stop_words='english')
                tfidf_matrix = tfidf.fit_transform(text_series)
                
                for i in range(min(5, tfidf_matrix.shape[1])):
                    data[f"{column}_tfidf_{i}"] = tfidf_matrix[:, i].toarray().flatten()
            
        except Exception as e:
            logger.warning(f"Text feature extraction failed for {column}: {e}")
        
        return data
    
    def _add_ratio_features(self, data: pd.DataFrame, 
                           feature_types: Dict[str, FeatureType]) -> pd.DataFrame:
        """Add ratio features between numeric columns."""
        numeric_columns = [col for col, ftype in feature_types.items() 
                          if ftype == FeatureType.NUMERIC]
        
        if len(numeric_columns) < 2:
            return data
        
        # Create ratio features
        for i, col1 in enumerate(numeric_columns):
            for col2 in numeric_columns[i+1:]:
                ratio_name = f"{col1}_div_{col2}"
                if ratio_name not in data.columns:
                    # Avoid division by zero
                    data[ratio_name] = data[col1] / (data[col2] + 1e-8)
        
        return data
    
    async def _apply_feature_selection(self, data: pd.DataFrame, target: pd.Series,
                                     config: FeatureConfig) -> Tuple[List[str], Dict[str, float]]:
        """Apply feature selection methods."""
        # Remove features with low variance
        variance_selector = VarianceThreshold(threshold=config.variance_threshold)
        variance_selector.fit(data)
        selected_features = data.columns[variance_selector.get_support()].tolist()
        
        if len(selected_features) == 0:
            return [], {}
        
        # Apply correlation-based selection
        selected_features = self._remove_correlated_features(
            data[selected_features], config.correlation_threshold
        )
        
        if len(selected_features) == 0:
            return [], {}
        
        # Apply additional selection methods
        if config.selection_method == SelectionMethod.SELECT_K_BEST:
            selected_features, feature_scores = self._select_k_best(
                data[selected_features], target, config.max_features
            )
        elif config.selection_method == SelectionMethod.SELECT_PERCENTILE:
            selected_features, feature_scores = self._select_percentile(
                data[selected_features], target, 50
            )
        elif config.selection_method == SelectionMethod.MUTUAL_INFO:
            selected_features, feature_scores = self._select_mutual_info(
                data[selected_features], target, config.max_features
            )
        else:
            # Default to all features
            feature_scores = {}
            for col in selected_features:
                feature_scores[col] = 1.0
        
        return selected_features, feature_scores
    
    def _remove_correlated_features(self, data: pd.DataFrame, 
                                   threshold: float) -> List[str]:
        """Remove highly correlated features."""
        corr_matrix = data.corr().abs()
        
        # Find pairs of highly correlated features
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > threshold:
                    high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j]))
        
        # Remove one feature from each highly correlated pair
        features_to_remove = set()
        for feat1, feat2 in high_corr_pairs:
            if feat1 not in features_to_remove:
                features_to_remove.add(feat2)
        
        return [col for col in data.columns if col not in features_to_remove]
    
    def _select_k_best(self, data: pd.DataFrame, target: pd.Series, 
                      k: int) -> Tuple[List[str], Dict[str, float]]:
        """Select k best features using f-test."""
        try:
            selector = SelectKBest(score_func=f_classif, k=min(k, data.shape[1]))
            selector.fit(data, target)
            
            selected_features = data.columns[selector.get_support()].tolist()
            feature_scores = dict(zip(data.columns, selector.scores_))
            
            return selected_features, feature_scores
        except Exception as e:
            logger.warning(f"K-best selection failed: {e}")
            return data.columns.tolist(), {}
    
    def _select_percentile(self, data: pd.DataFrame, target: pd.Series, 
                          percentile: int) -> Tuple[List[str], Dict[str, float]]:
        """Select top percentile of features."""
        try:
            selector = SelectPercentile(score_func=f_classif, percentile=percentile)
            selector.fit(data, target)
            
            selected_features = data.columns[selector.get_support()].tolist()
            feature_scores = dict(zip(data.columns, selector.scores_))
            
            return selected_features, feature_scores
        except Exception as e:
            logger.warning(f"Percentile selection failed: {e}")
            return data.columns.tolist(), {}
    
    def _select_mutual_info(self, data: pd.DataFrame, target: pd.Series, 
                           k: int) -> Tuple[List[str], Dict[str, float]]:
        """Select features using mutual information."""
        try:
            # Determine if classification or regression
            if target.nunique() < 10:  # Classification
                scores = mutual_info_classif(data, target)
            else:  # Regression
                scores = mutual_info_regression(data, target)
            
            # Select top k features
            feature_scores = dict(zip(data.columns, scores))
            sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
            selected_features = [feat for feat, score in sorted_features[:k]]
            
            return selected_features, feature_scores
        except Exception as e:
            logger.warning(f"Mutual info selection failed: {e}")
            return data.columns.tolist(), {}
    
    def _calculate_feature_importance(self, data: pd.DataFrame, 
                                    target: pd.Series) -> Dict[str, float]:
        """Calculate feature importance using correlation."""
        try:
            importance = {}
            for col in data.columns:
                if data[col].dtype in ['int64', 'float64']:
                    corr = abs(data[col].corr(target))
                    importance[col] = corr if not np.isnan(corr) else 0.0
                else:
                    importance[col] = 0.0
            
            return importance
        except Exception as e:
            logger.warning(f"Feature importance calculation failed: {e}")
            return {}
    
    def _create_engineering_summary(self, original_features: List[str],
                                   engineered_features: List[str],
                                   selected_features: List[str],
                                   config: FeatureConfig) -> Dict[str, Any]:
        """Create feature engineering summary."""
        return {
            "original_feature_count": len(original_features),
            "engineered_feature_count": len(engineered_features),
            "selected_feature_count": len(selected_features),
            "feature_reduction_ratio": len(selected_features) / (len(original_features) + len(engineered_features)),
            "engineering_methods_applied": {
                "polynomial": config.enable_polynomial_features,
                "interaction": config.enable_interaction_features,
                "binning": config.enable_binning,
                "log_transform": config.enable_log_transform,
                "time_features": config.enable_time_features,
                "text_features": config.enable_text_features,
                "ratio_features": config.enable_ratio_features
            },
            "selection_method": config.selection_method.value,
            "max_features": config.max_features
        }
    
    def get_engineering_history(self) -> List[Dict[str, Any]]:
        """Get feature engineering history."""
        return self.engineering_history
    
    def get_available_engineering_methods(self) -> List[str]:
        """Get available feature engineering methods."""
        return [method.value for method in EngineeringMethod]
    
    def get_available_selection_methods(self) -> List[str]:
        """Get available feature selection methods."""
        return [method.value for method in SelectionMethod]
    
    def get_engineering_statistics(self) -> Dict[str, Any]:
        """Get feature engineering statistics."""
        if not self.engineering_history:
            return {"total_engineering_sessions": 0}
        
        total_sessions = len(self.engineering_history)
        avg_original = np.mean([h["original_features"] for h in self.engineering_history])
        avg_engineered = np.mean([h["engineered_features"] for h in self.engineering_history])
        avg_selected = np.mean([h["selected_features"] for h in self.engineering_history])
        
        return {
            "total_engineering_sessions": total_sessions,
            "average_original_features": avg_original,
            "average_engineered_features": avg_engineered,
            "average_selected_features": avg_selected,
            "last_engineering": self.engineering_history[-1]["timestamp"] if self.engineering_history else None
        }
