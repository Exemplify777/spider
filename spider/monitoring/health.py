"""Health monitoring for SPIDER framework."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..core.exceptions import MonitoringError
from ..core.logger import get_logger


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration: float
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: float
    checks: List[HealthCheck]
    uptime: float
    version: str
    
    @property
    def healthy_checks(self) -> int:
        """Number of healthy checks."""
        return len([c for c in self.checks if c.status == HealthStatus.HEALTHY])
    
    @property
    def total_checks(self) -> int:
        """Total number of checks."""
        return len(self.checks)
    
    @property
    def health_percentage(self) -> float:
        """Health percentage (0-100)."""
        if self.total_checks == 0:
            return 100.0
        return (self.healthy_checks / self.total_checks) * 100.0


class BaseHealthChecker(ABC):
    """Base class for health checkers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize health checker.
        
        Args:
            name: Health checker name
            config: Health checker configuration
        """
        self.name = name
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.enabled = config.get('enabled', True)
        self.timeout = config.get('timeout', 5.0)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
    
    @abstractmethod
    async def check_health(self) -> HealthCheck:
        """Perform health check.
        
        Returns:
            Health check result
        """
        pass
    
    async def run_check(self) -> HealthCheck:
        """Run health check with retry logic."""
        if not self.enabled:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="Health checker disabled",
                timestamp=time.time(),
                duration=0.0
            )
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                check = await asyncio.wait_for(
                    self.check_health(),
                    timeout=self.timeout
                )
                check.duration = time.time() - start_time
                return check
            except asyncio.TimeoutError:
                last_error = f"Health check timeout after {self.timeout}s"
                self.logger.warning(f"Health check {self.name} timeout (attempt {attempt + 1})")
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Health check {self.name} failed (attempt {attempt + 1}): {e}")
            
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay)
        
        # All attempts failed
        return HealthCheck(
            name=self.name,
            status=HealthStatus.UNHEALTHY,
            message=f"Health check failed after {self.retry_attempts} attempts: {last_error}",
            timestamp=time.time(),
            duration=time.time() - start_time
        )


class DatabaseHealthChecker(BaseHealthChecker):
    """Database health checker."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database health checker."""
        super().__init__("database", config)
        self.connection_url = config.get('connection_url')
    
    async def check_health(self) -> HealthCheck:
        """Check database health."""
        try:
            # Import database connection based on URL
            if self.connection_url.startswith('sqlite'):
                import sqlite3
                conn = sqlite3.connect(self.connection_url.replace('sqlite:///', ''))
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                conn.close()
            elif self.connection_url.startswith('postgresql'):
                import psycopg2
                conn = psycopg2.connect(self.connection_url)
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                conn.close()
            else:
                raise ValueError(f"Unsupported database: {self.connection_url}")
            
            return HealthCheck(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                timestamp=time.time(),
                duration=0.0,
                details={'connection_url': self.connection_url}
            )
            
        except Exception as e:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
                timestamp=time.time(),
                duration=0.0,
                details={'error': str(e)}
            )


class RedisHealthChecker(BaseHealthChecker):
    """Redis health checker."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis health checker."""
        super().__init__("redis", config)
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
    
    async def check_health(self) -> HealthCheck:
        """Check Redis health."""
        try:
            import redis.asyncio as redis
            client = redis.from_url(self.redis_url)
            
            # Test connection
            await client.ping()
            
            # Get info
            info = await client.info()
            
            await client.close()
            
            return HealthCheck(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                timestamp=time.time(),
                duration=0.0,
                details={
                    'redis_version': info.get('redis_version'),
                    'used_memory': info.get('used_memory'),
                    'connected_clients': info.get('connected_clients')
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {e}",
                timestamp=time.time(),
                duration=0.0,
                details={'error': str(e)}
            )


class ProxyHealthChecker(BaseHealthChecker):
    """Proxy health checker."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize proxy health checker."""
        super().__init__("proxy", config)
        self.proxy_manager = config.get('proxy_manager')
    
    async def check_health(self) -> HealthCheck:
        """Check proxy health."""
        if not self.proxy_manager:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="Proxy manager not available",
                timestamp=time.time(),
                duration=0.0
            )
        
        try:
            # Get proxy from manager
            proxy = await self.proxy_manager.get_proxy()
            
            if proxy is None:
                return HealthCheck(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="No healthy proxies available",
                    timestamp=time.time(),
                    duration=0.0
                )
            
            # Test proxy with simple request
            import httpx
            async with httpx.AsyncClient(proxies=proxy.url, timeout=5.0) as client:
                response = await client.get("http://httpbin.org/ip")
                
                if response.status_code == 200:
                    return HealthCheck(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        message=f"Proxy {proxy.host}:{proxy.port} is healthy",
                        timestamp=time.time(),
                        duration=0.0,
                        details={
                            'proxy_host': proxy.host,
                            'proxy_port': proxy.port,
                            'success_rate': proxy.success_rate
                        }
                    )
                else:
                    return HealthCheck(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Proxy test failed with status {response.status_code}",
                        timestamp=time.time(),
                        duration=0.0
                    )
                    
        except Exception as e:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Proxy health check failed: {e}",
                timestamp=time.time(),
                duration=0.0,
                details={'error': str(e)}
            )


