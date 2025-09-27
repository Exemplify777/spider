"""
AutoML Manager

Comprehensive AutoML management system that orchestrates pipeline generation,
hyperparameter optimization, feature engineering, and model selection.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from .pipeline_generator import PipelineGenerator, PipelineConfig, PipelineResult
from .hyperparameter_optimizer import HyperparameterOptimizer, OptimizationConfig, OptimizationResult
from .feature_engineer import FeatureEngineer, FeatureConfig, FeatureResult
from .model_selector import ModelSelector, SelectionConfig, SelectionResult

logger = logging.getLogger(__name__)


class AutoMLMode(str, Enum):
    """AutoML mode enumeration."""
    QUICK = "quick"
    BALANCED = "balanced"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


class OptimizationLevel(str, Enum):
    """Optimization level enumeration."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class AutoMLConfig:
    """AutoML configuration."""
    mode: AutoMLMode = AutoMLMode.BALANCED
    optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE
    task_type: str = "classification"  # "classification" or "regression"
    target_column: str = "target"
    test_size: float = 0.2
    random_state: int = 42
    max_training_time: int = 3600  # seconds
    enable_feature_engineering: bool = True
    enable_hyperparameter_optimization: bool = True
    enable_model_selection: bool = True
    enable_ensemble: bool = True
    performance_metric: str = "accuracy"
    custom_metric: Optional[callable] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoMLResult:
    """AutoML result container."""
    automl_id: str
    best_pipeline: Pipeline
    best_model: Any
    performance_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    pipeline_result: Optional[PipelineResult] = None
    feature_result: Optional[FeatureResult] = None
    optimization_result: Optional[OptimizationResult] = None
    selection_result: Optional[SelectionResult] = None
    training_time: float = 0.0
    total_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    config: AutoMLConfig = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AutoMLManager:
    """
    Comprehensive AutoML management system.
    
    Features:
    - End-to-end automated machine learning pipeline
    - Intelligent configuration based on data characteristics
    - Multi-stage optimization and selection
    - Performance monitoring and analysis
    - Result caching and reproducibility
    """
    
    def __init__(self):
        """Initialize AutoML manager."""
        self.pipeline_generator = PipelineGenerator()
        self.hyperparameter_optimizer = HyperparameterOptimizer()
        self.feature_engineer = FeatureEngineer()
        self.model_selector = ModelSelector()
        self.results_cache = {}
        self.experiment_history = []
    
    async def run_automl(self, data: pd.DataFrame, config: AutoMLConfig) -> AutoMLResult:
        """
        Run complete AutoML pipeline.
        
        Args:
            data: Input data
            config: AutoML configuration
            
        Returns:
            AutoML result
        """
        automl_id = f"automl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        try:
            # Validate configuration
            self._validate_config(config)
            
            # Prepare data
            X, y = self._prepare_data(data, config)
            
            # Run AutoML pipeline based on mode
            if config.mode == AutoMLMode.QUICK:
                result = await self._run_quick_mode(X, y, config, automl_id)
            elif config.mode == AutoMLMode.BALANCED:
                result = await self._run_balanced_mode(X, y, config, automl_id)
            elif config.mode == AutoMLMode.COMPREHENSIVE:
                result = await self._run_comprehensive_mode(X, y, config, automl_id)
            else:
                result = await self._run_custom_mode(X, y, config, automl_id)
            
            # Calculate total time
            result.total_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store result
            self.results_cache[automl_id] = result
            
            # Store in history
            self.experiment_history.append({
                "automl_id": automl_id,
                "mode": config.mode.value,
                "task_type": config.task_type,
                "performance": result.performance_metrics,
                "training_time": result.training_time,
                "total_time": result.total_time,
                "timestamp": start_time.isoformat()
            })
            
            logger.info(f"AutoML completed: {automl_id} - Best score: {max(result.performance_metrics.values()) if result.performance_metrics else 0:.4f}")
            return result
            
        except Exception as e:
            error_msg = f"AutoML failed: {str(e)}"
            logger.error(error_msg)
            
            return AutoMLResult(
                automl_id=automl_id,
                best_pipeline=Pipeline([]),
                best_model=None,
                performance_metrics={},
                total_time=(datetime.utcnow() - start_time).total_seconds(),
                config=config,
                errors=[error_msg],
                created_at=start_time
            )
    
    def _validate_config(self, config: AutoMLConfig):
        """Validate AutoML configuration."""
        if config.task_type not in ["classification", "regression"]:
            raise ValueError("task_type must be 'classification' or 'regression'")
        
        if not 0 < config.test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
        
        if config.max_training_time <= 0:
            raise ValueError("max_training_time must be positive")
    
    def _prepare_data(self, data: pd.DataFrame, config: AutoMLConfig) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for AutoML."""
        if config.target_column not in data.columns:
            raise ValueError(f"Target column '{config.target_column}' not found in data")
        
        X = data.drop(columns=[config.target_column])
        y = data[config.target_column]
        
        # Handle missing values
        X = X.fillna(X.median() if X.select_dtypes(include=[np.number]).shape[1] > 0 else X.mode().iloc[0])
        
        return X, y
    
    async def _run_quick_mode(self, X: pd.DataFrame, y: pd.Series, 
                             config: AutoMLConfig, automl_id: str) -> AutoMLResult:
        """Run AutoML in quick mode."""
        # Quick mode: minimal feature engineering, basic model selection
        feature_config = FeatureConfig(
            enable_polynomial_features=False,
            enable_interaction_features=False,
            enable_binning=False,
            enable_log_transform=False,
            enable_time_features=False,
            enable_text_features=False,
            enable_aggregation=False,
            enable_ratio_features=False,
            max_features=20
        )
        
        selection_config = SelectionConfig(
            task_type=config.task_type,
            selection_strategy="best_single",
            performance_metric=config.performance_metric,
            cv_folds=3,
            max_models=3,
            enable_ensemble=False
        )
        
        # Run feature engineering
        feature_result = await self.feature_engineer.engineer_features(X, y, feature_config)
        X_engineered = X[feature_result.selected_features]
        
        # Run model selection
        selection_result = await self.model_selector.select_models(X_engineered, y, selection_config)
        
        if not selection_result.selected_models:
            raise ValueError("No models selected in quick mode")
        
        best_model = selection_result.best_model
        
        # Create simple pipeline
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', best_model.model)
        ])
        
        # Train and evaluate
        X_train, X_test, y_train, y_test = train_test_split(
            X_engineered, y, test_size=config.test_size, random_state=config.random_state
        )
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, config.task_type)
        
        return AutoMLResult(
            automl_id=automl_id,
            best_pipeline=pipeline,
            best_model=best_model.model,
            performance_metrics=metrics,
            feature_result=feature_result,
            selection_result=selection_result,
            training_time=best_model.training_time,
            config=config
        )
    
    async def _run_balanced_mode(self, X: pd.DataFrame, y: pd.Series, 
                                config: AutoMLConfig, automl_id: str) -> AutoMLResult:
        """Run AutoML in balanced mode."""
        # Balanced mode: moderate feature engineering, comprehensive model selection
        feature_config = FeatureConfig(
            enable_polynomial_features=True,
            enable_interaction_features=True,
            enable_binning=True,
            enable_log_transform=True,
            enable_time_features=True,
            enable_text_features=True,
            enable_aggregation=True,
            enable_ratio_features=True,
            max_features=50
        )
        
        selection_config = SelectionConfig(
            task_type=config.task_type,
            selection_strategy="top_k",
            performance_metric=config.performance_metric,
            cv_folds=5,
            max_models=5,
            enable_ensemble=True
        )
        
        # Run feature engineering
        feature_result = await self.feature_engineer.engineer_features(X, y, feature_config)
        X_engineered = X[feature_result.selected_features]
        
        # Run model selection
        selection_result = await self.model_selector.select_models(X_engineered, y, selection_config)
        
        if not selection_result.selected_models:
            raise ValueError("No models selected in balanced mode")
        
        best_model = selection_result.best_model
        
        # Hyperparameter optimization
        optimization_result = None
        if config.enable_hyperparameter_optimization:
            optimization_config = OptimizationConfig(
                method="bayesian_optimization",
                n_trials=50,
                cv_folds=5,
                metric=config.performance_metric
            )
            
            optimization_result = await self.hyperparameter_optimizer.optimize(
                best_model.model, X_engineered, y, optimization_config
            )
            
            # Update model with best parameters
            best_model.model.set_params(**optimization_result.best_params)
        
        # Create pipeline
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', best_model.model)
        ])
        
        # Train and evaluate
        X_train, X_test, y_train, y_test = train_test_split(
            X_engineered, y, test_size=config.test_size, random_state=config.random_state
        )
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, config.task_type)
        
        return AutoMLResult(
            automl_id=automl_id,
            best_pipeline=pipeline,
            best_model=best_model.model,
            performance_metrics=metrics,
            feature_result=feature_result,
            optimization_result=optimization_result,
            selection_result=selection_result,
            training_time=best_model.training_time,
            config=config
        )
    
    async def _run_comprehensive_mode(self, X: pd.DataFrame, y: pd.Series, 
                                     config: AutoMLConfig, automl_id: str) -> AutoMLResult:
        """Run AutoML in comprehensive mode."""
        # Comprehensive mode: full feature engineering, extensive optimization
        feature_config = FeatureConfig(
            enable_polynomial_features=True,
            enable_interaction_features=True,
            enable_binning=True,
            enable_log_transform=True,
            enable_time_features=True,
            enable_text_features=True,
            enable_aggregation=True,
            enable_ratio_features=True,
            max_features=100,
            max_polynomial_degree=3,
            max_interaction_features=20
        )
        
        selection_config = SelectionConfig(
            task_type=config.task_type,
            selection_strategy="ensemble",
            performance_metric=config.performance_metric,
            cv_folds=10,
            max_models=10,
            enable_ensemble=True,
            enable_stacking=True
        )
        
        # Run feature engineering
        feature_result = await self.feature_engineer.engineer_features(X, y, feature_config)
        X_engineered = X[feature_result.selected_features]
        
        # Run model selection
        selection_result = await self.model_selector.select_models(X_engineered, y, selection_config)
        
        if not selection_result.selected_models:
            raise ValueError("No models selected in comprehensive mode")
        
        best_model = selection_result.best_model
        
        # Hyperparameter optimization
        optimization_result = None
        if config.enable_hyperparameter_optimization:
            optimization_config = OptimizationConfig(
                method="bayesian_optimization",
                n_trials=100,
                cv_folds=10,
                metric=config.performance_metric,
                early_stopping=True
            )
            
            optimization_result = await self.hyperparameter_optimizer.optimize(
                best_model.model, X_engineered, y, optimization_config
            )
            
            # Update model with best parameters
            best_model.model.set_params(**optimization_result.best_params)
        
        # Use ensemble if available
        final_model = selection_result.ensemble_model if selection_result.ensemble_model else best_model.model
        
        # Create pipeline
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', final_model)
        ])
        
        # Train and evaluate
        X_train, X_test, y_train, y_test = train_test_split(
            X_engineered, y, test_size=config.test_size, random_state=config.random_state
        )
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, config.task_type)
        
        return AutoMLResult(
            automl_id=automl_id,
            best_pipeline=pipeline,
            best_model=final_model,
            performance_metrics=metrics,
            feature_result=feature_result,
            optimization_result=optimization_result,
            selection_result=selection_result,
            training_time=best_model.training_time,
            config=config
        )
    
    async def _run_custom_mode(self, X: pd.DataFrame, y: pd.Series, 
                              config: AutoMLConfig, automl_id: str) -> AutoMLResult:
        """Run AutoML in custom mode."""
        # Custom mode: use user-provided configuration
        feature_config = FeatureConfig(
            enable_polynomial_features=config.enable_feature_engineering,
            enable_interaction_features=config.enable_feature_engineering,
            enable_binning=config.enable_feature_engineering,
            enable_log_transform=config.enable_feature_engineering,
            enable_time_features=config.enable_feature_engineering,
            enable_text_features=config.enable_feature_engineering,
            enable_aggregation=config.enable_feature_engineering,
            enable_ratio_features=config.enable_feature_engineering,
            max_features=config.constraints.get('max_features', 50)
        )
        
        selection_config = SelectionConfig(
            task_type=config.task_type,
            selection_strategy=config.constraints.get('selection_strategy', 'top_k'),
            performance_metric=config.performance_metric,
            cv_folds=config.constraints.get('cv_folds', 5),
            max_models=config.constraints.get('max_models', 5),
            enable_ensemble=config.enable_ensemble
        )
        
        # Run feature engineering
        feature_result = None
        if config.enable_feature_engineering:
            feature_result = await self.feature_engineer.engineer_features(X, y, feature_config)
            X_engineered = X[feature_result.selected_features]
        else:
            X_engineered = X
        
        # Run model selection
        selection_result = None
        if config.enable_model_selection:
            selection_result = await self.model_selector.select_models(X_engineered, y, selection_config)
            
            if not selection_result.selected_models:
                raise ValueError("No models selected in custom mode")
            
            best_model = selection_result.best_model
        else:
            # Use default model
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            if config.task_type == "classification":
                best_model = type('Model', (), {'model': RandomForestClassifier(), 'training_time': 0.0})()
            else:
                best_model = type('Model', (), {'model': RandomForestRegressor(), 'training_time': 0.0})()
        
        # Hyperparameter optimization
        optimization_result = None
        if config.enable_hyperparameter_optimization and selection_result:
            optimization_config = OptimizationConfig(
                method=config.constraints.get('optimization_method', 'bayesian_optimization'),
                n_trials=config.constraints.get('n_trials', 50),
                cv_folds=config.constraints.get('cv_folds', 5),
                metric=config.performance_metric
            )
            
            optimization_result = await self.hyperparameter_optimizer.optimize(
                best_model.model, X_engineered, y, optimization_config
            )
            
            # Update model with best parameters
            best_model.model.set_params(**optimization_result.best_params)
        
        # Create pipeline
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', best_model.model)
        ])
        
        # Train and evaluate
        X_train, X_test, y_train, y_test = train_test_split(
            X_engineered, y, test_size=config.test_size, random_state=config.random_state
        )
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, config.task_type)
        
        return AutoMLResult(
            automl_id=automl_id,
            best_pipeline=pipeline,
            best_model=best_model.model,
            performance_metrics=metrics,
            feature_result=feature_result,
            optimization_result=optimization_result,
            selection_result=selection_result,
            training_time=best_model.training_time,
            config=config
        )
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray, 
                          task_type: str) -> Dict[str, float]:
        """Calculate performance metrics."""
        metrics = {}
        
        if task_type == "classification":
            metrics.update({
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, average='weighted'),
                "recall": recall_score(y_true, y_pred, average='weighted'),
                "f1_score": f1_score(y_true, y_pred, average='weighted')
            })
        else:
            metrics.update({
                "mse": mean_squared_error(y_true, y_pred),
                "mae": mean_absolute_error(y_true, y_pred),
                "r2_score": r2_score(y_true, y_pred)
            })
        
        return metrics
    
    def get_result(self, automl_id: str) -> Optional[AutoMLResult]:
        """Get AutoML result by ID."""
        return self.results_cache.get(automl_id)
    
    def list_results(self) -> List[Dict[str, Any]]:
        """List all AutoML results."""
        return [
            {
                "automl_id": result.automl_id,
                "mode": result.config.mode.value if result.config else "unknown",
                "task_type": result.config.task_type if result.config else "unknown",
                "performance": result.performance_metrics,
                "training_time": result.training_time,
                "total_time": result.total_time,
                "created_at": result.created_at.isoformat()
            }
            for result in self.results_cache.values()
        ]
    
    def get_experiment_history(self) -> List[Dict[str, Any]]:
        """Get experiment history."""
        return self.experiment_history
    
    def get_automl_statistics(self) -> Dict[str, Any]:
        """Get AutoML statistics."""
        if not self.experiment_history:
            return {"total_experiments": 0}
        
        total_experiments = len(self.experiment_history)
        modes = [exp["mode"] for exp in self.experiment_history]
        task_types = [exp["task_type"] for exp in self.experiment_history]
        
        return {
            "total_experiments": total_experiments,
            "mode_distribution": {mode: modes.count(mode) for mode in set(modes)},
            "task_type_distribution": {task: task_types.count(task) for task in set(task_types)},
            "average_training_time": np.mean([exp["training_time"] for exp in self.experiment_history]),
            "average_total_time": np.mean([exp["total_time"] for exp in self.experiment_history]),
            "last_experiment": self.experiment_history[-1]["timestamp"] if self.experiment_history else None
        }
    
    def get_available_modes(self) -> List[str]:
        """Get available AutoML modes."""
        return [mode.value for mode in AutoMLMode]
    
    def get_available_optimization_levels(self) -> List[str]:
        """Get available optimization levels."""
        return [level.value for level in OptimizationLevel]
    
    def clear_cache(self):
        """Clear results cache."""
        self.results_cache.clear()
        logger.info("AutoML results cache cleared")
    
    def export_result(self, automl_id: str, file_path: str) -> bool:
        """Export AutoML result to file."""
        result = self.get_result(automl_id)
        if not result:
            return False
        
        try:
            import joblib
            joblib.dump(result, file_path)
            logger.info(f"AutoML result exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export result: {e}")
            return False
    
    def import_result(self, file_path: str) -> bool:
        """Import AutoML result from file."""
        try:
            import joblib
            result = joblib.load(file_path)
            if isinstance(result, AutoMLResult):
                self.results_cache[result.automl_id] = result
                logger.info(f"AutoML result imported from {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to import result: {e}")
        
        return False
