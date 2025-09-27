"""
System Routes

System management endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from ...shared.types.api import APIResponse, SystemStatus
from ...shared.types.auth import User
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.system_service import SystemService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=APIResponse)
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    system_service: SystemService = Depends()
):
    """Get system status."""
    try:
        status = await system_service.get_system_status()
        
        return APIResponse(
            success=True,
            message="System status retrieved successfully",
            data=status.dict()
        )
        
    except Exception as e:
        logger.error(f"Get system status error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/info", response_model=APIResponse)
async def get_system_info(
    current_user: User = Depends(get_current_active_user),
    system_service: SystemService = Depends()
):
    """Get system information."""
    try:
        info = await system_service.get_system_info()
        
        return APIResponse(
            success=True,
            message="System information retrieved successfully",
            data=info
        )
        
    except Exception as e:
        logger.error(f"Get system info error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
