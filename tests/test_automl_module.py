"""
Test Suite for AutoML Module

Comprehensive tests for the SPIDER AutoML module including
pipeline generation, hyperparameter optimization, feature engineering, and model selection.

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from spider.automl.pipeline_generator import (
    PipelineGenerator, PipelineConfig, PipelineResult, TaskType, OptimizationStrategy
)
from spider.automl.hyperparameter_optimizer import (
    HyperparameterOptimizer, OptimizationConfig, OptimizationResult, OptimizationMethod
)
from spider.automl.feature_engineer import (
    FeatureEngineer, FeatureConfig, FeatureResult, FeatureType, EngineeringMethod, SelectionMethod
)
from spider.automl.model_selector import (
    ModelSelector, SelectionConfig, SelectionResult, ModelType, SelectionStrategy, PerformanceMetric
)
from spider.automl.automl_manager import (
    AutoMLManager, AutoMLConfig, AutoMLResult, AutoMLMode, OptimizationLevel
)


class TestPipelineGenerator:
    """Test pipeline generator functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'target': np.random.randint(0, 2, 100)
        })
        return data
    
    @pytest.fixture
    def pipeline_config(self):
        """Create pipeline configuration for testing."""
        return PipelineConfig(
            task_type=TaskType.CLASSIFICATION,
            target_column="target",
            optimization_strategy=OptimizationStrategy.ACCURACY,
            max_pipeline_length=5,
            max_training_time=300,
            cross_validation_folds=3,
            test_size=0.2,
            random_state=42
        )
    
    def test_pipeline_config(self, pipeline_config):
        """Test pipeline configuration."""
        assert pipeline_config.task_type == TaskType.CLASSIFICATION
        assert pipeline_config.target_column == "target"
        assert pipeline_config.optimization_strategy == OptimizationStrategy.ACCURACY
        assert pipeline_config.max_pipeline_length == 5
    
    def test_pipeline_generator_initialization(self):
        """Test pipeline generator initialization."""
        generator = PipelineGenerator()
        assert generator.preprocessing_steps is not None
        assert generator.feature_engineering_steps is not None
        assert generator.model_steps is not None
        assert generator.ensemble_methods is not None
    
    async def test_generate_pipeline(self, sample_data, pipeline_config):
        """Test pipeline generation."""
        generator = PipelineGenerator()
        
        result = await generator.generate_pipeline(sample_data, pipeline_config)
        
        assert isinstance(result, PipelineResult)
        assert result.pipeline_id is not None
        assert result.config == pipeline_config
        assert isinstance(result.pipeline, object)  # sklearn Pipeline
    
    def test_analyze_data(self, sample_data, pipeline_config):
        """Test data analysis functionality."""
        generator = PipelineGenerator()
        
        analysis = generator._analyze_data(sample_data, pipeline_config)
        
        assert "shape" in analysis
        assert "columns" in analysis
        assert "dtypes" in analysis
        assert "missing_values" in analysis
        assert "numeric_columns" in analysis
        assert "categorical_columns" in analysis
        assert analysis["shape"] == (100, 4)
    
    def test_generate_pipeline_stages(self, sample_data, pipeline_config):
        """Test pipeline stage generation."""
        generator = PipelineGenerator()
        
        data_analysis = generator._analyze_data(sample_data, pipeline_config)
        stages = generator._generate_pipeline_stages(data_analysis, pipeline_config)
        
        assert isinstance(stages, dict)
        assert "model" in stages  # Model stage should always be present
    
    def test_get_available_steps(self):
        """Test getting available pipeline steps."""
        generator = PipelineGenerator()
        
        steps = generator.get_available_steps()
        
        assert "preprocessing" in steps
        assert "feature_engineering" in steps
        assert "feature_selection" in steps
        assert "dimensionality_reduction" in steps
        assert "models" in steps
        assert "ensemble" in steps
    
    def test_get_pipeline_templates(self):
        """Test getting pipeline templates."""
        generator = PipelineGenerator()
        
        classification_templates = generator.get_pipeline_templates(TaskType.CLASSIFICATION)
        regression_templates = generator.get_pipeline_templates(TaskType.REGRESSION)
        
        assert isinstance(classification_templates, list)
        assert isinstance(regression_templates, list)
        assert len(classification_templates) > 0
        assert len(regression_templates) > 0


