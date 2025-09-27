"""
Test Suite for Explainability Module

Comprehensive tests for the SPIDER explainability module including
SHAP, LIME, feature importance, and explainability management.

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from spider.explainability.shap_explainer import (
    SHAPExplainer, SHAPConfig, SHAPResult, SHAPMethod, ExplanationType
)
from spider.explainability.lime_explainer import (
    LIMEExplainer, LIMEConfig, LIMEResult, LIMEMode, ExplanationMode
)
from spider.explainability.feature_importance import (
    FeatureImportanceAnalyzer, ImportanceConfig, ImportanceResult, 
    ImportanceMethod, ImportanceType
)
from spider.explainability.explainability_manager import (
    ExplainabilityManager, ExplainabilityConfig, ExplainabilityResult,
    ExplainabilityMethod, ExplanationScope
)


class TestSHAPExplainer:
    """Test SHAP explainer functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        return data
    
    @pytest.fixture
    def sample_model(self):
        """Create sample model for testing."""
        from sklearn.ensemble import RandomForestClassifier
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = np.random.randint(0, 2, 100)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model
    
    @pytest.fixture
    def shap_config(self):
        """Create SHAP configuration for testing."""
        return SHAPConfig(
            method=SHAPMethod.TREE_EXPLAINER,
            explanation_type=ExplanationType.LOCAL,
            max_samples=50,
            background_samples=20,
            random_state=42
        )
    
    def test_shap_config(self, shap_config):
        """Test SHAP configuration."""
        assert shap_config.method == SHAPMethod.TREE_EXPLAINER
        assert shap_config.explanation_type == ExplanationType.LOCAL
        assert shap_config.max_samples == 50
        assert shap_config.random_state == 42
    
    def test_shap_explainer_initialization(self):
        """Test SHAP explainer initialization."""
        explainer = SHAPExplainer()
        assert isinstance(explainer.explainer_cache, dict)
        assert isinstance(explainer.explanation_history, list)
    
    def test_get_available_methods(self):
        """Test getting available SHAP methods."""
        explainer = SHAPExplainer()
        
        methods = explainer.get_available_methods()
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "explainer" in methods
        assert "tree_explainer" in methods
    
    def test_get_available_explanation_types(self):
        """Test getting available explanation types."""
        explainer = SHAPExplainer()
        
        types = explainer.get_available_explanation_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "global" in types
        assert "local" in types
        assert "interaction" in types
    
    def test_get_explainer_info(self, sample_model):
        """Test getting explainer information for a model."""
        explainer = SHAPExplainer()
        
        info = explainer.get_explainer_info(sample_model)
        assert "model_type" in info
        assert "recommended_method" in info
        assert "description" in info
        assert "supports_interaction" in info
    
    def test_clear_cache(self):
        """Test clearing explainer cache."""
        explainer = SHAPExplainer()
        
        # Add dummy data to cache
        explainer.explainer_cache["test_key"] = "dummy_explainer"
        assert len(explainer.explainer_cache) == 1
        
        # Clear cache
        explainer.clear_cache()
        assert len(explainer.explainer_cache) == 0
    
    def test_get_cache_info(self):
        """Test getting cache information."""
        explainer = SHAPExplainer()
        
        info = explainer.get_cache_info()
        assert "cached_explainers" in info
        assert "cache_keys" in info
        assert "total_explanations" in info
    
    def test_get_explanation_history(self):
        """Test getting explanation history."""
        explainer = SHAPExplainer()
        
        history = explainer.get_explanation_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially empty


