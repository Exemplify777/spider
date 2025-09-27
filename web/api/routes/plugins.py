"""
Plugin Routes

Plugin management endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ...shared.types.api import (
    APIResponse, PluginInfo, PaginationParams, FilterParams, PaginatedResponse
)
from ...shared.types.auth import User
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.plugin_service import PluginService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_plugins(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Get all plugins."""
    try:
        plugins = await plugin_service.get_plugins(
            pagination=pagination,
            filters=filters
        )
        
        return APIResponse(
            success=True,
            message="Plugins retrieved successfully",
            data=plugins.dict()
        )
        
    except Exception as e:
        logger.error(f"Get plugins error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/{plugin_id}", response_model=APIResponse)
async def get_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Get a specific plugin."""
    try:
        plugin = await plugin_service.get_plugin(plugin_id)
        
        if not plugin:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin retrieved successfully",
            data=plugin.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get plugin error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/upload", response_model=APIResponse)
async def upload_plugin(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Upload a new plugin."""
    try:
        plugin = await plugin_service.upload_plugin(
            file=file,
            user_id=current_user.id
        )
        
        return APIResponse(
            success=True,
            message="Plugin uploaded successfully",
            data=plugin.dict()
        )
        
    except Exception as e:
        logger.error(f"Upload plugin error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/{plugin_id}/activate", response_model=APIResponse)
async def activate_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Activate a plugin."""
    try:
        success = await plugin_service.activate_plugin(
            plugin_id=plugin_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin activated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate plugin error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/{plugin_id}/deactivate", response_model=APIResponse)
async def deactivate_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Deactivate a plugin."""
    try:
        success = await plugin_service.deactivate_plugin(
            plugin_id=plugin_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin deactivated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate plugin error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.delete("/{plugin_id}", response_model=APIResponse)
async def delete_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Delete a plugin."""
    try:
        success = await plugin_service.delete_plugin(
            plugin_id=plugin_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete plugin error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/{plugin_id}/configuration", response_model=APIResponse)
async def get_plugin_configuration(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Get plugin configuration."""
    try:
        config = await plugin_service.get_plugin_configuration(plugin_id)
        
        if not config:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin configuration not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin configuration retrieved successfully",
            data=config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get plugin configuration error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/{plugin_id}/configuration", response_model=APIResponse)
async def update_plugin_configuration(
    plugin_id: str,
    configuration: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Update plugin configuration."""
    try:
        success = await plugin_service.update_plugin_configuration(
            plugin_id=plugin_id,
            configuration=configuration,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Plugin not found"
            )
        
        return APIResponse(
            success=True,
            message="Plugin configuration updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update plugin configuration error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/{plugin_id}/logs", response_model=APIResponse)
async def get_plugin_logs(
    plugin_id: str,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Get plugin logs."""
    try:
        logs = await plugin_service.get_plugin_logs(
            plugin_id=plugin_id,
            pagination=pagination
        )
        
        return APIResponse(
            success=True,
            message="Plugin logs retrieved successfully",
            data=logs.dict()
        )
        
    except Exception as e:
        logger.error(f"Get plugin logs error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/{plugin_id}/metrics", response_model=APIResponse)
async def get_plugin_metrics(
    plugin_id: str,
    time_range: str = Query("1h", description="Time range for metrics"),
    current_user: User = Depends(get_current_active_user),
    plugin_service: PluginService = Depends()
):
    """Get plugin metrics."""
    try:
        metrics = await plugin_service.get_plugin_metrics(
            plugin_id=plugin_id,
            time_range=time_range
        )
        
        return APIResponse(
            success=True,
            message="Plugin metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Get plugin metrics error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
