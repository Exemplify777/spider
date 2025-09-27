"""
SPIDER Framework Web API

FastAPI-based REST API for the SPIDER web dashboard.
Provides endpoints for system monitoring, configuration management,
and real-time data streaming.

Author: SPIDER Development Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uvicorn

from .routes import (
    auth, dashboard, monitoring, plugins, 
    configuration, users, system
)
from .middleware.auth import AuthMiddleware
from .middleware.rate_limiting import RateLimitMiddleware
from .models.database import get_database
from .models.websocket import ConnectionManager
from ..shared.types.api import APIResponse, SystemStatus, DashboardMetrics
from ..shared.types.auth import User, TokenData
from ..shared.constants.api import API_VERSION, CORS_ORIGINS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection manager for WebSocket connections
connection_manager = ConnectionManager()

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting SPIDER Web API...")
    
    # Initialize database connections
    await get_database().connect()
    
    # Start background tasks
    asyncio.create_task(connection_manager.start_heartbeat())
    
    logger.info("✅ SPIDER Web API started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SPIDER Web API...")
    
    # Close database connections
    await get_database().disconnect()
    
    # Stop background tasks
    await connection_manager.stop_heartbeat()
    
    logger.info("✅ SPIDER Web API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SPIDER Framework API",
    description="REST API for SPIDER web scraping framework",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["Plugins"])
app.include_router(configuration.router, prefix="/api/config", tags=["Configuration"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(system.router, prefix="/api/system", tags=["System"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return APIResponse(
        success=True,
        message="SPIDER API is healthy",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status."""
    try:
        # Get system metrics
        from spider.core.engine import EngineFactory
        from spider.monitoring.metrics import MetricsCollector
        
        engine = EngineFactory.create_engine()
        metrics = MetricsCollector()
        
        # Collect system metrics
        system_metrics = await metrics.collect_system_metrics()
        
        status = SystemStatus(
            status="operational",
            uptime=system_metrics.get("uptime", 0),
            memory_usage=system_metrics.get("memory_usage", 0),
            cpu_usage=system_metrics.get("cpu_usage", 0),
            active_sessions=system_metrics.get("active_sessions", 0),
            total_requests=system_metrics.get("total_requests", 0),
            error_rate=system_metrics.get("error_rate", 0),
            last_updated=datetime.utcnow()
        )
        
        return APIResponse(
            success=True,
            message="System status retrieved successfully",
            data=status.dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Get latest metrics
            try:
                from spider.monitoring.metrics import MetricsCollector
                metrics = MetricsCollector()
                system_metrics = await metrics.collect_system_metrics()
                
                # Send metrics to client
                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    "data": system_metrics,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Error sending metrics update: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Failed to update metrics",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


@app.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates."""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            await asyncio.sleep(1)  # Update every second for monitoring
            
            # Get monitoring data
            try:
                from spider.monitoring.health import HealthMonitor
                from spider.monitoring.performance import PerformanceMonitor
                
                health_monitor = HealthMonitor()
                perf_monitor = PerformanceMonitor()
                
                # Collect health and performance data
                health_data = await health_monitor.get_system_health()
                perf_data = await perf_monitor.get_performance_metrics()
                
                # Send combined data
                await websocket.send_text(json.dumps({
                    "type": "monitoring_update",
                    "data": {
                        "health": health_data,
                        "performance": perf_data
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Error sending monitoring update: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Failed to update monitoring data",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("Monitoring WebSocket client disconnected")


# Mount static files (for serving the React app)
app.mount("/", StaticFiles(directory="web/dashboard/build", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
