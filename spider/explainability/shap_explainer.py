"""
SHAP Explainer

SHAP (SHapley Additive exPlanations) integration for model explainability.
Provides global and local explanations for machine learning models.

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

# Optional SHAP imports
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available. Some features will be limited.")

logger = logging.getLogger(__name__)


class SHAPMethod(str, Enum):
    """SHAP explanation method enumeration."""
    EXPLAINER = "explainer"
    TREE_EXPLAINER = "tree_explainer"
    LINEAR_EXPLAINER = "linear_explainer"
    DEEP_EXPLAINER = "deep_explainer"
    KERNEL_EXPLAINER = "kernel_explainer"
    SAMPLING_EXPLAINER = "sampling_explainer"
    PARTITION_EXPLAINER = "partition_explainer"


class ExplanationType(str, Enum):
    """Explanation type enumeration."""
    GLOBAL = "global"
    LOCAL = "local"
    INTERACTION = "interaction"
    WATERFALL = "waterfall"
    FORCE = "force"
    BAR = "bar"
    BEESWARM = "beeswarm"
    HEATMAP = "heatmap"


@dataclass
class SHAPConfig:
    """SHAP configuration."""
    method: SHAPMethod = SHAPMethod.EXPLAINER
    explanation_type: ExplanationType = ExplanationType.LOCAL
    max_samples: int = 100
    background_samples: int = 50
    feature_names: Optional[List[str]] = None
    show_progress: bool = True
    random_state: int = 42
    max_evals: int = 1000
    nsamples: int = 100
    l1_reg: str = "aic"
    link: str = "identity"
    feature_perturbation: str = "interventional"
    model_output: str = "raw"


@dataclass
class SHAPResult:
    """SHAP explanation result."""
    explanation_id: str
    shap_values: np.ndarray
    base_value: float
    feature_names: List[str]
    feature_values: np.ndarray
    explanation_type: ExplanationType
    method: SHAPMethod
    model_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    plots: Dict[str, Any] = field(default_factory=dict)
    summary_stats: Dict[str, float] = field(default_factory=dict)


class SHAPExplainer:
    """
    SHAP-based model explainer.
    
    Features:
    - Multiple SHAP explainer types
    - Global and local explanations
    - Feature interaction analysis
    - Visualization generation
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize SHAP explainer."""
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available. Install with: pip install shap")
        
        self.explainer_cache = {}
        self.explanation_history = []
    
    async def explain_model(self, model: BaseEstimator, X: pd.DataFrame, 
                           config: SHAPConfig) -> SHAPResult:
        """
        Explain a machine learning model using SHAP.
        
        Args:
            model: Trained model to explain
            X: Feature data
            config: SHAP configuration
            
        Returns:
            SHAP explanation result
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP is required for model explanation. Install with: pip install shap")
        
        explanation_id = f"shap_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Select appropriate explainer
            explainer = self._get_explainer(model, X, config)
            
            # Generate explanations
            if config.explanation_type == ExplanationType.GLOBAL:
                shap_values, base_value = await self._explain_global(explainer, X, config)
            elif config.explanation_type == ExplanationType.LOCAL:
                shap_values, base_value = await self._explain_local(explainer, X, config)
            elif config.explanation_type == ExplanationType.INTERACTION:
                shap_values, base_value = await self._explain_interaction(explainer, X, config)
            else:
                shap_values, base_value = await self._explain_local(explainer, X, config)
            
            # Generate plots
            plots = await self._generate_plots(explainer, shap_values, X, config)
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_stats(shap_values, X)
            
            # Create result
            result = SHAPResult(
                explanation_id=explanation_id,
                shap_values=shap_values,
                base_value=base_value,
                feature_names=list(X.columns),
                feature_values=X.values,
                explanation_type=config.explanation_type,
                method=config.method,
                model_type=model.__class__.__name__,
                plots=plots,
                summary_stats=summary_stats,
                metadata={
                    "n_samples": len(X),
                    "n_features": len(X.columns),
                    "config": config.__dict__
                }
            )
            
            # Store in history
            self.explanation_history.append({
                "explanation_id": explanation_id,
                "model_type": model.__class__.__name__,
                "explanation_type": config.explanation_type.value,
                "method": config.method.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"SHAP explanation completed: {explanation_id}")
            return result
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            raise
    
    def _get_explainer(self, model: BaseEstimator, X: pd.DataFrame, 
                      config: SHAPConfig) -> Any:
        """Get appropriate SHAP explainer for the model."""
        model_type = model.__class__.__name__
        
        # Check cache first
        cache_key = f"{model_type}_{config.method.value}_{hash(str(X.columns))}"
        if cache_key in self.explainer_cache:
            return self.explainer_cache[cache_key]
        
        # Create explainer based on model type and method
        if config.method == SHAPMethod.TREE_EXPLAINER:
            explainer = shap.TreeExplainer(model)
        elif config.method == SHAPMethod.LINEAR_EXPLAINER:
            explainer = shap.LinearExplainer(model, X)
        elif config.method == SHAPMethod.DEEP_EXPLAINER:
            explainer = shap.DeepExplainer(model, X.iloc[:config.background_samples])
        elif config.method == SHAPMethod.KERNEL_EXPLAINER:
            explainer = shap.KernelExplainer(
                model.predict, 
                X.iloc[:config.background_samples],
                feature_names=config.feature_names or list(X.columns)
            )
        elif config.method == SHAPMethod.SAMPLING_EXPLAINER:
            explainer = shap.SamplingExplainer(
                model.predict,
                X.iloc[:config.background_samples]
            )
        elif config.method == SHAPMethod.PARTITION_EXPLAINER:
            explainer = shap.PartitionExplainer(
                model.predict,
                X.iloc[:config.background_samples]
            )
        else:
            # Default to appropriate explainer based on model type
            if hasattr(model, 'tree_') or 'Tree' in model_type or 'Forest' in model_type:
                explainer = shap.TreeExplainer(model)
            elif hasattr(model, 'coef_'):
                explainer = shap.LinearExplainer(model, X)
            else:
                explainer = shap.KernelExplainer(
                    model.predict,
                    X.iloc[:config.background_samples],
                    feature_names=config.feature_names or list(X.columns)
                )
        
        # Cache explainer
        self.explainer_cache[cache_key] = explainer
        return explainer
    
    async def _explain_global(self, explainer: Any, X: pd.DataFrame, 
                             config: SHAPConfig) -> Tuple[np.ndarray, float]:
        """Generate global SHAP explanations."""
        # Sample data if too large
        if len(X) > config.max_samples:
            X_sample = X.sample(n=config.max_samples, random_state=config.random_state)
        else:
            X_sample = X
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X_sample)
        
        # Handle different output formats
        if isinstance(shap_values, list):
            # Multi-class classification
            shap_values = np.array(shap_values)
            base_value = explainer.expected_value
        else:
            # Single output
            base_value = explainer.expected_value if hasattr(explainer, 'expected_value') else 0.0
        
        return shap_values, base_value
    
    async def _explain_local(self, explainer: Any, X: pd.DataFrame, 
                            config: SHAPConfig) -> Tuple[np.ndarray, float]:
        """Generate local SHAP explanations."""
        # Sample data if too large
        if len(X) > config.max_samples:
            X_sample = X.sample(n=config.max_samples, random_state=config.random_state)
        else:
            X_sample = X
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X_sample)
        
        # Handle different output formats
        if isinstance(shap_values, list):
            # Multi-class classification
            shap_values = np.array(shap_values)
            base_value = explainer.expected_value
        else:
            # Single output
            base_value = explainer.expected_value if hasattr(explainer, 'expected_value') else 0.0
        
        return shap_values, base_value
    
    async def _explain_interaction(self, explainer: Any, X: pd.DataFrame, 
                                  config: SHAPConfig) -> Tuple[np.ndarray, float]:
        """Generate SHAP interaction explanations."""
        # Sample data if too large
        if len(X) > config.max_samples:
            X_sample = X.sample(n=config.max_samples, random_state=config.random_state)
        else:
            X_sample = X
        
        # Calculate SHAP interaction values
        shap_interaction_values = explainer.shap_interaction_values(X_sample)
        
        # Handle different output formats
        if isinstance(shap_interaction_values, list):
            # Multi-class classification
            shap_values = np.array(shap_interaction_values)
            base_value = explainer.expected_value
        else:
            # Single output
            shap_values = shap_interaction_values
            base_value = explainer.expected_value if hasattr(explainer, 'expected_value') else 0.0
        
        return shap_values, base_value
    
    async def _generate_plots(self, explainer: Any, shap_values: np.ndarray, 
                             X: pd.DataFrame, config: SHAPConfig) -> Dict[str, Any]:
        """Generate SHAP plots."""
        plots = {}
        
        try:
            # Waterfall plot
            if config.explanation_type == ExplanationType.WATERFALL:
                plots["waterfall"] = self._create_waterfall_plot(shap_values, X, config)
            
            # Force plot
            elif config.explanation_type == ExplanationType.FORCE:
                plots["force"] = self._create_force_plot(shap_values, X, config)
            
            # Bar plot
            elif config.explanation_type == ExplanationType.BAR:
                plots["bar"] = self._create_bar_plot(shap_values, X, config)
            
            # Beeswarm plot
            elif config.explanation_type == ExplanationType.BEESWARM:
                plots["beeswarm"] = self._create_beeswarm_plot(shap_values, X, config)
            
            # Heatmap plot
            elif config.explanation_type == ExplanationType.HEATMAP:
                plots["heatmap"] = self._create_heatmap_plot(shap_values, X, config)
            
            # Default to summary plot
            else:
                plots["summary"] = self._create_summary_plot(shap_values, X, config)
        
        except Exception as e:
            logger.warning(f"Plot generation failed: {e}")
            plots["error"] = str(e)
        
        return plots
    
    def _create_waterfall_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                              config: SHAPConfig) -> Dict[str, Any]:
        """Create waterfall plot data."""
        # For single instance
        if len(shap_values.shape) == 1:
            instance_idx = 0
        else:
            instance_idx = 0
        
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create waterfall data
        waterfall_data = {
            "feature_names": feature_names,
            "shap_values": shap_values[instance_idx] if len(shap_values.shape) > 1 else shap_values,
            "feature_values": X.iloc[instance_idx].values if len(X) > instance_idx else X.iloc[0].values,
            "base_value": 0.0  # Will be updated with actual base value
        }
        
        return waterfall_data
    
    def _create_force_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                          config: SHAPConfig) -> Dict[str, Any]:
        """Create force plot data."""
        # For single instance
        if len(shap_values.shape) == 1:
            instance_idx = 0
        else:
            instance_idx = 0
        
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create force plot data
        force_data = {
            "feature_names": feature_names,
            "shap_values": shap_values[instance_idx] if len(shap_values.shape) > 1 else shap_values,
            "feature_values": X.iloc[instance_idx].values if len(X) > instance_idx else X.iloc[0].values,
            "base_value": 0.0  # Will be updated with actual base value
        }
        
        return force_data
    
    def _create_bar_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                        config: SHAPConfig) -> Dict[str, Any]:
        """Create bar plot data."""
        # Calculate mean absolute SHAP values
        if len(shap_values.shape) > 1:
            mean_shap = np.mean(np.abs(shap_values), axis=0)
        else:
            mean_shap = np.abs(shap_values)
        
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create bar plot data
        bar_data = {
            "feature_names": feature_names,
            "mean_shap_values": mean_shap.tolist(),
            "sorted_indices": np.argsort(mean_shap)[::-1].tolist()
        }
        
        return bar_data
    
    def _create_beeswarm_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                             config: SHAPConfig) -> Dict[str, Any]:
        """Create beeswarm plot data."""
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create beeswarm plot data
        beeswarm_data = {
            "feature_names": feature_names,
            "shap_values": shap_values.tolist() if len(shap_values.shape) > 1 else [shap_values.tolist()],
            "feature_values": X.values.tolist()
        }
        
        return beeswarm_data
    
    def _create_heatmap_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                            config: SHAPConfig) -> Dict[str, Any]:
        """Create heatmap plot data."""
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create heatmap plot data
        heatmap_data = {
            "feature_names": feature_names,
            "shap_values": shap_values.tolist() if len(shap_values.shape) > 1 else [shap_values.tolist()],
            "feature_values": X.values.tolist()
        }
        
        return heatmap_data
    
    def _create_summary_plot(self, shap_values: np.ndarray, X: pd.DataFrame, 
                           config: SHAPConfig) -> Dict[str, Any]:
        """Create summary plot data."""
        # Calculate mean absolute SHAP values
        if len(shap_values.shape) > 1:
            mean_shap = np.mean(np.abs(shap_values), axis=0)
        else:
            mean_shap = np.abs(shap_values)
        
        # Get feature names
        feature_names = config.feature_names or list(X.columns)
        
        # Create summary plot data
        summary_data = {
            "feature_names": feature_names,
            "mean_shap_values": mean_shap.tolist(),
            "shap_values": shap_values.tolist() if len(shap_values.shape) > 1 else [shap_values.tolist()],
            "feature_values": X.values.tolist()
        }
        
        return summary_data
    
    def _calculate_summary_stats(self, shap_values: np.ndarray, X: pd.DataFrame) -> Dict[str, float]:
        """Calculate summary statistics for SHAP values."""
        stats = {}
        
        try:
            # Basic statistics
            stats["mean_abs_shap"] = float(np.mean(np.abs(shap_values)))
            stats["std_abs_shap"] = float(np.std(np.abs(shap_values)))
            stats["max_abs_shap"] = float(np.max(np.abs(shap_values)))
            stats["min_abs_shap"] = float(np.min(np.abs(shap_values)))
            
            # Feature importance (mean absolute SHAP values)
            if len(shap_values.shape) > 1:
                feature_importance = np.mean(np.abs(shap_values), axis=0)
                stats["feature_importance_mean"] = float(np.mean(feature_importance))
                stats["feature_importance_std"] = float(np.std(feature_importance))
            
            # Interaction strength (if interaction values)
            if len(shap_values.shape) == 3:  # Interaction matrix
                interaction_strength = np.mean(np.abs(shap_values), axis=0)
                stats["interaction_strength"] = float(np.mean(interaction_strength))
            
        except Exception as e:
            logger.warning(f"Summary statistics calculation failed: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def get_explanation_history(self) -> List[Dict[str, Any]]:
        """Get explanation history."""
        return self.explanation_history
    
    def get_available_methods(self) -> List[str]:
        """Get available SHAP methods."""
        return [method.value for method in SHAPMethod]
    
    def get_available_explanation_types(self) -> List[str]:
        """Get available explanation types."""
        return [explanation_type.value for explanation_type in ExplanationType]
    
    def get_explainer_info(self, model: BaseEstimator) -> Dict[str, Any]:
        """Get information about which explainer would be used for a model."""
        model_type = model.__class__.__name__
        
        if hasattr(model, 'tree_') or 'Tree' in model_type or 'Forest' in model_type:
            recommended_method = SHAPMethod.TREE_EXPLAINER
            description = "Tree-based explainer for tree and ensemble models"
        elif hasattr(model, 'coef_'):
            recommended_method = SHAPMethod.LINEAR_EXPLAINER
            description = "Linear explainer for linear models"
        else:
            recommended_method = SHAPMethod.KERNEL_EXPLAINER
            description = "Kernel explainer for general models"
        
        return {
            "model_type": model_type,
            "recommended_method": recommended_method.value,
            "description": description,
            "supports_interaction": recommended_method in [SHAPMethod.TREE_EXPLAINER, SHAPMethod.LINEAR_EXPLAINER]
        }
    
    def clear_cache(self):
        """Clear explainer cache."""
        self.explainer_cache.clear()
        logger.info("SHAP explainer cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "cached_explainers": len(self.explainer_cache),
            "cache_keys": list(self.explainer_cache.keys()),
            "total_explanations": len(self.explanation_history)
        }
