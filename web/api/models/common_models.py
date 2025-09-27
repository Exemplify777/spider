"""
SPIDER Framework - Common API Models

Common Pydantic models used across the API.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    """Response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ErrorCode(str, Enum):
    """Error code enumeration."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    CSRF_ERROR = "CSRF_ERROR"
    BRUTE_FORCE_ERROR = "BRUTE_FORCE_ERROR"

class BaseResponse(BaseModel):
    """Base response model."""
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class SuccessResponse(BaseResponse):
    """Success response model."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseResponse):
    """Error response model."""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: ErrorCode
    details: Optional[Dict[str, Any]] = None

class PaginationResponse(BaseModel):
    """Pagination response model."""
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=1000)
    total: int = Field(..., ge=0)
    pages: int = Field(..., ge=0)
    has_next: bool = Field(default=False)
    has_prev: bool = Field(default=False)

class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    data: List[Dict[str, Any]]
    pagination: PaginationResponse

class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""
    field: str
    message: str
    value: Any
    type: str

class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""
    error_code: ErrorCode = ErrorCode.VALIDATION_ERROR
    validation_errors: List[ValidationErrorDetail]

class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response model."""
    error_code: ErrorCode = ErrorCode.AUTHENTICATION_ERROR

class AuthorizationErrorResponse(ErrorResponse):
    """Authorization error response model."""
    error_code: ErrorCode = ErrorCode.AUTHORIZATION_ERROR

class NotFoundErrorResponse(ErrorResponse):
    """Not found error response model."""
    error_code: ErrorCode = ErrorCode.NOT_FOUND

class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response model."""
    error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED
    retry_after: int = Field(..., ge=0)

class SecurityErrorResponse(ErrorResponse):
    """Security error response model."""
    error_code: ErrorCode = ErrorCode.SECURITY_ERROR

class CSRFErrorResponse(ErrorResponse):
    """CSRF error response model."""
    error_code: ErrorCode = ErrorCode.CSRF_ERROR

class BruteForceErrorResponse(ErrorResponse):
    """Brute force error response model."""
    error_code: ErrorCode = ErrorCode.BRUTE_FORCE_ERROR

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ServiceStatus(BaseModel):
    """Service status model."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    response_time: Optional[float] = None
    last_check: Optional[datetime] = None

class HealthCheckResponse(BaseResponse):
    """Health check response model."""
    status: HealthStatus
    services: Dict[str, ServiceStatus]
    uptime: int
    version: str

class MetricsResponse(BaseResponse):
    """Metrics response model."""
    metrics: Dict[str, Any]
    period: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"

class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertResponse(BaseResponse):
    """Alert response model."""
    id: str
    name: str
    status: AlertStatus
    severity: AlertSeverity
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = Field(default_factory=dict)

class DashboardPanel(BaseModel):
    """Dashboard panel model."""
    id: str
    title: str
    type: str
    targets: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

class DashboardResponse(BaseResponse):
    """Dashboard response model."""
    id: str
    name: str
    description: str
    panels: List[DashboardPanel]
    created_at: datetime
    updated_at: datetime

class ScraperStatsResponse(BaseResponse):
    """Scraper statistics response model."""
    scraper_id: str
    period: str
    statistics: Dict[str, Any]
    timeline: List[Dict[str, Any]]

class ModelInfoResponse(BaseResponse):
    """Model information response model."""
    name: str
    type: str
    version: str
    status: str
    accuracy: Optional[float] = None
    created_at: datetime
    last_updated: datetime

class SentimentAnalysisResponse(BaseResponse):
    """Sentiment analysis response model."""
    sentiment: str
    confidence: float
    scores: Dict[str, float]
    model: str
    processing_time: float

class EntityRecognitionResponse(BaseResponse):
    """Entity recognition response model."""
    entities: List[Dict[str, Any]]
    model: str
    processing_time: float

class TextClassificationResponse(BaseResponse):
    """Text classification response model."""
    classification: str
    confidence: float
    scores: Dict[str, float]
    model: str
    processing_time: float

class ImageProcessingResponse(BaseResponse):
    """Image processing response model."""
    extracted_text: Optional[str] = None
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    content_classification: Optional[str] = None
    processing_time: float

class SystemInfoResponse(BaseResponse):
    """System information response model."""
    name: str
    version: str
    description: str
    features: List[str]
    capabilities: Dict[str, Any]
    uptime: int

class SystemMetricsResponse(BaseResponse):
    """System metrics response model."""
    system: Dict[str, Any]
    application: Dict[str, Any]
    database: Dict[str, Any]
    redis: Dict[str, Any]

class ConfigurationResponse(BaseResponse):
    """Configuration response model."""
    database: Dict[str, Any]
    redis: Dict[str, Any]
    scraping: Dict[str, Any]
    ai: Dict[str, Any]
    monitoring: Dict[str, Any]
    security: Dict[str, Any]

class UserResponse(BaseResponse):
    """User response model."""
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class UserListResponse(BaseResponse):
    """User list response model."""
    users: List[UserResponse]
    pagination: PaginationResponse

class ScraperResponse(BaseResponse):
    """Scraper response model."""
    id: str
    name: str
    description: Optional[str] = None
    url: str
    engine: str
    selectors: Dict[str, str]
    schedule: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class ScraperListResponse(BaseResponse):
    """Scraper list response model."""
    scrapers: List[ScraperResponse]
    pagination: PaginationResponse

class ScraperRunResponse(BaseResponse):
    """Scraper run response model."""
    job_id: str
    scraper_id: str
    status: str
    created_at: datetime
    estimated_duration: Optional[int] = None

class ScraperResultsResponse(BaseResponse):
    """Scraper results response model."""
    results: List[Dict[str, Any]]
    pagination: PaginationResponse
    statistics: Dict[str, Any]

class JobStatusResponse(BaseResponse):
    """Job status response model."""
    job_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseResponse):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str

class RefreshTokenResponse(BaseResponse):
    """Refresh token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutResponse(BaseResponse):
    """Logout response model."""
    message: str = "Logged out successfully"

class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordResponse(BaseResponse):
    """Change password response model."""
    message: str = "Password changed successfully"

class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')

class ResetPasswordResponse(BaseResponse):
    """Reset password response model."""
    message: str = "Password reset email sent"

class ConfirmResetPasswordRequest(BaseModel):
    """Confirm reset password request model."""
    token: str
    new_password: str = Field(..., min_length=8)

class ConfirmResetPasswordResponse(BaseResponse):
    """Confirm reset password response model."""
    message: str = "Password reset successfully"
