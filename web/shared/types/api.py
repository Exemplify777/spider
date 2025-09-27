"""
API Types and Models

Shared type definitions for the SPIDER web API.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemStatus(BaseModel):
    """System status information."""
    status: str  # operational, degraded, down
    uptime: float
    memory_usage: float
    cpu_usage: float
    active_sessions: int
    total_requests: int
    error_rate: float
    last_updated: datetime


class DashboardMetrics(BaseModel):
    """Dashboard metrics data."""
    system_health: SystemStatus
    performance_metrics: Dict[str, Any]
    active_plugins: List[str]
    recent_activities: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]


class PluginInfo(BaseModel):
    """Plugin information."""
    name: str
    version: str
    description: str
    status: str  # active, inactive, error
    last_updated: datetime
    configuration: Dict[str, Any]


class UserSession(BaseModel):
    """User session information."""
    user_id: str
    username: str
    role: str
    login_time: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str


class AlertInfo(BaseModel):
    """Alert information."""
    id: str
    type: str  # error, warning, info
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None


class ConfigurationItem(BaseModel):
    """Configuration item."""
    key: str
    value: Any
    type: str  # string, number, boolean, object, array
    description: str
    required: bool
    default_value: Optional[Any] = None


class PerformanceMetrics(BaseModel):
    """Performance metrics."""
    response_time: float
    throughput: float
    error_rate: float
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    database_connections: int
    cache_hit_rate: float


class HealthCheck(BaseModel):
    """Health check result."""
    component: str
    status: str  # healthy, degraded, unhealthy
    message: str
    last_check: datetime
    response_time: Optional[float] = None


class LogEntry(BaseModel):
    """Log entry."""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component: str
    message: str
    details: Optional[Dict[str, Any]] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class FilterParams(BaseModel):
    """Filter parameters."""
    search: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Export request."""
    format: ExportFormat
    filters: Optional[FilterParams] = None
    fields: Optional[List[str]] = None
    filename: Optional[str] = None


class NotificationSettings(BaseModel):
    """Notification settings."""
    email_enabled: bool = True
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    alert_levels: List[str] = Field(default=["error", "warning"])
    quiet_hours: Optional[Dict[str, str]] = None  # {"start": "22:00", "end": "08:00"}


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    id: str
    type: str  # chart, metric, table, log
    title: str
    position: Dict[str, int]  # {"x": 0, "y": 0, "w": 4, "h": 3}
    configuration: Dict[str, Any]
    refresh_interval: int = 30  # seconds


class DashboardLayout(BaseModel):
    """Dashboard layout configuration."""
    name: str
    widgets: List[DashboardWidget]
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
