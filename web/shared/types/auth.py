"""
Authentication Types and Models

Authentication-related type definitions for the SPIDER web API.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    """User permissions."""
    # System permissions
    MANAGE_SYSTEM = "manage_system"
    VIEW_SYSTEM = "view_system"
    
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Plugin management
    MANAGE_PLUGINS = "manage_plugins"
    VIEW_PLUGINS = "view_plugins"
    
    # Configuration management
    MANAGE_CONFIG = "manage_config"
    VIEW_CONFIG = "view_config"
    
    # Monitoring
    VIEW_MONITORING = "view_monitoring"
    MANAGE_ALERTS = "manage_alerts"
    
    # Dashboard
    VIEW_DASHBOARD = "view_dashboard"
    MANAGE_DASHBOARD = "manage_dashboard"


class User(BaseModel):
    """User model."""
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    permissions: List[Permission]
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(BaseModel):
    """User creation model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str
    remember_me: bool = False


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    username: str
    role: UserRole
    permissions: List[Permission]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenRefresh(BaseModel):
    """Token refresh model."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    """Password reset model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str = Field(..., min_length=8)


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    user_id: str
    username: str
    role: UserRole
    login_time: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


class LoginAttempt(BaseModel):
    """Login attempt model."""
    username: str
    ip_address: str
    user_agent: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    failure_reason: Optional[str] = None


class SecurityEvent(BaseModel):
    """Security event model."""
    event_type: str  # login, logout, failed_login, password_change, etc.
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: str
    user_agent: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "info"  # info, warning, error, critical


class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup."""
    secret: str
    qr_code: str
    backup_codes: List[str]


class TwoFactorVerify(BaseModel):
    """Two-factor authentication verification."""
    code: str


class APIKey(BaseModel):
    """API key model."""
    id: str
    name: str
    key: str
    user_id: str
    permissions: List[Permission]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[Permission]
    expires_in_days: Optional[int] = None  # None for no expiration


class APIKeyUpdate(BaseModel):
    """API key update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    permissions: Optional[List[Permission]] = None


class AuditLog(BaseModel):
    """Audit log entry."""
    id: str
    user_id: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
