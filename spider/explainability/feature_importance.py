"""
Feature Importance Analyzer

Advanced feature importance analysis for machine learning models.
Includes multiple importance calculation methods and visualization.

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
from sklearn.base import BaseEstimator
from sklearn.inspection import permutation_importance, partial_dependence
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error

logger = logging.getLogger(__name__)


class ImportanceMethod(str, Enum):
    """Feature importance method enumeration."""
    MODEL_BASED = "model_based"
    PERMUTATION = "permutation"
    MUTUAL_INFO = "mutual_info"
    PARTIAL_DEPENDENCE = "partial_dependence"
    SHAP_VALUES = "shap_values"
    LIME_VALUES = "lime_values"
    CORRELATION = "correlation"
    UNIVARIATE = "univariate"


class ImportanceType(str, Enum):
    """Importance type enumeration."""
    GLOBAL = "global"
    LOCAL = "local"
    INTERACTION = "interaction"
    CONDITIONAL = "conditional"


@dataclass
class ImportanceConfig:
    """Feature importance configuration."""
    method: ImportanceMethod = ImportanceMethod.MODEL_BASED
    importance_type: ImportanceType = ImportanceType.GLOBAL
    n_repeats: int = 10
    random_state: int = 42
    cv_folds: int = 5
    scoring: str = "accuracy"
    max_features: int = 20
    interaction_depth: int = 2
    partial_dependence_features: Optional[List[str]] = None
    feature_names: Optional[List[str]] = None
    normalize: bool = True
    sort_by_importance: bool = True


@dataclass
class ImportanceResult:
    """Feature importance result."""
    importance_id: str
    feature_importance: Dict[str, float]
    feature_rankings: List[str]
    importance_scores: Dict[str, float]
    importance_type: ImportanceType
    method: ImportanceMethod
    model_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    plots: Dict[str, Any] = field(default_factory=dict)
    summary_stats: Dict[str, float] = field(default_factory=dict)


class FeatureImportanceAnalyzer:
    """
    Advanced feature importance analyzer.
    
    Features:
    - Multiple importance calculation methods
    - Global and local importance analysis
    - Feature interaction analysis
    - Visualization and ranking
    - Performance comparison
    """
    
    def __init__(self):
        """Initialize feature importance analyzer."""
        self.analysis_history = []
        self.importance_cache = {}
    
    async def analyze_importance(self, model: BaseEstimator, X: pd.DataFrame, 
                                y: pd.Series, config: ImportanceConfig) -> ImportanceResult:
        """
        Analyze feature importance for a model.
        
        Args:
            model: Trained model
            X: Feature data
            y: Target data
            config: Importance configuration
            
        Returns:
            Feature importance result
        """
        importance_id = f"importance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Calculate feature importance based on method
            if config.method == ImportanceMethod.MODEL_BASED:
                importance_scores = await self._calculate_model_based_importance(model, X, y, config)
            elif config.method == ImportanceMethod.PERMUTATION:
                importance_scores = await self._calculate_permutation_importance(model, X, y, config)
            elif config.method == ImportanceMethod.MUTUAL_INFO:
                importance_scores = await self._calculate_mutual_info_importance(X, y, config)
            elif config.method == ImportanceMethod.PARTIAL_DEPENDENCE:
                importance_scores = await self._calculate_partial_dependence_importance(model, X, y, config)
            elif config.method == ImportanceMethod.CORRELATION:
                importance_scores = await self._calculate_correlation_importance(X, y, config)
            elif config.method == ImportanceMethod.UNIVARIATE:
                importance_scores = await self._calculate_univariate_importance(X, y, config)
            else:
                raise ValueError(f"Unsupported importance method: {config.method}")
            
            # Normalize importance scores if requested
            if config.normalize:
                importance_scores = self._normalize_importance_scores(importance_scores)
            
            # Create feature rankings
            feature_rankings = self._create_feature_rankings(importance_scores, config)
            
            # Generate plots
            plots = await self._generate_plots(importance_scores, feature_rankings, config)
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_stats(importance_scores, feature_rankings)
            
            # Create result
            result = ImportanceResult(
                importance_id=importance_id,
                feature_importance=importance_scores,
                feature_rankings=feature_rankings,
                importance_scores=importance_scores,
                importance_type=config.importance_type,
                method=config.method,
                model_type=model.__class__.__name__,
                plots=plots,
                summary_stats=summary_stats,
                metadata={
                    "n_features": len(X.columns),
                    "n_samples": len(X),
                    "config": config.__dict__
                }
            )
            
            # Store in history
            self.analysis_history.append({
                "importance_id": importance_id,
                "model_type": model.__class__.__name__,
                "method": config.method.value,
                "importance_type": config.importance_type.value,
                "n_features": len(X.columns),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Feature importance analysis completed: {importance_id}")
            return result
            
        except Exception as e:
            logger.error(f"Feature importance analysis failed: {e}")
            raise
    
    async def _calculate_model_based_importance(self, model: BaseEstimator, X: pd.DataFrame, 
                                               y: pd.Series, config: ImportanceConfig) -> Dict[str, float]:
        """Calculate model-based feature importance."""
        importance_scores = {}
        
        try:
            # Check if model has feature_importances_ attribute
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                feature_names = config.feature_names or list(X.columns)
                importance_scores = dict(zip(feature_names, importances))
            
            # Check if model has coef_ attribute (linear models)
            elif hasattr(model, 'coef_'):
                coef = model.coef_
                if coef.ndim > 1:
                    coef = coef[0]  # Take first class for multi-class
                feature_names = config.feature_names or list(X.columns)
                importance_scores = dict(zip(feature_names, np.abs(coef)))
            
            # For models without built-in importance, use permutation importance
            else:
                logger.warning("Model does not have built-in feature importance, using permutation importance")
                perm_importance = permutation_importance(
                    model, X, y, n_repeats=config.n_repeats, random_state=config.random_state
                )
                feature_names = config.feature_names or list(X.columns)
                importance_scores = dict(zip(feature_names, perm_importance.importances_mean))
        
        except Exception as e:
            logger.error(f"Model-based importance calculation failed: {e}")
            # Fallback to correlation-based importance
            importance_scores = await self._calculate_correlation_importance(X, y, config)
        
        return importance_scores
    
    async def _calculate_permutation_importance(self, model: BaseEstimator, X: pd.DataFrame, 
                                               y: pd.Series, config: ImportanceConfig) -> Dict[str, float]:
        """Calculate permutation-based feature importance."""
        try:
            perm_importance = permutation_importance(
                model, X, y, 
                n_repeats=config.n_repeats, 
                random_state=config.random_state,
                scoring=config.scoring
            )
            
            feature_names = config.feature_names or list(X.columns)
            importance_scores = dict(zip(feature_names, perm_importance.importances_mean))
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Permutation importance calculation failed: {e}")
            return {}
    
    async def _calculate_mutual_info_importance(self, X: pd.DataFrame, y: pd.Series, 
                                               config: ImportanceConfig) -> Dict[str, float]:
        """Calculate mutual information-based feature importance."""
        try:
            # Determine if classification or regression
            if y.nunique() < 10:  # Classification
                scores = mutual_info_classif(X, y, random_state=config.random_state)
            else:  # Regression
                scores = mutual_info_regression(X, y, random_state=config.random_state)
            
            feature_names = config.feature_names or list(X.columns)
            importance_scores = dict(zip(feature_names, scores))
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Mutual information importance calculation failed: {e}")
            return {}
    
    async def _calculate_partial_dependence_importance(self, model: BaseEstimator, X: pd.DataFrame, 
                                                      y: pd.Series, config: ImportanceConfig) -> Dict[str, float]:
        """Calculate partial dependence-based feature importance."""
        try:
            importance_scores = {}
            feature_names = config.feature_names or list(X.columns)
            
            # Calculate partial dependence for each feature
            for i, feature_name in enumerate(feature_names):
                try:
                    # Calculate partial dependence
                    pd_values = partial_dependence(
                        model, X, [i], 
                        kind='average',
                        grid_resolution=20
                    )
                    
                    # Calculate importance as variance of partial dependence
                    importance = np.var(pd_values['average'][0])
                    importance_scores[feature_name] = importance
                    
                except Exception as e:
                    logger.warning(f"Partial dependence calculation failed for {feature_name}: {e}")
                    importance_scores[feature_name] = 0.0
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Partial dependence importance calculation failed: {e}")
            return {}
    
    async def _calculate_correlation_importance(self, X: pd.DataFrame, y: pd.Series, 
                                               config: ImportanceConfig) -> Dict[str, float]:
        """Calculate correlation-based feature importance."""
        try:
            importance_scores = {}
            feature_names = config.feature_names or list(X.columns)
            
            for feature_name in feature_names:
                if feature_name in X.columns:
                    # Calculate absolute correlation
                    corr = abs(X[feature_name].corr(y))
                    importance_scores[feature_name] = corr if not np.isnan(corr) else 0.0
                else:
                    importance_scores[feature_name] = 0.0
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Correlation importance calculation failed: {e}")
            return {}
    
    async def _calculate_univariate_importance(self, X: pd.DataFrame, y: pd.Series, 
                                              config: ImportanceConfig) -> Dict[str, float]:
        """Calculate univariate feature importance."""
        try:
            importance_scores = {}
            feature_names = config.feature_names or list(X.columns)
            
            # Use a simple model to calculate univariate importance
            if y.nunique() < 10:  # Classification
                from sklearn.feature_selection import f_classif
                scores, _ = f_classif(X, y)
            else:  # Regression
                from sklearn.feature_selection import f_regression
                scores, _ = f_regression(X, y)
            
            importance_scores = dict(zip(feature_names, scores))
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Univariate importance calculation failed: {e}")
            return {}
    
    def _normalize_importance_scores(self, importance_scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize importance scores to [0, 1] range."""
        if not importance_scores:
            return importance_scores
        
        values = list(importance_scores.values())
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All values are the same
            return {k: 1.0 for k in importance_scores.keys()}
        
        # Normalize to [0, 1]
        normalized = {}
        for k, v in importance_scores.items():
            normalized[k] = (v - min_val) / (max_val - min_val)
        
        return normalized
    
    def _create_feature_rankings(self, importance_scores: Dict[str, float], 
                                config: ImportanceConfig) -> List[str]:
        """Create feature rankings based on importance scores."""
        if not importance_scores:
            return []
        
        # Sort features by importance
        sorted_features = sorted(
            importance_scores.items(), 
            key=lambda x: x[1], 
            reverse=config.sort_by_importance
        )
        
        # Return feature names in order
        return [feature for feature, _ in sorted_features]
    
    async def _generate_plots(self, importance_scores: Dict[str, float], 
                             feature_rankings: List[str], config: ImportanceConfig) -> Dict[str, Any]:
        """Generate feature importance plots."""
        plots = {}
        
        try:
            # Bar plot
            plots["bar_plot"] = self._create_bar_plot(importance_scores, feature_rankings, config)
            
            # Horizontal bar plot
            plots["horizontal_bar_plot"] = self._create_horizontal_bar_plot(importance_scores, feature_rankings, config)
            
            # Feature importance distribution
            plots["distribution_plot"] = self._create_distribution_plot(importance_scores, config)
            
            # Top features plot
            plots["top_features_plot"] = self._create_top_features_plot(importance_scores, feature_rankings, config)
        
        except Exception as e:
            logger.warning(f"Plot generation failed: {e}")
            plots["error"] = str(e)
        
        return plots
    
    def _create_bar_plot(self, importance_scores: Dict[str, float], 
                        feature_rankings: List[str], config: ImportanceConfig) -> Dict[str, Any]:
        """Create bar plot data."""
        # Limit to top features
        top_features = feature_rankings[:config.max_features]
        
        return {
            "feature_names": top_features,
            "importance_values": [importance_scores.get(f, 0.0) for f in top_features],
            "title": f"Feature Importance ({config.method.value})",
            "x_label": "Features",
            "y_label": "Importance Score"
        }
    
    def _create_horizontal_bar_plot(self, importance_scores: Dict[str, float], 
                                   feature_rankings: List[str], config: ImportanceConfig) -> Dict[str, Any]:
        """Create horizontal bar plot data."""
        # Limit to top features
        top_features = feature_rankings[:config.max_features]
        
        return {
            "feature_names": top_features,
            "importance_values": [importance_scores.get(f, 0.0) for f in top_features],
            "title": f"Feature Importance ({config.method.value})",
            "x_label": "Importance Score",
            "y_label": "Features"
        }
    
    def _create_distribution_plot(self, importance_scores: Dict[str, float], 
                                 config: ImportanceConfig) -> Dict[str, Any]:
        """Create distribution plot data."""
        values = list(importance_scores.values())
        
        return {
            "values": values,
            "title": "Feature Importance Distribution",
            "x_label": "Importance Score",
            "y_label": "Frequency",
            "statistics": {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values)
            }
        }
    
    def _create_top_features_plot(self, importance_scores: Dict[str, float], 
                                 feature_rankings: List[str], config: ImportanceConfig) -> Dict[str, Any]:
        """Create top features plot data."""
        # Get top features
        top_features = feature_rankings[:min(10, len(feature_rankings))]
        
        return {
            "feature_names": top_features,
            "importance_values": [importance_scores.get(f, 0.0) for f in top_features],
            "cumulative_importance": np.cumsum([importance_scores.get(f, 0.0) for f in top_features]).tolist(),
            "title": f"Top {len(top_features)} Features",
            "x_label": "Features",
            "y_label": "Importance Score"
        }
    
    def _calculate_summary_stats(self, importance_scores: Dict[str, float], 
                                feature_rankings: List[str]) -> Dict[str, float]:
        """Calculate summary statistics for feature importance."""
        stats = {}
        
        try:
            if not importance_scores:
                return stats
            
            values = list(importance_scores.values())
            
            # Basic statistics
            stats["n_features"] = len(importance_scores)
            stats["mean_importance"] = float(np.mean(values))
            stats["std_importance"] = float(np.std(values))
            stats["min_importance"] = float(np.min(values))
            stats["max_importance"] = float(np.max(values))
            stats["median_importance"] = float(np.median(values))
            
            # Top feature statistics
            if feature_rankings:
                top_feature = feature_rankings[0]
                stats["top_feature"] = top_feature
                stats["top_feature_importance"] = float(importance_scores.get(top_feature, 0.0))
                
                # Calculate how much of total importance is in top 5 features
                top_5_importance = sum(importance_scores.get(f, 0.0) for f in feature_rankings[:5])
                total_importance = sum(values)
                if total_importance > 0:
                    stats["top_5_importance_ratio"] = float(top_5_importance / total_importance)
            
            # Importance distribution
            stats["importance_range"] = float(np.max(values) - np.min(values))
            stats["importance_cv"] = float(np.std(values) / np.mean(values)) if np.mean(values) > 0 else 0.0
        
        except Exception as e:
            logger.warning(f"Summary statistics calculation failed: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get analysis history."""
        return self.analysis_history
    
    def get_available_methods(self) -> List[str]:
        """Get available importance methods."""
        return [method.value for method in ImportanceMethod]
    
    def get_available_importance_types(self) -> List[str]:
        """Get available importance types."""
        return [importance_type.value for importance_type in ImportanceType]
    
    def get_method_info(self, method: ImportanceMethod) -> Dict[str, Any]:
        """Get information about an importance method."""
        method_info = {
            ImportanceMethod.MODEL_BASED: {
                "name": "Model-based Importance",
                "description": "Uses built-in model feature importance (e.g., tree-based models)",
                "pros": ["Fast", "Model-specific", "Built-in"],
                "cons": ["Not available for all models", "May be biased"]
            },
            ImportanceMethod.PERMUTATION: {
                "name": "Permutation Importance",
                "description": "Measures importance by permuting features and measuring performance drop",
                "pros": ["Model-agnostic", "Reliable", "Interpretable"],
                "cons": ["Computationally expensive", "May be affected by feature interactions"]
            },
            ImportanceMethod.MUTUAL_INFO: {
                "name": "Mutual Information",
                "description": "Measures mutual information between features and target",
                "pros": ["Model-agnostic", "Captures non-linear relationships", "Fast"],
                "cons": ["May miss feature interactions", "Univariate only"]
            },
            ImportanceMethod.PARTIAL_DEPENDENCE: {
                "name": "Partial Dependence",
                "description": "Measures feature importance using partial dependence plots",
                "pros": ["Captures feature interactions", "Interpretable", "Model-agnostic"],
                "cons": ["Computationally expensive", "May be affected by feature correlations"]
            },
            ImportanceMethod.CORRELATION: {
                "name": "Correlation-based",
                "description": "Uses correlation between features and target as importance",
                "pros": ["Very fast", "Simple", "Linear relationships"],
                "cons": ["Only captures linear relationships", "May miss important non-linear features"]
            },
            ImportanceMethod.UNIVARIATE: {
                "name": "Univariate Selection",
                "description": "Uses univariate statistical tests for feature importance",
                "pros": ["Fast", "Model-agnostic", "Statistical significance"],
                "cons": ["Univariate only", "May miss feature interactions"]
            }
        }
        
        return method_info.get(method, {"name": "Unknown", "description": "Unknown method"})
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics."""
        if not self.analysis_history:
            return {"total_analyses": 0}
        
        total_analyses = len(self.analysis_history)
        methods = [h["method"] for h in self.analysis_history]
        model_types = [h["model_type"] for h in self.analysis_history]
        
        return {
            "total_analyses": total_analyses,
            "method_distribution": {method: methods.count(method) for method in set(methods)},
            "model_type_distribution": {model_type: model_types.count(model_type) for model_type in set(model_types)},
            "last_analysis": self.analysis_history[-1]["timestamp"] if self.analysis_history else None
        }
