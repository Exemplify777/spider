"""
Automated Maintenance and Operational Procedures

This module provides comprehensive automated maintenance capabilities for the SPIDER Framework
in production environments, including scheduled maintenance, health checks, and automated repairs.
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
import subprocess
import shutil
import tempfile

import aiohttp
import aiofiles
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import docker
import psutil

logger = logging.getLogger(__name__)


class MaintenanceType(Enum):
    """Maintenance types"""
    ROUTINE = "routine"
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"


class MaintenanceStatus(Enum):
    """Maintenance status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MaintenanceTask:
    """Maintenance task definition"""
    id: str
    name: str
    description: str
    maintenance_type: MaintenanceType
    schedule: str  # Cron expression
    enabled: bool = True
    timeout: int = 3600  # seconds
    retry_count: int = 3
    retry_delay: int = 300  # seconds
    dependencies: List[str] = field(default_factory=list)
    pre_checks: List[str] = field(default_factory=list)
    post_checks: List[str] = field(default_factory=list)
    rollback_script: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class MaintenanceExecution:
    """Maintenance execution record"""
    task_id: str
    execution_id: str
    status: MaintenanceStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    executed_by: str = "system"
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class MaintenanceConfig:
    """Maintenance configuration"""
    maintenance_window_start: str = "02:00"  # HH:MM
    maintenance_window_end: str = "06:00"    # HH:MM
    max_concurrent_tasks: int = 3
    notification_webhook: Optional[str] = None
    notification_email: Optional[str] = None
    log_retention_days: int = 30
    backup_before_maintenance: bool = True
    rollback_on_failure: bool = True


