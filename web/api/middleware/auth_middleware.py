"""
SPIDER Framework - Authentication Middleware

Handles JWT token validation, user authentication, and authorization.
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from datetime import datetime, timedelta
import asyncio

from ...core.config import get_settings
from ...core.logger import get_logger
from ...enterprise.user_management import User, UserRole

logger = get_logger(__name__)

class AuthMiddleware:
    """Authentication middleware for JWT token validation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request, call_next):
        """Process authentication for each request."""
        try:
            # Skip authentication for public endpoints
            if self._is_public_endpoint(request.url.path):
                return await call_next(request)
            
            # Extract token from request
            token = await self._extract_token(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required"
                )
            
            # Validate token
            user = await self._validate_token(token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
            
            # Add user to request state
            request.state.user = user
            request.state.tenant_id = user.tenant_id
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is deactivated"
                )
            
            # Update last activity
            await self._update_last_activity(user)
            
            logger.debug(f"Authenticated user {user.id} for {request.method} {request.url.path}")
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public and doesn't require authentication."""
        public_paths = [
            "/health",
            "/health/detailed",
            "/ready",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh"
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)
    
    async def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            return None
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        
        return token
    
    async def _validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user."""
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            
            # Extract user information
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")
            
            if not user_id or not tenant_id:
                return None
            
            # Get user from database
            try:
                from ...core.database import get_db
                db = next(get_db())
                user = db.query(User).filter(User.id == payload["user_id"]).first()
                if not user:
                    return None
            except Exception as e:
                logger.warning(f"Failed to get user from database: {e}")
                return None
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None
    
    async def _update_last_activity(self, user: User) -> None:
        """Update user's last activity timestamp."""
        try:
            # Update last activity in database
            try:
                from ...core.database import get_db
                db = next(get_db())
                user.last_activity = datetime.utcnow()
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to update last activity: {e}")
        except Exception as e:
            logger.error(f"Failed to update last activity for user {user.id}: {str(e)}")

class AuthorizationMiddleware:
    """Authorization middleware for role-based access control."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process authorization for each request."""
        try:
            # Skip authorization for public endpoints
            if self._is_public_endpoint(request.url.path):
                return await call_next(request)
            
            # Get user from request state
            user = getattr(request.state, 'user', None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated"
                )
            
            # Check endpoint permissions
            if not self._check_permissions(request, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization failed"
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        public_paths = [
            "/health",
            "/health/detailed",
            "/ready",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh"
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _check_permissions(self, request: Request, user: User) -> bool:
        """Check if user has permission to access endpoint."""
        path = request.url.path
        method = request.method
        
        # Define role-based permissions
        permissions = {
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
            UserRole.ADMIN: [
                "GET /api/v1/users",
                "POST /api/v1/users",
                "PUT /api/v1/users/*",
                "DELETE /api/v1/users/*",
                "GET /api/v1/scrapers",
                "POST /api/v1/scrapers",
                "PUT /api/v1/scrapers/*",
                "DELETE /api/v1/scrapers/*",
                "GET /api/v1/system/*",
                "POST /api/v1/system/*"
            ],
            UserRole.MANAGER: [
                "GET /api/v1/users",
                "GET /api/v1/scrapers",
                "POST /api/v1/scrapers",
                "PUT /api/v1/scrapers/*",
                "DELETE /api/v1/scrapers/*",
                "GET /api/v1/monitoring/*"
            ],
            UserRole.DEVELOPER: [
                "GET /api/v1/scrapers",
                "POST /api/v1/scrapers",
                "PUT /api/v1/scrapers/*",
                "DELETE /api/v1/scrapers/*",
                "GET /api/v1/ai/*"
            ],
            UserRole.VIEWER: [
                "GET /api/v1/scrapers",
                "GET /api/v1/monitoring/*"
            ]
        }
        
        user_permissions = permissions.get(user.role, [])
        
        # Check if user has wildcard permission
        if "*" in user_permissions:
            return True
        
        # Check specific permission
        endpoint_permission = f"{method} {path}"
        return endpoint_permission in user_permissions

class TenantMiddleware:
    """Middleware for tenant isolation."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Process tenant isolation for each request."""
        try:
            # Get tenant from request state
            tenant_id = getattr(request.state, 'tenant_id', None)
            if not tenant_id:
                # Skip tenant isolation for public endpoints
                if self._is_public_endpoint(request.url.path):
                    return await call_next(request)
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant not identified"
                )
            
            # Add tenant context to request
            request.state.tenant_context = {
                "tenant_id": tenant_id,
                "isolation_level": "database"  # Could be database, schema, or table
            }
            
            # Apply tenant-specific database routing
            try:
                from ...enterprise.multi_tenant import get_tenant_database
                tenant_db = get_tenant_database(user.tenant_id)
                if tenant_db:
                    request.state.tenant_db = tenant_db
            except Exception as e:
                logger.warning(f"Failed to apply tenant-specific database routing: {e}")
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant isolation failed"
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        public_paths = [
            "/health",
            "/health/detailed",
            "/ready",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh"
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)
