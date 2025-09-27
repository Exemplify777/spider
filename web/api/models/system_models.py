"""
SPIDER Framework - System API Models

Pydantic models for system-related API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .common_models import BaseResponse

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ServiceStatus(BaseModel):
    """Service status model."""
    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service status")
    message: Optional[str] = Field(None, description="Status message")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    last_check: Optional[datetime] = Field(None, description="Last check timestamp")

class SystemInfoResponse(BaseResponse):
    """Response model for system information."""
    name: str = Field(..., description="System name")
    version: str = Field(..., description="System version")
    description: str = Field(..., description="System description")
    features: List[str] = Field(..., description="Available features")
    capabilities: Dict[str, Any] = Field(..., description="System capabilities")
    uptime: int = Field(..., description="System uptime in seconds")

class HealthCheckResponse(BaseResponse):
    """Response model for health check."""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="System version")
    services: Dict[str, ServiceStatus] = Field(..., description="Service statuses")
    uptime: int = Field(..., description="System uptime in seconds")
    memory_usage: float = Field(..., description="Memory usage percentage")
    cpu_usage: float = Field(..., description="CPU usage percentage")

class SystemMetricsResponse(BaseResponse):
    """Response model for system metrics."""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    system: Dict[str, Any] = Field(..., description="System metrics")
    application: Dict[str, Any] = Field(..., description="Application metrics")
    database: Dict[str, Any] = Field(..., description="Database metrics")
    redis: Dict[str, Any] = Field(..., description="Redis metrics")

class ConfigurationResponse(BaseResponse):
    """Response model for system configuration."""
    database: Dict[str, Any] = Field(..., description="Database configuration")
    redis: Dict[str, Any] = Field(..., description="Redis configuration")
    scraping: Dict[str, Any] = Field(..., description="Scraping configuration")
    ai: Dict[str, Any] = Field(..., description="AI configuration")
    monitoring: Dict[str, Any] = Field(..., description="Monitoring configuration")
    security: Dict[str, Any] = Field(..., description="Security configuration")

class LogsResponse(BaseResponse):
    """Response model for system logs."""
    logs: List[dict] = Field(..., description="Log entries")
    level: str = Field(..., description="Log level")
    limit: int = Field(..., description="Log limit")
    total: int = Field(..., description="Total log entries")

class RestartServicesRequest(BaseModel):
    """Request model for restarting services."""
    services: List[str] = Field(..., min_items=1, description="Services to restart")

class RestartServicesResponse(BaseResponse):
    """Response model for service restart."""
    message: str = Field(..., description="Success message")
    restarted_services: List[str] = Field(..., description="Restarted services")
