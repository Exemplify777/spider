"""
LIME Explainer

LIME (Local Interpretable Model-agnostic Explanations) integration for model explainability.
Provides local explanations for individual predictions.

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

# Optional LIME imports
try:
    import lime
    import lime.lime_tabular
    import lime.lime_text
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    logger.warning("LIME not available. Some features will be limited.")

logger = logging.getLogger(__name__)


class LIMEMode(str, Enum):
    """LIME mode enumeration."""
    TABULAR = "tabular"
    TEXT = "text"
    IMAGE = "image"


class ExplanationMode(str, Enum):
    """Explanation mode enumeration."""
    SINGLE = "single"
    BATCH = "batch"
    FEATURE_IMPORTANCE = "feature_importance"
    INTERACTION = "interaction"


@dataclass
class LIMEConfig:
    """LIME configuration."""
    mode: LIMEMode = LIMEMode.TABULAR
    explanation_mode: ExplanationMode = ExplanationMode.SINGLE
    num_features: int = 10
    num_samples: int = 5000
    random_state: int = 42
    kernel_width: float = 0.75
    feature_selection: str = "auto"
    discretize_continuous: bool = True
    discretizer: str = "quartile"
    sample_around_instance: bool = True
    distance_metric: str = "euclidean"
    model_regressor: Optional[Any] = None
    feature_names: Optional[List[str]] = None
    categorical_features: Optional[List[int]] = None
    categorical_names: Optional[Dict[int, List[str]]] = None


@dataclass
class LIMEResult:
    """LIME explanation result."""
    explanation_id: str
    explanations: List[Dict[str, Any]]
    feature_names: List[str]
    feature_values: np.ndarray
    prediction: float
    explanation_mode: ExplanationMode
    mode: LIMEMode
    model_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    plots: Dict[str, Any] = field(default_factory=dict)
    summary_stats: Dict[str, float] = field(default_factory=dict)


class LIMEExplainer:
    """
    LIME-based model explainer.
    
    Features:
    - Local explanations for individual predictions
    - Support for tabular, text, and image data
    - Feature importance analysis
    - Batch explanation processing
    - Visualization generation
    """
    
    def __init__(self):
        """Initialize LIME explainer."""
        if not LIME_AVAILABLE:
            logger.warning("LIME not available. Install with: pip install lime")
        
        self.explainer_cache = {}
        self.explanation_history = []
    
    async def explain_model(self, model: BaseEstimator, X: pd.DataFrame, 
                           config: LIMEConfig, instances: Optional[List[int]] = None) -> LIMEResult:
        """
        Explain a machine learning model using LIME.
        
        Args:
            model: Trained model to explain
            X: Feature data
            config: LIME configuration
            instances: Specific instances to explain (if None, explains first instance)
            
        Returns:
            LIME explanation result
        """
        if not LIME_AVAILABLE:
            raise ImportError("LIME is required for model explanation. Install with: pip install lime")
        
        explanation_id = f"lime_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Get or create explainer
            explainer = self._get_explainer(model, X, config)
            
            # Determine instances to explain
            if instances is None:
                instances = [0]  # Default to first instance
            
            # Generate explanations
            explanations = []
            predictions = []
            
            for instance_idx in instances:
                if instance_idx >= len(X):
                    logger.warning(f"Instance {instance_idx} out of range, skipping")
                    continue
                
                explanation = await self._explain_instance(
                    explainer, model, X.iloc[instance_idx:instance_idx+1], config
                )
                explanations.append(explanation)
                
                # Get prediction
                prediction = model.predict(X.iloc[instance_idx:instance_idx+1])[0]
                predictions.append(prediction)
            
            # Generate plots
            plots = await self._generate_plots(explanations, X, config)
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_stats(explanations, predictions)
            
            # Create result
            result = LIMEResult(
                explanation_id=explanation_id,
                explanations=explanations,
                feature_names=list(X.columns),
                feature_values=X.iloc[instances].values if instances else X.iloc[0:1].values,
                prediction=predictions[0] if predictions else 0.0,
                explanation_mode=config.explanation_mode,
                mode=config.mode,
                model_type=model.__class__.__name__,
                plots=plots,
                summary_stats=summary_stats,
                metadata={
                    "n_instances": len(instances) if instances else 1,
                    "n_features": len(X.columns),
                    "config": config.__dict__
                }
            )
            
            # Store in history
            self.explanation_history.append({
                "explanation_id": explanation_id,
                "model_type": model.__class__.__name__,
                "explanation_mode": config.explanation_mode.value,
                "mode": config.mode.value,
                "n_instances": len(instances) if instances else 1,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"LIME explanation completed: {explanation_id}")
            return result
            
        except Exception as e:
            logger.error(f"LIME explanation failed: {e}")
            raise
    
    def _get_explainer(self, model: BaseEstimator, X: pd.DataFrame, 
                      config: LIMEConfig) -> Any:
        """Get appropriate LIME explainer for the data."""
        # Check cache first
        cache_key = f"{config.mode.value}_{hash(str(X.columns))}_{config.num_features}"
        if cache_key in self.explainer_cache:
            return self.explainer_cache[cache_key]
        
        # Create explainer based on mode
        if config.mode == LIMEMode.TABULAR:
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X.values,
                feature_names=config.feature_names or list(X.columns),
                categorical_features=config.categorical_features,
                categorical_names=config.categorical_names,
                class_names=None,  # Will be determined from model
                discretize_continuous=config.discretize_continuous,
                discretizer=config.discretizer,
                random_state=config.random_state,
                mode='regression' if hasattr(model, 'predict') and not hasattr(model, 'predict_proba') else 'classification'
            )
        elif config.mode == LIMEMode.TEXT:
            # For text data, we would need text data and a text explainer
            # This is a simplified version
            explainer = lime.lime_text.LimeTextExplainer(
                class_names=None,
                random_state=config.random_state
            )
        else:
            raise ValueError(f"Unsupported LIME mode: {config.mode}")
        
        # Cache explainer
        self.explainer_cache[cache_key] = explainer
        return explainer
    
    async def _explain_instance(self, explainer: Any, model: BaseEstimator, 
                               instance: pd.DataFrame, config: LIMEConfig) -> Dict[str, Any]:
        """Explain a single instance."""
        try:
            # Generate explanation
            explanation = explainer.explain_instance(
                instance.values[0],
                model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                num_features=config.num_features,
                num_samples=config.num_samples,
                distance_metric=config.distance_metric,
                model_regressor=config.model_regressor
            )
            
            # Extract explanation data
            explanation_data = {
                "feature_names": [name for name, _ in explanation.as_list()],
                "feature_values": [value for _, value in explanation.as_list()],
                "feature_importance": dict(explanation.as_list()),
                "score": explanation.score,
                "intercept": explanation.intercept,
                "local_pred": explanation.local_pred,
                "local_exp": explanation.local_exp
            }
            
            return explanation_data
            
        except Exception as e:
            logger.warning(f"Instance explanation failed: {e}")
            return {
                "error": str(e),
                "feature_names": [],
                "feature_values": [],
                "feature_importance": {},
                "score": 0.0,
                "intercept": 0.0,
                "local_pred": 0.0,
                "local_exp": []
            }
    
    async def _generate_plots(self, explanations: List[Dict[str, Any]], 
                             X: pd.DataFrame, config: LIMEConfig) -> Dict[str, Any]:
        """Generate LIME plots."""
        plots = {}
        
        try:
            # Feature importance plot
            plots["feature_importance"] = self._create_feature_importance_plot(explanations, config)
            
            # Instance comparison plot
            if len(explanations) > 1:
                plots["instance_comparison"] = self._create_instance_comparison_plot(explanations, config)
            
            # Feature value plot
            plots["feature_values"] = self._create_feature_values_plot(explanations, X, config)
            
            # Summary plot
            plots["summary"] = self._create_summary_plot(explanations, config)
        
        except Exception as e:
            logger.warning(f"Plot generation failed: {e}")
            plots["error"] = str(e)
        
        return plots
    
    def _create_feature_importance_plot(self, explanations: List[Dict[str, Any]], 
                                       config: LIMEConfig) -> Dict[str, Any]:
        """Create feature importance plot data."""
        if not explanations:
            return {"error": "No explanations available"}
        
        # Aggregate feature importance across instances
        all_features = set()
        for exp in explanations:
            all_features.update(exp.get("feature_names", []))
        
        feature_importance = {}
        for feature in all_features:
            importance_values = []
            for exp in explanations:
                if feature in exp.get("feature_importance", {}):
                    importance_values.append(exp["feature_importance"][feature])
            
            if importance_values:
                feature_importance[feature] = np.mean(importance_values)
        
        # Sort by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return {
            "feature_names": [f[0] for f in sorted_features],
            "importance_values": [f[1] for f in sorted_features],
            "sorted_indices": list(range(len(sorted_features)))
        }
    
    def _create_instance_comparison_plot(self, explanations: List[Dict[str, Any]], 
                                        config: LIMEConfig) -> Dict[str, Any]:
        """Create instance comparison plot data."""
        if len(explanations) < 2:
            return {"error": "Need at least 2 instances for comparison"}
        
        # Get common features
        all_features = set()
        for exp in explanations:
            all_features.update(exp.get("feature_names", []))
        
        common_features = list(all_features)
        
        # Create comparison data
        comparison_data = {
            "feature_names": common_features,
            "instances": []
        }
        
        for i, exp in enumerate(explanations):
            instance_data = {
                "instance_id": i,
                "feature_importance": []
            }
            
            for feature in common_features:
                importance = exp.get("feature_importance", {}).get(feature, 0.0)
                instance_data["feature_importance"].append(importance)
            
            comparison_data["instances"].append(instance_data)
        
        return comparison_data
    
    def _create_feature_values_plot(self, explanations: List[Dict[str, Any]], 
                                   X: pd.DataFrame, config: LIMEConfig) -> Dict[str, Any]:
        """Create feature values plot data."""
        if not explanations:
            return {"error": "No explanations available"}
        
        # Get feature values for explained instances
        feature_values_data = {
            "feature_names": list(X.columns),
            "instances": []
        }
        
        for i, exp in enumerate(explanations):
            if i < len(X):
                instance_data = {
                    "instance_id": i,
                    "feature_values": X.iloc[i].values.tolist(),
                    "feature_importance": []
                }
                
                # Get importance for each feature
                for feature in X.columns:
                    importance = exp.get("feature_importance", {}).get(feature, 0.0)
                    instance_data["feature_importance"].append(importance)
                
                feature_values_data["instances"].append(instance_data)
        
        return feature_values_data
    
    def _create_summary_plot(self, explanations: List[Dict[str, Any]], 
                           config: LIMEConfig) -> Dict[str, Any]:
        """Create summary plot data."""
        if not explanations:
            return {"error": "No explanations available"}
        
        # Aggregate statistics
        all_scores = [exp.get("score", 0.0) for exp in explanations]
        all_intercepts = [exp.get("intercept", 0.0) for exp in explanations]
        
        # Feature importance statistics
        all_features = set()
        for exp in explanations:
            all_features.update(exp.get("feature_names", []))
        
        feature_stats = {}
        for feature in all_features:
            importance_values = []
            for exp in explanations:
                if feature in exp.get("feature_importance", {}):
                    importance_values.append(exp["feature_importance"][feature])
            
            if importance_values:
                feature_stats[feature] = {
                    "mean": np.mean(importance_values),
                    "std": np.std(importance_values),
                    "count": len(importance_values)
                }
        
        return {
            "n_instances": len(explanations),
            "score_stats": {
                "mean": np.mean(all_scores),
                "std": np.std(all_scores),
                "min": np.min(all_scores),
                "max": np.max(all_scores)
            },
            "intercept_stats": {
                "mean": np.mean(all_intercepts),
                "std": np.std(all_intercepts),
                "min": np.min(all_intercepts),
                "max": np.max(all_intercepts)
            },
            "feature_stats": feature_stats
        }
    
    def _calculate_summary_stats(self, explanations: List[Dict[str, Any]], 
                                predictions: List[float]) -> Dict[str, float]:
        """Calculate summary statistics for LIME explanations."""
        stats = {}
        
        try:
            # Basic statistics
            stats["n_explanations"] = len(explanations)
            stats["n_predictions"] = len(predictions)
            
            if predictions:
                stats["prediction_mean"] = float(np.mean(predictions))
                stats["prediction_std"] = float(np.std(predictions))
                stats["prediction_min"] = float(np.min(predictions))
                stats["prediction_max"] = float(np.max(predictions))
            
            # Explanation quality statistics
            scores = [exp.get("score", 0.0) for exp in explanations if "score" in exp]
            if scores:
                stats["explanation_score_mean"] = float(np.mean(scores))
                stats["explanation_score_std"] = float(np.std(scores))
                stats["explanation_score_min"] = float(np.min(scores))
                stats["explanation_score_max"] = float(np.max(scores))
            
            # Feature importance statistics
            all_importances = []
            for exp in explanations:
                importances = exp.get("feature_importance", {})
                all_importances.extend(importances.values())
            
            if all_importances:
                stats["feature_importance_mean"] = float(np.mean(all_importances))
                stats["feature_importance_std"] = float(np.std(all_importances))
                stats["feature_importance_abs_mean"] = float(np.mean(np.abs(all_importances)))
            
        except Exception as e:
            logger.warning(f"Summary statistics calculation failed: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def get_explanation_history(self) -> List[Dict[str, Any]]:
        """Get explanation history."""
        return self.explanation_history
    
    def get_available_modes(self) -> List[str]:
        """Get available LIME modes."""
        return [mode.value for mode in LIMEMode]
    
    def get_available_explanation_modes(self) -> List[str]:
        """Get available explanation modes."""
        return [mode.value for mode in ExplanationMode]
    
    def get_explainer_info(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Get information about which explainer would be used for the data."""
        data_type = "tabular"  # Default for DataFrame
        
        if data_type == "tabular":
            recommended_mode = LIMEMode.TABULAR
            description = "Tabular explainer for structured data"
        else:
            recommended_mode = LIMEMode.TABULAR
            description = "Default tabular explainer"
        
        return {
            "data_type": data_type,
            "recommended_mode": recommended_mode.value,
            "description": description,
            "n_features": len(X.columns),
            "n_samples": len(X)
        }
    
    def clear_cache(self):
        """Clear explainer cache."""
        self.explainer_cache.clear()
        logger.info("LIME explainer cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "cached_explainers": len(self.explainer_cache),
            "cache_keys": list(self.explainer_cache.keys()),
            "total_explanations": len(self.explanation_history)
        }
