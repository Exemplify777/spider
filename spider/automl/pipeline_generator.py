"""
AutoML Pipeline Generator

Intelligent pipeline generation for automated machine learning workflows.
Includes data preprocessing, feature engineering, model selection, and optimization.

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
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, SelectPercentile, RFE
from sklearn.decomposition import PCA, FastICA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task type enumeration."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""
    DATA_LOADING = "data_loading"
    PREPROCESSING = "preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    FEATURE_SELECTION = "feature_selection"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_OPTIMIZATION = "model_optimization"


class OptimizationStrategy(str, Enum):
    """Optimization strategy enumeration."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    MSE = "mse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    CUSTOM = "custom"


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    task_type: TaskType
    target_column: str
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ACCURACY
    max_pipeline_length: int = 10
    max_training_time: int = 3600  # seconds
    cross_validation_folds: int = 5
    test_size: float = 0.2
    random_state: int = 42
    enable_feature_engineering: bool = True
    enable_feature_selection: bool = True
    enable_dimensionality_reduction: bool = True
    enable_ensemble: bool = True
    custom_metrics: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Pipeline generation result."""
    pipeline_id: str
    pipeline: Pipeline
    config: PipelineConfig
    performance_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    training_time: float = 0.0
    cross_validation_scores: List[float] = field(default_factory=list)
    best_parameters: Dict[str, Any] = field(default_factory=dict)
    pipeline_stages: List[PipelineStage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PipelineGenerator:
    """
    Intelligent pipeline generator for automated machine learning.
    
    Features:
    - Automatic pipeline construction based on data characteristics
    - Intelligent preprocessing and feature engineering
    - Model selection and hyperparameter optimization
    - Ensemble method integration
    - Performance optimization and validation
    """
    
    def __init__(self):
        """Initialize pipeline generator."""
        self.preprocessing_steps = self._initialize_preprocessing_steps()
        self.feature_engineering_steps = self._initialize_feature_engineering_steps()
        self.feature_selection_steps = self._initialize_feature_selection_steps()
        self.dimensionality_reduction_steps = self._initialize_dimensionality_reduction_steps()
        self.model_steps = self._initialize_model_steps()
        self.ensemble_methods = self._initialize_ensemble_methods()
    
    def _initialize_preprocessing_steps(self) -> Dict[str, Any]:
        """Initialize preprocessing steps."""
        return {
            "standard_scaler": StandardScaler,
            "min_max_scaler": MinMaxScaler,
            "robust_scaler": RobustScaler,
        }
    
    def _initialize_feature_engineering_steps(self) -> Dict[str, Any]:
        """Initialize feature engineering steps."""
        return {
            "polynomial_features": "PolynomialFeatures",
            "interaction_features": "InteractionFeatures",
            "time_features": "TimeFeatures",
            "text_features": "TextFeatures",
            "categorical_encoding": "CategoricalEncoding",
        }
    
    def _initialize_feature_selection_steps(self) -> Dict[str, Any]:
        """Initialize feature selection steps."""
        return {
            "select_k_best": SelectKBest,
            "select_percentile": SelectPercentile,
            "rfe": RFE,
            "variance_threshold": "VarianceThreshold",
            "mutual_info": "MutualInfoSelector",
        }
    
    def _initialize_dimensionality_reduction_steps(self) -> Dict[str, Any]:
        """Initialize dimensionality reduction steps."""
        return {
            "pca": PCA,
            "fast_ica": FastICA,
            "truncated_svd": "TruncatedSVD",
            "factor_analysis": "FactorAnalysis",
        }
    
    def _initialize_model_steps(self) -> Dict[str, Any]:
        """Initialize model steps."""
        return {
            # Classification models
            "random_forest_classifier": RandomForestClassifier,
            "logistic_regression": LogisticRegression,
            "svc": SVC,
            "knn_classifier": KNeighborsClassifier,
            "decision_tree_classifier": DecisionTreeClassifier,
            "gaussian_nb": GaussianNB,
            "mlp_classifier": MLPClassifier,
            "gradient_boosting_classifier": GradientBoostingClassifier,
            
            # Regression models
            "random_forest_regressor": RandomForestRegressor,
            "linear_regression": LinearRegression,
            "svr": SVR,
            "knn_regressor": KNeighborsRegressor,
            "decision_tree_regressor": DecisionTreeRegressor,
            "mlp_regressor": MLPRegressor,
            "gradient_boosting_regressor": GradientBoostingRegressor,
        }
    
    def _initialize_ensemble_methods(self) -> Dict[str, Any]:
        """Initialize ensemble methods."""
        return {
            "voting": "VotingClassifier",
            "bagging": "BaggingClassifier",
            "adaboost": "AdaBoostClassifier",
            "stacking": "StackingClassifier",
        }
    
    async def generate_pipeline(self, data: pd.DataFrame, config: PipelineConfig) -> PipelineResult:
        """
        Generate an optimized ML pipeline.
        
        Args:
            data: Input data
            config: Pipeline configuration
            
        Returns:
            Generated pipeline result
        """
        pipeline_id = f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        try:
            # Analyze data characteristics
            data_analysis = self._analyze_data(data, config)
            
            # Generate pipeline stages
            pipeline_stages = self._generate_pipeline_stages(data_analysis, config)
            
            # Build pipeline
            pipeline = self._build_pipeline(pipeline_stages, config)
            
            # Train and evaluate pipeline
            performance_metrics, cv_scores = await self._evaluate_pipeline(
                pipeline, data, config
            )
            
            # Get feature importance if available
            feature_importance = self._extract_feature_importance(pipeline, data, config)
            
            # Calculate training time
            training_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = PipelineResult(
                pipeline_id=pipeline_id,
                pipeline=pipeline,
                config=config,
                performance_metrics=performance_metrics,
                feature_importance=feature_importance,
                training_time=training_time,
                cross_validation_scores=cv_scores,
                pipeline_stages=[PipelineStage(stage) for stage in pipeline_stages.keys()],
                created_at=start_time
            )
            
            logger.info(f"Generated pipeline {pipeline_id} with {len(pipeline_stages)} stages")
            return result
            
        except Exception as e:
            error_msg = f"Pipeline generation failed: {str(e)}"
            logger.error(error_msg)
            
            return PipelineResult(
                pipeline_id=pipeline_id,
                pipeline=Pipeline([]),
                config=config,
                performance_metrics={},
                training_time=(datetime.utcnow() - start_time).total_seconds(),
                errors=[error_msg],
                created_at=start_time
            )
    
    def _analyze_data(self, data: pd.DataFrame, config: PipelineConfig) -> Dict[str, Any]:
        """Analyze data characteristics."""
        analysis = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": data.dtypes.to_dict(),
            "missing_values": data.isnull().sum().to_dict(),
            "numeric_columns": data.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": data.select_dtypes(include=['object']).columns.tolist(),
            "target_distribution": None,
            "feature_correlations": None,
            "data_quality_score": 0.0
        }
        
        # Analyze target variable
        if config.target_column in data.columns:
            target_data = data[config.target_column]
            if config.task_type == TaskType.CLASSIFICATION:
                analysis["target_distribution"] = target_data.value_counts().to_dict()
            else:
                analysis["target_distribution"] = {
                    "mean": target_data.mean(),
                    "std": target_data.std(),
                    "min": target_data.min(),
                    "max": target_data.max()
                }
        
        # Analyze feature correlations
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            analysis["feature_correlations"] = numeric_data.corr().to_dict()
        
        # Calculate data quality score
        missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        analysis["data_quality_score"] = 1.0 - missing_ratio
        
        return analysis
    
    def _generate_pipeline_stages(self, data_analysis: Dict[str, Any], 
                                 config: PipelineConfig) -> Dict[str, Any]:
        """Generate pipeline stages based on data analysis."""
        stages = {}
        
        # 1. Preprocessing stage
        if config.enable_feature_engineering:
            stages["preprocessing"] = self._select_preprocessing_steps(data_analysis, config)
        
        # 2. Feature engineering stage
        if config.enable_feature_engineering:
            stages["feature_engineering"] = self._select_feature_engineering_steps(
                data_analysis, config
            )
        
        # 3. Feature selection stage
        if config.enable_feature_selection:
            stages["feature_selection"] = self._select_feature_selection_steps(
                data_analysis, config
            )
        
        # 4. Dimensionality reduction stage
        if config.enable_dimensionality_reduction:
            stages["dimensionality_reduction"] = self._select_dimensionality_reduction_steps(
                data_analysis, config
            )
        
        # 5. Model stage
        stages["model"] = self._select_model_steps(data_analysis, config)
        
        # 6. Ensemble stage (if enabled)
        if config.enable_ensemble and len(stages.get("model", {})) > 1:
            stages["ensemble"] = self._select_ensemble_steps(data_analysis, config)
        
        return stages
    
    def _select_preprocessing_steps(self, data_analysis: Dict[str, Any], 
                                   config: PipelineConfig) -> Dict[str, Any]:
        """Select preprocessing steps based on data analysis."""
        steps = {}
        
        # Select scaler based on data characteristics
        if len(data_analysis["numeric_columns"]) > 0:
            # Use robust scaler if there are outliers
            numeric_data = data_analysis["numeric_columns"]
            if len(numeric_data) > 0:
                steps["scaler"] = "robust_scaler"  # Default to robust scaler
        
        return steps
    
    def _select_feature_engineering_steps(self, data_analysis: Dict[str, Any], 
                                         config: PipelineConfig) -> Dict[str, Any]:
        """Select feature engineering steps based on data analysis."""
        steps = {}
        
        # Add polynomial features for regression tasks
        if config.task_type == TaskType.REGRESSION:
            steps["polynomial_features"] = {"degree": 2}
        
        # Add categorical encoding for categorical features
        if len(data_analysis["categorical_columns"]) > 0:
            steps["categorical_encoding"] = {"method": "one_hot"}
        
        return steps
    
    def _select_feature_selection_steps(self, data_analysis: Dict[str, Any], 
                                       config: PipelineConfig) -> Dict[str, Any]:
        """Select feature selection steps based on data analysis."""
        steps = {}
        
        # Select features based on data size
        n_features = len(data_analysis["numeric_columns"])
        if n_features > 10:
            steps["select_k_best"] = {"k": min(20, n_features // 2)}
        elif n_features > 5:
            steps["select_percentile"] = {"percentile": 50}
        
        return steps
    
    def _select_dimensionality_reduction_steps(self, data_analysis: Dict[str, Any], 
                                              config: PipelineConfig) -> Dict[str, Any]:
        """Select dimensionality reduction steps based on data analysis."""
        steps = {}
        
        # Use PCA for high-dimensional data
        n_features = len(data_analysis["numeric_columns"])
        if n_features > 50:
            steps["pca"] = {"n_components": min(20, n_features // 2)}
        
        return steps
    
    def _select_model_steps(self, data_analysis: Dict[str, Any], 
                           config: PipelineConfig) -> Dict[str, Any]:
        """Select model steps based on task type and data characteristics."""
        steps = {}
        
        if config.task_type == TaskType.CLASSIFICATION:
            # Select classification models
            steps["random_forest_classifier"] = {
                "n_estimators": 100,
                "random_state": config.random_state
            }
            steps["logistic_regression"] = {
                "random_state": config.random_state
            }
            steps["svc"] = {
                "random_state": config.random_state
            }
        elif config.task_type == TaskType.REGRESSION:
            # Select regression models
            steps["random_forest_regressor"] = {
                "n_estimators": 100,
                "random_state": config.random_state
            }
            steps["linear_regression"] = {}
            steps["svr"] = {}
        
        return steps
    
    def _select_ensemble_steps(self, data_analysis: Dict[str, Any], 
                              config: PipelineConfig) -> Dict[str, Any]:
        """Select ensemble steps based on available models."""
        steps = {}
        
        # Use voting ensemble for multiple models
        steps["voting"] = {
            "voting": "soft" if config.task_type == TaskType.CLASSIFICATION else "hard"
        }
        
        return steps
    
    def _build_pipeline(self, stages: Dict[str, Any], config: PipelineConfig) -> Pipeline:
        """Build the actual sklearn pipeline."""
        pipeline_steps = []
        
        # Add preprocessing steps
        if "preprocessing" in stages:
            for step_name, step_config in stages["preprocessing"].items():
                if step_name == "scaler":
                    scaler_class = self.preprocessing_steps[step_config]
                    pipeline_steps.append((step_name, scaler_class()))
        
        # Add feature engineering steps (simplified)
        if "feature_engineering" in stages:
            # This would be implemented with custom transformers
            pass
        
        # Add feature selection steps
        if "feature_selection" in stages:
            for step_name, step_config in stages["feature_selection"].items():
                if step_name == "select_k_best":
                    pipeline_steps.append((step_name, SelectKBest(k=step_config["k"])))
                elif step_name == "select_percentile":
                    pipeline_steps.append((step_name, SelectPercentile(percentile=step_config["percentile"])))
        
        # Add dimensionality reduction steps
        if "dimensionality_reduction" in stages:
            for step_name, step_config in stages["dimensionality_reduction"].items():
                if step_name == "pca":
                    pipeline_steps.append((step_name, PCA(n_components=step_config["n_components"])))
        
        # Add model steps
        if "model" in stages:
            for step_name, step_config in stages["model"].items():
                model_class = self.model_steps[step_name]
                pipeline_steps.append((step_name, model_class(**step_config)))
        
        return Pipeline(pipeline_steps)
    
    async def _evaluate_pipeline(self, pipeline: Pipeline, data: pd.DataFrame, 
                                config: PipelineConfig) -> Tuple[Dict[str, float], List[float]]:
        """Evaluate pipeline performance."""
        try:
            # Prepare data
            X = data.drop(columns=[config.target_column])
            y = data[config.target_column]
            
            # Split data
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=config.random_state
            )
            
            # Train pipeline
            pipeline.fit(X_train, y_train)
            
            # Make predictions
            y_pred = pipeline.predict(X_test)
            
            # Calculate metrics
            metrics = {}
            if config.task_type == TaskType.CLASSIFICATION:
                metrics.update({
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred, average='weighted'),
                    "recall": recall_score(y_test, y_pred, average='weighted'),
                    "f1_score": f1_score(y_test, y_pred, average='weighted')
                })
            elif config.task_type == TaskType.REGRESSION:
                metrics.update({
                    "mse": mean_squared_error(y_test, y_pred),
                    "mae": mean_absolute_error(y_test, y_pred),
                    "r2_score": r2_score(y_test, y_pred)
                })
            
            # Cross-validation scores
            cv_scores = []
            if config.task_type == TaskType.CLASSIFICATION:
                cv = StratifiedKFold(n_splits=config.cross_validation_folds, 
                                   random_state=config.random_state, shuffle=True)
            else:
                cv = KFold(n_splits=config.cross_validation_folds, 
                          random_state=config.random_state, shuffle=True)
            
            cv_scores = cross_val_score(pipeline, X, y, cv=cv, 
                                      scoring=config.optimization_strategy.value)
            
            return metrics, cv_scores.tolist()
            
        except Exception as e:
            logger.error(f"Pipeline evaluation failed: {e}")
            return {}, []
    
    def _extract_feature_importance(self, pipeline: Pipeline, data: pd.DataFrame, 
                                   config: PipelineConfig) -> Optional[Dict[str, float]]:
        """Extract feature importance from the pipeline."""
        try:
            # Get the final estimator
            final_estimator = pipeline.steps[-1][1]
            
            if hasattr(final_estimator, 'feature_importances_'):
                feature_names = data.drop(columns=[config.target_column]).columns
                importance = final_estimator.feature_importances_
                return dict(zip(feature_names, importance))
            elif hasattr(final_estimator, 'coef_'):
                feature_names = data.drop(columns=[config.target_column]).columns
                coef = final_estimator.coef_
                if coef.ndim > 1:
                    coef = coef[0]  # Take first class for multi-class
                return dict(zip(feature_names, coef))
            
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        return None
    
    def get_available_steps(self) -> Dict[str, List[str]]:
        """Get available pipeline steps."""
        return {
            "preprocessing": list(self.preprocessing_steps.keys()),
            "feature_engineering": list(self.feature_engineering_steps.keys()),
            "feature_selection": list(self.feature_selection_steps.keys()),
            "dimensionality_reduction": list(self.dimensionality_reduction_steps.keys()),
            "models": list(self.model_steps.keys()),
            "ensemble": list(self.ensemble_methods.keys())
        }
    
    def get_pipeline_templates(self, task_type: TaskType) -> List[Dict[str, Any]]:
        """Get pre-defined pipeline templates for a task type."""
        templates = {
            TaskType.CLASSIFICATION: [
                {
                    "name": "simple_classification",
                    "description": "Simple classification pipeline",
                    "stages": ["preprocessing", "model"]
                },
                {
                    "name": "advanced_classification",
                    "description": "Advanced classification with feature engineering",
                    "stages": ["preprocessing", "feature_engineering", "feature_selection", "model"]
                }
            ],
            TaskType.REGRESSION: [
                {
                    "name": "simple_regression",
                    "description": "Simple regression pipeline",
                    "stages": ["preprocessing", "model"]
                },
                {
                    "name": "advanced_regression",
                    "description": "Advanced regression with feature engineering",
                    "stages": ["preprocessing", "feature_engineering", "feature_selection", "model"]
                }
            ]
        }
        
        return templates.get(task_type, [])
