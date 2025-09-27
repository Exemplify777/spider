"""
Test Suite for AI Module

Comprehensive tests for the SPIDER AI/ML module including model registry,
training pipeline, NLP processing, computer vision, and predictive analytics.

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from spider.ai.model_registry import (
    ModelRegistry, ModelType, ModelStatus, ModelMetadata, ModelVersion
)
from spider.ai.training_pipeline import (
    TrainingPipeline, TrainingConfig, TaskType, DataPreprocessor
)
from spider.ai.nlp_processor import (
    NLPProcessor, SentimentAnalyzer, EntityRecognizer, TextClassifier,
    SentimentType, EntityType, TextPreprocessor
)
from spider.ai.computer_vision import (
    ImageProcessor, OCRProcessor, ObjectDetector, ImageClassifier,
    ImageFormat, ObjectType, ComputerVisionProcessor
)
from spider.ai.predictive_analytics import (
    PredictiveAnalytics, AnomalyDetector, ForecastingEngine, TrendAnalyzer,
    AnomalyType, ForecastType
)
from spider.ai.model_manager import (
    ModelManager, ModelDeployment, ModelMonitoring, DeploymentStatus,
    MonitoringMetric
)


class TestModelRegistry:
    """Test model registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create a temporary registry for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ModelRegistry(registry_path=temp_dir)
    
    def test_register_model(self, registry):
        """Test model registration."""
        from sklearn.ensemble import RandomForestClassifier
        
        # Create a simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        # Register model
        model_id = registry.register_model(
            model=model,
            name="test_classifier",
            model_type=ModelType.CLASSIFICATION,
            description="Test classification model",
            author="test_user",
            tags=["test", "classification"],
            metrics={"accuracy": 0.85}
        )
        
        assert model_id is not None
        assert model_id in registry._metadata
    
    def test_get_model(self, registry):
        """Test model retrieval."""
        from sklearn.ensemble import RandomForestClassifier
        
        # Create and register model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        model_id = registry.register_model(
            model=model,
            name="test_classifier",
            model_type=ModelType.CLASSIFICATION
        )
        
        # Retrieve model
        retrieved_model = registry.get_model(model_id)
        assert retrieved_model is not None
        assert hasattr(retrieved_model, 'predict')
    
    def test_list_models(self, registry):
        """Test model listing."""
        from sklearn.ensemble import RandomForestClassifier
        
        # Register multiple models
        for i in range(3):
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            X = np.random.rand(100, 4)
            y = np.random.randint(0, 2, 100)
            model.fit(X, y)
            
            registry.register_model(
                model=model,
                name=f"test_classifier_{i}",
                model_type=ModelType.CLASSIFICATION
            )
        
        # List models
        models = registry.list_models()
        assert len(models) == 3
        assert all(isinstance(m, ModelMetadata) for m in models)
    
    def test_model_versioning(self, registry):
        """Test model versioning."""
        from sklearn.ensemble import RandomForestClassifier
        
        # Register first version
        model1 = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model1.fit(X, y)
        
        model_id = registry.register_model(
            model=model1,
            name="versioned_model",
            model_type=ModelType.CLASSIFICATION
        )
        
        # Register second version
        model2 = RandomForestClassifier(n_estimators=20, random_state=42)
        model2.fit(X, y)
        
        registry.register_model(
            model=model2,
            name="versioned_model",
            model_type=ModelType.CLASSIFICATION
        )
        
        # Check versions
        versions = registry._metadata[model_id]
        assert len(versions) == 2
        assert versions[0].version == "1.0.0"
        assert versions[1].version == "1.0.1"
    
    def test_model_metadata(self, registry):
        """Test model metadata management."""
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        model_id = registry.register_model(
            model=model,
            name="metadata_test",
            model_type=ModelType.CLASSIFICATION,
            description="Test model for metadata",
            author="test_user",
            tags=["test", "metadata"],
            metrics={"accuracy": 0.9, "precision": 0.85}
        )
        
        # Get metadata
        metadata = registry.get_model_metadata(model_id)
        assert metadata.name == "metadata_test"
        assert metadata.model_type == ModelType.CLASSIFICATION
        assert metadata.author == "test_user"
        assert "test" in metadata.tags
        assert metadata.metrics["accuracy"] == 0.9
    
    def test_model_comparison(self, registry):
        """Test model comparison."""
        from sklearn.ensemble import RandomForestClassifier
        
        # Register two versions
        model1 = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model1.fit(X, y)
        
        model_id = registry.register_model(
            model=model1,
            name="comparison_test",
            model_type=ModelType.CLASSIFICATION,
            metrics={"accuracy": 0.8}
        )
        
        model2 = RandomForestClassifier(n_estimators=20, random_state=42)
        model2.fit(X, y)
        
        registry.register_model(
            model=model2,
            name="comparison_test",
            model_type=ModelType.CLASSIFICATION,
            metrics={"accuracy": 0.85}
        )
        
        # Compare versions
        comparison = registry.compare_models(model_id, "1.0.0", "1.0.1")
        assert "metrics_comparison" in comparison
        assert "accuracy" in comparison["metrics_comparison"]


