"""
SPIDER Model Explainability Module

Advanced model explainability and interpretability capabilities for AI/ML models.
Includes SHAP, LIME, feature importance, and model debugging tools.

Author: SPIDER Development Team
Version: 1.0.0
"""

from .shap_explainer import SHAPExplainer, SHAPConfig, SHAPResult
from .lime_explainer import LIMEExplainer, LIMEConfig, LIMEResult
from .feature_importance import FeatureImportanceAnalyzer, ImportanceConfig, ImportanceResult
from .model_debugger import ModelDebugger, DebugConfig, DebugResult
from .bias_detector import BiasDetector, BiasConfig, BiasResult
from .explainability_manager import ExplainabilityManager, ExplainabilityConfig, ExplainabilityResult

__all__ = [
    # SHAP Integration
    "SHAPExplainer",
    "SHAPConfig",
    "SHAPResult",
    
    # LIME Integration
    "LIMEExplainer", 
    "LIMEConfig",
    "LIMEResult",
    
    # Feature Importance
    "FeatureImportanceAnalyzer",
    "ImportanceConfig",
    "ImportanceResult",
    
    # Model Debugging
    "ModelDebugger",
    "DebugConfig", 
    "DebugResult",
    
    # Bias Detection
    "BiasDetector",
    "BiasConfig",
    "BiasResult",
    
    # Explainability Management
    "ExplainabilityManager",
    "ExplainabilityConfig",
    "ExplainabilityResult",
]
