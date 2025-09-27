"""
SPIDER Framework - API Models

This module contains Pydantic models for API request/response validation
and data serialization.
"""

from .scraper_models import (
    ScraperCreateRequest,
    ScraperUpdateRequest,
    ScraperResponse,
    ScraperRunRequest,
    ScraperRunResponse,
    ScraperListResponse
)

from .user_models import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    PasswordChangeRequest,
    UserProfileResponse
)

from .system_models import (
    SystemInfoResponse,
    HealthCheckResponse,
    SystemMetricsResponse,
    ConfigurationResponse
)

from .monitoring_models import (
    MetricsResponse,
    AlertResponse,
    DashboardResponse,
    ScraperStatsResponse
)

from .ai_models import (
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    EntityRecognitionRequest,
    EntityRecognitionResponse,
    TextClassificationRequest,
    TextClassificationResponse,
    ImageProcessingRequest,
    ImageProcessingResponse,
    ModelInfoResponse
)

from .common_models import (
    ErrorResponse,
    SuccessResponse,
    PaginationResponse,
    BaseResponse
)

__all__ = [
    # Scraper models
    'ScraperCreateRequest',
    'ScraperUpdateRequest',
    'ScraperResponse',
    'ScraperRunRequest',
    'ScraperRunResponse',
    'ScraperListResponse',
    
    # User models
    'UserCreateRequest',
    'UserUpdateRequest',
    'UserResponse',
    'UserListResponse',
    'PasswordChangeRequest',
    'UserProfileResponse',
    
    # System models
    'SystemInfoResponse',
    'HealthCheckResponse',
    'SystemMetricsResponse',
    'ConfigurationResponse',
    
    # Monitoring models
    'MetricsResponse',
    'AlertResponse',
    'DashboardResponse',
    'ScraperStatsResponse',
    
    # AI models
    'SentimentAnalysisRequest',
    'SentimentAnalysisResponse',
    'EntityRecognitionRequest',
    'EntityRecognitionResponse',
    'TextClassificationRequest',
    'TextClassificationResponse',
    'ImageProcessingRequest',
    'ImageProcessingResponse',
    'ModelInfoResponse',
    
    # Common models
    'ErrorResponse',
    'SuccessResponse',
    'PaginationResponse',
    'BaseResponse'
]

__version__ = '2.0.0'
__author__ = 'SPIDER Framework Team'
__email__ = 'team@example.com'
