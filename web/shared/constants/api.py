"""
API Constants

Constants and configuration values for the SPIDER web API.
"""

from typing import List

# API Configuration
API_VERSION = "1.0.0"
API_PREFIX = "/api"

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://localhost:3001",  # Alternative React port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://spider-dashboard.example.com",  # Production domain
]

# Rate Limiting
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_BURST = 10  # burst requests

# Authentication
JWT_SECRET_KEY = "spider-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

# Session Configuration
SESSION_TIMEOUT_MINUTES = 30
MAX_CONCURRENT_SESSIONS = 5
SESSION_CLEANUP_INTERVAL = 300  # seconds

# WebSocket Configuration
WEBSOCKET_HEARTBEAT_INTERVAL = 30  # seconds
WEBSOCKET_MAX_CONNECTIONS = 100
WEBSOCKET_MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/json",
    "text/csv",
    "application/pdf"
]

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
CACHE_MAX_SIZE = 1000

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/spider_api.log"

# Database Configuration
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600

# Monitoring
METRICS_COLLECTION_INTERVAL = 60  # seconds
HEALTH_CHECK_INTERVAL = 30  # seconds
PERFORMANCE_MONITORING = True

# Security
ENABLE_2FA = True
ENABLE_API_KEYS = True
ENABLE_AUDIT_LOGGING = True
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 900  # 15 minutes

# Notification
NOTIFICATION_RETRY_ATTEMPTS = 3
NOTIFICATION_RETRY_DELAY = 5  # seconds
EMAIL_TEMPLATES_DIR = "templates/email"

# Export Configuration
EXPORT_MAX_RECORDS = 10000
EXPORT_TIMEOUT = 300  # seconds

# Dashboard Configuration
DASHBOARD_REFRESH_INTERVAL = 30  # seconds
DASHBOARD_MAX_WIDGETS = 50
DASHBOARD_DEFAULT_LAYOUT = "default"

# Plugin Configuration
PLUGIN_MAX_SIZE = 50 * 1024 * 1024  # 50MB
PLUGIN_ALLOWED_EXTENSIONS = [".py", ".zip", ".tar.gz"]
PLUGIN_SANDBOX_TIMEOUT = 30  # seconds

# Error Messages
ERROR_MESSAGES = {
    "INVALID_CREDENTIALS": "Invalid username or password",
    "ACCOUNT_LOCKED": "Account is temporarily locked due to too many failed login attempts",
    "ACCOUNT_DISABLED": "Account is disabled",
    "TOKEN_EXPIRED": "Authentication token has expired",
    "TOKEN_INVALID": "Invalid authentication token",
    "INSUFFICIENT_PERMISSIONS": "Insufficient permissions to perform this action",
    "RESOURCE_NOT_FOUND": "Requested resource not found",
    "VALIDATION_ERROR": "Validation error in request data",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded, please try again later",
    "INTERNAL_SERVER_ERROR": "Internal server error occurred",
    "SERVICE_UNAVAILABLE": "Service is temporarily unavailable",
    "MAINTENANCE_MODE": "System is in maintenance mode",
}

# Success Messages
SUCCESS_MESSAGES = {
    "LOGIN_SUCCESS": "Login successful",
    "LOGOUT_SUCCESS": "Logout successful",
    "PASSWORD_CHANGED": "Password changed successfully",
    "PROFILE_UPDATED": "Profile updated successfully",
    "RESOURCE_CREATED": "Resource created successfully",
    "RESOURCE_UPDATED": "Resource updated successfully",
    "RESOURCE_DELETED": "Resource deleted successfully",
    "OPERATION_SUCCESS": "Operation completed successfully",
}

# HTTP Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# WebSocket Message Types
WS_MESSAGE_TYPES = {
    "METRICS_UPDATE": "metrics_update",
    "MONITORING_UPDATE": "monitoring_update",
    "ALERT": "alert",
    "NOTIFICATION": "notification",
    "ERROR": "error",
    "HEARTBEAT": "heartbeat",
    "CONNECTION_STATUS": "connection_status",
}

# Dashboard Widget Types
WIDGET_TYPES = {
    "METRIC_CARD": "metric_card",
    "LINE_CHART": "line_chart",
    "BAR_CHART": "bar_chart",
    "PIE_CHART": "pie_chart",
    "TABLE": "table",
    "LOG_VIEWER": "log_viewer",
    "ALERT_LIST": "alert_list",
    "SYSTEM_STATUS": "system_status",
}

# Chart Colors
CHART_COLORS = [
    "#3B82F6",  # Blue
    "#EF4444",  # Red
    "#10B981",  # Green
    "#F59E0B",  # Yellow
    "#8B5CF6",  # Purple
    "#06B6D4",  # Cyan
    "#F97316",  # Orange
    "#84CC16",  # Lime
    "#EC4899",  # Pink
    "#6B7280",  # Gray
]

# Time Ranges
TIME_RANGES = {
    "LAST_HOUR": "1h",
    "LAST_4_HOURS": "4h",
    "LAST_24_HOURS": "24h",
    "LAST_7_DAYS": "7d",
    "LAST_30_DAYS": "30d",
    "LAST_90_DAYS": "90d",
    "CUSTOM": "custom",
}

# System Health Levels
HEALTH_LEVELS = {
    "HEALTHY": "healthy",
    "DEGRADED": "degraded",
    "UNHEALTHY": "unhealthy",
    "UNKNOWN": "unknown",
}

# Alert Severities
ALERT_SEVERITIES = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical",
}

# Log Levels
LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}
