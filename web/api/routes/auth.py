"""
Authentication Routes

Authentication endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import logging

from ...shared.types.api import APIResponse
from ...shared.types.auth import (
    User, UserCreate, UserUpdate, UserLogin, Token, TokenRefresh,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    SessionInfo, LoginAttempt, SecurityEvent, TwoFactorSetup,
    TwoFactorVerify, APIKey, APIKeyCreate, APIKeyUpdate, AuditLog
)
from ...shared.constants.api import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
)
from ..middleware.auth import get_current_user, get_current_active_user
from ..models.database import get_database
from ..services.auth_service import AuthService
from ..services.user_service import UserService
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers first (for load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return "127.0.0.1"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "Unknown")


@router.post("/login", response_model=APIResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    audit_service: AuditService = Depends()
):
    """Authenticate user and return access token."""
    try:
        auth_service = AuthService()
        user_service = UserService()
        
        # Validate credentials
        user = await auth_service.authenticate_user(
            login_data.username, 
            login_data.password
        )
        
        if not user:
            # Log failed login attempt
            await audit_service.log_security_event(
                SecurityEvent(
                    event_type="failed_login",
                    username=login_data.username,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    failure_reason="Invalid credentials"
                )
            )
            
            raise HTTPException(
                status_code=HTTP_STATUS["UNAUTHORIZED"],
                detail=ERROR_MESSAGES["INVALID_CREDENTIALS"]
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=HTTP_STATUS["UNAUTHORIZED"],
                detail=ERROR_MESSAGES["ACCOUNT_LOCKED"]
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=HTTP_STATUS["UNAUTHORIZED"],
                detail=ERROR_MESSAGES["ACCOUNT_DISABLED"]
            )
        
        # Generate tokens
        access_token = await auth_service.create_access_token(user)
        refresh_token = await auth_service.create_refresh_token(user)
        
        # Update user login info
        await user_service.update_last_login(user.id)
        
        # Log successful login
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="login",
                user_id=user.id,
                username=user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
        )
        
        return APIResponse(
            success=True,
            message=SUCCESS_MESSAGES["LOGIN_SUCCESS"],
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    audit_service: AuditService = Depends()
):
    """Logout user and invalidate tokens."""
    try:
        auth_service = AuthService()
        
        # Invalidate user tokens
        await auth_service.invalidate_user_tokens(current_user.id)
        
        # Log logout
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="logout",
                user_id=current_user.id,
                username=current_user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
        )
        
        return APIResponse(
            success=True,
            message=SUCCESS_MESSAGES["LOGOUT_SUCCESS"]
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    token_data: TokenRefresh,
    audit_service: AuditService = Depends()
):
    """Refresh access token using refresh token."""
    try:
        auth_service = AuthService()
        
        # Validate refresh token
        user = await auth_service.validate_refresh_token(token_data.refresh_token)
        
        if not user:
            raise HTTPException(
                status_code=HTTP_STATUS["UNAUTHORIZED"],
                detail=ERROR_MESSAGES["TOKEN_INVALID"]
            )
        
        # Generate new access token
        new_access_token = await auth_service.create_access_token(user)
        
        return APIResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return APIResponse(
        success=True,
        message="User information retrieved successfully",
        data=current_user.dict()
    )


@router.put("/me", response_model=APIResponse)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(),
    audit_service: AuditService = Depends()
):
    """Update current user information."""
    try:
        # Update user
        updated_user = await user_service.update_user(current_user.id, user_update)
        
        # Log profile update
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="profile_update",
                user_id=current_user.id,
                username=current_user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
        )
        
        return APIResponse(
            success=True,
            message=SUCCESS_MESSAGES["PROFILE_UPDATED"],
            data=updated_user.dict()
        )
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/change-password", response_model=APIResponse)
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(),
    audit_service: AuditService = Depends()
):
    """Change user password."""
    try:
        # Verify current password
        if not await auth_service.verify_password(
            password_data.current_password, 
            current_user.password
        ):
            raise HTTPException(
                status_code=HTTP_STATUS["BAD_REQUEST"],
                detail="Current password is incorrect"
            )
        
        # Update password
        await auth_service.update_password(current_user.id, password_data.new_password)
        
        # Log password change
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="password_change",
                user_id=current_user.id,
                username=current_user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
        )
        
        return APIResponse(
            success=True,
            message=SUCCESS_MESSAGES["PASSWORD_CHANGED"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    reset_data: PasswordReset,
    request: Request,
    auth_service: AuthService = Depends()
):
    """Request password reset."""
    try:
        # Send password reset email
        await auth_service.send_password_reset_email(reset_data.email)
        
        return APIResponse(
            success=True,
            message="Password reset email sent successfully"
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/reset-password/confirm", response_model=APIResponse)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(),
    audit_service: AuditService = Depends()
):
    """Confirm password reset with token."""
    try:
        # Validate reset token and update password
        user = await auth_service.confirm_password_reset(
            confirm_data.token, 
            confirm_data.new_password
        )
        
        if not user:
            raise HTTPException(
                status_code=HTTP_STATUS["BAD_REQUEST"],
                detail="Invalid or expired reset token"
            )
        
        # Log password reset
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="password_reset",
                user_id=user.id,
                username=user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
        )
        
        return APIResponse(
            success=True,
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/sessions", response_model=APIResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends()
):
    """Get user's active sessions."""
    try:
        sessions = await auth_service.get_user_sessions(current_user.id)
        
        return APIResponse(
            success=True,
            message="Sessions retrieved successfully",
            data=[session.dict() for session in sessions]
        )
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.delete("/sessions/{session_id}", response_model=APIResponse)
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(),
    audit_service: AuditService = Depends()
):
    """Revoke a specific session."""
    try:
        # Revoke session
        success = await auth_service.revoke_session(session_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Session not found"
            )
        
        # Log session revocation
        await audit_service.log_security_event(
            SecurityEvent(
                event_type="session_revoked",
                user_id=current_user.id,
                username=current_user.username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True,
                details={"session_id": session_id}
            )
        )
        
        return APIResponse(
            success=True,
            message="Session revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
