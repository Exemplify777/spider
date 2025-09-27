"""
SPIDER AI/ML Module

Advanced AI and machine learning capabilities for the SPIDER framework.
Includes model registry, training pipelines, NLP, computer vision, and predictive analytics.

Author: SPIDER Development Team
Version: 1.0.0
"""

from .model_registry import ModelRegistry, ModelVersion, ModelMetadata
from .training_pipeline import TrainingPipeline, TrainingConfig, TrainingResult
from .nlp_processor import NLPProcessor, SentimentAnalyzer, EntityRecognizer, TextClassifier
from .computer_vision import ImageProcessor, OCRProcessor, ObjectDetector, ImageClassifier
from .predictive_analytics import PredictiveAnalytics, AnomalyDetector, ForecastingEngine
from .model_manager import ModelManager, ModelDeployment, ModelMonitoring
from .advanced_models import AdvancedAIModels, ModelConfig, ModelPerformance, ModelMetadata as AdvancedModelMetadata
from .optimization import AIOptimizer, OptimizationConfig, OptimizationResult, CompressionResult
from .integration import AIIntegrationManager, ModelEnsemble, FederatedNode, EdgeDeployment
from .analytics import AIAnalytics, AnalyticsResult, Insight, AnalyticsType, InsightType

__all__ = [
    # Model Registry
    "ModelRegistry",
    "ModelVersion", 
    "ModelMetadata",
    
    # Training Pipeline
    "TrainingPipeline",
    "TrainingConfig",
    "TrainingResult",
    
    # NLP Processing
    "NLPProcessor",
    "SentimentAnalyzer",
    "EntityRecognizer", 
    "TextClassifier",
    
    # Computer Vision
    "ImageProcessor",
    "OCRProcessor",
    "ObjectDetector",
    "ImageClassifier",
    
    # Predictive Analytics
    "PredictiveAnalytics",
    "AnomalyDetector",
    "ForecastingEngine",
    
    # Model Management
    "ModelManager",
    "ModelDeployment",
    "ModelMonitoring",
    
    # Advanced AI Models (Phase 14)
    "AdvancedAIModels",
    "ModelConfig",
    "ModelPerformance",
    "AdvancedModelMetadata",
    
    # AI Optimization (Phase 14)
    "AIOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "CompressionResult",
    
    # AI Integration (Phase 14)
    "AIIntegrationManager",
    "ModelEnsemble",
    "FederatedNode",
    "EdgeDeployment",
    
    # AI Analytics (Phase 14)
    "AIAnalytics",
    "AnalyticsResult",
    "Insight",
    "AnalyticsType",
    "InsightType",
]
