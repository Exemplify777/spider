"""
ML Training Pipeline

Comprehensive training pipeline for machine learning models with
automated preprocessing, training, validation, and deployment.

Author: SPIDER Development Team
Version: 1.0.0
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)
from sklearn.base import BaseEstimator, TransformerMixin
import joblib

from .model_registry import ModelRegistry, ModelType, ModelStatus

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task type enumeration."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class TrainingConfig:
    """Training configuration."""
    task_type: TaskType
    model_class: str
    model_params: Dict[str, Any] = field(default_factory=dict)
    preprocessing_steps: List[str] = field(default_factory=list)
    feature_columns: List[str] = field(default_factory=list)
    target_column: str = ""
    test_size: float = 0.2
    validation_size: float = 0.2
    random_state: int = 42
    cross_validation_folds: int = 5
    hyperparameter_tuning: bool = False
    hyperparameter_grid: Dict[str, List] = field(default_factory=dict)
    early_stopping: bool = False
    early_stopping_patience: int = 10
    max_training_time: Optional[int] = None  # seconds
    save_best_model: bool = True
    model_name: str = ""
    model_description: str = ""
    tags: List[str] = field(default_factory=list)
    author: str = "unknown"


@dataclass
class TrainingResult:
    """Training result container."""
    model_id: str
    model_version: str
    training_time: float
    best_score: float
    test_score: float
    validation_score: float
    metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    confusion_matrix: Optional[np.ndarray] = None
    classification_report: Optional[Dict[str, Any]] = None
    training_history: Optional[Dict[str, List[float]]] = None
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    preprocessing_pipeline: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DataPreprocessor(TransformerMixin, BaseEstimator):
    """Custom data preprocessor."""
    
    def __init__(self, 
                 numeric_columns: List[str] = None,
                 categorical_columns: List[str] = None,
                 text_columns: List[str] = None,
                 target_encoding: bool = False,
                 feature_scaling: bool = True,
                 handle_missing: str = "mean"):  # "mean", "median", "mode", "drop"
        self.numeric_columns = numeric_columns or []
        self.categorical_columns = categorical_columns or []
        self.text_columns = text_columns or []
        self.target_encoding = target_encoding
        self.feature_scaling = feature_scaling
        self.handle_missing = handle_missing
        
        self.scalers = {}
        self.encoders = {}
        self.label_encoders = {}
        self.feature_names_ = []
    
    def fit(self, X, y=None):
        """Fit the preprocessor."""
        X = pd.DataFrame(X) if not isinstance(X, pd.DataFrame) else X
        
        # Handle missing values
        if self.handle_missing == "mean":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].mean())
        elif self.handle_missing == "median":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].median())
        elif self.handle_missing == "mode":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].mode().iloc[0])
        elif self.handle_missing == "drop":
            X = X.dropna()
        
        # Process numeric columns
        if self.numeric_columns and self.feature_scaling:
            for col in self.numeric_columns:
                if col in X.columns:
                    scaler = StandardScaler()
                    X[col] = scaler.fit_transform(X[[col]])
                    self.scalers[col] = scaler
        
        # Process categorical columns
        if self.categorical_columns:
            for col in self.categorical_columns:
                if col in X.columns:
                    if self.target_encoding and y is not None:
                        # Target encoding
                        target_means = y.groupby(X[col]).mean()
                        X[col] = X[col].map(target_means)
                    else:
                        # One-hot encoding
                        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                        encoded = encoder.fit_transform(X[[col]])
                        encoded_df = pd.DataFrame(encoded, columns=[f"{col}_{i}" for i in range(encoded.shape[1])])
                        X = pd.concat([X.drop(columns=[col]), encoded_df], axis=1)
                        self.encoders[col] = encoder
        
        # Process text columns (basic TF-IDF)
        if self.text_columns:
            from sklearn.feature_extraction.text import TfidfVectorizer
            for col in self.text_columns:
                if col in X.columns:
                    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    text_features = vectorizer.fit_transform(X[col].fillna(''))
                    text_df = pd.DataFrame(text_features.toarray(), 
                                         columns=[f"{col}_tfidf_{i}" for i in range(text_features.shape[1])])
                    X = pd.concat([X.drop(columns=[col]), text_df], axis=1)
                    self.encoders[col] = vectorizer
        
        self.feature_names_ = list(X.columns)
        return self
    
    def transform(self, X):
        """Transform the data."""
        X = pd.DataFrame(X) if not isinstance(X, pd.DataFrame) else X
        
        # Handle missing values
        if self.handle_missing == "mean":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].mean())
        elif self.handle_missing == "median":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].median())
        elif self.handle_missing == "mode":
            X[self.numeric_columns] = X[self.numeric_columns].fillna(X[self.numeric_columns].mode().iloc[0])
        elif self.handle_missing == "drop":
            X = X.dropna()
        
        # Apply scaling
        if self.numeric_columns and self.feature_scaling:
            for col in self.numeric_columns:
                if col in X.columns and col in self.scalers:
                    X[col] = self.scalers[col].transform(X[[col]])
        
        # Apply categorical encoding
        if self.categorical_columns:
            for col in self.categorical_columns:
                if col in X.columns and col in self.encoders:
                    if isinstance(self.encoders[col], OneHotEncoder):
                        encoded = self.encoders[col].transform(X[[col]])
                        encoded_df = pd.DataFrame(encoded, columns=[f"{col}_{i}" for i in range(encoded.shape[1])])
                        X = pd.concat([X.drop(columns=[col]), encoded_df], axis=1)
        
        # Apply text encoding
        if self.text_columns:
            for col in self.text_columns:
                if col in X.columns and col in self.encoders:
                    text_features = self.encoders[col].transform(X[col].fillna(''))
                    text_df = pd.DataFrame(text_features.toarray(), 
                                         columns=[f"{col}_tfidf_{i}" for i in range(text_features.shape[1])])
                    X = pd.concat([X.drop(columns=[col]), text_df], axis=1)
        
        return X


class TrainingPipeline:
    """
    Comprehensive ML training pipeline.
    
    Features:
    - Automated data preprocessing
    - Model training with hyperparameter tuning
    - Cross-validation and evaluation
    - Model registry integration
    - Performance monitoring
    - Async training support
    """
    
    def __init__(self, registry: ModelRegistry = None):
        """
        Initialize the training pipeline.
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry or ModelRegistry()
        self.model_classes = self._load_model_classes()
    
    def _load_model_classes(self) -> Dict[str, Any]:
        """Load available model classes."""
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.linear_model import LogisticRegression, LinearRegression
            from sklearn.svm import SVC, SVR
            from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
            from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
            from sklearn.naive_bayes import GaussianNB
            from sklearn.cluster import KMeans, DBSCAN
            from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
            from sklearn.neural_network import MLPClassifier, MLPRegressor
            
            return {
                # Classification
                "RandomForestClassifier": RandomForestClassifier,
                "LogisticRegression": LogisticRegression,
                "SVC": SVC,
                "KNeighborsClassifier": KNeighborsClassifier,
                "DecisionTreeClassifier": DecisionTreeClassifier,
                "GaussianNB": GaussianNB,
                "GradientBoostingClassifier": GradientBoostingClassifier,
                "MLPClassifier": MLPClassifier,
                
                # Regression
                "RandomForestRegressor": RandomForestRegressor,
                "LinearRegression": LinearRegression,
                "SVR": SVR,
                "KNeighborsRegressor": KNeighborsRegressor,
                "DecisionTreeRegressor": DecisionTreeRegressor,
                "GradientBoostingRegressor": GradientBoostingRegressor,
                "MLPRegressor": MLPRegressor,
                
                # Clustering
                "KMeans": KMeans,
                "DBSCAN": DBSCAN,
            }
        except ImportError as e:
            logger.warning(f"Some model classes not available: {e}")
            return {}
    
    async def train_model(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        config: TrainingConfig,
        target: Optional[Union[pd.Series, np.ndarray]] = None
    ) -> TrainingResult:
        """
        Train a model with the given configuration.
        
        Args:
            data: Training data
            config: Training configuration
            target: Target variable (for supervised learning)
            
        Returns:
            Training result
        """
        start_time = datetime.utcnow()
        result = TrainingResult(
            model_id="",
            model_version="",
            training_time=0,
            best_score=0,
            test_score=0,
            validation_score=0,
            metrics={}
        )
        
        try:
            # Convert to DataFrame if needed
            if isinstance(data, np.ndarray):
                data = pd.DataFrame(data)
            
            # Prepare data
            X, y = self._prepare_data(data, config, target)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=config.random_state
            )
            
            if config.validation_size > 0:
                X_train, X_val, y_train, y_val = train_test_split(
                    X_train, y_train, test_size=config.validation_size, 
                    random_state=config.random_state
                )
            else:
                X_val, y_val = X_test, y_test
            
            # Create and fit preprocessor
            preprocessor = self._create_preprocessor(config, X_train, y_train)
            X_train_processed = preprocessor.fit_transform(X_train)
            X_test_processed = preprocessor.transform(X_test)
            X_val_processed = preprocessor.transform(X_val)
            
            # Get model class
            model_class = self.model_classes.get(config.model_class)
            if not model_class:
                raise ValueError(f"Unknown model class: {config.model_class}")
            
            # Create model
            model = model_class(**config.model_params)
            
            # Hyperparameter tuning
            if config.hyperparameter_tuning and config.hyperparameter_grid:
                model = self._tune_hyperparameters(
                    model, X_train_processed, y_train, config
                )
            
            # Train model
            model.fit(X_train_processed, y_train)
            
            # Evaluate model
            train_score = self._evaluate_model(model, X_train_processed, y_train, config.task_type)
            test_score = self._evaluate_model(model, X_test_processed, y_test, config.task_type)
            val_score = self._evaluate_model(model, X_val_processed, y_val, config.task_type)
            
            # Calculate additional metrics
            metrics = self._calculate_metrics(model, X_test_processed, y_test, config.task_type)
            
            # Get feature importance if available
            feature_importance = self._get_feature_importance(model, preprocessor.feature_names_)
            
            # Get confusion matrix for classification
            confusion_mat = None
            if config.task_type == TaskType.CLASSIFICATION:
                y_pred = model.predict(X_test_processed)
                confusion_mat = confusion_matrix(y_test, y_pred)
            
            # Register model
            model_id = self.registry.register_model(
                model=model,
                name=config.model_name or f"{config.model_class}_{config.task_type.value}",
                model_type=ModelType(config.task_type.value),
                description=config.model_description,
                author=config.author,
                tags=config.tags,
                parameters=model.get_params(),
                metrics=metrics,
                training_data_hash=self._calculate_data_hash(X_train),
                validation_data_hash=self._calculate_data_hash(X_val)
            )
            
            # Get model version
            metadata = self.registry.get_model_metadata(model_id)
            model_version = metadata.version if metadata else "unknown"
            
            # Update result
            result.model_id = model_id
            result.model_version = model_version
            result.training_time = (datetime.utcnow() - start_time).total_seconds()
            result.best_score = train_score
            result.test_score = test_score
            result.validation_score = val_score
            result.metrics = metrics
            result.feature_importance = feature_importance
            result.confusion_matrix = confusion_mat
            result.hyperparameters = model.get_params()
            result.preprocessing_pipeline = preprocessor
            
            logger.info(f"Successfully trained model {model_id} v{model_version}")
            
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.training_time = (datetime.utcnow() - start_time).total_seconds()
        
        return result
    
    def _prepare_data(self, data: pd.DataFrame, config: TrainingConfig, target: Optional[Any] = None) -> Tuple[pd.DataFrame, Optional[Any]]:
        """Prepare data for training."""
        X = data.copy()
        y = target
        
        # Select feature columns
        if config.feature_columns:
            X = X[config.feature_columns]
        
        # Select target column
        if config.target_column and config.target_column in data.columns:
            y = data[config.target_column]
            X = X.drop(columns=[config.target_column])
        
        return X, y
    
    def _create_preprocessor(self, config: TrainingConfig, X: pd.DataFrame, y: Optional[Any] = None) -> DataPreprocessor:
        """Create data preprocessor."""
        # Auto-detect column types if not specified
        numeric_columns = []
        categorical_columns = []
        text_columns = []
        
        for col in X.columns:
            if X[col].dtype in ['int64', 'float64']:
                numeric_columns.append(col)
            elif X[col].dtype == 'object':
                # Check if it's text or categorical
                unique_ratio = X[col].nunique() / len(X[col])
                if unique_ratio > 0.5:  # Likely text
                    text_columns.append(col)
                else:  # Likely categorical
                    categorical_columns.append(col)
        
        return DataPreprocessor(
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            text_columns=text_columns,
            feature_scaling=True,
            handle_missing="mean"
        )
    
    def _tune_hyperparameters(self, model: Any, X: pd.DataFrame, y: Any, config: TrainingConfig) -> Any:
        """Perform hyperparameter tuning."""
        if not config.hyperparameter_grid:
            return model
        
        # Use GridSearchCV for hyperparameter tuning
        grid_search = GridSearchCV(
            model,
            config.hyperparameter_grid,
            cv=config.cross_validation_folds,
            scoring=self._get_scoring_metric(config.task_type),
            n_jobs=-1
        )
        
        grid_search.fit(X, y)
        return grid_search.best_estimator_
    
    def _evaluate_model(self, model: Any, X: pd.DataFrame, y: Any, task_type: TaskType) -> float:
        """Evaluate model performance."""
        if task_type == TaskType.CLASSIFICATION:
            return model.score(X, y)
        elif task_type == TaskType.REGRESSION:
            return model.score(X, y)
        else:
            # For clustering, use silhouette score
            from sklearn.metrics import silhouette_score
            try:
                y_pred = model.predict(X)
                return silhouette_score(X, y_pred)
            except:
                return 0.0
    
    def _calculate_metrics(self, model: Any, X: pd.DataFrame, y: Any, task_type: TaskType) -> Dict[str, float]:
        """Calculate detailed metrics."""
        metrics = {}
        
        if task_type == TaskType.CLASSIFICATION:
            y_pred = model.predict(X)
            metrics.update({
                "accuracy": accuracy_score(y, y_pred),
                "precision": precision_score(y, y_pred, average='weighted'),
                "recall": recall_score(y, y_pred, average='weighted'),
                "f1_score": f1_score(y, y_pred, average='weighted')
            })
        elif task_type == TaskType.REGRESSION:
            y_pred = model.predict(X)
            metrics.update({
                "mse": mean_squared_error(y, y_pred),
                "mae": mean_absolute_error(y, y_pred),
                "r2_score": r2_score(y, y_pred)
            })
        
        return metrics
    
    def _get_feature_importance(self, model: Any, feature_names: List[str]) -> Optional[Dict[str, float]]:
        """Get feature importance if available."""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                return dict(zip(feature_names, importance))
            elif hasattr(model, 'coef_'):
                # For linear models
                coef = model.coef_
                if coef.ndim > 1:
                    coef = coef[0]  # Take first class for multi-class
                return dict(zip(feature_names, coef))
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        return None
    
    def _get_scoring_metric(self, task_type: TaskType) -> str:
        """Get appropriate scoring metric for task type."""
        if task_type == TaskType.CLASSIFICATION:
            return "accuracy"
        elif task_type == TaskType.REGRESSION:
            return "r2"
        else:
            return "accuracy"
    
    def _calculate_data_hash(self, data: pd.DataFrame) -> str:
        """Calculate hash of data for tracking."""
        import hashlib
        data_str = data.to_string()
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get_available_models(self) -> List[str]:
        """Get list of available model classes."""
        return list(self.model_classes.keys())
    
    def get_model_info(self, model_class: str) -> Dict[str, Any]:
        """Get information about a model class."""
        if model_class not in self.model_classes:
            return {}
        
        model = self.model_classes[model_class]
        return {
            "name": model_class,
            "class": model,
            "parameters": model().get_params() if hasattr(model(), 'get_params') else {},
            "task_types": self._get_supported_task_types(model_class)
        }
    
    def _get_supported_task_types(self, model_class: str) -> List[TaskType]:
        """Get supported task types for a model class."""
        classification_models = [
            "RandomForestClassifier", "LogisticRegression", "SVC", 
            "KNeighborsClassifier", "DecisionTreeClassifier", "GaussianNB",
            "GradientBoostingClassifier", "MLPClassifier"
        ]
        
        regression_models = [
            "RandomForestRegressor", "LinearRegression", "SVR",
            "KNeighborsRegressor", "DecisionTreeRegressor", 
            "GradientBoostingRegressor", "MLPRegressor"
        ]
        
        clustering_models = ["KMeans", "DBSCAN"]
        
        if model_class in classification_models:
            return [TaskType.CLASSIFICATION]
        elif model_class in regression_models:
            return [TaskType.REGRESSION]
        elif model_class in clustering_models:
            return [TaskType.CLUSTERING]
        else:
            return []
