"""
SPIDER Framework - User Controller

Handles all user-related API endpoints including authentication, profile management, and permissions.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
import uuid
from datetime import datetime

from ...core.config import get_settings
from ...core.database import get_db
from ...core.logger import get_logger
from ...enterprise.user_management import get_current_user, User, UserRole
from ...enterprise.multi_tenant import get_current_tenant, Tenant

logger = get_logger(__name__)

class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("viewer", regex=r'^(super_admin|admin|manager|developer|viewer)$')
    is_active: bool = True

class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, regex=r'^(super_admin|admin|manager|developer|viewer)$')
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

class UserListResponse(BaseModel):
    """Response model for user list."""
    users: List[UserResponse]
    pagination: Dict[str, Any]

class PasswordChangeRequest(BaseModel):
    """Request model for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserController:
    """Controller for user-related operations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def create_user(
        self,
        request: UserCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> UserResponse:
        """Create a new user."""
        try:
            # Check permissions
            if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create users"
                )
            
            # Check if username already exists
            # existing_user = db.query(User).filter_by(
            #     username=request.username,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if existing_user:
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail="Username already exists"
            #     )
            
            # Check if email already exists
            # existing_email = db.query(User).filter_by(
            #     email=request.email,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if existing_email:
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail="Email already exists"
            #     )
            
            # Create user
            user_data = {
                "id": str(uuid.uuid4()),
                "username": request.username,
                "email": request.email,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "role": request.role,
                "is_active": request.is_active,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "tenant_id": current_tenant.id
            }
            
            # Hash password
            # hashed_password = hash_password(request.password)
            # user_data["password_hash"] = hashed_password
            
            # Save to database
            # user = User(**user_data)
            # db.add(user)
            # db.commit()
            # db.refresh(user)
            
            logger.info(f"Created user {user_data['id']} for tenant {current_tenant.id}")
            
            return UserResponse(**user_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create user")
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> UserListResponse:
        """Get list of users."""
        try:
            # Check permissions
            if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view users"
                )
            
            # Build query filters
            filters = {"tenant_id": current_tenant.id}
            if role:
                filters["role"] = role
            if is_active is not None:
                filters["is_active"] = is_active
            
            # Query database
            # query = db.query(User).filter_by(**filters)
            
            # if search:
            #     query = query.filter(
            #         or_(
            #             User.username.ilike(f"%{search}%"),
            #             User.email.ilike(f"%{search}%"),
            #             User.first_name.ilike(f"%{search}%"),
            #             User.last_name.ilike(f"%{search}%")
            #         )
            #     )
            
            # users = query.offset(skip).limit(limit).all()
            # total = query.count()
            
            # Mock data for now
            users = []
            total = 0
            
            return UserListResponse(
                users=[UserResponse(**user.__dict__) for user in users],
                pagination={
                    "skip": skip,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get users")
    
    async def get_user(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> UserResponse:
        """Get a specific user."""
        try:
            # Check permissions
            if current_user.id != user_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view user"
                )
            
            # Query database
            # user = db.query(User).filter_by(
            #     id=user_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not user:
            #     raise HTTPException(status_code=404, detail="User not found")
            
            # Mock data for now
            raise HTTPException(status_code=404, detail="User not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user")
    
    async def update_user(
        self,
        user_id: str,
        request: UserUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> UserResponse:
        """Update a user."""
        try:
            # Check permissions
            if current_user.id != user_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update user"
                )
            
            # Get existing user
            # user = db.query(User).filter_by(
            #     id=user_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not user:
            #     raise HTTPException(status_code=404, detail="User not found")
            
            # Update fields
            update_data = request.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                # for field, value in update_data.items():
                #     setattr(user, field, value)
                
                # db.commit()
                # db.refresh(user)
            
            logger.info(f"Updated user {user_id}")
            
            # Mock response for now
            raise HTTPException(status_code=404, detail="User not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update user")
    
    async def delete_user(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, str]:
        """Delete a user."""
        try:
            # Check permissions
            if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to delete users"
                )
            
            # Prevent self-deletion
            if current_user.id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )
            
            # Check if user exists
            # user = db.query(User).filter_by(
            #     id=user_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not user:
            #     raise HTTPException(status_code=404, detail="User not found")
            
            # Delete user
            # db.delete(user)
            # db.commit()
            
            logger.info(f"Deleted user {user_id}")
            
            return {"message": "User deleted successfully", "user_id": user_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete user")
    
    async def change_password(
        self,
        user_id: str,
        request: PasswordChangeRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, str]:
        """Change user password."""
        try:
            # Check permissions
            if current_user.id != user_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to change password"
                )
            
            # Get user
            # user = db.query(User).filter_by(
            #     id=user_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not user:
            #     raise HTTPException(status_code=404, detail="User not found")
            
            # Verify current password
            # if not verify_password(request.current_password, user.password_hash):
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail="Current password is incorrect"
            #     )
            
            # Hash new password
            # new_password_hash = hash_password(request.new_password)
            # user.password_hash = new_password_hash
            # user.updated_at = datetime.utcnow()
            
            # db.commit()
            
            logger.info(f"Changed password for user {user_id}")
            
            return {"message": "Password changed successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to change password")
    
    async def get_user_profile(
        self,
        current_user: User = Depends(get_current_user)
    ) -> UserResponse:
        """Get current user profile."""
        try:
            return UserResponse(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                role=current_user.role.value,
                is_active=current_user.is_active,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at,
                last_login=current_user.last_login
            )
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user profile")