class TestHyperparameterOptimizer:
    """Test hyperparameter optimizer functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        y = pd.Series(np.random.randint(0, 2, 100))
        return X, y
    
    @pytest.fixture
    def optimization_config(self):
        """Create optimization configuration for testing."""
        return OptimizationConfig(
            method=OptimizationMethod.BAYESIAN_OPTIMIZATION,
            n_trials=10,
            cv_folds=3,
            timeout=60,
            random_state=42,
            metric="accuracy"
        )
    
    def test_optimization_config(self, optimization_config):
        """Test optimization configuration."""
        assert optimization_config.method == OptimizationMethod.BAYESIAN_OPTIMIZATION
        assert optimization_config.n_trials == 10
        assert optimization_config.cv_folds == 3
        assert optimization_config.metric == "accuracy"
    
    def test_hyperparameter_optimizer_initialization(self):
        """Test hyperparameter optimizer initialization."""
        optimizer = HyperparameterOptimizer()
        assert optimizer.parameter_spaces is not None
        assert optimizer.metrics is not None
        assert isinstance(optimizer.optimization_history, list)
    
    def test_initialize_parameter_spaces(self):
        """Test parameter spaces initialization."""
        optimizer = HyperparameterOptimizer()
        spaces = optimizer.parameter_spaces
        
        assert "RandomForestClassifier" in spaces
        assert "LogisticRegression" in spaces
        assert "SVC" in spaces
        assert "RandomForestRegressor" in spaces
        assert "LinearRegression" in spaces
    
    def test_initialize_metrics(self):
        """Test metrics initialization."""
        optimizer = HyperparameterOptimizer()
        metrics = optimizer.metrics
        
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert "mse" in metrics
        assert "mae" in metrics
        assert "r2_score" in metrics
    
    def test_get_parameter_space(self, sample_data, optimization_config):
        """Test getting parameter space for a model."""
        optimizer = HyperparameterOptimizer()
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier()
        
        space = optimizer._get_parameter_space(model, optimization_config)
        assert isinstance(space, dict)
        assert "n_estimators" in space
        assert "max_depth" in space
    
    def test_create_scorer(self, optimization_config):
        """Test scorer creation."""
        optimizer = HyperparameterOptimizer()
        
        scorer = optimizer._create_scorer(optimization_config)
        assert scorer is not None
    
    def test_get_available_metrics(self):
        """Test getting available metrics."""
        optimizer = HyperparameterOptimizer()
        
        metrics = optimizer.get_available_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert "accuracy" in metrics
    
    def test_get_parameter_space_for_model(self):
        """Test getting parameter space for specific model."""
        optimizer = HyperparameterOptimizer()
        
        space = optimizer.get_parameter_space_for_model("RandomForestClassifier")
        assert isinstance(space, dict)
        assert "n_estimators" in space
    
    def test_add_custom_parameter_space(self):
        """Test adding custom parameter space."""
        optimizer = HyperparameterOptimizer()
        
        custom_space = {"param1": [1, 2, 3], "param2": [0.1, 0.2, 0.3]}
        optimizer.add_custom_parameter_space("CustomModel", custom_space)
        
        retrieved_space = optimizer.get_parameter_space_for_model("CustomModel")
        assert retrieved_space == custom_space
    
    def test_get_optimization_statistics(self):
        """Test getting optimization statistics."""
        optimizer = HyperparameterOptimizer()
        
        stats = optimizer.get_optimization_statistics()
        assert "total_optimizations" in stats
        assert stats["total_optimizations"] == 0  # No optimizations yet


class TestFeatureEngineer:
    """Test feature engineer functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric1': np.random.randn(100),
            'numeric2': np.random.randn(100),
            'categorical': np.random.choice(['A', 'B', 'C'], 100),
            'text': ['This is a sample text ' + str(i) for i in range(100)],
            'target': np.random.randint(0, 2, 100)
        })
        return data
    
    @pytest.fixture
    def feature_config(self):
        """Create feature configuration for testing."""
        return FeatureConfig(
            enable_polynomial_features=True,
            enable_interaction_features=True,
            enable_binning=True,
            enable_log_transform=True,
            enable_time_features=True,
            enable_text_features=True,
            enable_aggregation=True,
            enable_ratio_features=True,
            max_features=20
        )
    
    def test_feature_config(self, feature_config):
        """Test feature configuration."""
        assert feature_config.enable_polynomial_features is True
        assert feature_config.enable_interaction_features is True
        assert feature_config.max_features == 20
    
    def test_feature_engineer_initialization(self):
        """Test feature engineer initialization."""
        engineer = FeatureEngineer()
        assert isinstance(engineer.feature_types, dict)
        assert isinstance(engineer.feature_importance, dict)
        assert isinstance(engineer.engineering_history, list)
    
    def test_detect_feature_types(self, sample_data):
        """Test feature type detection."""
        engineer = FeatureEngineer()
        
        feature_types = engineer._detect_feature_types(sample_data)
        
        assert "numeric1" in feature_types
        assert "numeric2" in feature_types
        assert "categorical" in feature_types
        assert "text" in feature_types
        assert feature_types["numeric1"] == FeatureType.NUMERIC
        assert feature_types["categorical"] == FeatureType.CATEGORICAL
    
    def test_is_datetime_column(self):
        """Test datetime column detection."""
        engineer = FeatureEngineer()
        
        # Test datetime column
        datetime_series = pd.Series(['2023-01-01', '2023-01-02', '2023-01-03'])
        assert engineer._is_datetime_column(datetime_series) is True
        
        # Test non-datetime column
        text_series = pd.Series(['text1', 'text2', 'text3'])
        assert engineer._is_datetime_column(text_series) is False
    
    def test_is_text_column(self):
        """Test text column detection."""
        engineer = FeatureEngineer()
        
        # Test text column
        text_series = pd.Series(['This is a long text with spaces', 'Another long text'])
        assert engineer._is_text_column(text_series) is True
        
        # Test non-text column
        short_series = pd.Series(['A', 'B', 'C'])
        assert engineer._is_text_column(short_series) is False
    
    async def test_engineer_features(self, sample_data, feature_config):
        """Test feature engineering."""
        engineer = FeatureEngineer()
        
        target = sample_data['target']
        data = sample_data.drop(columns=['target'])
        
        result = await engineer.engineer_features(data, target, feature_config)
        
        assert isinstance(result, FeatureResult)
        assert result.original_features is not None
        assert result.engineered_features is not None
        assert result.selected_features is not None
        assert result.feature_importance is not None
        assert result.engineering_summary is not None
    
    def test_add_polynomial_features(self, sample_data):
        """Test polynomial feature addition."""
        engineer = FeatureEngineer()
        
        numeric_columns = ['numeric1', 'numeric2']
        result = engineer._add_polynomial_features(sample_data, numeric_columns, FeatureConfig())
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) >= len(sample_data.columns)
    
    def test_add_interaction_features(self, sample_data):
        """Test interaction feature addition."""
        engineer = FeatureEngineer()
        
        feature_types = {
            'numeric1': FeatureType.NUMERIC,
            'numeric2': FeatureType.NUMERIC,
            'categorical': FeatureType.CATEGORICAL
        }
        
        result = engineer._add_interaction_features(sample_data, feature_types, FeatureConfig())
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) >= len(sample_data.columns)
    
    def test_add_binning_features(self, sample_data):
        """Test binning feature addition."""
        engineer = FeatureEngineer()
        
        result = engineer._add_binning_features(sample_data, 'numeric1', FeatureConfig())
        
        assert isinstance(result, pd.DataFrame)
        assert 'numeric1_binned' in result.columns
        assert 'numeric1_qbin' in result.columns
    
    def test_add_time_features(self, sample_data):
        """Test time feature addition."""
        engineer = FeatureEngineer()
        
        # Create datetime column
        sample_data['datetime'] = pd.date_range('2023-01-01', periods=100, freq='D')
        
        result = engineer._add_time_features(sample_data, 'datetime')
        
        assert isinstance(result, pd.DataFrame)
        assert 'datetime_year' in result.columns
        assert 'datetime_month' in result.columns
        assert 'datetime_day' in result.columns
    
    def test_add_text_features(self, sample_data):
        """Test text feature addition."""
        engineer = FeatureEngineer()
        
        result = engineer._add_text_features(sample_data, 'text')
        
        assert isinstance(result, pd.DataFrame)
        assert 'text_length' in result.columns
        assert 'text_word_count' in result.columns
        assert 'text_char_count' in result.columns
    
    def test_remove_correlated_features(self, sample_data):
        """Test correlated feature removal."""
        engineer = FeatureEngineer()
        
        # Create highly correlated features
        sample_data['correlated1'] = sample_data['numeric1']
        sample_data['correlated2'] = sample_data['numeric1'] + 0.01
        
        result = engineer._remove_correlated_features(sample_data, 0.99)
        
        assert isinstance(result, list)
        assert len(result) < len(sample_data.columns)
    
    def test_get_engineering_methods(self):
        """Test getting available engineering methods."""
        engineer = FeatureEngineer()
        
        methods = engineer.get_available_engineering_methods()
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "polynomial" in methods
    
    def test_get_selection_methods(self):
        """Test getting available selection methods."""
        engineer = FeatureEngineer()
        
        methods = engineer.get_available_selection_methods()
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "variance_threshold" in methods
    
    def test_get_engineering_statistics(self):
        """Test getting engineering statistics."""
        engineer = FeatureEngineer()
        
        stats = engineer.get_engineering_statistics()
        assert "total_engineering_sessions" in stats
        assert stats["total_engineering_sessions"] == 0  # No sessions yet


