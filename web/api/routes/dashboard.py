"""
Dashboard Routes

Dashboard endpoints for the SPIDER web API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...shared.types.api import (
    APIResponse, DashboardMetrics, SystemStatus, PerformanceMetrics,
    DashboardWidget, DashboardLayout, PaginationParams, FilterParams
)
from ...shared.types.auth import User
from ...shared.constants.api import ERROR_MESSAGES, SUCCESS_MESSAGES, HTTP_STATUS
from ..middleware.auth import get_current_active_user
from ..services.dashboard_service import DashboardService
from ..services.monitoring_service import MonitoringService
from ..services.metrics_service import MetricsService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics", response_model=APIResponse)
async def get_dashboard_metrics(
    time_range: str = Query("24h", description="Time range for metrics"),
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Get dashboard metrics."""
    try:
        metrics = await dashboard_service.get_dashboard_metrics(
            user_id=current_user.id,
            time_range=time_range
        )
        
        return APIResponse(
            success=True,
            message="Dashboard metrics retrieved successfully",
            data=metrics.dict()
        )
        
    except Exception as e:
        logger.error(f"Get dashboard metrics error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/system-status", response_model=APIResponse)
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    monitoring_service: MonitoringService = Depends()
):
    """Get system status information."""
    try:
        status = await monitoring_service.get_system_status()
        
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


@router.get("/performance", response_model=APIResponse)
async def get_performance_metrics(
    time_range: str = Query("1h", description="Time range for performance metrics"),
    current_user: User = Depends(get_current_active_user),
    metrics_service: MetricsService = Depends()
):
    """Get performance metrics."""
    try:
        metrics = await metrics_service.get_performance_metrics(time_range)
        
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


@router.get("/widgets", response_model=APIResponse)
async def get_dashboard_widgets(
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Get user's dashboard widgets."""
    try:
        widgets = await dashboard_service.get_user_widgets(current_user.id)
        
        return APIResponse(
            success=True,
            message="Dashboard widgets retrieved successfully",
            data=[widget.dict() for widget in widgets]
        )
        
    except Exception as e:
        logger.error(f"Get dashboard widgets error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/widgets", response_model=APIResponse)
async def create_dashboard_widget(
    widget: DashboardWidget,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Create a new dashboard widget."""
    try:
        created_widget = await dashboard_service.create_widget(
            user_id=current_user.id,
            widget=widget
        )
        
        return APIResponse(
            success=True,
            message="Dashboard widget created successfully",
            data=created_widget.dict()
        )
        
    except Exception as e:
        logger.error(f"Create dashboard widget error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/widgets/{widget_id}", response_model=APIResponse)
async def update_dashboard_widget(
    widget_id: str,
    widget: DashboardWidget,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Update a dashboard widget."""
    try:
        updated_widget = await dashboard_service.update_widget(
            user_id=current_user.id,
            widget_id=widget_id,
            widget=widget
        )
        
        if not updated_widget:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Widget not found"
            )
        
        return APIResponse(
            success=True,
            message="Dashboard widget updated successfully",
            data=updated_widget.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update dashboard widget error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.delete("/widgets/{widget_id}", response_model=APIResponse)
async def delete_dashboard_widget(
    widget_id: str,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Delete a dashboard widget."""
    try:
        success = await dashboard_service.delete_widget(
            user_id=current_user.id,
            widget_id=widget_id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Widget not found"
            )
        
        return APIResponse(
            success=True,
            message="Dashboard widget deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete dashboard widget error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/layouts", response_model=APIResponse)
async def get_dashboard_layouts(
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Get user's dashboard layouts."""
    try:
        layouts = await dashboard_service.get_user_layouts(current_user.id)
        
        return APIResponse(
            success=True,
            message="Dashboard layouts retrieved successfully",
            data=[layout.dict() for layout in layouts]
        )
        
    except Exception as e:
        logger.error(f"Get dashboard layouts error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/layouts", response_model=APIResponse)
async def create_dashboard_layout(
    layout: DashboardLayout,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Create a new dashboard layout."""
    try:
        created_layout = await dashboard_service.create_layout(
            user_id=current_user.id,
            layout=layout
        )
        
        return APIResponse(
            success=True,
            message="Dashboard layout created successfully",
            data=created_layout.dict()
        )
        
    except Exception as e:
        logger.error(f"Create dashboard layout error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.put("/layouts/{layout_id}", response_model=APIResponse)
async def update_dashboard_layout(
    layout_id: str,
    layout: DashboardLayout,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Update a dashboard layout."""
    try:
        updated_layout = await dashboard_service.update_layout(
            user_id=current_user.id,
            layout_id=layout_id,
            layout=layout
        )
        
        if not updated_layout:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Layout not found"
            )
        
        return APIResponse(
            success=True,
            message="Dashboard layout updated successfully",
            data=updated_layout.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update dashboard layout error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.delete("/layouts/{layout_id}", response_model=APIResponse)
async def delete_dashboard_layout(
    layout_id: str,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Delete a dashboard layout."""
    try:
        success = await dashboard_service.delete_layout(
            user_id=current_user.id,
            layout_id=layout_id
        )
        
        if not success:
            raise HTTPException(
                status_code=HTTP_STATUS["NOT_FOUND"],
                detail="Layout not found"
            )
        
        return APIResponse(
            success=True,
            message="Dashboard layout deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete dashboard layout error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/activities", response_model=APIResponse)
async def get_recent_activities(
    limit: int = Query(20, ge=1, le=100, description="Number of activities to retrieve"),
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Get recent activities."""
    try:
        activities = await dashboard_service.get_recent_activities(
            user_id=current_user.id,
            limit=limit
        )
        
        return APIResponse(
            success=True,
            message="Recent activities retrieved successfully",
            data=activities
        )
        
    except Exception as e:
        logger.error(f"Get recent activities error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.get("/alerts", response_model=APIResponse)
async def get_dashboard_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status"),
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    limit: int = Query(50, ge=1, le=200, description="Number of alerts to retrieve"),
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Get dashboard alerts."""
    try:
        alerts = await dashboard_service.get_alerts(
            user_id=current_user.id,
            status=status,
            severity=severity,
            limit=limit
        )
        
        return APIResponse(
            success=True,
            message="Dashboard alerts retrieved successfully",
            data=alerts
        )
        
    except Exception as e:
        logger.error(f"Get dashboard alerts error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS["INTERNAL_SERVER_ERROR"],
            detail=ERROR_MESSAGES["INTERNAL_SERVER_ERROR"]
        )


@router.post("/alerts/{alert_id}/resolve", response_model=APIResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends()
):
    """Resolve a dashboard alert."""
    try:
        success = await dashboard_service.resolve_alert(
            user_id=current_user.id,
            alert_id=alert_id
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
