"""
SPIDER AutoML Module

Advanced Automated Machine Learning capabilities for pipeline generation,
hyperparameter optimization, feature engineering, and model selection.

Author: SPIDER Development Team
Version: 1.0.0
"""

from .pipeline_generator import PipelineGenerator, PipelineConfig, PipelineResult
from .hyperparameter_optimizer import HyperparameterOptimizer, OptimizationConfig, OptimizationResult
from .feature_engineer import FeatureEngineer, FeatureConfig, FeatureResult
from .model_selector import ModelSelector, SelectionConfig, SelectionResult
from .ensemble_builder import EnsembleBuilder, EnsembleConfig, EnsembleResult
from .pipeline_optimizer import PipelineOptimizer, OptimizationStrategy
from .automl_manager import AutoMLManager, AutoMLConfig, AutoMLResult

__all__ = [
    # Pipeline Generation
    "PipelineGenerator",
    "PipelineConfig", 
    "PipelineResult",
    
    # Hyperparameter Optimization
    "HyperparameterOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    
    # Feature Engineering
    "FeatureEngineer",
    "FeatureConfig",
    "FeatureResult",
    
    # Model Selection
    "ModelSelector",
    "SelectionConfig",
    "SelectionResult",
    
    # Ensemble Building
    "EnsembleBuilder",
    "EnsembleConfig",
    "EnsembleResult",
    
    # Pipeline Optimization
    "PipelineOptimizer",
    "OptimizationStrategy",
    
    # AutoML Management
    "AutoMLManager",
    "AutoMLConfig",
    "AutoMLResult",
]
