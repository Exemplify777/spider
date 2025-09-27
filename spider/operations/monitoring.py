"""
Advanced Operational Monitoring and Alerting

This module provides comprehensive operational monitoring capabilities for the SPIDER Framework
in production environments, including real-time monitoring, alerting, and incident management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path

import aiohttp
import aiofiles
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import psutil
import docker
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status levels"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    source: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    operator: str = "gt"  # gt, lt, eq, ne
    duration: int = 300  # seconds
    enabled: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    prometheus_url: str = "http://prometheus:9090"
    grafana_url: str = "http://grafana:3000"
    alertmanager_url: str = "http://alertmanager:9093"
    check_interval: int = 30
    alert_cooldown: int = 300
    max_alerts_per_minute: int = 100
    retention_days: int = 30
    enabled_checks: List[str] = field(default_factory=lambda: [
        "system_health", "application_health", "database_health", 
        "cache_health", "network_health", "security_health"
    ])


class OperationalMonitor:
    """
    Advanced operational monitoring and alerting system for SPIDER Framework
    """
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.registry = CollectorRegistry()
        self.alerts: Dict[str, Alert] = {}
        self.metrics_cache: Dict[str, Any] = {}
        self.thresholds: Dict[str, MetricThreshold] = {}
        self.running = False
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Prometheus metrics
        self.alert_counter = Counter(
            'spider_operations_alerts_total',
            'Total number of alerts generated',
            ['severity', 'source', 'status'],
            registry=self.registry
        )
        
        self.metric_check_duration = Histogram(
            'spider_operations_metric_check_duration_seconds',
            'Time spent checking metrics',
            ['check_type'],
            registry=self.registry
        )
        
        self.active_alerts = Gauge(
            'spider_operations_active_alerts',
            'Number of active alerts',
            ['severity'],
            registry=self.registry
        )
        
        # Initialize monitoring components
        self._initialize_monitoring()
    
    def _initialize_monitoring(self):
        """Initialize monitoring components"""
        try:
            # Load Kubernetes client
            config.load_incluster_config()
            self.k8s_client = client.CoreV1Api()
            self.k8s_apps_client = client.AppsV1Api()
        except Exception as e:
            logger.warning(f"Kubernetes client not available: {e}")
            self.k8s_client = None
            self.k8s_apps_client = None
        
        # Load Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client not available: {e}")
            self.docker_client = None
        
        # Load default thresholds
        self._load_default_thresholds()
    
    def _load_default_thresholds(self):
        """Load default metric thresholds"""
        default_thresholds = [
            MetricThreshold("cpu_usage_percent", 70.0, 90.0, "gt"),
            MetricThreshold("memory_usage_percent", 80.0, 95.0, "gt"),
            MetricThreshold("disk_usage_percent", 85.0, 95.0, "gt"),
            MetricThreshold("network_latency_ms", 100.0, 500.0, "gt"),
            MetricThreshold("error_rate_percent", 1.0, 5.0, "gt"),
            MetricThreshold("response_time_ms", 1000.0, 5000.0, "gt"),
            MetricThreshold("queue_length", 1000.0, 5000.0, "gt"),
            MetricThreshold("database_connections", 80.0, 95.0, "gt"),
            MetricThreshold("cache_hit_rate_percent", 90.0, 95.0, "lt"),
            MetricThreshold("pod_restart_count", 5.0, 10.0, "gt"),
        ]
        
        for threshold in default_thresholds:
            self.thresholds[threshold.metric_name] = threshold
    
    async def start_monitoring(self):
        """Start the operational monitoring system"""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        self.running = True
        logger.info("Starting operational monitoring system")
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._monitor_application_health()),
            asyncio.create_task(self._monitor_database_health()),
            asyncio.create_task(self._monitor_cache_health()),
            asyncio.create_task(self._monitor_network_health()),
            asyncio.create_task(self._monitor_security_health()),
            asyncio.create_task(self._process_alerts()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.monitoring_tasks)
        except Exception as e:
            logger.error(f"Error in monitoring tasks: {e}")
        finally:
            self.running = False
    
    async def stop_monitoring(self):
        """Stop the operational monitoring system"""
        if not self.running:
            return
        
        logger.info("Stopping operational monitoring system")
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
    
    async def _monitor_system_health(self):
        """Monitor system health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="system_health").time():
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    await self._check_metric("cpu_usage_percent", cpu_percent)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    await self._check_metric("memory_usage_percent", memory.percent)
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    disk_percent = (disk.used / disk.total) * 100
                    await self._check_metric("disk_usage_percent", disk_percent)
                    
                    # Load average
                    load_avg = psutil.getloadavg()[0]
                    await self._check_metric("load_average", load_avg)
                    
                    # Network I/O
                    net_io = psutil.net_io_counters()
                    await self._check_metric("network_bytes_sent", net_io.bytes_sent)
                    await self._check_metric("network_bytes_recv", net_io.bytes_recv)
                    
            except Exception as e:
                logger.error(f"Error monitoring system health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _monitor_application_health(self):
        """Monitor application health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="application_health").time():
                    # Check application endpoints
                    await self._check_application_endpoints()
                    
                    # Check application metrics
                    await self._check_application_metrics()
                    
                    # Check pod health
                    await self._check_pod_health()
                    
            except Exception as e:
                logger.error(f"Error monitoring application health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _monitor_database_health(self):
        """Monitor database health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="database_health").time():
                    # Check database connectivity
                    await self._check_database_connectivity()
                    
                    # Check database performance
                    await self._check_database_performance()
                    
                    # Check database connections
                    await self._check_database_connections()
                    
            except Exception as e:
                logger.error(f"Error monitoring database health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _monitor_cache_health(self):
        """Monitor cache health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="cache_health").time():
                    # Check Redis health
                    await self._check_redis_health()
                    
                    # Check Memcached health
                    await self._check_memcached_health()
                    
                    # Check cache performance
                    await self._check_cache_performance()
                    
            except Exception as e:
                logger.error(f"Error monitoring cache health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _monitor_network_health(self):
        """Monitor network health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="network_health").time():
                    # Check network connectivity
                    await self._check_network_connectivity()
                    
                    # Check network latency
                    await self._check_network_latency()
                    
                    # Check DNS resolution
                    await self._check_dns_resolution()
                    
            except Exception as e:
                logger.error(f"Error monitoring network health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _monitor_security_health(self):
        """Monitor security health metrics"""
        while self.running:
            try:
                with self.metric_check_duration.labels(check_type="security_health").time():
                    # Check security events
                    await self._check_security_events()
                    
                    # Check authentication failures
                    await self._check_auth_failures()
                    
                    # Check suspicious activities
                    await self._check_suspicious_activities()
                    
            except Exception as e:
                logger.error(f"Error monitoring security health: {e}")
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _check_metric(self, metric_name: str, value: float):
        """Check a metric against its threshold"""
        if metric_name not in self.thresholds:
            return
        
        threshold = self.thresholds[metric_name]
        if not threshold.enabled:
            return
        
        # Check threshold
        alert_triggered = False
        severity = AlertSeverity.INFO
        
        if threshold.operator == "gt" and value > threshold.critical_threshold:
            alert_triggered = True
            severity = AlertSeverity.CRITICAL
        elif threshold.operator == "gt" and value > threshold.warning_threshold:
            alert_triggered = True
            severity = AlertSeverity.WARNING
        elif threshold.operator == "lt" and value < threshold.critical_threshold:
            alert_triggered = True
            severity = AlertSeverity.CRITICAL
        elif threshold.operator == "lt" and value < threshold.warning_threshold:
            alert_triggered = True
            severity = AlertSeverity.WARNING
        
        if alert_triggered:
            await self._create_alert(
                title=f"Metric threshold exceeded: {metric_name}",
                description=f"Metric {metric_name} value {value} exceeds threshold",
                severity=severity,
                source="monitoring",
                labels={"metric_name": metric_name, "value": str(value)},
                annotations={"threshold": str(threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold)}
            )
    
    async def _check_application_endpoints(self):
        """Check application health endpoints"""
        endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/ready",
            "http://localhost:8000/metrics"
        ]
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=5) as response:
                        if response.status != 200:
                            await self._create_alert(
                                title=f"Application endpoint unhealthy: {endpoint}",
                                description=f"Endpoint {endpoint} returned status {response.status}",
                                severity=AlertSeverity.WARNING,
                                source="application",
                                labels={"endpoint": endpoint, "status": str(response.status)}
                            )
            except Exception as e:
                await self._create_alert(
                    title=f"Application endpoint unreachable: {endpoint}",
                    description=f"Endpoint {endpoint} is unreachable: {str(e)}",
                    severity=AlertSeverity.CRITICAL,
                    source="application",
                    labels={"endpoint": endpoint, "error": str(e)}
                )
    
    async def _check_application_metrics(self):
        """Check application metrics from Prometheus"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.prometheus_url}/api/v1/query", 
                                     params={"query": "spider_http_requests_total"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Process metrics data
                        pass
        except Exception as e:
            logger.error(f"Error checking application metrics: {e}")
    
    async def _check_pod_health(self):
        """Check Kubernetes pod health"""
        if not self.k8s_client:
            return
        
        try:
            pods = self.k8s_client.list_namespaced_pod(namespace="spider")
            for pod in pods.items:
                if pod.status.phase != "Running":
                    await self._create_alert(
                        title=f"Pod not running: {pod.metadata.name}",
                        description=f"Pod {pod.metadata.name} is in {pod.status.phase} state",
                        severity=AlertSeverity.WARNING,
                        source="kubernetes",
                        labels={"pod_name": pod.metadata.name, "phase": pod.status.phase}
                    )
        except Exception as e:
            logger.error(f"Error checking pod health: {e}")
    
    async def _check_database_connectivity(self):
        """Check database connectivity"""
        # Implementation for database connectivity check
        pass
    
    async def _check_database_performance(self):
        """Check database performance metrics"""
        # Implementation for database performance check
        pass
    
    async def _check_database_connections(self):
        """Check database connection pool"""
        # Implementation for database connections check
        pass
    
    async def _check_redis_health(self):
        """Check Redis health"""
        # Implementation for Redis health check
        pass
    
    async def _check_memcached_health(self):
        """Check Memcached health"""
        # Implementation for Memcached health check
        pass
    
    async def _check_cache_performance(self):
        """Check cache performance metrics"""
        # Implementation for cache performance check
        pass
    
    async def _check_network_connectivity(self):
        """Check network connectivity"""
        # Implementation for network connectivity check
        pass
    
    async def _check_network_latency(self):
        """Check network latency"""
        # Implementation for network latency check
        pass
    
    async def _check_dns_resolution(self):
        """Check DNS resolution"""
        # Implementation for DNS resolution check
        pass
    
    async def _check_security_events(self):
        """Check security events"""
        # Implementation for security events check
        pass
    
    async def _check_auth_failures(self):
        """Check authentication failures"""
        # Implementation for authentication failures check
        pass
    
    async def _check_suspicious_activities(self):
        """Check suspicious activities"""
        # Implementation for suspicious activities check
        pass
    
    async def _create_alert(self, title: str, description: str, severity: AlertSeverity, 
                           source: str, labels: Dict[str, str] = None, 
                           annotations: Dict[str, str] = None):
        """Create a new alert"""
        alert_id = f"{source}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.ACTIVE,
            source=source,
            timestamp=datetime.now(),
            labels=labels or {},
            annotations=annotations or {}
        )
        
        self.alerts[alert_id] = alert
        self.alert_counter.labels(
            severity=severity.value,
            source=source,
            status=alert.status.value
        ).inc()
        
        logger.info(f"Alert created: {alert_id} - {title}")
        
        # Send alert to external systems
        await self._send_alert(alert)
    
    async def _send_alert(self, alert: Alert):
        """Send alert to external systems"""
        # Send to AlertManager
        await self._send_to_alertmanager(alert)
        
        # Send to webhook
        await self._send_to_webhook(alert)
        
        # Send to email
        await self._send_to_email(alert)
    
    async def _send_to_alertmanager(self, alert: Alert):
        """Send alert to AlertManager"""
        try:
            alert_data = {
                "labels": {
                    "alertname": alert.title,
                    "severity": alert.severity.value,
                    "source": alert.source,
                    **alert.labels
                },
                "annotations": {
                    "description": alert.description,
                    **alert.annotations
                },
                "startsAt": alert.timestamp.isoformat(),
                "generatorURL": f"http://spider-monitor:8000/alerts/{alert.id}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.alertmanager_url}/api/v1/alerts",
                    json=[alert_data],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send alert to AlertManager: {response.status}")
        except Exception as e:
            logger.error(f"Error sending alert to AlertManager: {e}")
    
    async def _send_to_webhook(self, alert: Alert):
        """Send alert to webhook"""
        # Implementation for webhook notification
        pass
    
    async def _send_to_email(self, alert: Alert):
        """Send alert to email"""
        # Implementation for email notification
        pass
    
    async def _process_alerts(self):
        """Process and manage alerts"""
        while self.running:
            try:
                # Update alert metrics
                for severity in AlertSeverity:
                    count = sum(1 for alert in self.alerts.values() 
                              if alert.severity == severity and alert.status == AlertStatus.ACTIVE)
                    self.active_alerts.labels(severity=severity.value).set(count)
                
                # Clean up resolved alerts
                await self._cleanup_resolved_alerts()
                
            except Exception as e:
                logger.error(f"Error processing alerts: {e}")
            
            await asyncio.sleep(60)  # Process every minute
    
    async def _cleanup_resolved_alerts(self):
        """Clean up resolved alerts"""
        cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
        
        alerts_to_remove = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.status == AlertStatus.RESOLVED and alert.timestamp < cutoff_time
        ]
        
        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        while self.running:
            try:
                # Clean up old metrics cache
                current_time = time.time()
                self.metrics_cache = {
                    key: value for key, value in self.metrics_cache.items()
                    if current_time - value.get('timestamp', 0) < 3600  # Keep 1 hour
                }
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(3600)  # Clean up every hour
    
    async def get_alerts(self, status: Optional[AlertStatus] = None, 
                        severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = list(self.alerts.values())
        
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    async def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.now()
            
            logger.info(f"Alert {alert_id} acknowledged by {user}")
    
    async def resolve_alert(self, alert_id: str, user: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            logger.info(f"Alert {alert_id} resolved by {user}")
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]),
            "acknowledged_alerts": len([a for a in self.alerts.values() if a.status == AlertStatus.ACKNOWLEDGED]),
            "resolved_alerts": len([a for a in self.alerts.values() if a.status == AlertStatus.RESOLVED]),
            "alerts_by_severity": {
                severity.value: len([a for a in self.alerts.values() if a.severity == severity])
                for severity in AlertSeverity
            },
            "monitoring_running": self.running,
            "last_check": datetime.now().isoformat()
        }