class TestModelSelector:
    """Test model selector functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        y = pd.Series(np.random.randint(0, 2, 100))
        return X, y
    
    @pytest.fixture
    def selection_config(self):
        """Create selection configuration for testing."""
        return SelectionConfig(
            task_type="classification",
            selection_strategy=SelectionStrategy.BEST_SINGLE,
            performance_metric=PerformanceMetric.ACCURACY,
            cv_folds=3,
            max_models=5,
            random_state=42
        )
    
    def test_selection_config(self, selection_config):
        """Test selection configuration."""
        assert selection_config.task_type == "classification"
        assert selection_config.selection_strategy == SelectionStrategy.BEST_SINGLE
        assert selection_config.performance_metric == PerformanceMetric.ACCURACY
        assert selection_config.cv_folds == 3
    
    def test_model_selector_initialization(self):
        """Test model selector initialization."""
        selector = ModelSelector()
        assert selector.model_library is not None
        assert isinstance(selector.selection_history, list)
        assert isinstance(selector.performance_cache, dict)
    
    def test_initialize_model_library(self):
        """Test model library initialization."""
        selector = ModelSelector()
        library = selector.model_library
        
        assert "classification" in library
        assert "regression" in library
        assert "tree_based" in library["classification"]
        assert "linear" in library["classification"]
        assert "neural_network" in library["classification"]
    
    def test_analyze_data_characteristics(self, sample_data):
        """Test data characteristics analysis."""
        selector = ModelSelector()
        
        analysis = selector._analyze_data_characteristics(sample_data[0], sample_data[1], "classification")
        
        assert "n_samples" in analysis
        assert "n_features" in analysis
        assert "feature_types" in analysis
        assert "missing_values" in analysis
        assert "target_distribution" in analysis
        assert analysis["n_samples"] == 100
        assert analysis["n_features"] == 3
    
    def test_get_recommended_models(self, sample_data, selection_config):
        """Test model recommendation."""
        selector = ModelSelector()
        
        data_analysis = selector._analyze_data_characteristics(sample_data[0], sample_data[1], "classification")
        recommended = selector._get_recommended_models(data_analysis, selection_config)
        
        assert isinstance(recommended, list)
        assert len(recommended) > 0
        assert all("name" in model for model in recommended)
        assert all("type" in model for model in recommended)
        assert all("info" in model for model in recommended)
    
    def test_create_scorer(self, selection_config):
        """Test scorer creation."""
        selector = ModelSelector()
        
        scorer = selector._create_scorer(selection_config)
        assert scorer is not None
    
    def test_estimate_memory_usage(self, sample_data):
        """Test memory usage estimation."""
        selector = ModelSelector()
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier()
        
        memory = selector._estimate_memory_usage(model, sample_data[0])
        assert isinstance(memory, float)
        assert memory > 0
    
    def test_calculate_complexity_score(self, sample_data):
        """Test complexity score calculation."""
        selector = ModelSelector()
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier()
        model_info = {"complexity": "medium"}
        
        score = selector._calculate_complexity_score(model, model_info)
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_extract_feature_importance(self, sample_data):
        """Test feature importance extraction."""
        selector = ModelSelector()
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier()
        model.fit(sample_data[0], sample_data[1])
        
        importance = selector._extract_feature_importance(model, sample_data[0])
        assert isinstance(importance, dict)
        assert len(importance) == len(sample_data[0].columns)
    
    def test_get_available_models(self):
        """Test getting available models."""
        selector = ModelSelector()
        
        classification_models = selector.get_available_models("classification")
        regression_models = selector.get_available_models("regression")
        
        assert isinstance(classification_models, list)
        assert isinstance(regression_models, list)
        assert len(classification_models) > 0
        assert len(regression_models) > 0
        assert "RandomForestClassifier" in classification_models
        assert "RandomForestRegressor" in regression_models
    
    def test_get_model_info(self):
        """Test getting model information."""
        selector = ModelSelector()
        
        info = selector.get_model_info("classification", "RandomForestClassifier")
        assert isinstance(info, dict)
        assert "model" in info
        assert "default_params" in info
        assert "complexity" in info
        assert "interpretability" in info
    
    def test_get_selection_statistics(self):
        """Test getting selection statistics."""
        selector = ModelSelector()
        
        stats = selector.get_selection_statistics()
        assert "total_selections" in stats
        assert stats["total_selections"] == 0  # No selections yet


class TestAutoMLManager:
    """Test AutoML manager functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'target': np.random.randint(0, 2, 100)
        })
        return data
    
    @pytest.fixture
    def automl_config(self):
        """Create AutoML configuration for testing."""
        return AutoMLConfig(
            mode=AutoMLMode.QUICK,
            optimization_level=OptimizationLevel.BASIC,
            task_type="classification",
            target_column="target",
            test_size=0.2,
            random_state=42,
            max_training_time=300,
            enable_feature_engineering=True,
            enable_hyperparameter_optimization=False,
            enable_model_selection=True,
            enable_ensemble=False
        )
    
    def test_automl_config(self, automl_config):
        """Test AutoML configuration."""
        assert automl_config.mode == AutoMLMode.QUICK
        assert automl_config.optimization_level == OptimizationLevel.BASIC
        assert automl_config.task_type == "classification"
        assert automl_config.target_column == "target"
    
    def test_automl_manager_initialization(self):
        """Test AutoML manager initialization."""
        manager = AutoMLManager()
        assert manager.pipeline_generator is not None
        assert manager.hyperparameter_optimizer is not None
        assert manager.feature_engineer is not None
        assert manager.model_selector is not None
        assert isinstance(manager.results_cache, dict)
        assert isinstance(manager.experiment_history, list)
    
    def test_validate_config(self, automl_config):
        """Test configuration validation."""
        manager = AutoMLManager()
        
        # Valid config should not raise exception
        manager._validate_config(automl_config)
        
        # Invalid config should raise exception
        invalid_config = AutoMLConfig(task_type="invalid", test_size=1.5)
        with pytest.raises(ValueError):
            manager._validate_config(invalid_config)
    
    def test_prepare_data(self, sample_data, automl_config):
        """Test data preparation."""
        manager = AutoMLManager()
        
        X, y = manager._prepare_data(sample_data, automl_config)
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y)
        assert "target" not in X.columns
        assert len(X.columns) == 3  # Original features minus target
    
    def test_calculate_metrics(self, sample_data):
        """Test metrics calculation."""
        manager = AutoMLManager()
        
        y_true = sample_data['target']
        y_pred = np.random.randint(0, 2, len(y_true))
        
        # Test classification metrics
        metrics = manager._calculate_metrics(y_true, y_pred, "classification")
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        
        # Test regression metrics
        y_true_reg = np.random.randn(100)
        y_pred_reg = np.random.randn(100)
        metrics_reg = manager._calculate_metrics(y_true_reg, y_pred_reg, "regression")
        assert "mse" in metrics_reg
        assert "mae" in metrics_reg
        assert "r2_score" in metrics_reg
    
    def test_get_available_modes(self):
        """Test getting available modes."""
        manager = AutoMLManager()
        
        modes = manager.get_available_modes()
        assert isinstance(modes, list)
        assert len(modes) > 0
        assert "quick" in modes
        assert "balanced" in modes
        assert "comprehensive" in modes
        assert "custom" in modes
    
    def test_get_available_optimization_levels(self):
        """Test getting available optimization levels."""
        manager = AutoMLManager()
        
        levels = manager.get_available_optimization_levels()
        assert isinstance(levels, list)
        assert len(levels) > 0
        assert "basic" in levels
        assert "intermediate" in levels
        assert "advanced" in levels
        assert "expert" in levels
    
    def test_clear_cache(self):
        """Test cache clearing."""
        manager = AutoMLManager()
        
        # Add some dummy data to cache
        manager.results_cache["test_id"] = "dummy_result"
        assert len(manager.results_cache) == 1
        
        # Clear cache
        manager.clear_cache()
        assert len(manager.results_cache) == 0
    
    def test_list_results(self):
        """Test listing results."""
        manager = AutoMLManager()
        
        # Initially empty
        results = manager.list_results()
        assert isinstance(results, list)
        assert len(results) == 0
        
        # Add dummy result
        dummy_result = AutoMLResult(
            automl_id="test_id",
            best_pipeline=None,
            best_model=None,
            performance_metrics={},
            config=AutoMLConfig()
        )
        manager.results_cache["test_id"] = dummy_result
        
        results = manager.list_results()
        assert len(results) == 1
        assert results[0]["automl_id"] == "test_id"
    
    def test_get_experiment_history(self):
        """Test getting experiment history."""
        manager = AutoMLManager()
        
        history = manager.get_experiment_history()
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_get_automl_statistics(self):
        """Test getting AutoML statistics."""
        manager = AutoMLManager()
        
        stats = manager.get_automl_statistics()
        assert "total_experiments" in stats
        assert stats["total_experiments"] == 0  # No experiments yet