class SystemResourceHealthChecker(BaseHealthChecker):
    """System resource health checker."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize system resource health checker."""
        super().__init__("system_resources", config)
        self.max_cpu_percent = config.get('max_cpu_percent', 90)
        self.max_memory_percent = config.get('max_memory_percent', 90)
        self.max_disk_percent = config.get('max_disk_percent', 90)
    
    async def check_health(self) -> HealthCheck:
        """Check system resource health."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check thresholds
            issues = []
            if cpu_percent > self.max_cpu_percent:
                issues.append(f"CPU usage {cpu_percent}% exceeds threshold {self.max_cpu_percent}%")
            
            if memory.percent > self.max_memory_percent:
                issues.append(f"Memory usage {memory.percent}% exceeds threshold {self.max_memory_percent}%")
            
            if disk.percent > self.max_disk_percent:
                issues.append(f"Disk usage {disk.percent}% exceeds threshold {self.max_disk_percent}%")
            
            if issues:
                status = HealthStatus.UNHEALTHY
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "System resources within normal limits"
            
            return HealthCheck(
                name=self.name,
                status=status,
                message=message,
                timestamp=time.time(),
                duration=0.0,
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available': memory.available,
                    'disk_free': disk.free
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"System resource check failed: {e}",
                timestamp=time.time(),
                duration=0.0,
                details={'error': str(e)}
            )


class HealthChecker:
    """Main health checker class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize health checker.
        
        Args:
            config: Health checker configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.enabled = config.get('enabled', True)
        self.checkers: List[BaseHealthChecker] = []
        self.start_time = time.time()
        self.version = config.get('version', '1.0.0')
        
        if not self.enabled:
            return
        
        # Initialize health checkers
        self._initialize_checkers()
    
    def _initialize_checkers(self) -> None:
        """Initialize health checkers based on configuration."""
        checker_configs = self.config.get('checkers', {})
        
        # Database checker
        if 'database' in checker_configs:
            self.checkers.append(DatabaseHealthChecker(checker_configs['database']))
        
        # Redis checker
        if 'redis' in checker_configs:
            self.checkers.append(RedisHealthChecker(checker_configs['redis']))
        
        # Proxy checker
        if 'proxy' in checker_configs:
            self.checkers.append(ProxyHealthChecker(checker_configs['proxy']))
        
        # System resources checker
        if 'system_resources' in checker_configs:
            self.checkers.append(SystemResourceHealthChecker(checker_configs['system_resources']))
    
    async def check_health(self) -> SystemHealth:
        """Perform comprehensive health check.
        
        Returns:
            Overall system health status
        """
        if not self.enabled:
            return SystemHealth(
                status=HealthStatus.UNKNOWN,
                timestamp=time.time(),
                checks=[],
                uptime=time.time() - self.start_time,
                version=self.version
            )
        
        # Run all health checks in parallel
        check_tasks = [checker.run_check() for checker in self.checkers]
        checks = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        processed_checks = []
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                processed_checks.append(HealthCheck(
                    name=f"checker_{i}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {check}",
                    timestamp=time.time(),
                    duration=0.0
                ))
            else:
                processed_checks.append(check)
        
        # Determine overall status
        unhealthy_checks = [c for c in processed_checks if c.status == HealthStatus.UNHEALTHY]
        degraded_checks = [c for c in processed_checks if c.status == HealthStatus.DEGRADED]
        
        if unhealthy_checks:
            status = HealthStatus.UNHEALTHY
        elif degraded_checks:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return SystemHealth(
            status=status,
            timestamp=time.time(),
            checks=processed_checks,
            uptime=time.time() - self.start_time,
            version=self.version
        )
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for monitoring."""
        health = await self.check_health()
        
        return {
            'status': health.status.value,
            'timestamp': health.timestamp,
            'uptime': health.uptime,
            'version': health.version,
            'health_percentage': health.health_percentage,
            'healthy_checks': health.healthy_checks,
            'total_checks': health.total_checks,
            'checks': [
                {
                    'name': check.name,
                    'status': check.status.value,
                    'message': check.message,
                    'duration': check.duration,
                    'details': check.details
                }
                for check in health.checks
            ]
        }
    
    def add_checker(self, checker: BaseHealthChecker) -> None:
        """Add custom health checker.
        
        Args:
            checker: Health checker instance
        """
        self.checkers.append(checker)
    
    def remove_checker(self, name: str) -> None:
        """Remove health checker by name.
        
        Args:
            name: Health checker name
        """
        self.checkers = [c for c in self.checkers if c.name != name]
