"""
Monitoring Routes

Monitoring endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...shared.types.api import (
    APIResponse, SystemStatus, PerformanceMetrics, HealthCheck,
    LogEntry, PaginationParams, FilterParams, PaginatedResponse
)
from ...shared.types.auth import User
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.monitoring_service import MonitoringService
from ..services.log_service import LogService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=APIResponse)
async def get_health_status(
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Get system health status."""
    try:
        health_status = await monitoring_service.get_health_status()
        
        return APIResponse(
            success=True,
            message="Health status retrieved successfully",
            data=[status.dict() for status in health_status]
        )
        
    except Exception as e:
        logger.error(f"Get health status error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/performance", response_model=APIResponse)
async def get_performance_metrics(
    time_range: str = Query("1h", description="Time range for metrics"),
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Get performance metrics."""
    try:
        metrics = await monitoring_service.get_performance_metrics(time_range)
        
        return APIResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=metrics.dict()
        )
        
    except Exception as e:
        logger.error(f"Get performance metrics error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/logs", response_model=APIResponse)
async def get_logs(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    log_service: LogService = Depends()
):
    """Get system logs."""
    try:
        logs = await log_service.get_logs(
            pagination=pagination,
            filters=filters
        )
        
        return APIResponse(
            success=True,
            message="Logs retrieved successfully",
            data=logs.dict()
        )
        
    except Exception as e:
        logger.error(f"Get logs error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/metrics", response_model=APIResponse)
async def get_metrics(
    metric_name: Optional[str] = Query(None, description="Specific metric name"),
    time_range: str = Query("1h", description="Time range for metrics"),
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Get monitoring metrics."""
    try:
        metrics = await monitoring_service.get_metrics(
            metric_name=metric_name,
            time_range=time_range
        )
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/alerts", response_model=APIResponse)
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Get monitoring alerts."""
    try:
        alerts = await monitoring_service.get_alerts(
            status=status,
            severity=severity,
            pagination=pagination
        )
        
        return APIResponse(
            success=True,
            message="Alerts retrieved successfully",
            data=alerts.dict()
        )
        
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Acknowledge an alert."""
    try:
        success = await monitoring_service.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Alert not found"
            )
        
        return APIResponse(
            success=True,
            message="Alert acknowledged successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Acknowledge alert error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/alerts/{alert_id}/resolve", response_model=APIResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Resolve an alert."""
    try:
        success = await monitoring_service.resolve_alert(
            alert_id=alert_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Alert not found"
            )
        
        return APIResponse(
            success=True,
            message="Alert resolved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resolve alert error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )
