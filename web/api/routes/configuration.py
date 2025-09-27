"""
Configuration Routes

Configuration management endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging

from ...shared.types.api import APIResponse, ConfigurationItem
from ...shared.types.auth import User
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.config_service import ConfigService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_configuration(
    current_user: User = Depends(get_current_active_user),
    config_service: ConfigService = Depends()
):
    """Get system configuration."""
    try:
        config = await config_service.get_configuration()
        
        return APIResponse(
            success=True,
            message="Configuration retrieved successfully",
            data=config
        )
        
    except Exception as e:
        logger.error(f"Get configuration error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/", response_model=APIResponse)
async def update_configuration(
    configuration: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    config_service: ConfigService = Depends()
):
    """Update system configuration."""
    try:
        success = await config_service.update_configuration(
            configuration=configuration,
            user_id=current_user.id
        )
        
        return APIResponse(
            success=True,
            message="Configuration updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Update configuration error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