class TestLIMEExplainer:
    """Test LIME explainer functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        return data
    
    @pytest.fixture
    def sample_model(self):
        """Create sample model for testing."""
        from sklearn.ensemble import RandomForestClassifier
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = np.random.randint(0, 2, 100)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model
    
    @pytest.fixture
    def lime_config(self):
        """Create LIME configuration for testing."""
        return LIMEConfig(
            mode=LIMEMode.TABULAR,
            explanation_mode=ExplanationMode.SINGLE,
            num_features=5,
            num_samples=1000,
            random_state=42
        )
    
    def test_lime_config(self, lime_config):
        """Test LIME configuration."""
        assert lime_config.mode == LIMEMode.TABULAR
        assert lime_config.explanation_mode == ExplanationMode.SINGLE
        assert lime_config.num_features == 5
        assert lime_config.num_samples == 1000
    
    def test_lime_explainer_initialization(self):
        """Test LIME explainer initialization."""
        explainer = LIMEExplainer()
        assert isinstance(explainer.explainer_cache, dict)
        assert isinstance(explainer.explanation_history, list)
    
    def test_get_available_modes(self):
        """Test getting available LIME modes."""
        explainer = LIMEExplainer()
        
        modes = explainer.get_available_modes()
        assert isinstance(modes, list)
        assert len(modes) > 0
        assert "tabular" in modes
        assert "text" in modes
        assert "image" in modes
    
    def test_get_available_explanation_modes(self):
        """Test getting available explanation modes."""
        explainer = LIMEExplainer()
        
        modes = explainer.get_available_explanation_modes()
        assert isinstance(modes, list)
        assert len(modes) > 0
        assert "single" in modes
        assert "batch" in modes
        assert "feature_importance" in modes
    
    def test_get_explainer_info(self, sample_data):
        """Test getting explainer information for data."""
        explainer = LIMEExplainer()
        
        info = explainer.get_explainer_info(sample_data)
        assert "data_type" in info
        assert "recommended_mode" in info
        assert "description" in info
        assert "n_features" in info
        assert "n_samples" in info
    
    def test_clear_cache(self):
        """Test clearing explainer cache."""
        explainer = LIMEExplainer()
        
        # Add dummy data to cache
        explainer.explainer_cache["test_key"] = "dummy_explainer"
        assert len(explainer.explainer_cache) == 1
        
        # Clear cache
        explainer.clear_cache()
        assert len(explainer.explainer_cache) == 0
    
    def test_get_cache_info(self):
        """Test getting cache information."""
        explainer = LIMEExplainer()
        
        info = explainer.get_cache_info()
        assert "cached_explainers" in info
        assert "cache_keys" in info
        assert "total_explanations" in info
    
    def test_get_explanation_history(self):
        """Test getting explanation history."""
        explainer = LIMEExplainer()
        
        history = explainer.get_explanation_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially empty


class TestFeatureImportanceAnalyzer:
    """Test feature importance analyzer functionality."""
    
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
    def sample_model(self):
        """Create sample model for testing."""
        from sklearn.ensemble import RandomForestClassifier
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = np.random.randint(0, 2, 100)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model
    
    @pytest.fixture
    def importance_config(self):
        """Create importance configuration for testing."""
        return ImportanceConfig(
            method=ImportanceMethod.MODEL_BASED,
            importance_type=ImportanceType.GLOBAL,
            n_repeats=5,
            random_state=42,
            max_features=10
        )
    
    def test_importance_config(self, importance_config):
        """Test importance configuration."""
        assert importance_config.method == ImportanceMethod.MODEL_BASED
        assert importance_config.importance_type == ImportanceType.GLOBAL
        assert importance_config.n_repeats == 5
        assert importance_config.max_features == 10
    
    def test_feature_importance_analyzer_initialization(self):
        """Test feature importance analyzer initialization."""
        analyzer = FeatureImportanceAnalyzer()
        assert isinstance(analyzer.analysis_history, list)
        assert isinstance(analyzer.importance_cache, dict)
    
    def test_get_available_methods(self):
        """Test getting available importance methods."""
        analyzer = FeatureImportanceAnalyzer()
        
        methods = analyzer.get_available_methods()
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "model_based" in methods
        assert "permutation" in methods
        assert "mutual_info" in methods
    
    def test_get_available_importance_types(self):
        """Test getting available importance types."""
        analyzer = FeatureImportanceAnalyzer()
        
        types = analyzer.get_available_importance_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "global" in types
        assert "local" in types
        assert "interaction" in types
    
    def test_get_method_info(self):
        """Test getting method information."""
        analyzer = FeatureImportanceAnalyzer()
        
        info = analyzer.get_method_info(ImportanceMethod.MODEL_BASED)
        assert "name" in info
        assert "description" in info
        assert "pros" in info
        assert "cons" in info
    
    def test_normalize_importance_scores(self):
        """Test importance score normalization."""
        analyzer = FeatureImportanceAnalyzer()
        
        scores = {"feature1": 0.5, "feature2": 1.0, "feature3": 0.2}
        normalized = analyzer._normalize_importance_scores(scores)
        
        assert isinstance(normalized, dict)
        assert len(normalized) == len(scores)
        assert all(0 <= v <= 1 for v in normalized.values())
    
    def test_create_feature_rankings(self):
        """Test feature ranking creation."""
        analyzer = FeatureImportanceAnalyzer()
        
        scores = {"feature1": 0.5, "feature2": 1.0, "feature3": 0.2}
        rankings = analyzer._create_feature_rankings(scores, ImportanceConfig())
        
        assert isinstance(rankings, list)
        assert len(rankings) == len(scores)
        assert rankings[0] == "feature2"  # Highest importance first
    
    def test_get_analysis_history(self):
        """Test getting analysis history."""
        analyzer = FeatureImportanceAnalyzer()
        
        history = analyzer.get_analysis_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially empty
    
    def test_get_analysis_statistics(self):
        """Test getting analysis statistics."""
        analyzer = FeatureImportanceAnalyzer()
        
        stats = analyzer.get_analysis_statistics()
        assert "total_analyses" in stats
        assert stats["total_analyses"] == 0  # Initially zero


class TestExplainabilityManager:
    """Test explainability manager functionality."""
    
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
    def sample_model(self):
        """Create sample model for testing."""
        from sklearn.ensemble import RandomForestClassifier
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = np.random.randint(0, 2, 100)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model
    
    @pytest.fixture
    def explainability_config(self):
        """Create explainability configuration for testing."""
        return ExplainabilityConfig(
            methods=[ExplainabilityMethod.SHAP, ExplainabilityMethod.FEATURE_IMPORTANCE],
            scope=ExplanationScope.BOTH,
            max_features=10,
            max_samples=50,
            random_state=42
        )
    
    def test_explainability_config(self, explainability_config):
        """Test explainability configuration."""
        assert ExplainabilityMethod.SHAP in explainability_config.methods
        assert ExplainabilityMethod.FEATURE_IMPORTANCE in explainability_config.methods
        assert explainability_config.scope == ExplanationScope.BOTH
        assert explainability_config.max_features == 10
    
    def test_explainability_manager_initialization(self):
        """Test explainability manager initialization."""
        manager = ExplainabilityManager()
        assert manager.shap_explainer is not None
        assert manager.lime_explainer is not None
        assert manager.feature_importance_analyzer is not None
        assert isinstance(manager.explanation_cache, dict)
        assert isinstance(manager.explanation_history, list)
    
    def test_get_available_methods(self):
        """Test getting available explainability methods."""
        manager = ExplainabilityManager()
        
        methods = manager.get_available_methods()
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert "shap" in methods
        assert "lime" in methods
        assert "feature_importance" in methods
        assert "combined" in methods
    
    def test_get_available_scopes(self):
        """Test getting available explanation scopes."""
        manager = ExplainabilityManager()
        
        scopes = manager.get_available_scopes()
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        assert "global" in scopes
        assert "local" in scopes
        assert "both" in scopes
    
    def test_clear_cache(self):
        """Test clearing explanation cache."""
        manager = ExplainabilityManager()
        
        # Add dummy data to cache
        manager.explanation_cache["test_id"] = "dummy_result"
        assert len(manager.explanation_cache) == 1
        
        # Clear cache
        manager.clear_cache()
        assert len(manager.explanation_cache) == 0
    
    def test_get_cache_info(self):
        """Test getting cache information."""
        manager = ExplainabilityManager()
        
        info = manager.get_cache_info()
        assert "cached_explanations" in info
        assert "cache_keys" in info
        assert "total_explanations" in info
    
    def test_get_explanation_history(self):
        """Test getting explanation history."""
        manager = ExplainabilityManager()
        
        history = manager.get_explanation_history()
        assert isinstance(history, list)
        assert len(history) == 0  # Initially empty
    
    def test_list_explanations(self):
        """Test listing explanations."""
        manager = ExplainabilityManager()
        
        explanations = manager.list_explanations()
        assert isinstance(explanations, list)
        assert len(explanations) == 0  # Initially empty
    
    def test_get_explainability_statistics(self):
        """Test getting explainability statistics."""
        manager = ExplainabilityManager()
        
        stats = manager.get_explainability_statistics()
        assert "total_explanations" in stats
        assert stats["total_explanations"] == 0  # Initially zero


class TestIntegration:
    """Integration tests for explainability module."""
    
    def test_shap_lime_integration(self):
        """Test SHAP and LIME integration."""
        # Create sample data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50)
        })
        y = pd.Series(np.random.randint(0, 2, 50))
        
        # Create sample model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Create explainers
        shap_explainer = SHAPExplainer()
        lime_explainer = LIMEExplainer()
        
        # Test explainer initialization
        assert shap_explainer is not None
        assert lime_explainer is not None
        
        # Test configuration
        shap_config = SHAPConfig(method=SHAPMethod.TREE_EXPLAINER)
        lime_config = LIMEConfig(mode=LIMEMode.TABULAR)
        
        assert shap_config.method == SHAPMethod.TREE_EXPLAINER
        assert lime_config.mode == LIMEMode.TABULAR
    
    def test_feature_importance_integration(self):
        """Test feature importance integration."""
        # Create sample data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50)
        })
        y = pd.Series(np.random.randint(0, 2, 50))
        
        # Create sample model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Create analyzer
        analyzer = FeatureImportanceAnalyzer()
        
        # Test analyzer initialization
        assert analyzer is not None
        
        # Test configuration
        config = ImportanceConfig(method=ImportanceMethod.MODEL_BASED)
        assert config.method == ImportanceMethod.MODEL_BASED
    
    def test_explainability_manager_integration(self):
        """Test explainability manager integration."""
        # Create sample data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50)
        })
        y = pd.Series(np.random.randint(0, 2, 50))
        
        # Create sample model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Create manager
        manager = ExplainabilityManager()
        
        # Test manager initialization
        assert manager is not None
        assert manager.shap_explainer is not None
        assert manager.lime_explainer is not None
        assert manager.feature_importance_analyzer is not None
        
        # Test configuration
        config = ExplainabilityConfig(
            methods=[ExplainabilityMethod.SHAP],
            scope=ExplanationScope.LOCAL
        )
        assert ExplainabilityMethod.SHAP in config.methods
        assert config.scope == ExplanationScope.LOCAL
    
    def test_explainability_workflow(self):
        """Test complete explainability workflow."""
        # Create sample data
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50)
        })
        y = pd.Series(np.random.randint(0, 2, 50))
        
        # Create sample model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Create explainability manager
        manager = ExplainabilityManager()
        
        # Test workflow components
        assert manager.get_available_methods() is not None
        assert manager.get_available_scopes() is not None
        assert manager.get_explanation_history() is not None
        assert manager.get_explainability_statistics() is not None
        
        # Test cache operations
        manager.clear_cache()
        assert len(manager.explanation_cache) == 0
        
        info = manager.get_cache_info()
        assert "cached_explanations" in info
        assert "total_explanations" in info


if __name__ == "__main__":
    pytest.main([__file__])
