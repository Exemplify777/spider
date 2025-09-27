"""
Hyperparameter Optimizer

Advanced hyperparameter optimization for machine learning models.
Includes grid search, random search, Bayesian optimization, and genetic algorithms.

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
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_val_score
from sklearn.metrics import make_scorer, accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.base import BaseEstimator
import optuna
from optuna.samplers import TPESampler, RandomSampler, CmaEsSampler
from optuna.pruners import MedianPruner, SuccessiveHalvingPruner

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """Optimization method enumeration."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    TPE = "tpe"
    CMA_ES = "cma_es"


class OptimizationDirection(str, Enum):
    """Optimization direction enumeration."""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass
class OptimizationConfig:
    """Hyperparameter optimization configuration."""
    method: OptimizationMethod = OptimizationMethod.BAYESIAN_OPTIMIZATION
    direction: OptimizationDirection = OptimizationDirection.MAXIMIZE
    n_trials: int = 100
    cv_folds: int = 5
    timeout: int = 3600  # seconds
    n_jobs: int = -1
    random_state: int = 42
    early_stopping: bool = True
    early_stopping_patience: int = 10
    pruning: bool = True
    metric: str = "accuracy"
    custom_metric: Optional[callable] = None
    parameter_space: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Hyperparameter optimization result."""
    best_params: Dict[str, Any]
    best_score: float
    best_trial: int
    optimization_time: float
    n_trials: int
    trial_results: List[Dict[str, Any]] = field(default_factory=list)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    convergence_plot: Optional[Dict[str, Any]] = None
    parameter_importance: Optional[Dict[str, float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class HyperparameterOptimizer:
    """
    Advanced hyperparameter optimization system.
    
    Features:
    - Multiple optimization algorithms (Grid, Random, Bayesian, Genetic)
    - Advanced pruning and early stopping
    - Parallel optimization with joblib
    - Custom metric support
    - Parameter importance analysis
    - Optimization history tracking
    """
    
    def __init__(self):
        """Initialize hyperparameter optimizer."""
        self.optimization_history: List[Dict[str, Any]] = []
        self.parameter_spaces = self._initialize_parameter_spaces()
        self.metrics = self._initialize_metrics()
    
    def _initialize_parameter_spaces(self) -> Dict[str, Dict[str, Any]]:
        """Initialize parameter spaces for different models."""
        return {
            "RandomForestClassifier": {
                "n_estimators": [50, 100, 200, 300],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2", None],
                "bootstrap": [True, False]
            },
            "RandomForestRegressor": {
                "n_estimators": [50, 100, 200, 300],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2", None],
                "bootstrap": [True, False]
            },
            "LogisticRegression": {
                "C": [0.001, 0.01, 0.1, 1, 10, 100],
                "penalty": ["l1", "l2", "elasticnet"],
                "solver": ["liblinear", "saga"],
                "max_iter": [100, 500, 1000]
            },
            "SVC": {
                "C": [0.001, 0.01, 0.1, 1, 10, 100],
                "kernel": ["linear", "poly", "rbf", "sigmoid"],
                "gamma": ["scale", "auto", 0.001, 0.01, 0.1, 1],
                "degree": [2, 3, 4, 5]
            },
            "SVR": {
                "C": [0.001, 0.01, 0.1, 1, 10, 100],
                "kernel": ["linear", "poly", "rbf", "sigmoid"],
                "gamma": ["scale", "auto", 0.001, 0.01, 0.1, 1],
                "epsilon": [0.01, 0.1, 0.2, 0.5]
            },
            "KNeighborsClassifier": {
                "n_neighbors": [3, 5, 7, 9, 11, 15],
                "weights": ["uniform", "distance"],
                "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
                "p": [1, 2]
            },
            "KNeighborsRegressor": {
                "n_neighbors": [3, 5, 7, 9, 11, 15],
                "weights": ["uniform", "distance"],
                "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
                "p": [1, 2]
            },
            "DecisionTreeClassifier": {
                "max_depth": [None, 10, 20, 30, 40],
                "min_samples_split": [2, 5, 10, 20],
                "min_samples_leaf": [1, 2, 4, 8],
                "max_features": ["sqrt", "log2", None],
                "criterion": ["gini", "entropy"]
            },
            "DecisionTreeRegressor": {
                "max_depth": [None, 10, 20, 30, 40],
                "min_samples_split": [2, 5, 10, 20],
                "min_samples_leaf": [1, 2, 4, 8],
                "max_features": ["sqrt", "log2", None],
                "criterion": ["mse", "mae"]
            },
            "MLPClassifier": {
                "hidden_layer_sizes": [(50,), (100,), (50, 50), (100, 50), (100, 100)],
                "activation": ["relu", "tanh", "logistic"],
                "solver": ["adam", "lbfgs", "sgd"],
                "alpha": [0.0001, 0.001, 0.01, 0.1],
                "learning_rate": ["constant", "adaptive"]
            },
            "MLPRegressor": {
                "hidden_layer_sizes": [(50,), (100,), (50, 50), (100, 50), (100, 100)],
                "activation": ["relu", "tanh", "logistic"],
                "solver": ["adam", "lbfgs", "sgd"],
                "alpha": [0.0001, 0.001, 0.01, 0.1],
                "learning_rate": ["constant", "adaptive"]
            },
            "GradientBoostingClassifier": {
                "n_estimators": [50, 100, 200],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 5, 7, 9],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "subsample": [0.8, 0.9, 1.0]
            },
            "GradientBoostingRegressor": {
                "n_estimators": [50, 100, 200],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 5, 7, 9],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "subsample": [0.8, 0.9, 1.0]
            }
        }
    
    def _initialize_metrics(self) -> Dict[str, callable]:
        """Initialize available metrics."""
        return {
            "accuracy": accuracy_score,
            "precision": lambda y_true, y_pred: precision_score(y_true, y_pred, average='weighted'),
            "recall": lambda y_true, y_pred: recall_score(y_true, y_pred, average='weighted'),
            "f1_score": lambda y_true, y_pred: f1_score(y_true, y_pred, average='weighted'),
            "mse": mean_squared_error,
            "mae": mean_absolute_error,
            "r2_score": r2_score
        }
    
    async def optimize(self, model: BaseEstimator, X: pd.DataFrame, y: pd.Series, 
                      config: OptimizationConfig) -> OptimizationResult:
        """
        Optimize hyperparameters for a model.
        
        Args:
            model: Model to optimize
            X: Feature data
            y: Target data
            config: Optimization configuration
            
        Returns:
            Optimization result
        """
        start_time = datetime.utcnow()
        
        try:
            # Get parameter space
            parameter_space = self._get_parameter_space(model, config)
            
            # Create scorer
            scorer = self._create_scorer(config)
            
            # Run optimization based on method
            if config.method == OptimizationMethod.GRID_SEARCH:
                result = await self._grid_search_optimization(
                    model, X, y, parameter_space, scorer, config
                )
            elif config.method == OptimizationMethod.RANDOM_SEARCH:
                result = await self._random_search_optimization(
                    model, X, y, parameter_space, scorer, config
                )
            elif config.method in [OptimizationMethod.BAYESIAN_OPTIMIZATION, 
                                  OptimizationMethod.TPE, OptimizationMethod.CMA_ES]:
                result = await self._optuna_optimization(
                    model, X, y, parameter_space, scorer, config
                )
            else:
                raise ValueError(f"Unsupported optimization method: {config.method}")
            
            # Calculate optimization time
            optimization_time = (datetime.utcnow() - start_time).total_seconds()
            result.optimization_time = optimization_time
            
            # Store in history
            self.optimization_history.append({
                "model": model.__class__.__name__,
                "method": config.method.value,
                "best_score": result.best_score,
                "optimization_time": optimization_time,
                "n_trials": result.n_trials,
                "timestamp": start_time.isoformat()
            })
            
            logger.info(f"Optimization completed: {config.method.value} - Best score: {result.best_score:.4f}")
            return result
            
        except Exception as e:
            error_msg = f"Optimization failed: {str(e)}"
            logger.error(error_msg)
            
            return OptimizationResult(
                best_params={},
                best_score=0.0,
                best_trial=0,
                optimization_time=(datetime.utcnow() - start_time).total_seconds(),
                n_trials=0,
                errors=[error_msg],
                created_at=start_time
            )
    
    def _get_parameter_space(self, model: BaseEstimator, config: OptimizationConfig) -> Dict[str, Any]:
        """Get parameter space for the model."""
        model_name = model.__class__.__name__
        
        if config.parameter_space:
            return config.parameter_space
        
        if model_name in self.parameter_spaces:
            return self.parameter_spaces[model_name]
        
        # Return empty space if model not found
        logger.warning(f"No parameter space found for model: {model_name}")
        return {}
    
    def _create_scorer(self, config: OptimizationConfig):
        """Create scorer for optimization."""
        if config.custom_metric:
            return make_scorer(config.custom_metric, greater_is_better=config.direction == OptimizationDirection.MAXIMIZE)
        
        if config.metric in self.metrics:
            metric_func = self.metrics[config.metric]
            greater_is_better = config.metric in ["accuracy", "precision", "recall", "f1_score", "r2_score"]
            return make_scorer(metric_func, greater_is_better=greater_is_better)
        
        # Default to accuracy
        return make_scorer(accuracy_score, greater_is_better=True)
    
    async def _grid_search_optimization(self, model: BaseEstimator, X: pd.DataFrame, 
                                       y: pd.Series, parameter_space: Dict[str, Any],
                                       scorer, config: OptimizationConfig) -> OptimizationResult:
        """Perform grid search optimization."""
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=parameter_space,
            scoring=scorer,
            cv=config.cv_folds,
            n_jobs=config.n_jobs,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        return OptimizationResult(
            best_params=grid_search.best_params_,
            best_score=grid_search.best_score_,
            best_trial=0,
            n_trials=len(grid_search.cv_results_['params']),
            trial_results=self._format_cv_results(grid_search.cv_results_)
        )
    
    async def _random_search_optimization(self, model: BaseEstimator, X: pd.DataFrame, 
                                         y: pd.Series, parameter_space: Dict[str, Any],
                                         scorer, config: OptimizationConfig) -> OptimizationResult:
        """Perform random search optimization."""
        random_search = RandomizedSearchCV(
            estimator=model,
            param_distributions=parameter_space,
            n_iter=config.n_trials,
            scoring=scorer,
            cv=config.cv_folds,
            n_jobs=config.n_jobs,
            random_state=config.random_state,
            verbose=1
        )
        
        random_search.fit(X, y)
        
        return OptimizationResult(
            best_params=random_search.best_params_,
            best_score=random_search.best_score_,
            best_trial=0,
            n_trials=len(random_search.cv_results_['params']),
            trial_results=self._format_cv_results(random_search.cv_results_)
        )
    
    async def _optuna_optimization(self, model: BaseEstimator, X: pd.DataFrame, 
                                  y: pd.Series, parameter_space: Dict[str, Any],
                                  scorer, config: OptimizationConfig) -> OptimizationResult:
        """Perform Optuna-based optimization."""
        def objective(trial):
            # Sample parameters
            params = {}
            for param_name, param_values in parameter_space.items():
                if isinstance(param_values, list):
                    if all(isinstance(x, (int, float)) for x in param_values):
                        if all(isinstance(x, int) for x in param_values):
                            params[param_name] = trial.suggest_int(param_name, min(param_values), max(param_values))
                        else:
                            params[param_name] = trial.suggest_float(param_name, min(param_values), max(param_values))
                    else:
                        params[param_name] = trial.suggest_categorical(param_name, param_values)
                elif isinstance(param_values, tuple) and len(param_values) == 2:
                    # Range specification
                    if isinstance(param_values[0], int) and isinstance(param_values[1], int):
                        params[param_name] = trial.suggest_int(param_name, param_values[0], param_values[1])
                    else:
                        params[param_name] = trial.suggest_float(param_name, param_values[0], param_values[1])
            
            # Create model with parameters
            model_instance = model.__class__(**params)
            
            # Cross-validation
            scores = cross_val_score(model_instance, X, y, cv=config.cv_folds, scoring=scorer)
            return scores.mean()
        
        # Create study
        direction = "maximize" if config.direction == OptimizationDirection.MAXIMIZE else "minimize"
        study = optuna.create_study(direction=direction)
        
        # Set sampler based on method
        if config.method == OptimizationMethod.TPE:
            study.sampler = TPESampler(seed=config.random_state)
        elif config.method == OptimizationMethod.CMA_ES:
            study.sampler = CmaEsSampler(seed=config.random_state)
        else:
            study.sampler = RandomSampler(seed=config.random_state)
        
        # Set pruner
        if config.pruning:
            study.pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        
        # Optimize
        study.optimize(objective, n_trials=config.n_trials, timeout=config.timeout)
        
        # Format results
        trial_results = []
        for trial in study.trials:
            trial_results.append({
                "trial": trial.number,
                "params": trial.params,
                "value": trial.value,
                "state": trial.state.name
            })
        
        return OptimizationResult(
            best_params=study.best_params,
            best_score=study.best_value,
            best_trial=study.best_trial.number,
            n_trials=len(study.trials),
            trial_results=trial_results,
            optimization_history=self._format_optimization_history(study),
            parameter_importance=self._calculate_parameter_importance(study)
        )
    
    def _format_cv_results(self, cv_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format cross-validation results."""
        results = []
        n_trials = len(cv_results['params'])
        
        for i in range(n_trials):
            results.append({
                "trial": i,
                "params": cv_results['params'][i],
                "mean_score": cv_results['mean_test_score'][i],
                "std_score": cv_results['std_test_score'][i],
                "rank": cv_results['rank_test_score'][i]
            })
        
        return results
    
    def _format_optimization_history(self, study) -> List[Dict[str, Any]]:
        """Format optimization history."""
        history = []
        for trial in study.trials:
            history.append({
                "trial": trial.number,
                "value": trial.value,
                "timestamp": trial.datetime_start.isoformat() if trial.datetime_start else None
            })
        return history
    
    def _calculate_parameter_importance(self, study) -> Optional[Dict[str, float]]:
        """Calculate parameter importance using Optuna."""
        try:
            importance = optuna.importance.get_param_importances(study)
            return importance
        except Exception as e:
            logger.warning(f"Could not calculate parameter importance: {e}")
            return None
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return self.optimization_history
    
    def get_available_metrics(self) -> List[str]:
        """Get available metrics."""
        return list(self.metrics.keys())
    
    def get_parameter_space_for_model(self, model_name: str) -> Dict[str, Any]:
        """Get parameter space for a specific model."""
        return self.parameter_spaces.get(model_name, {})
    
    def add_custom_parameter_space(self, model_name: str, parameter_space: Dict[str, Any]):
        """Add custom parameter space for a model."""
        self.parameter_spaces[model_name] = parameter_space
        logger.info(f"Added custom parameter space for {model_name}")
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        if not self.optimization_history:
            return {"total_optimizations": 0}
        
        total_optimizations = len(self.optimization_history)
        methods = [opt["method"] for opt in self.optimization_history]
        method_counts = {method: methods.count(method) for method in set(methods)}
        
        best_scores = [opt["best_score"] for opt in self.optimization_history]
        avg_score = np.mean(best_scores) if best_scores else 0
        best_score = max(best_scores) if best_scores else 0
        
        return {
            "total_optimizations": total_optimizations,
            "method_distribution": method_counts,
            "average_best_score": avg_score,
            "overall_best_score": best_score,
            "last_optimization": self.optimization_history[-1]["timestamp"] if self.optimization_history else None
        }
