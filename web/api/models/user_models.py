"""
SPIDER Framework - User API Models

Pydantic models for user-related API endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
import re

from .common_models import BaseResponse, PaginationResponse

class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    role: str = Field("viewer", regex=r'^(super_admin|admin|manager|developer|viewer)$', description="User role")
    is_active: bool = Field(True, description="Whether user is active")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    role: Optional[str] = Field(None, regex=r'^(super_admin|admin|manager|developer|viewer)$', description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

class UserResponse(BaseResponse):
    """Response model for user data."""
    id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class UserListResponse(BaseResponse):
    """Response model for user list."""
    users: List[UserResponse] = Field(..., description="List of users")
    pagination: PaginationResponse = Field(..., description="Pagination information")

class UserProfileResponse(BaseResponse):
    """Response model for user profile."""
    id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    preferences: Optional[dict] = Field(None, description="User preferences")

class PasswordChangeRequest(BaseModel):
    """Request model for changing password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

class PasswordChangeResponse(BaseResponse):
    """Response model for password change."""
    message: str = Field("Password changed successfully", description="Success message")

class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., min_length=1, max_length=50, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: bool = Field(False, description="Remember login")

class LoginResponse(BaseResponse):
    """Response model for user login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    refresh_token: str = Field(..., description="Refresh token")
    user: UserResponse = Field(..., description="User information")

class RefreshTokenRequest(BaseModel):
    """Request model for refreshing token."""
    refresh_token: str = Field(..., description="Refresh token")

class RefreshTokenResponse(BaseResponse):
    """Response model for token refresh."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

class LogoutRequest(BaseModel):
    """Request model for user logout."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")

class LogoutResponse(BaseResponse):
    """Response model for user logout."""
    message: str = Field("Logged out successfully", description="Success message")

class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr = Field(..., description="Email address")

class ResetPasswordResponse(BaseResponse):
    """Response model for password reset."""
    message: str = Field("Password reset email sent", description="Success message")

class ConfirmResetPasswordRequest(BaseModel):
    """Request model for confirming password reset."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

class ConfirmResetPasswordResponse(BaseResponse):
    """Response model for password reset confirmation."""
    message: str = Field("Password reset successfully", description="Success message")

class UserPreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    theme: Optional[str] = Field(None, regex=r'^(light|dark|auto)$', description="UI theme")
    language: Optional[str] = Field(None, regex=r'^[a-z]{2}(-[A-Z]{2})?$', description="Language code")
    timezone: Optional[str] = Field(None, description="Timezone")
    notifications: Optional[dict] = Field(None, description="Notification preferences")
    dashboard: Optional[dict] = Field(None, description="Dashboard preferences")

class UserPreferencesResponse(BaseResponse):
    """Response model for user preferences."""
    theme: str = Field(..., description="UI theme")
    language: str = Field(..., description="Language code")
    timezone: str = Field(..., description="Timezone")
    notifications: dict = Field(..., description="Notification preferences")
    dashboard: dict = Field(..., description="Dashboard preferences")

class UserActivityResponse(BaseResponse):
    """Response model for user activity."""
    user_id: str = Field(..., description="User identifier")
    activities: List[dict] = Field(..., description="User activities")
    pagination: PaginationResponse = Field(..., description="Pagination information")

class UserSessionsResponse(BaseResponse):
    """Response model for user sessions."""
    user_id: str = Field(..., description="User identifier")
    sessions: List[dict] = Field(..., description="Active sessions")
    pagination: PaginationResponse = Field(..., description="Pagination information")

class RevokeSessionRequest(BaseModel):
    """Request model for revoking a session."""
    session_id: str = Field(..., description="Session identifier")

class RevokeSessionResponse(BaseResponse):
    """Response model for session revocation."""
    message: str = Field("Session revoked successfully", description="Success message")

class UserStatsResponse(BaseResponse):
    """Response model for user statistics."""
    user_id: str = Field(..., description="User identifier")
    stats: dict = Field(..., description="User statistics")
    period: str = Field(..., description="Statistics period")

class UserSearchRequest(BaseModel):
    """Request model for searching users."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    role: Optional[str] = Field(None, regex=r'^(super_admin|admin|manager|developer|viewer)$', description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")

class UserSearchResponse(BaseResponse):
    """Response model for user search."""
    users: List[UserResponse] = Field(..., description="Matching users")
    pagination: PaginationResponse = Field(..., description="Pagination information")
    total_matches: int = Field(..., description="Total number of matches")
