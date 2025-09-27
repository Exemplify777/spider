"""
SPIDER Framework - Monitoring API Models

Pydantic models for monitoring-related API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .common_models import BaseResponse, PaginationResponse

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

class MetricsResponse(BaseResponse):
    """Response model for metrics data."""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    metrics: Dict[str, Any] = Field(..., description="Metrics data")
    period: str = Field(..., description="Metrics period")

class AlertResponse(BaseResponse):
    """Response model for alert data."""
    id: str = Field(..., description="Alert identifier")
    name: str = Field(..., description="Alert name")
    status: AlertStatus = Field(..., description="Alert status")
    severity: AlertSeverity = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution timestamp")
    labels: Dict[str, str] = Field(default_factory=dict, description="Alert labels")

class DashboardPanel(BaseModel):
    """Dashboard panel model."""
    id: str = Field(..., description="Panel identifier")
    title: str = Field(..., description="Panel title")
    type: str = Field(..., description="Panel type")
    targets: List[Dict[str, Any]] = Field(..., description="Panel targets")
    options: Optional[Dict[str, Any]] = Field(None, description="Panel options")

class DashboardResponse(BaseResponse):
    """Response model for dashboard data."""
    id: str = Field(..., description="Dashboard identifier")
    name: str = Field(..., description="Dashboard name")
    description: str = Field(..., description="Dashboard description")
    panels: List[DashboardPanel] = Field(..., description="Dashboard panels")
    created_at: datetime = Field(..., description="Dashboard creation timestamp")
    updated_at: datetime = Field(..., description="Dashboard update timestamp")

class ScraperStatsResponse(BaseResponse):
    """Response model for scraper statistics."""
    scraper_id: str = Field(..., description="Scraper identifier")
    period: str = Field(..., description="Statistics period")
    statistics: Dict[str, Any] = Field(..., description="Statistics data")
    timeline: List[Dict[str, Any]] = Field(..., description="Timeline data")

class CreateAlertRuleRequest(BaseModel):
    """Request model for creating alert rule."""
    name: str = Field(..., min_length=1, max_length=255, description="Alert rule name")
    condition: str = Field(..., description="Alert condition")
    severity: AlertSeverity = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")

class CreateAlertRuleResponse(BaseResponse):
    """Response model for alert rule creation."""
    message: str = Field(..., description="Success message")
    alert_rule_id: str = Field(..., description="Alert rule identifier")

class ResolveAlertRequest(BaseModel):
    """Request model for resolving alert."""
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

class ResolveAlertResponse(BaseResponse):
    """Response model for alert resolution."""
    message: str = Field(..., description="Success message")
    alert_id: str = Field(..., description="Alert identifier")

class HealthStatusResponse(BaseResponse):
    """Response model for health status."""
    overall: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Service health statuses")
    metrics: Dict[str, Any] = Field(..., description="Health metrics")
    last_check: datetime = Field(..., description="Last check timestamp")