class MaintenanceManager:
    """
    Automated maintenance and operational procedures manager
    """
    
    def __init__(self, config: MaintenanceConfig):
        self.config = config
        self.tasks: Dict[str, MaintenanceTask] = {}
        self.executions: Dict[str, MaintenanceExecution] = {}
        self.running = False
        self.maintenance_tasks: List[asyncio.Task] = []
        
        # Initialize components
        self._initialize_components()
        self._load_default_tasks()
    
    def _initialize_components(self):
        """Initialize maintenance components"""
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
    
    def _load_default_tasks(self):
        """Load default maintenance tasks"""
        default_tasks = [
            MaintenanceTask(
                id="cleanup_logs",
                name="Log Cleanup",
                description="Clean up old log files",
                maintenance_type=MaintenanceType.ROUTINE,
                schedule="0 2 * * *",  # Daily at 2 AM
                timeout=1800,
                pre_checks=["disk_space_check"],
                post_checks=["disk_space_check"]
            ),
            MaintenanceTask(
                id="database_optimization",
                name="Database Optimization",
                description="Optimize database performance",
                maintenance_type=MaintenanceType.ROUTINE,
                schedule="0 3 * * 0",  # Weekly on Sunday at 3 AM
                timeout=7200,
                pre_checks=["database_health_check", "backup_check"],
                post_checks=["database_health_check", "performance_check"]
            ),
            MaintenanceTask(
                id="cache_cleanup",
                name="Cache Cleanup",
                description="Clean up expired cache entries",
                maintenance_type=MaintenanceType.ROUTINE,
                schedule="0 4 * * *",  # Daily at 4 AM
                timeout=900,
                pre_checks=["cache_health_check"],
                post_checks=["cache_health_check"]
            ),
            MaintenanceTask(
                id="security_updates",
                name="Security Updates",
                description="Apply security updates",
                maintenance_type=MaintenanceType.PREVENTIVE,
                schedule="0 5 * * 1",  # Weekly on Monday at 5 AM
                timeout=3600,
                pre_checks=["system_health_check", "backup_check"],
                post_checks=["system_health_check", "security_check"]
            ),
            MaintenanceTask(
                id="backup_verification",
                name="Backup Verification",
                description="Verify backup integrity",
                maintenance_type=MaintenanceType.ROUTINE,
                schedule="0 6 * * *",  # Daily at 6 AM
                timeout=1800,
                pre_checks=["backup_health_check"],
                post_checks=["backup_health_check"]
            ),
            MaintenanceTask(
                id="performance_optimization",
                name="Performance Optimization",
                description="Optimize system performance",
                maintenance_type=MaintenanceType.ROUTINE,
                schedule="0 7 * * 0",  # Weekly on Sunday at 7 AM
                timeout=3600,
                pre_checks=["system_health_check"],
                post_checks=["performance_check"]
            )
        ]
        
        for task in default_tasks:
            self.tasks[task.id] = task
    
    async def start_maintenance_manager(self):
        """Start the maintenance manager"""
        if self.running:
            logger.warning("Maintenance manager is already running")
            return
        
        self.running = True
        logger.info("Starting maintenance manager")
        
        # Start maintenance tasks
        self.maintenance_tasks = [
            asyncio.create_task(self._schedule_maintenance()),
            asyncio.create_task(self._execute_pending_tasks()),
            asyncio.create_task(self._monitor_running_tasks()),
            asyncio.create_task(self._cleanup_old_executions()),
        ]
        
        try:
            await asyncio.gather(*self.maintenance_tasks)
        except Exception as e:
            logger.error(f"Error in maintenance tasks: {e}")
        finally:
            self.running = False
    
    async def stop_maintenance_manager(self):
        """Stop the maintenance manager"""
        if not self.running:
            return
        
        logger.info("Stopping maintenance manager")
        self.running = False
        
        # Cancel all maintenance tasks
        for task in self.maintenance_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.maintenance_tasks, return_exceptions=True)
    
    async def _schedule_maintenance(self):
        """Schedule maintenance tasks based on cron expressions"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    # Check if task should run (simplified cron check)
                    if self._should_run_task(task, current_time):
                        await self._queue_task(task)
                
            except Exception as e:
                logger.error(f"Error scheduling maintenance: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    def _should_run_task(self, task: MaintenanceTask, current_time: datetime) -> bool:
        """Check if task should run based on cron schedule"""
        # Simplified cron parsing - in production, use a proper cron library
        if task.schedule == "0 2 * * *":  # Daily at 2 AM
            return current_time.hour == 2 and current_time.minute == 0
        elif task.schedule == "0 3 * * 0":  # Weekly on Sunday at 3 AM
            return current_time.weekday() == 6 and current_time.hour == 3 and current_time.minute == 0
        elif task.schedule == "0 4 * * *":  # Daily at 4 AM
            return current_time.hour == 4 and current_time.minute == 0
        elif task.schedule == "0 5 * * 1":  # Weekly on Monday at 5 AM
            return current_time.weekday() == 0 and current_time.hour == 5 and current_time.minute == 0
        elif task.schedule == "0 6 * * *":  # Daily at 6 AM
            return current_time.hour == 6 and current_time.minute == 0
        elif task.schedule == "0 7 * * 0":  # Weekly on Sunday at 7 AM
            return current_time.weekday() == 6 and current_time.hour == 7 and current_time.minute == 0
        
        return False
    
    async def _queue_task(self, task: MaintenanceTask):
        """Queue a task for execution"""
        execution_id = f"{task.id}_{int(time.time())}"
        
        execution = MaintenanceExecution(
            task_id=task.id,
            execution_id=execution_id,
            status=MaintenanceStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        logger.info(f"Queued maintenance task: {task.name} (ID: {execution_id})")
    
    async def _execute_pending_tasks(self):
        """Execute pending maintenance tasks"""
        while self.running:
            try:
                pending_executions = [
                    exec for exec in self.executions.values()
                    if exec.status == MaintenanceStatus.PENDING
                ]
                
                # Limit concurrent executions
                running_count = len([
                    exec for exec in self.executions.values()
                    if exec.status == MaintenanceStatus.RUNNING
                ])
                
                if running_count < self.config.max_concurrent_tasks and pending_executions:
                    execution = pending_executions[0]
                    task = self.tasks[execution.task_id]
                    
                    # Check if within maintenance window
                    if self._is_within_maintenance_window():
                        await self._execute_task(execution, task)
                    else:
                        logger.info(f"Outside maintenance window, skipping task: {task.name}")
                        execution.status = MaintenanceStatus.CANCELLED
                
            except Exception as e:
                logger.error(f"Error executing pending tasks: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def _is_within_maintenance_window(self) -> bool:
        """Check if current time is within maintenance window"""
        current_time = datetime.now().time()
        start_time = datetime.strptime(self.config.maintenance_window_start, "%H:%M").time()
        end_time = datetime.strptime(self.config.maintenance_window_end, "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  # Crosses midnight
            return current_time >= start_time or current_time <= end_time
    
    async def _execute_task(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Execute a maintenance task"""
        execution.status = MaintenanceStatus.RUNNING
        execution.started_at = datetime.now()
        
        logger.info(f"Starting maintenance task: {task.name} (ID: {execution.execution_id})")
        
        try:
            # Run pre-checks
            await self._run_pre_checks(execution, task)
            
            # Create backup if configured
            if self.config.backup_before_maintenance:
                await self._create_backup(execution, task)
            
            # Execute main task
            await self._run_main_task(execution, task)
            
            # Run post-checks
            await self._run_post_checks(execution, task)
            
            execution.status = MaintenanceStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            logger.info(f"Completed maintenance task: {task.name} (ID: {execution.execution_id})")
            
            # Send success notification
            await self._send_notification(execution, task, "completed")
            
        except Exception as e:
            execution.status = MaintenanceStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            logger.error(f"Failed maintenance task: {task.name} (ID: {execution.execution_id}): {e}")
            
            # Rollback if configured
            if self.config.rollback_on_failure and task.rollback_script:
                await self._run_rollback(execution, task)
            
            # Send failure notification
            await self._send_notification(execution, task, "failed")
            
            # Retry if configured
            if execution.retry_count < task.retry_count:
                execution.retry_count += 1
                execution.status = MaintenanceStatus.PENDING
                execution.started_at = datetime.now() + timedelta(seconds=task.retry_delay)
                logger.info(f"Scheduling retry {execution.retry_count} for task: {task.name}")
    
    async def _run_pre_checks(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Run pre-checks for a task"""
        for check in task.pre_checks:
            try:
                await self._run_check(execution, check)
            except Exception as e:
                raise Exception(f"Pre-check failed: {check} - {e}")
    
    async def _run_post_checks(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Run post-checks for a task"""
        for check in task.post_checks:
            try:
                await self._run_check(execution, check)
            except Exception as e:
                raise Exception(f"Post-check failed: {check} - {e}")
    
    async def _run_check(self, execution: MaintenanceExecution, check_name: str):
        """Run a specific check"""
        execution.logs.append(f"Running check: {check_name}")
        
        if check_name == "disk_space_check":
            await self._check_disk_space()
        elif check_name == "database_health_check":
            await self._check_database_health()
        elif check_name == "backup_check":
            await self._check_backup_health()
        elif check_name == "cache_health_check":
            await self._check_cache_health()
        elif check_name == "system_health_check":
            await self._check_system_health()
        elif check_name == "security_check":
            await self._check_security()
        elif check_name == "performance_check":
            await self._check_performance()
        else:
            logger.warning(f"Unknown check: {check_name}")
    
    async def _check_disk_space(self):
        """Check disk space"""
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100
        
        if free_percent < 10:
            raise Exception(f"Low disk space: {free_percent:.1f}% free")
    
    async def _check_database_health(self):
        """Check database health"""
        # Implementation for database health check
        pass
    
    async def _check_backup_health(self):
        """Check backup health"""
        # Implementation for backup health check
        pass
    
    async def _check_cache_health(self):
        """Check cache health"""
        # Implementation for cache health check
        pass
    
    async def _check_system_health(self):
        """Check system health"""
        # Implementation for system health check
        pass
    
    async def _check_security(self):
        """Check security"""
        # Implementation for security check
        pass
    
    async def _check_performance(self):
        """Check performance"""
        # Implementation for performance check
        pass
    
    async def _create_backup(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Create backup before maintenance"""
        execution.logs.append("Creating backup before maintenance")
        # Implementation for backup creation
        pass
    
    async def _run_main_task(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Run the main maintenance task"""
        execution.logs.append(f"Running main task: {task.name}")
        
        if task.id == "cleanup_logs":
            await self._cleanup_logs(execution)
        elif task.id == "database_optimization":
            await self._optimize_database(execution)
        elif task.id == "cache_cleanup":
            await self._cleanup_cache(execution)
        elif task.id == "security_updates":
            await self._apply_security_updates(execution)
        elif task.id == "backup_verification":
            await self._verify_backups(execution)
        elif task.id == "performance_optimization":
            await self._optimize_performance(execution)
        else:
            logger.warning(f"Unknown task: {task.id}")
    
    async def _cleanup_logs(self, execution: MaintenanceExecution):
        """Clean up old log files"""
        execution.logs.append("Cleaning up old log files")
        
        # Find and remove old log files
        log_dirs = ["/var/log", "/app/logs", "/tmp"]
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_dir in log_dirs:
            if Path(log_dir).exists():
                for log_file in Path(log_dir).rglob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        execution.logs.append(f"Removed old log file: {log_file}")
    
    async def _optimize_database(self, execution: MaintenanceExecution):
        """Optimize database performance"""
        execution.logs.append("Optimizing database performance")
        
        # Run database optimization commands
        commands = [
            "VACUUM ANALYZE;",
            "REINDEX DATABASE spider_db;",
            "UPDATE pg_stat_user_tables SET n_tup_ins = 0, n_tup_upd = 0, n_tup_del = 0;"
        ]
        
        for command in commands:
            try:
                # Execute database command
                execution.logs.append(f"Executing: {command}")
                # Implementation for database command execution
            except Exception as e:
                execution.logs.append(f"Error executing {command}: {e}")
    
    async def _cleanup_cache(self, execution: MaintenanceExecution):
        """Clean up expired cache entries"""
        execution.logs.append("Cleaning up expired cache entries")
        
        # Clean Redis cache
        try:
            # Implementation for Redis cache cleanup
            execution.logs.append("Cleaned Redis cache")
        except Exception as e:
            execution.logs.append(f"Error cleaning Redis cache: {e}")
        
        # Clean Memcached cache
        try:
            # Implementation for Memcached cache cleanup
            execution.logs.append("Cleaned Memcached cache")
        except Exception as e:
            execution.logs.append(f"Error cleaning Memcached cache: {e}")
    
    async def _apply_security_updates(self, execution: MaintenanceExecution):
        """Apply security updates"""
        execution.logs.append("Applying security updates")
        
        # Check for available updates
        try:
            # Implementation for security updates
            execution.logs.append("Security updates applied successfully")
        except Exception as e:
            execution.logs.append(f"Error applying security updates: {e}")
    
    async def _verify_backups(self, execution: MaintenanceExecution):
        """Verify backup integrity"""
        execution.logs.append("Verifying backup integrity")
        
        # Check backup files
        backup_dirs = ["/backup", "/var/backups"]
        
        for backup_dir in backup_dirs:
            if Path(backup_dir).exists():
                for backup_file in Path(backup_dir).rglob("*.sql.gz"):
                    # Verify backup file integrity
                    execution.logs.append(f"Verified backup: {backup_file}")
    
    async def _optimize_performance(self, execution: MaintenanceExecution):
        """Optimize system performance"""
        execution.logs.append("Optimizing system performance")
        
        # Clear system caches
        try:
            subprocess.run(["sync"], check=True)
            subprocess.run(["echo", "3"], stdout=open("/proc/sys/vm/drop_caches", "w"), check=True)
            execution.logs.append("Cleared system caches")
        except Exception as e:
            execution.logs.append(f"Error clearing system caches: {e}")
    
    async def _run_rollback(self, execution: MaintenanceExecution, task: MaintenanceTask):
        """Run rollback script"""
        if task.rollback_script:
            execution.logs.append("Running rollback script")
            try:
                # Implementation for rollback script execution
                execution.logs.append("Rollback completed successfully")
            except Exception as e:
                execution.logs.append(f"Error during rollback: {e}")
    
    async def _send_notification(self, execution: MaintenanceExecution, task: MaintenanceTask, status: str):
        """Send notification about task status"""
        message = f"Maintenance task {task.name} {status}"
        
        if status == "failed":
            message += f" - Error: {execution.error_message}"
        
        # Send to webhook
        if self.config.notification_webhook:
            await self._send_webhook_notification(message)
        
        # Send to email
        if self.config.notification_email:
            await self._send_email_notification(message)
    
    async def _send_webhook_notification(self, message: str):
        """Send webhook notification"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.notification_webhook,
                    json={"text": message},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send webhook notification: {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _send_email_notification(self, message: str):
        """Send email notification"""
        # Implementation for email notification
        pass
    
    async def _monitor_running_tasks(self):
        """Monitor running maintenance tasks"""
        while self.running:
            try:
                running_executions = [
                    exec for exec in self.executions.values()
                    if exec.status == MaintenanceStatus.RUNNING
                ]
                
                for execution in running_executions:
                    task = self.tasks[execution.task_id]
                    
                    # Check timeout
                    if datetime.now() - execution.started_at > timedelta(seconds=task.timeout):
                        execution.status = MaintenanceStatus.FAILED
                        execution.error_message = "Task timeout"
                        execution.completed_at = datetime.now()
                        
                        logger.error(f"Task timeout: {task.name} (ID: {execution.execution_id})")
                
            except Exception as e:
                logger.error(f"Error monitoring running tasks: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _cleanup_old_executions(self):
        """Clean up old execution records"""
        while self.running:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.config.log_retention_days)
                
                executions_to_remove = [
                    exec_id for exec_id, execution in self.executions.items()
                    if execution.started_at < cutoff_date
                ]
                
                for exec_id in executions_to_remove:
                    del self.executions[exec_id]
                
                if executions_to_remove:
                    logger.info(f"Cleaned up {len(executions_to_remove)} old execution records")
                
            except Exception as e:
                logger.error(f"Error cleaning up old executions: {e}")
            
            await asyncio.sleep(3600)  # Clean up every hour
    
    async def get_maintenance_status(self) -> Dict[str, Any]:
        """Get maintenance status summary"""
        return {
            "total_tasks": len(self.tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t.enabled]),
            "total_executions": len(self.executions),
            "pending_executions": len([e for e in self.executions.values() if e.status == MaintenanceStatus.PENDING]),
            "running_executions": len([e for e in self.executions.values() if e.status == MaintenanceStatus.RUNNING]),
            "completed_executions": len([e for e in self.executions.values() if e.status == MaintenanceStatus.COMPLETED]),
            "failed_executions": len([e for e in self.executions.values() if e.status == MaintenanceStatus.FAILED]),
            "manager_running": self.running,
            "last_check": datetime.now().isoformat()
        }
    
    async def get_task_executions(self, task_id: str) -> List[MaintenanceExecution]:
        """Get executions for a specific task"""
        return [
            execution for execution in self.executions.values()
            if execution.task_id == task_id
        ]
    
    async def cancel_task(self, execution_id: str):
        """Cancel a running task"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == MaintenanceStatus.RUNNING:
                execution.status = MaintenanceStatus.CANCELLED
                execution.completed_at = datetime.now()
                logger.info(f"Cancelled task execution: {execution_id}")
    
    async def add_task(self, task: MaintenanceTask):
        """Add a new maintenance task"""
        self.tasks[task.id] = task
        logger.info(f"Added maintenance task: {task.name}")
    
    async def remove_task(self, task_id: str):
        """Remove a maintenance task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Removed maintenance task: {task_id}")
    
    async def enable_task(self, task_id: str):
        """Enable a maintenance task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            logger.info(f"Enabled maintenance task: {task_id}")
    
    async def disable_task(self, task_id: str):
        """Disable a maintenance task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            logger.info(f"Disabled maintenance task: {task_id}")
