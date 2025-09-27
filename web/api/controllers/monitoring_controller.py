"""
SPIDER Framework - Monitoring Controller

Handles monitoring-related API endpoints including metrics, alerts, and dashboards.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio

from ...core.config import get_settings
from ...core.database import get_db
from ...core.logger import get_logger
from ...enterprise.user_management import get_current_user, User
from ...enterprise.multi_tenant import get_current_tenant, Tenant

logger = get_logger(__name__)

class MonitoringController:
    """Monitoring controller for handling monitoring-related operations."""
    
    async def _collect_metrics(self, db: Session, period: str) -> Dict[str, Any]:
        """Collect metrics from database or Prometheus."""
        try:
            # Try to get metrics from database first
            if period == "1h":
                time_filter = "timestamp >= NOW() - INTERVAL '1 hour'"
            elif period == "24h":
                time_filter = "timestamp >= NOW() - INTERVAL '24 hours'"
            elif period == "7d":
                time_filter = "timestamp >= NOW() - INTERVAL '7 days'"
            else:  # 30d
                time_filter = "timestamp >= NOW() - INTERVAL '30 days'"
            
            # Get system metrics
            system_metrics = db.execute(f"""
                SELECT 
                    AVG(cpu_usage) as avg_cpu,
                    AVG(memory_usage) as avg_memory,
                    AVG(disk_usage) as avg_disk,
                    AVG(load_average) as avg_load
                FROM system_metrics 
                WHERE {time_filter}
            """).fetchone()
            
            # Get application metrics
            app_metrics = db.execute(f"""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
                FROM request_logs 
                WHERE {time_filter}
            """).fetchone()
            
            return {
                "system": {
                    "cpu_usage": float(system_metrics.avg_cpu or 0),
                    "memory_usage": float(system_metrics.avg_memory or 0),
                    "disk_usage": float(system_metrics.avg_disk or 0),
                    "load_average": [float(system_metrics.avg_load or 0)]
                },
                "application": {
                    "total_requests": app_metrics.total_requests or 0,
                    "avg_response_time": float(app_metrics.avg_response_time or 0),
                    "error_rate": (app_metrics.error_count or 0) / max(app_metrics.total_requests or 1, 1)
                },
                "scrapers": {
                    "active_count": db.execute("SELECT COUNT(*) FROM scrapers WHERE status = 'running'").scalar() or 0,
                    "total_scraped": db.execute(f"SELECT COUNT(*) FROM scraped_data WHERE {time_filter}").scalar() or 0
                }
            }
        except Exception as e:
            logger.warning(f"Failed to collect metrics from database: {e}")
            # Fallback to default metrics
            return {
                "system": {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "disk_usage": 0.0,
                    "load_average": [0.0]
                },
                "application": {
                    "total_requests": 0,
                    "avg_response_time": 0.0,
                    "error_rate": 0.0
                },
                "scrapers": {
                    "active_count": 0,
                    "total_scraped": 0
                }
            }
    
    async def _get_alerts(self, db: Session, status: Optional[str], severity: Optional[str]) -> List[Dict[str, Any]]:
        """Get alerts from database."""
        try:
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if severity:
                query += " AND severity = %s"
                params.append(severity)
            
            query += " ORDER BY created_at DESC LIMIT 100"
            
            alerts = db.execute(query, params).fetchall()
            
            return [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "status": alert.status,
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at,
                    "resolved_at": alert.resolved_at,
                    "labels": alert.labels or {}
                }
                for alert in alerts
            ]
        except Exception as e:
            logger.warning(f"Failed to get alerts from database: {e}")
            return []

class MetricsResponse(BaseModel):
    """Response model for metrics data."""
    timestamp: datetime
    metrics: Dict[str, Any]
    period: str

class AlertResponse(BaseModel):
    """Response model for alert data."""
    id: str
    name: str
    status: str
    severity: str
    message: str
    created_at: datetime
    resolved_at: Optional[datetime]
    labels: Dict[str, str]

class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    id: str
    name: str
    description: str
    panels: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class ScraperStatsResponse(BaseModel):
    """Response model for scraper statistics."""
    scraper_id: str
    period: str
    statistics: Dict[str, Any]
    timeline: List[Dict[str, Any]]

class MonitoringController:
    """Controller for monitoring-related operations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def get_metrics(
        self,
        period: str = Query("1h", regex=r'^(1h|24h|7d|30d)$'),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> MetricsResponse:
        """Get system metrics."""
        try:
            # Implement metrics collection from Prometheus or database
            controller = MonitoringController()
            metrics = await controller._collect_metrics(db, period)
            
            return MetricsResponse(
                timestamp=datetime.utcnow(),
                metrics=metrics,
                period=period
            )
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    async def get_alerts(
        self,
        status: Optional[str] = Query(None, regex=r'^(active|resolved|suppressed)$'),
        severity: Optional[str] = Query(None, regex=r'^(critical|warning|info)$'),
        limit: int = Query(100, ge=1, le=1000),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> List[AlertResponse]:
        """Get system alerts."""
        try:
            # Implement alert retrieval from Alertmanager or database
            controller = MonitoringController()
            alerts = await controller._get_alerts(db, status, severity)
            
            # Filter alerts based on query parameters
            if status:
                alerts = [alert for alert in alerts if alert["status"] == status]
            if severity:
                alerts = [alert for alert in alerts if alert["severity"] == severity]
            
            return [AlertResponse(**alert) for alert in alerts[:limit]]
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get alerts")
    
    async def get_dashboards(
        self,
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> List[DashboardResponse]:
        """Get available dashboards."""
        try:
            # TODO: Implement dashboard retrieval from Grafana or database
            dashboards = [
                {
                    "id": "dashboard_001",
                    "name": "System Overview",
                    "description": "High-level system metrics and health",
                    "panels": [
                        {
                            "title": "CPU Usage",
                            "type": "graph",
                            "targets": ["cpu_usage_percent"]
                        },
                        {
                            "title": "Memory Usage",
                            "type": "graph",
                            "targets": ["memory_usage_percent"]
                        },
                        {
                            "title": "Active Scrapers",
                            "type": "singlestat",
                            "targets": ["active_scrapers_count"]
                        }
                    ],
                    "created_at": datetime.utcnow() - timedelta(days=30),
                    "updated_at": datetime.utcnow() - timedelta(days=1)
                },
                {
                    "id": "dashboard_002",
                    "name": "Scraping Metrics",
                    "description": "Detailed scraping performance metrics",
                    "panels": [
                        {
                            "title": "Scraper Success Rate",
                            "type": "graph",
                            "targets": ["scraper_success_rate"]
                        },
                        {
                            "title": "Items Scraped",
                            "type": "graph",
                            "targets": ["scraper_items_total"]
                        },
                        {
                            "title": "Scraper Duration",
                            "type": "graph",
                            "targets": ["scraper_duration_seconds"]
                        }
                    ],
                    "created_at": datetime.utcnow() - timedelta(days=15),
                    "updated_at": datetime.utcnow() - timedelta(hours=6)
                }
            ]
            
            return [DashboardResponse(**dashboard) for dashboard in dashboards]
            
        except Exception as e:
            logger.error(f"Failed to get dashboards: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get dashboards")
    
    async def get_scraper_stats(
        self,
        scraper_id: str,
        period: str = Query("7d", regex=r'^(1h|24h|7d|30d)$'),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> ScraperStatsResponse:
        """Get scraper statistics."""
        try:
            # TODO: Implement scraper statistics retrieval from database
            statistics = {
                "total_runs": 168,
                "successful_runs": 165,
                "failed_runs": 3,
                "success_rate": 0.982,
                "average_duration": 42.1,
                "total_items_scraped": 15000,
                "average_items_per_run": 89.3
            }
            
            timeline = [
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=24),
                    "runs": 24,
                    "successful": 24,
                    "failed": 0,
                    "items_scraped": 2400
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=12),
                    "runs": 12,
                    "successful": 11,
                    "failed": 1,
                    "items_scraped": 1200
                },
                {
                    "timestamp": datetime.utcnow(),
                    "runs": 6,
                    "successful": 6,
                    "failed": 0,
                    "items_scraped": 600
                }
            ]
            
            return ScraperStatsResponse(
                scraper_id=scraper_id,
                period=period,
                statistics=statistics,
                timeline=timeline
            )
            
        except Exception as e:
            logger.error(f"Failed to get scraper stats for {scraper_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get scraper stats")
    
    async def create_alert_rule(
        self,
        name: str,
        condition: str,
        severity: str,
        message: str,
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, str]:
        """Create a new alert rule."""
        try:
            # Check permissions
            if current_user.role not in ["super_admin", "admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions to create alert rules"
                )
            
            # TODO: Implement alert rule creation
            alert_rule_id = f"rule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Created alert rule {alert_rule_id} for tenant {current_tenant.id}")
            
            return {
                "message": "Alert rule created successfully",
                "alert_rule_id": alert_rule_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create alert rule: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create alert rule")
    
    async def resolve_alert(
        self,
        alert_id: str,
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, str]:
        """Resolve an alert."""
        try:
            # Check permissions
            if current_user.role not in ["super_admin", "admin", "manager"]:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions to resolve alerts"
                )
            
            # TODO: Implement alert resolution
            logger.info(f"Resolved alert {alert_id} by user {current_user.id}")
            
            return {
                "message": "Alert resolved successfully",
                "alert_id": alert_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to resolve alert")
    
    async def get_health_status(
        self,
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, Any]:
        """Get overall health status."""
        try:
            # TODO: Implement comprehensive health check
            health_status = {
                "overall": "healthy",
                "services": {
                    "api": "healthy",
                    "database": "healthy",
                    "redis": "healthy",
                    "scraper_engine": "healthy",
                    "ai_services": "healthy"
                },
                "metrics": {
                    "response_time": 150,
                    "error_rate": 0.01,
                    "uptime": 99.9
                },
                "last_check": datetime.utcnow()
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get health status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get health status")