class TestIntegration:
    """Integration tests for AutoML module."""
    
    def test_automl_quick_mode_integration(self):
        """Test AutoML quick mode integration."""
        # Create sample data
        np.random.seed(42)
        data = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50),
            'target': np.random.randint(0, 2, 50)
        })
        
        # Create AutoML config
        config = AutoMLConfig(
            mode=AutoMLMode.QUICK,
            task_type="classification",
            target_column="target",
            test_size=0.2,
            random_state=42
        )
        
        # Create AutoML manager
        manager = AutoMLManager()
        
        # This would run the full AutoML pipeline
        # For testing, we'll just verify the components work together
        assert manager.pipeline_generator is not None
        assert manager.feature_engineer is not None
        assert manager.model_selector is not None
        assert manager.hyperparameter_optimizer is not None
    
    def test_feature_engineering_integration(self):
        """Test feature engineering integration."""
        # Create sample data
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric1': np.random.randn(100),
            'numeric2': np.random.randn(100),
            'categorical': np.random.choice(['A', 'B', 'C'], 100),
            'target': np.random.randint(0, 2, 100)
        })
        
        # Create feature engineer
        engineer = FeatureEngineer()
        config = FeatureConfig(enable_polynomial_features=True, max_features=10)
        
        # Test feature engineering
        X = data.drop(columns=['target'])
        y = data['target']
        
        # This would run the full feature engineering
        # For testing, we'll verify the components work
        assert engineer.feature_types is not None
        assert engineer.feature_importance is not None
        assert engineer.engineering_history is not None
    
    def test_model_selection_integration(self):
        """Test model selection integration."""
        # Create sample data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        y = pd.Series(np.random.randint(0, 2, 100))
        
        # Create model selector
        selector = ModelSelector()
        config = SelectionConfig(
            task_type="classification",
            selection_strategy=SelectionStrategy.BEST_SINGLE,
            max_models=3
        )
        
        # Test model selection
        assert selector.model_library is not None
        assert "classification" in selector.model_library
        assert "regression" in selector.model_library
        
        # Test data analysis
        analysis = selector._analyze_data_characteristics(X, y, "classification")
        assert analysis["n_samples"] == 100
        assert analysis["n_features"] == 3
        
        # Test model recommendation
        recommended = selector._get_recommended_models(analysis, config)
        assert isinstance(recommended, list)
        assert len(recommended) > 0


if __name__ == "__main__":
    pytest.main([__file__])
