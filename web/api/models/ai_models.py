"""
SPIDER Framework - AI API Models

Pydantic models for AI/ML-related API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .common_models import BaseResponse

class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    model: Optional[str] = Field("distilbert-base-uncased", description="Model to use")

class SentimentAnalysisResponse(BaseResponse):
    """Response model for sentiment analysis."""
    sentiment: str = Field(..., description="Sentiment classification")
    confidence: float = Field(..., description="Confidence score")
    scores: Dict[str, float] = Field(..., description="Score breakdown")
    model: str = Field(..., description="Model used")
    processing_time: float = Field(..., description="Processing time in seconds")

class EntityRecognitionRequest(BaseModel):
    """Request model for entity recognition."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    model: Optional[str] = Field("en_core_web_sm", description="Model to use")

class EntityRecognitionResponse(BaseResponse):
    """Response model for entity recognition."""
    entities: List[Dict[str, Any]] = Field(..., description="Extracted entities")
    model: str = Field(..., description="Model used")
    processing_time: float = Field(..., description="Processing time in seconds")

class TextClassificationRequest(BaseModel):
    """Request model for text classification."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to classify")
    categories: List[str] = Field(..., min_items=2, description="Classification categories")
    model: Optional[str] = Field("bert-base-uncased", description="Model to use")

class TextClassificationResponse(BaseResponse):
    """Response model for text classification."""
    classification: str = Field(..., description="Classification result")
    confidence: float = Field(..., description="Confidence score")
    scores: Dict[str, float] = Field(..., description="Score breakdown")
    model: str = Field(..., description="Model used")
    processing_time: float = Field(..., description="Processing time in seconds")

class ImageProcessingRequest(BaseModel):
    """Request model for image processing."""
    image_url: str = Field(..., regex=r'^https?://.+', description="Image URL")
    tasks: List[str] = Field(..., min_items=1, description="Processing tasks")

class ImageProcessingResponse(BaseResponse):
    """Response model for image processing."""
    extracted_text: Optional[str] = Field(None, description="Extracted text")
    objects: List[Dict[str, Any]] = Field(default_factory=list, description="Detected objects")
    content_classification: Optional[str] = Field(None, description="Content classification")
    processing_time: float = Field(..., description="Processing time in seconds")

class ModelInfoResponse(BaseResponse):
    """Response model for model information."""
    name: str = Field(..., description="Model name")
    type: str = Field(..., description="Model type")
    version: str = Field(..., description="Model version")
    status: str = Field(..., description="Model status")
    accuracy: Optional[float] = Field(None, description="Model accuracy")
    created_at: datetime = Field(..., description="Model creation timestamp")
    last_updated: datetime = Field(..., description="Last update timestamp")

class TrainModelRequest(BaseModel):
    """Request model for training model."""
    model_name: str = Field(..., description="Model name")
    training_data: Dict[str, Any] = Field(..., description="Training data")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Hyperparameters")

class TrainModelResponse(BaseResponse):
    """Response model for model training."""
    message: str = Field(..., description="Success message")
    training_job_id: str = Field(..., description="Training job identifier")
    model_name: str = Field(..., description="Model name")

class TrainingStatusResponse(BaseResponse):
    """Response model for training status."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Training status")
    progress: float = Field(..., description="Training progress")
    current_epoch: int = Field(..., description="Current epoch")
    total_epochs: int = Field(..., description="Total epochs")
    loss: float = Field(..., description="Current loss")
    accuracy: float = Field(..., description="Current accuracy")
    started_at: datetime = Field(..., description="Training start timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion")

class AIAnalyticsResponse(BaseResponse):
    """Response model for AI analytics."""
    total_predictions: int = Field(..., description="Total predictions")
    predictions_by_type: Dict[str, int] = Field(..., description="Predictions by type")
    accuracy_trends: Dict[str, float] = Field(..., description="Accuracy trends")
    processing_times: Dict[str, float] = Field(..., description="Processing times")
    model_usage: Dict[str, int] = Field(..., description="Model usage statistics")