class TestTrainingPipeline:
    """Test training pipeline functionality."""
    
    @pytest.fixture
    def pipeline(self):
        """Create training pipeline."""
        return TrainingPipeline()
    
    def test_data_preprocessor(self):
        """Test data preprocessor."""
        # Create sample data
        data = pd.DataFrame({
            'numeric1': [1, 2, 3, 4, 5],
            'numeric2': [1.1, 2.2, 3.3, 4.4, 5.5],
            'categorical': ['A', 'B', 'A', 'C', 'B'],
            'text': ['hello world', 'test text', 'another text', 'more text', 'final text']
        })
        
        preprocessor = DataPreprocessor(
            numeric_columns=['numeric1', 'numeric2'],
            categorical_columns=['categorical'],
            text_columns=['text']
        )
        
        # Fit and transform
        preprocessor.fit(data)
        transformed = preprocessor.transform(data)
        
        assert transformed.shape[0] == data.shape[0]
        assert len(transformed.columns) > len(data.columns)  # Due to one-hot encoding
    
    def test_training_config(self):
        """Test training configuration."""
        config = TrainingConfig(
            task_type=TaskType.CLASSIFICATION,
            model_class="RandomForestClassifier",
            model_params={"n_estimators": 10},
            feature_columns=["feature1", "feature2"],
            target_column="target",
            test_size=0.2
        )
        
        assert config.task_type == TaskType.CLASSIFICATION
        assert config.model_class == "RandomForestClassifier"
        assert config.test_size == 0.2
    
    @pytest.mark.asyncio
    async def test_train_model(self, pipeline):
        """Test model training."""
        # Create sample data
        np.random.seed(42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        
        data = pd.DataFrame(X, columns=['feature1', 'feature2', 'feature3', 'feature4'])
        data['target'] = y
        
        config = TrainingConfig(
            task_type=TaskType.CLASSIFICATION,
            model_class="RandomForestClassifier",
            model_params={"n_estimators": 10, "random_state": 42},
            target_column="target"
        )
        
        # Train model
        result = await pipeline.train_model(data, config)
        
        assert result.model_id is not None
        assert result.training_time > 0
        assert result.best_score > 0
        assert result.test_score > 0
        assert "accuracy" in result.metrics
    
    def test_available_models(self, pipeline):
        """Test available models listing."""
        models = pipeline.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "RandomForestClassifier" in models
    
    def test_model_info(self, pipeline):
        """Test model information."""
        info = pipeline.get_model_info("RandomForestClassifier")
        assert "name" in info
        assert "parameters" in info
        assert "task_types" in info


class TestNLPProcessor:
    """Test NLP processing functionality."""
    
    def test_text_preprocessor(self):
        """Test text preprocessing."""
        preprocessor = TextPreprocessor()
        
        text = "Hello World! This is a test. Visit https://example.com for more info."
        cleaned = preprocessor.clean_text(text)
        
        assert "https://example.com" not in cleaned
        assert cleaned.islower()
        assert "!" not in cleaned
    
    def test_sentiment_analyzer(self):
        """Test sentiment analysis."""
        analyzer = SentimentAnalyzer()
        
        # Test positive sentiment
        result = analyzer.analyze("I love this product! It's amazing!")
        assert result.sentiment in [SentimentType.POSITIVE, SentimentType.NEUTRAL]
        assert result.confidence > 0
        
        # Test negative sentiment
        result = analyzer.analyze("This is terrible and awful!")
        assert result.sentiment in [SentimentType.NEGATIVE, SentimentType.NEUTRAL]
        assert result.confidence > 0
    
    def test_entity_recognizer(self):
        """Test entity recognition."""
        recognizer = EntityRecognizer()
        
        text = "Contact John Doe at john@example.com or call (555) 123-4567"
        entities = recognizer.extract_entities(text)
        
        assert len(entities) > 0
        # Should find email and phone number
        entity_texts = [e.entity for e in entities]
        assert any("john@example.com" in text for text in entity_texts)
    
    def test_text_classifier(self):
        """Test text classification."""
        classifier = TextClassifier()
        
        # Training data
        texts = [
            "This is a positive review",
            "I love this product",
            "This is terrible",
            "I hate this",
            "This is okay",
            "Not bad"
        ]
        labels = ["positive", "positive", "negative", "negative", "neutral", "neutral"]
        
        # Train classifier
        classifier.train(texts, labels)
        
        # Test classification
        result = classifier.predict("This is great!")
        assert result.predicted_class in ["positive", "negative", "neutral"]
        assert result.confidence > 0
    
    def test_nlp_processor(self):
        """Test main NLP processor."""
        processor = NLPProcessor()
        
        text = "I love this product! Contact us at support@example.com"
        
        # Process text
        result = processor.process_text(text, sentiment=True, entities=True)
        
        assert "sentiment" in result
        assert "entities" in result
        assert result["sentiment"] is not None
        assert isinstance(result["entities"], list)


class TestComputerVision:
    """Test computer vision functionality."""
    
    def test_image_processor(self):
        """Test image processing."""
        processor = ImageProcessor()
        
        # Create a test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test image info
        info = processor.get_image_info(image)
        assert info.width == 100
        assert info.height == 100
        assert info.channels == 3
        
        # Test resize
        resized = processor.resize_image(image, 50, 50)
        assert resized.shape[:2] == (50, 50)
    
    def test_ocr_processor(self):
        """Test OCR processing."""
        processor = OCRProcessor()
        
        # Create a test image with text (simplified)
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        
        # Test OCR (will likely return empty due to no actual text)
        result = processor.extract_text(image)
        assert isinstance(result.text, str)
        assert isinstance(result.confidence, float)
    
    def test_object_detector(self):
        """Test object detection."""
        detector = ObjectDetector()
        
        # Create a test image
        image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        
        # Test detection
        objects = detector.detect_objects(image)
        assert isinstance(objects, list)
    
    def test_image_classifier(self):
        """Test image classification."""
        classifier = ImageClassifier()
        
        # Create a test image
        image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        # Test classification
        result = classifier.classify_image(image)
        assert isinstance(result.predicted_class, str)
        assert isinstance(result.confidence, float)
    
    def test_computer_vision_processor(self):
        """Test main computer vision processor."""
        processor = ComputerVisionProcessor()
        
        # Create a test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Process image
        result = processor.process_image(image, ocr=True, object_detection=True)
        
        assert "image_info" in result
        assert "ocr" in result
        assert "objects" in result
        assert result["image_info"] is not None


class TestPredictiveAnalytics:
    """Test predictive analytics functionality."""
    
    def test_anomaly_detector(self):
        """Test anomaly detection."""
        detector = AnomalyDetector()
        
        # Create sample data
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, (100, 2))
        anomaly_data = np.random.normal(5, 1, (10, 2))
        data = np.vstack([normal_data, anomaly_data])
        
        # Fit detector
        detector.fit(data)
        
        # Detect anomalies
        anomalies = detector.detect_anomalies(data)
        
        assert len(anomalies) == len(data)
        assert any(a.is_anomaly for a in anomalies)  # Should detect some anomalies
    
    def test_forecasting_engine(self):
        """Test forecasting engine."""
        engine = ForecastingEngine()
        
        # Create sample time series data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        values = np.cumsum(np.random.randn(100)) + 100
        data = pd.DataFrame({'date': dates, 'value': values})
        
        # Fit model
        engine.fit(data, 'value', time_column='date')
        
        # Generate forecast
        forecasts = engine.forecast(10)
        
        assert len(forecasts) == 10
        assert all(isinstance(f.predicted_value, float) for f in forecasts)
    
    def test_trend_analyzer(self):
        """Test trend analysis."""
        analyzer = TrendAnalyzer()
        
        # Create sample data with trend
        values = np.linspace(0, 100, 50) + np.random.normal(0, 5, 50)
        
        # Analyze trend
        result = analyzer.analyze_trend(values)
        
        assert result.trend_direction in ["increasing", "decreasing", "stable"]
        assert 0 <= result.trend_strength <= 1
        assert result.confidence > 0
    
    def test_predictive_analytics(self):
        """Test main predictive analytics processor."""
        processor = PredictiveAnalytics()
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        values = np.cumsum(np.random.randn(100)) + 100
        data = pd.DataFrame({
            'date': dates,
            'value': values,
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        
        # Analyze data
        result = processor.analyze_data(
            data, 
            target_column='value',
            time_column='date',
            forecast_periods=10
        )
        
        assert "data_info" in result
        assert "anomalies" in result
        assert "forecasts" in result
        assert "trend_analysis" in result


class TestModelManager:
    """Test model management functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create model manager."""
        return ModelManager()
    
    def test_deployment_config(self):
        """Test deployment configuration."""
        config = DeploymentConfig(
            model_id="test_model",
            model_version="1.0.0",
            deployment_name="test_deployment",
            endpoint_url="http://localhost:8000/test"
        )
        
        assert config.model_id == "test_model"
        assert config.replicas == 1
        assert config.cpu_limit == "1000m"
    
    def test_model_monitoring(self):
        """Test model monitoring."""
        monitoring = ModelMonitoring()
        
        # Record metrics
        monitoring.record_metric(
            "test_model", "1.0.0", MonitoringMetric.ACCURACY, 0.85
        )
        
        # Get performance history
        history = monitoring.get_performance_history("test_model")
        assert len(history) == 1
        assert history[0].value == 0.85
    
    def test_model_health(self, manager):
        """Test model health monitoring."""
        # Record some metrics
        manager.monitoring.record_metric(
            "test_model", "1.0.0", MonitoringMetric.ACCURACY, 0.9
        )
        
        # Get health
        health = manager.monitoring.get_model_health("test_model")
        assert "health_score" in health
        assert "status" in health
        assert health["health_score"] > 0
    
    def test_model_status(self, manager):
        """Test model status retrieval."""
        # Register a test model
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        model_id = manager.registry.register_model(
            model=model,
            name="status_test",
            model_type=ModelType.CLASSIFICATION
        )
        
        # Get status
        status = manager.get_model_status(model_id)
        assert "model_info" in status
        assert "deployments" in status
        assert "health" in status
        assert status["model_info"]["model_id"] == model_id


class TestIntegration:
    """Integration tests for the AI module."""
    
    def test_end_to_end_workflow(self):
        """Test complete AI workflow."""
        # Create components
        registry = ModelRegistry()
        pipeline = TrainingPipeline(registry)
        nlp = NLPProcessor()
        cv = ComputerVisionProcessor()
        analytics = PredictiveAnalytics()
        manager = ModelManager(registry)
        
        # 1. Train a model
        np.random.seed(42)
        X = np.random.rand(100, 4)
        y = np.random.randint(0, 2, 100)
        data = pd.DataFrame(X, columns=['f1', 'f2', 'f3', 'f4'])
        data['target'] = y
        
        config = TrainingConfig(
            task_type=TaskType.CLASSIFICATION,
            model_class="RandomForestClassifier",
            target_column="target"
        )
        
        # This would be async in real usage
        # result = await pipeline.train_model(data, config)
        
        # 2. Process text
        text_result = nlp.process_text("I love this product!")
        assert "sentiment" in text_result
        
        # 3. Process image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image_result = cv.process_image(image)
        assert "image_info" in image_result
        
        # 4. Analyze data
        time_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=50, freq='D'),
            'value': np.cumsum(np.random.randn(50)) + 100
        })
        
        analytics_result = analytics.analyze_data(
            time_data, 'value', time_column='date'
        )
        assert "trend_analysis" in analytics_result
        
        # 5. Check manager stats
        stats = manager.get_registry_stats()
        assert "total_models" in stats


if __name__ == "__main__":
    pytest.main([__file__])
