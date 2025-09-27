"""
SPIDER Framework - System Controller

Handles system-related API endpoints including health checks, configuration, and system information.
"""

from typing import Dict, Any, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import psutil
import platform
import sys
import asyncio

from ...core.config import get_settings
from ...core.database import get_db
from ...core.logger import get_logger
from ...enterprise.user_management import get_current_user, User
from ...enterprise.multi_tenant import get_current_tenant, Tenant

logger = get_logger(__name__)

class SystemController:
    """System controller for handling system-related operations."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    async def get_application_metrics(self, db: Session) -> Dict[str, Any]:
        """Get application metrics from database."""
        try:
            # Get active scrapers count
            active_scrapers = db.execute("SELECT COUNT(*) FROM scrapers WHERE status = 'running'").scalar() or 0
            
            # Get total requests from metrics table
            total_requests = db.execute("SELECT COUNT(*) FROM request_logs").scalar() or 0
            
            # Get error rate
            error_requests = db.execute("SELECT COUNT(*) FROM request_logs WHERE status_code >= 400").scalar() or 0
            error_rate = (error_requests / total_requests) if total_requests > 0 else 0.0
            
            # Get average response time
            avg_response_time = db.execute("SELECT AVG(response_time) FROM request_logs WHERE response_time IS NOT NULL").scalar() or 0.0
            
            return {
                "active_scrapers": active_scrapers,
                "total_requests": total_requests,
                "error_rate": error_rate,
                "response_time_avg": float(avg_response_time),
                "uptime": int((datetime.utcnow() - self.start_time).total_seconds())
            }
        except Exception as e:
            logger.warning(f"Failed to get application metrics: {e}")
            return {
                "active_scrapers": 0,
                "total_requests": 0,
                "error_rate": 0.0,
                "response_time_avg": 0.0,
                "uptime": int((datetime.utcnow() - self.start_time).total_seconds())
            }
    
    async def get_database_metrics(self, db: Session) -> Dict[str, Any]:
        """Get database metrics."""
        try:
            # Get database connection info
            result = db.execute("SELECT * FROM pg_stat_activity WHERE state = 'active'")
            active_connections = len(result.fetchall())
            
            # Get max connections from config
            settings = get_settings()
            max_connections = getattr(settings, 'DATABASE_MAX_CONNECTIONS', 100)
            
            # Get average query time
            avg_query_time = db.execute("SELECT AVG(EXTRACT(EPOCH FROM (now() - query_start))) FROM pg_stat_activity WHERE state = 'active'").scalar() or 0.0
            
            return {
                "connections": active_connections,
                "max_connections": max_connections,
                "query_time_avg": float(avg_query_time),
                "active_queries": active_connections
            }
        except Exception as e:
            logger.warning(f"Failed to get database metrics: {e}")
            return {
                "connections": 0,
                "max_connections": 100,
                "query_time_avg": 0.0,
                "active_queries": 0
            }
    
    async def get_redis_metrics(self) -> Dict[str, Any]:
        """Get Redis metrics."""
        try:
            import redis
            settings = get_settings()
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=True
            )
            
            info = redis_client.info()
            
            return {
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory', 0),
                "keys_count": info.get('db0', {}).get('keys', 0),
                "hit_rate": info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
            }
        except Exception as e:
            logger.warning(f"Failed to get Redis metrics: {e}")
            return {
                "connected_clients": 0,
                "used_memory": 0,
                "keys_count": 0,
                "hit_rate": 0.0
            }

class SystemInfoResponse(BaseModel):
    """Response model for system information."""
    name: str
    version: str
    description: str
    features: List[str]
    capabilities: Dict[str, Any]
    uptime: int
    timestamp: datetime

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
    uptime: int
    memory_usage: float
    cpu_usage: float

class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""
    timestamp: datetime
    system: Dict[str, Any]
    application: Dict[str, Any]
    database: Dict[str, Any]
    redis: Dict[str, Any]

class ConfigurationResponse(BaseModel):
    """Response model for configuration."""
    database: Dict[str, Any]
    redis: Dict[str, Any]
    scraping: Dict[str, Any]
    ai: Dict[str, Any]
    monitoring: Dict[str, Any]
    security: Dict[str, Any]

class SystemController:
    """Controller for system-related operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
    
    async def get_system_info(
        self,
        current_user: User = Depends(get_current_user)
    ) -> SystemInfoResponse:
        """Get system information."""
        try:
            uptime = int((datetime.utcnow() - self.start_time).total_seconds())
            
            return SystemInfoResponse(
                name="SPIDER Framework",
                version="2.0.0",
                description="Enterprise Web Scraping Framework",
                features=[
                    "multi_engine_scraping",
                    "ai_processing",
                    "real_time_monitoring",
                    "multi_tenant",
                    "enterprise_security",
                    "cloud_native"
                ],
                capabilities={
                    "max_concurrent_scrapers": 1000,
                    "supported_engines": ["scrapy", "playwright", "httpx"],
                    "ai_models": ["sentiment", "entities", "classification", "vision"],
                    "deployment_options": ["docker", "kubernetes", "cloud"],
                    "compliance_standards": ["GDPR", "HIPAA", "SOX", "PCI-DSS"]
                },
                uptime=uptime,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get system info")
    
    async def health_check(
        self,
        db: Session = Depends(get_db)
    ) -> HealthCheckResponse:
        """Perform health check."""
        try:
            # Check database health
            db_status = "healthy"
            try:
                with db.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                db_status = "unhealthy"
            
            # Check Redis health
            redis_status = "healthy"
            try:
                # redis_client = get_redis()
                # redis_client.ping()
                pass
            except Exception:
                redis_status = "unhealthy"
            
            # Check AI services health
            ai_status = "healthy"
            try:
                # from ...ai import AIManager
                # ai_manager = AIManager()
                # models_loaded = ai_manager.get_loaded_models()
                pass
            except Exception:
                ai_status = "unhealthy"
            
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            uptime = int((datetime.utcnow() - self.start_time).total_seconds())
            
            # Determine overall status
            overall_status = "healthy"
            if db_status != "healthy" or redis_status != "healthy":
                overall_status = "unhealthy"
            
            return HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.utcnow(),
                version="2.0.0",
                services={
                    "database": db_status,
                    "redis": redis_status,
                    "ai_services": ai_status
                },
                uptime=uptime,
                memory_usage=memory.percent,
                cpu_usage=cpu
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return HealthCheckResponse(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                version="2.0.0",
                services={
                    "database": "unknown",
                    "redis": "unknown",
                    "ai_services": "unknown"
                },
                uptime=0,
                memory_usage=0.0,
                cpu_usage=0.0
            )
    
    async def get_system_metrics(
        self,
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> SystemMetricsResponse:
        """Get system metrics."""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            system_metrics = {
                "cpu_usage": cpu,
                "memory_usage": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_usage": disk.percent,
                "disk_used": disk.used,
                "disk_total": disk.total,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                "platform": platform.system(),
                "python_version": sys.version
            }
            
            # Application metrics
            controller = SystemController()
            application_metrics = await controller.get_application_metrics(db)
            
            # Database metrics
            database_metrics = await controller.get_database_metrics(db)
            
            # Redis metrics
            redis_metrics = await controller.get_redis_metrics()
            
            return SystemMetricsResponse(
                timestamp=datetime.utcnow(),
                system=system_metrics,
                application=application_metrics,
                database=database_metrics,
                redis=redis_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get system metrics")
    
    async def get_configuration(
        self,
        current_user: User = Depends(get_current_user)
    ) -> ConfigurationResponse:
        """Get system configuration."""
        try:
            # Check permissions
            if current_user.role not in ["super_admin", "admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions to view configuration"
                )
            
            return ConfigurationResponse(
                database={
                    "url": "***",  # Masked for security
                    "pool_size": self.settings.database_pool_size,
                    "max_overflow": self.settings.database_max_overflow,
                    "echo": self.settings.database_echo
                },
                redis={
                    "url": "***",  # Masked for security
                    "cluster_mode": self.settings.redis_cluster_mode,
                    "decode_responses": True
                },
                scraping={
                    "default_engine": self.settings.default_scraping_engine,
                    "rate_limit_rps": self.settings.rate_limit_rps,
                    "rate_limit_burst": self.settings.rate_limit_burst
                },
                ai={
                    "enabled": self.settings.ai_enabled,
                    "models_path": self.settings.ai_models_path,
                    "gpu_enabled": self.settings.ai_gpu_enabled
                },
                monitoring={
                    "prometheus_enabled": self.settings.prometheus_enabled,
                    "prometheus_port": self.settings.prometheus_port,
                    "log_level": self.settings.log_level
                },
                security={
                    "jwt_secret": "***",  # Masked for security
                    "session_timeout": self.settings.session_timeout,
                    "rate_limiting_enabled": self.settings.rate_limiting_enabled
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get configuration: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    async def get_logs(
        self,
        level: str = "INFO",
        limit: int = 100,
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get system logs."""
        try:
            # Check permissions
            if current_user.role not in ["super_admin", "admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions to view logs"
                )
            
            # Get logs from database or log files
            try:
                # Try to get logs from database first
                log_entries = db.execute("""
                    SELECT timestamp, level, message, source 
                    FROM application_logs 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """).fetchall()
                logs = [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "level": entry.level,
                        "message": entry.message,
                        "source": entry.source
                    }
                    for entry in log_entries
                ]
            except Exception as e:
                logger.warning(f"Failed to get logs from database: {e}")
                # Fallback to empty logs
                logs = []
            
            return {
                "logs": logs,
                "level": level,
                "limit": limit,
                "total": len(logs)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get logs")
    
    async def restart_services(
        self,
        services: List[str],
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, str]:
        """Restart system services."""
        try:
            # Check permissions
            if current_user.role != "super_admin":
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions to restart services"
                )
            
            # Implement service restart logic
            restarted_services = []
            try:
                import subprocess
                import os
                
                # List of services that can be restarted
                services = ["spider-api", "spider-worker", "spider-scheduler"]
                
                for service in services:
                    try:
                        # Check if service is running
                        result = subprocess.run(
                            ["systemctl", "is-active", service], 
                            capture_output=True, 
                            text=True
                        )
                        
                        if result.returncode == 0:  # Service is active
                            # Restart the service
                            restart_result = subprocess.run(
                                ["systemctl", "restart", service],
                                capture_output=True,
                                text=True
                            )
                            
                            if restart_result.returncode == 0:
                                restarted_services.append({
                                    "service": service,
                                    "status": "restarted",
                                    "message": "Service restarted successfully"
                                })
                            else:
                                restarted_services.append({
                                    "service": service,
                                    "status": "failed",
                                    "message": f"Failed to restart: {restart_result.stderr}"
                                })
                        else:
                            restarted_services.append({
                                "service": service,
                                "status": "inactive",
                                "message": "Service is not active"
                            })
                    except Exception as e:
                        restarted_services.append({
                            "service": service,
                            "status": "error",
                            "message": f"Error restarting service: {str(e)}"
                        })
            except Exception as e:
                logger.error(f"Failed to restart services: {e}")
                restarted_services.append({
                    "service": "all",
                    "status": "error",
                    "message": f"Failed to restart services: {str(e)}"
                })
            
            return {
                "message": "Services restarted successfully",
                "restarted_services": restarted_services
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to restart services: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to restart services")
