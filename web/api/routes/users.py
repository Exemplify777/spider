"""
User Management Routes

User management endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import logging

from ...shared.types.api import APIResponse, PaginationParams, FilterParams, PaginatedResponse
from ...shared.types.auth import User, UserCreate, UserUpdate
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_users(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends()
):
    """Get all users."""
    try:
        users = await user_service.get_users(
            pagination=pagination,
            filters=filters
        )
        
        return APIResponse(
            success=True,
            message="Users retrieved successfully",
            data=users.dict()
        )
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/", response_model=APIResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends()
):
    """Create a new user."""
    try:
        user = await user_service.create_user(
            user_data=user_data,
            created_by=current_user.id
        )
        
        return APIResponse(
            success=True,
            message="User created successfully",
            data=user.dict()
        )
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends()
):
    """Get a specific user."""
    try:
        user = await user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/{user_id}", response_model=APIResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends()
):
    """Update a user."""
    try:
        user = await user_service.update_user(
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user.id
        )
        
        if not user:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="User updated successfully",
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends()
):
    """Delete a user."""
    try:
        success = await user_service.delete_user(
            user_id=user_id,
            deleted_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
