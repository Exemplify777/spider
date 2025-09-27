"""
Model Selector

Intelligent model selection for automated machine learning.
Includes model recommendation, ensemble building, and performance comparison.

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
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.ensemble import VotingClassifier, VotingRegressor, BaggingClassifier, BaggingRegressor
from sklearn.ensemble import AdaBoostClassifier, AdaBoostRegressor, StackingClassifier, StackingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.svm import LinearSVC, LinearSVR
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.base import BaseEstimator
import joblib

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Model type enumeration."""
    TREE_BASED = "tree_based"
    LINEAR = "linear"
    NEURAL_NETWORK = "neural_network"
    BAYESIAN = "bayesian"
    SUPPORT_VECTOR = "support_vector"
    NEIGHBORS = "neighbors"
    ENSEMBLE = "ensemble"


class SelectionStrategy(str, Enum):
    """Model selection strategy enumeration."""
    BEST_SINGLE = "best_single"
    TOP_K = "top_k"
    ENSEMBLE = "ensemble"
    STACKING = "stacking"
    VOTING = "voting"
    BAGGING = "bagging"
    ADABOOST = "adaboost"


class PerformanceMetric(str, Enum):
    """Performance metric enumeration."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    MSE = "mse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    CUSTOM = "custom"


@dataclass
class SelectionConfig:
    """Model selection configuration."""
    task_type: str  # "classification" or "regression"
    selection_strategy: SelectionStrategy = SelectionStrategy.BEST_SINGLE
    performance_metric: PerformanceMetric = PerformanceMetric.ACCURACY
    cv_folds: int = 5
    n_jobs: int = -1
    random_state: int = 42
    max_models: int = 10
    ensemble_size: int = 5
    enable_ensemble: bool = True
    enable_stacking: bool = True
    custom_metric: Optional[callable] = None
    model_constraints: Dict[str, Any] = field(default_factory=dict)
    performance_threshold: float = 0.0


@dataclass
class ModelPerformance:
    """Model performance information."""
    model_name: str
    model_type: ModelType
    model: BaseEstimator
    performance_score: float
    cv_scores: List[float]
    cv_mean: float
    cv_std: float
    training_time: float
    prediction_time: float
    memory_usage: float
    complexity_score: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class SelectionResult:
    """Model selection result."""
    selected_models: List[ModelPerformance]
    best_model: ModelPerformance
    ensemble_model: Optional[BaseEstimator] = None
    selection_summary: Dict[str, Any] = field(default_factory=dict)
    performance_comparison: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ModelSelector:
    """
    Intelligent model selection system.
    
    Features:
    - Automated model recommendation based on data characteristics
    - Performance comparison across multiple models
    - Ensemble model building and optimization
    - Model complexity and interpretability analysis
    - Cross-validation and robust evaluation
    """
    
    def __init__(self):
        """Initialize model selector."""
        self.model_library = self._initialize_model_library()
        self.selection_history = []
        self.performance_cache = {}
    
    def _initialize_model_library(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the model library with available models."""
        return {
            "classification": {
                "tree_based": {
                    "RandomForestClassifier": {
                        "model": RandomForestClassifier,
                        "default_params": {"n_estimators": 100, "random_state": 42},
                        "complexity": "medium",
                        "interpretability": "medium"
                    },
                    "GradientBoostingClassifier": {
                        "model": GradientBoostingClassifier,
                        "default_params": {"random_state": 42},
                        "complexity": "high",
                        "interpretability": "medium"
                    },
                    "DecisionTreeClassifier": {
                        "model": DecisionTreeClassifier,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "high"
                    }
                },
                "linear": {
                    "LogisticRegression": {
                        "model": LogisticRegression,
                        "default_params": {"random_state": 42, "max_iter": 1000},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "LinearSVC": {
                        "model": LinearSVC,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "medium"
                    },
                    "SGDClassifier": {
                        "model": SGDClassifier,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "medium"
                    }
                },
                "neural_network": {
                    "MLPClassifier": {
                        "model": MLPClassifier,
                        "default_params": {"random_state": 42, "max_iter": 1000},
                        "complexity": "high",
                        "interpretability": "low"
                    }
                },
                "bayesian": {
                    "GaussianNB": {
                        "model": GaussianNB,
                        "default_params": {},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "MultinomialNB": {
                        "model": MultinomialNB,
                        "default_params": {},
                        "complexity": "low",
                        "interpretability": "high"
                    }
                },
                "support_vector": {
                    "SVC": {
                        "model": SVC,
                        "default_params": {"random_state": 42, "probability": True},
                        "complexity": "medium",
                        "interpretability": "low"
                    }
                },
                "neighbors": {
                    "KNeighborsClassifier": {
                        "model": KNeighborsClassifier,
                        "default_params": {"n_neighbors": 5},
                        "complexity": "low",
                        "interpretability": "medium"
                    }
                },
                "discriminant": {
                    "LinearDiscriminantAnalysis": {
                        "model": LinearDiscriminantAnalysis,
                        "default_params": {},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "QuadraticDiscriminantAnalysis": {
                        "model": QuadraticDiscriminantAnalysis,
                        "default_params": {},
                        "complexity": "medium",
                        "interpretability": "medium"
                    }
                }
            },
            "regression": {
                "tree_based": {
                    "RandomForestRegressor": {
                        "model": RandomForestRegressor,
                        "default_params": {"n_estimators": 100, "random_state": 42},
                        "complexity": "medium",
                        "interpretability": "medium"
                    },
                    "GradientBoostingRegressor": {
                        "model": GradientBoostingRegressor,
                        "default_params": {"random_state": 42},
                        "complexity": "high",
                        "interpretability": "medium"
                    },
                    "DecisionTreeRegressor": {
                        "model": DecisionTreeRegressor,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "high"
                    }
                },
                "linear": {
                    "LinearRegression": {
                        "model": LinearRegression,
                        "default_params": {},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "Ridge": {
                        "model": Ridge,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "Lasso": {
                        "model": Lasso,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "ElasticNet": {
                        "model": ElasticNet,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "high"
                    },
                    "SGDRegressor": {
                        "model": SGDRegressor,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "medium"
                    }
                },
                "neural_network": {
                    "MLPRegressor": {
                        "model": MLPRegressor,
                        "default_params": {"random_state": 42, "max_iter": 1000},
                        "complexity": "high",
                        "interpretability": "low"
                    }
                },
                "support_vector": {
                    "SVR": {
                        "model": SVR,
                        "default_params": {},
                        "complexity": "medium",
                        "interpretability": "low"
                    },
                    "LinearSVR": {
                        "model": LinearSVR,
                        "default_params": {"random_state": 42},
                        "complexity": "low",
                        "interpretability": "medium"
                    }
                },
                "neighbors": {
                    "KNeighborsRegressor": {
                        "model": KNeighborsRegressor,
                        "default_params": {"n_neighbors": 5},
                        "complexity": "low",
                        "interpretability": "medium"
                    }
                }
            }
        }
    
    async def select_models(self, X: pd.DataFrame, y: pd.Series, 
                           config: SelectionConfig) -> SelectionResult:
        """
        Select the best models for the given data.
        
        Args:
            X: Feature data
            y: Target data
            config: Selection configuration
            
        Returns:
            Model selection result
        """
        start_time = datetime.utcnow()
        
        try:
            # Analyze data characteristics
            data_analysis = self._analyze_data_characteristics(X, y, config.task_type)
            
            # Get recommended models
            recommended_models = self._get_recommended_models(data_analysis, config)
            
            # Evaluate models
            model_performances = await self._evaluate_models(
                recommended_models, X, y, config
            )
            
            # Filter models by performance threshold
            filtered_models = [
                model for model in model_performances
                if model.performance_score >= config.performance_threshold
            ]
            
            # Sort by performance
            filtered_models.sort(key=lambda x: x.performance_score, reverse=True)
            
            # Select models based on strategy
            selected_models = self._select_models_by_strategy(
                filtered_models, config
            )
            
            # Build ensemble if enabled
            ensemble_model = None
            if config.enable_ensemble and len(selected_models) > 1:
                ensemble_model = await self._build_ensemble_model(
                    selected_models, X, y, config
                )
            
            # Create performance comparison
            performance_comparison = {
                model.model_name: model.performance_score
                for model in selected_models
            }
            
            # Create selection summary
            selection_summary = self._create_selection_summary(
                data_analysis, selected_models, config
            )
            
            result = SelectionResult(
                selected_models=selected_models,
                best_model=selected_models[0] if selected_models else None,
                ensemble_model=ensemble_model,
                selection_summary=selection_summary,
                performance_comparison=performance_comparison,
                created_at=start_time
            )
            
            # Store in history
            self.selection_history.append({
                "timestamp": start_time.isoformat(),
                "task_type": config.task_type,
                "strategy": config.selection_strategy.value,
                "models_selected": len(selected_models),
                "best_score": selected_models[0].performance_score if selected_models else 0.0
            })
            
            logger.info(f"Model selection completed: {len(selected_models)} models selected")
            return result
            
        except Exception as e:
            error_msg = f"Model selection failed: {str(e)}"
            logger.error(error_msg)
            
            return SelectionResult(
                selected_models=[],
                best_model=None,
                errors=[error_msg],
                created_at=start_time
            )
    
    def _analyze_data_characteristics(self, X: pd.DataFrame, y: pd.Series, 
                                     task_type: str) -> Dict[str, Any]:
        """Analyze data characteristics for model recommendation."""
        analysis = {
            "n_samples": len(X),
            "n_features": len(X.columns),
            "feature_types": X.dtypes.value_counts().to_dict(),
            "missing_values": X.isnull().sum().sum(),
            "target_distribution": None,
            "data_complexity": "medium",
            "recommended_models": []
        }
        
        # Analyze target distribution
        if task_type == "classification":
            analysis["target_distribution"] = y.value_counts().to_dict()
            analysis["n_classes"] = y.nunique()
        else:
            analysis["target_distribution"] = {
                "mean": y.mean(),
                "std": y.std(),
                "min": y.min(),
                "max": y.max()
            }
        
        # Determine data complexity
        n_samples = analysis["n_samples"]
        n_features = analysis["n_features"]
        
        if n_samples < 1000:
            analysis["data_complexity"] = "small"
        elif n_samples > 10000:
            analysis["data_complexity"] = "large"
        
        if n_features > 100:
            analysis["data_complexity"] = "high_dimensional"
        
        return analysis
    
    def _get_recommended_models(self, data_analysis: Dict[str, Any], 
                               config: SelectionConfig) -> List[Dict[str, Any]]:
        """Get recommended models based on data analysis."""
        task_type = config.task_type
        complexity = data_analysis["data_complexity"]
        n_samples = data_analysis["n_samples"]
        n_features = data_analysis["n_features"]
        
        recommended = []
        
        # Get models for the task type
        if task_type in self.model_library:
            models = self.model_library[task_type]
            
            # Recommend models based on data characteristics
            for model_type, model_dict in models.items():
                for model_name, model_info in model_dict.items():
                    # Skip complex models for small datasets
                    if complexity == "small" and model_info["complexity"] == "high":
                        continue
                    
                    # Skip simple models for large datasets
                    if complexity == "large" and model_info["complexity"] == "low":
                        continue
                    
                    # Skip high-dimensional models for low-dimensional data
                    if n_features < 10 and model_info["complexity"] == "high":
                        continue
                    
                    recommended.append({
                        "name": model_name,
                        "type": model_type,
                        "info": model_info
                    })
        
        # Limit number of models
        return recommended[:config.max_models]
    
    async def _evaluate_models(self, recommended_models: List[Dict[str, Any]], 
                              X: pd.DataFrame, y: pd.Series, 
                              config: SelectionConfig) -> List[ModelPerformance]:
        """Evaluate recommended models."""
        model_performances = []
        
        for model_info in recommended_models:
            try:
                # Create model instance
                model_class = model_info["info"]["model"]
                default_params = model_info["info"]["default_params"].copy()
                model = model_class(**default_params)
                
                # Evaluate model
                performance = await self._evaluate_single_model(
                    model, model_info, X, y, config
                )
                
                if performance:
                    model_performances.append(performance)
                    
            except Exception as e:
                logger.warning(f"Failed to evaluate model {model_info['name']}: {e}")
                continue
        
        return model_performances
    
    async def _evaluate_single_model(self, model: BaseEstimator, model_info: Dict[str, Any],
                                    X: pd.DataFrame, y: pd.Series, 
                                    config: SelectionConfig) -> Optional[ModelPerformance]:
        """Evaluate a single model."""
        start_time = datetime.utcnow()
        
        try:
            # Set up cross-validation
            if config.task_type == "classification":
                cv = StratifiedKFold(n_splits=config.cv_folds, random_state=config.random_state, shuffle=True)
            else:
                cv = KFold(n_splits=config.cv_folds, random_state=config.random_state, shuffle=True)
            
            # Create scorer
            scorer = self._create_scorer(config)
            
            # Perform cross-validation
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring=scorer, n_jobs=config.n_jobs)
            
            # Calculate performance metrics
            performance_score = cv_scores.mean()
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Calculate training time
            training_start = datetime.utcnow()
            model.fit(X, y)
            training_time = (datetime.utcnow() - training_start).total_seconds()
            
            # Calculate prediction time
            prediction_start = datetime.utcnow()
            model.predict(X.iloc[:100])  # Predict on subset
            prediction_time = (datetime.utcnow() - prediction_start).total_seconds()
            
            # Estimate memory usage (simplified)
            memory_usage = self._estimate_memory_usage(model, X)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(model, model_info)
            
            # Get feature importance if available
            feature_importance = self._extract_feature_importance(model, X)
            
            return ModelPerformance(
                model_name=model_info["name"],
                model_type=ModelType(model_info["type"]),
                model=model,
                performance_score=performance_score,
                cv_scores=cv_scores.tolist(),
                cv_mean=cv_mean,
                cv_std=cv_std,
                training_time=training_time,
                prediction_time=prediction_time,
                memory_usage=memory_usage,
                complexity_score=complexity_score,
                parameters=model.get_params(),
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.warning(f"Model evaluation failed for {model_info['name']}: {e}")
            return None
    
    def _create_scorer(self, config: SelectionConfig):
        """Create scorer for model evaluation."""
        from sklearn.metrics import make_scorer
        
        if config.custom_metric:
            return make_scorer(config.custom_metric, greater_is_better=True)
        
        metric_map = {
            PerformanceMetric.ACCURACY: "accuracy",
            PerformanceMetric.PRECISION: "precision_weighted",
            PerformanceMetric.RECALL: "recall_weighted",
            PerformanceMetric.F1_SCORE: "f1_weighted",
            PerformanceMetric.ROC_AUC: "roc_auc",
            PerformanceMetric.MSE: "neg_mean_squared_error",
            PerformanceMetric.MAE: "neg_mean_absolute_error",
            PerformanceMetric.R2_SCORE: "r2"
        }
        
        return metric_map.get(config.performance_metric, "accuracy")
    
    def _estimate_memory_usage(self, model: BaseEstimator, X: pd.DataFrame) -> float:
        """Estimate model memory usage in MB."""
        try:
            # Serialize model to estimate size
            model_bytes = len(joblib.dumps(model))
            return model_bytes / (1024 * 1024)  # Convert to MB
        except:
            return 1.0  # Default estimate
    
    def _calculate_complexity_score(self, model: BaseEstimator, model_info: Dict[str, Any]) -> float:
        """Calculate model complexity score (0-1)."""
        complexity_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        base_complexity = complexity_map.get(model_info["complexity"], 0.5)
        
        # Adjust based on model parameters
        params = model.get_params()
        if "n_estimators" in params:
            base_complexity += min(0.2, params["n_estimators"] / 1000)
        if "max_depth" in params and params["max_depth"]:
            base_complexity += min(0.2, params["max_depth"] / 50)
        
        return min(1.0, base_complexity)
    
    def _extract_feature_importance(self, model: BaseEstimator, X: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Extract feature importance from model."""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                return dict(zip(X.columns, importance))
            elif hasattr(model, 'coef_'):
                coef = model.coef_
                if coef.ndim > 1:
                    coef = coef[0]  # Take first class for multi-class
                return dict(zip(X.columns, coef))
        except:
            pass
        
        return None
    
    def _select_models_by_strategy(self, models: List[ModelPerformance], 
                                  config: SelectionConfig) -> List[ModelPerformance]:
        """Select models based on selection strategy."""
        if not models:
            return []
        
        if config.selection_strategy == SelectionStrategy.BEST_SINGLE:
            return models[:1]
        elif config.selection_strategy == SelectionStrategy.TOP_K:
            return models[:config.ensemble_size]
        elif config.selection_strategy == SelectionStrategy.ENSEMBLE:
            return models[:config.ensemble_size]
        else:
            return models
    
    async def _build_ensemble_model(self, models: List[ModelPerformance], 
                                   X: pd.DataFrame, y: pd.Series, 
                                   config: SelectionConfig) -> Optional[BaseEstimator]:
        """Build ensemble model from selected models."""
        if len(models) < 2:
            return None
        
        try:
            # Prepare base models
            base_models = [(f"model_{i}", model.model) for i, model in enumerate(models)]
            
            # Create ensemble based on task type
            if config.task_type == "classification":
                if config.selection_strategy == SelectionStrategy.VOTING:
                    ensemble = VotingClassifier(base_models, voting='soft')
                elif config.selection_strategy == SelectionStrategy.STACKING:
                    ensemble = StackingClassifier(
                        base_models, 
                        final_estimator=LogisticRegression(),
                        cv=3
                    )
                else:
                    ensemble = VotingClassifier(base_models, voting='soft')
            else:
                if config.selection_strategy == SelectionStrategy.VOTING:
                    ensemble = VotingRegressor(base_models)
                elif config.selection_strategy == SelectionStrategy.STACKING:
                    ensemble = StackingRegressor(
                        base_models,
                        final_estimator=LinearRegression(),
                        cv=3
                    )
                else:
                    ensemble = VotingRegressor(base_models)
            
            # Train ensemble
            ensemble.fit(X, y)
            
            return ensemble
            
        except Exception as e:
            logger.warning(f"Ensemble building failed: {e}")
            return None
    
    def _create_selection_summary(self, data_analysis: Dict[str, Any], 
                                 selected_models: List[ModelPerformance],
                                 config: SelectionConfig) -> Dict[str, Any]:
        """Create model selection summary."""
        if not selected_models:
            return {"error": "No models selected"}
        
        best_model = selected_models[0]
        
        return {
            "data_characteristics": {
                "n_samples": data_analysis["n_samples"],
                "n_features": data_analysis["n_features"],
                "complexity": data_analysis["data_complexity"]
            },
            "selection_strategy": config.selection_strategy.value,
            "performance_metric": config.performance_metric.value,
            "models_selected": len(selected_models),
            "best_model": {
                "name": best_model.model_name,
                "type": best_model.model_type.value,
                "score": best_model.performance_score,
                "cv_mean": best_model.cv_mean,
                "cv_std": best_model.cv_std
            },
            "performance_range": {
                "best": max(model.performance_score for model in selected_models),
                "worst": min(model.performance_score for model in selected_models),
                "average": np.mean([model.performance_score for model in selected_models])
            }
        }
    
    def get_selection_history(self) -> List[Dict[str, Any]]:
        """Get model selection history."""
        return self.selection_history
    
    def get_available_models(self, task_type: str) -> List[str]:
        """Get available models for a task type."""
        if task_type in self.model_library:
            models = []
            for model_type, model_dict in self.model_library[task_type].items():
                models.extend(model_dict.keys())
            return models
        return []
    
    def get_model_info(self, task_type: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        if task_type in self.model_library:
            for model_type, model_dict in self.model_library[task_type].items():
                if model_name in model_dict:
                    return model_dict[model_name]
        return None
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get model selection statistics."""
        if not self.selection_history:
            return {"total_selections": 0}
        
        total_selections = len(self.selection_history)
        task_types = [h["task_type"] for h in self.selection_history]
        strategies = [h["strategy"] for h in self.selection_history]
        
        return {
            "total_selections": total_selections,
            "task_type_distribution": {t: task_types.count(t) for t in set(task_types)},
            "strategy_distribution": {s: strategies.count(s) for s in set(strategies)},
            "average_models_selected": np.mean([h["models_selected"] for h in self.selection_history]),
            "average_best_score": np.mean([h["best_score"] for h in self.selection_history]),
            "last_selection": self.selection_history[-1]["timestamp"] if self.selection_history else None
        }
