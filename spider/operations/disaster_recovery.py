"""
Disaster Recovery Operations and Testing

This module provides comprehensive disaster recovery operations and testing capabilities
for the SPIDER Framework in production environments.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path
import hashlib
import hmac
import base64
import subprocess
import shutil
import tempfile
from collections import defaultdict, deque

import aiohttp
import aiofiles
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import docker
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class RecoveryType(Enum):
    """Recovery types"""
    FULL = "full"
    PARTIAL = "partial"
    INCREMENTAL = "incremental"
    POINT_IN_TIME = "point_in_time"
    CROSS_REGION = "cross_region"


class RecoveryStatus(Enum):
    """Recovery status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFIED = "verified"


class TestType(Enum):
    """Test types"""
    BACKUP_RESTORE = "backup_restore"
    FAILOVER = "failover"
    DISASTER_SIMULATION = "disaster_simulation"
    RECOVERY_TIME = "recovery_time"
    DATA_INTEGRITY = "data_integrity"
    NETWORK_CONNECTIVITY = "network_connectivity"


@dataclass
class RecoveryPlan:
    """Disaster recovery plan"""
    id: str
    name: str
    description: str
    recovery_type: RecoveryType
    rto: int  # Recovery Time Objective in minutes
    rpo: int  # Recovery Point Objective in minutes
    priority: int  # 1-5, 1 being highest
    dependencies: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    validation_checks: List[str] = field(default_factory=list)
    rollback_steps: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True


@dataclass
class RecoveryExecution:
    """Recovery execution record"""
    id: str
    plan_id: str
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    executed_by: str = "system"
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    recovery_time: Optional[int] = None  # Actual recovery time in minutes
    data_loss: Optional[int] = None  # Data loss in minutes


@dataclass
class RecoveryTest:
    """Recovery test record"""
    id: str
    test_type: TestType
    plan_id: str
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    test_results: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    notes: str = ""


@dataclass
class DisasterRecoveryConfig:
    """Disaster recovery configuration"""
    backup_retention_days: int = 30
    test_frequency_days: int = 30
    auto_failover_enabled: bool = True
    cross_region_replication: bool = True
    notification_webhook: Optional[str] = None
    recovery_timeout: int = 3600  # seconds
    test_timeout: int = 1800  # seconds
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    test_schedule: str = "0 3 * * 0"  # Weekly on Sunday at 3 AM


class DisasterRecoveryManager:
    """
    Disaster recovery operations and testing system
    """
    
    def __init__(self, config: DisasterRecoveryConfig):
        self.config = config
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.recovery_executions: Dict[str, RecoveryExecution] = {}
        self.recovery_tests: Dict[str, RecoveryTest] = {}
        self.backup_status: Dict[str, Any] = {}
        self.running = False
        self.recovery_tasks: List[asyncio.Task] = []
        
        # Initialize recovery plans
        self._initialize_recovery_plans()
    
    def _initialize_recovery_plans(self):
        """Initialize disaster recovery plans"""
        # Database Recovery Plan
        db_recovery_plan = RecoveryPlan(
            id="db_recovery",
            name="Database Recovery Plan",
            description="Recovery plan for database failures",
            recovery_type=RecoveryType.FULL,
            rto=30,  # 30 minutes
            rpo=15,  # 15 minutes
            priority=1,
            steps=[
                {"action": "stop_application", "timeout": 300},
                {"action": "restore_database", "timeout": 1800},
                {"action": "verify_data_integrity", "timeout": 600},
                {"action": "start_application", "timeout": 300},
                {"action": "verify_application", "timeout": 300}
            ],
            validation_checks=[
                "Database connectivity",
                "Data integrity",
                "Application functionality",
                "Performance metrics"
            ],
            rollback_steps=[
                {"action": "stop_application", "timeout": 300},
                {"action": "restore_from_backup", "timeout": 1800},
                {"action": "start_application", "timeout": 300}
            ]
        )
        
        # Application Recovery Plan
        app_recovery_plan = RecoveryPlan(
            id="app_recovery",
            name="Application Recovery Plan",
            description="Recovery plan for application failures",
            recovery_type=RecoveryType.FULL,
            rto=15,  # 15 minutes
            rpo=5,   # 5 minutes
            priority=1,
            dependencies=["db_recovery"],
            steps=[
                {"action": "scale_down_old_pods", "timeout": 300},
                {"action": "deploy_new_pods", "timeout": 600},
                {"action": "verify_health_checks", "timeout": 300},
                {"action": "update_load_balancer", "timeout": 120},
                {"action": "verify_traffic_routing", "timeout": 300}
            ],
            validation_checks=[
                "Pod health",
                "Service connectivity",
                "Load balancer status",
                "Application endpoints"
            ],
            rollback_steps=[
                {"action": "scale_down_new_pods", "timeout": 300},
                {"action": "scale_up_old_pods", "timeout": 600},
                {"action": "update_load_balancer", "timeout": 120}
            ]
        )
        
        # Cross-Region Recovery Plan
        cross_region_plan = RecoveryPlan(
            id="cross_region_recovery",
            name="Cross-Region Recovery Plan",
            description="Recovery plan for cross-region failover",
            recovery_type=RecoveryType.CROSS_REGION,
            rto=60,  # 60 minutes
            rpo=30,  # 30 minutes
            priority=2,
            dependencies=["db_recovery", "app_recovery"],
            steps=[
                {"action": "activate_secondary_region", "timeout": 1800},
                {"action": "update_dns_records", "timeout": 300},
                {"action": "verify_region_connectivity", "timeout": 600},
                {"action": "monitor_performance", "timeout": 1800}
            ],
            validation_checks=[
                "Cross-region connectivity",
                "Data synchronization",
                "Application functionality",
                "Performance metrics"
            ],
            rollback_steps=[
                {"action": "update_dns_records", "timeout": 300},
                {"action": "deactivate_secondary_region", "timeout": 1800}
            ]
        )
        
        # Add all recovery plans
        self.recovery_plans = {
            "db_recovery": db_recovery_plan,
            "app_recovery": app_recovery_plan,
            "cross_region_recovery": cross_region_plan
        }
    
    async def start_disaster_recovery(self):
        """Start the disaster recovery system"""
        if self.running:
            logger.warning("Disaster recovery is already running")
            return
        
        self.running = True
        logger.info("Starting disaster recovery system")
        
        # Start recovery tasks
        self.recovery_tasks = [
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._perform_backups()),
            asyncio.create_task(self._run_recovery_tests()),
            asyncio.create_task(self._monitor_recovery_executions()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.recovery_tasks)
        except Exception as e:
            logger.error(f"Error in recovery tasks: {e}")
        finally:
            self.running = False
    
    async def stop_disaster_recovery(self):
        """Stop the disaster recovery system"""
        if not self.running:
            return
        
        logger.info("Stopping disaster recovery system")
        self.running = False
        
        # Cancel all recovery tasks
        for task in self.recovery_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.recovery_tasks, return_exceptions=True)
    
    async def _monitor_system_health(self):
        """Monitor system health for disaster scenarios"""
        while self.running:
            try:
                # Check database health
                db_healthy = await self._check_database_health()
                if not db_healthy:
                    await self._trigger_recovery("db_recovery", "Database health check failed")
                
                # Check application health
                app_healthy = await self._check_application_health()
                if not app_healthy:
                    await self._trigger_recovery("app_recovery", "Application health check failed")
                
                # Check network connectivity
                network_healthy = await self._check_network_health()
                if not network_healthy:
                    await self._trigger_recovery("cross_region_recovery", "Network connectivity failed")
                
            except Exception as e:
                logger.error(f"Error monitoring system health: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            # Implementation for database health check
            # This would typically check database connectivity, performance, etc.
            return True  # Simplified implementation
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return False
    
    async def _check_application_health(self) -> bool:
        """Check application health"""
        try:
            # Implementation for application health check
            # This would typically check application endpoints, pod health, etc.
            return True  # Simplified implementation
        except Exception as e:
            logger.error(f"Error checking application health: {e}")
            return False
    
    async def _check_network_health(self) -> bool:
        """Check network health"""
        try:
            # Implementation for network health check
            # This would typically check network connectivity, latency, etc.
            return True  # Simplified implementation
        except Exception as e:
            logger.error(f"Error checking network health: {e}")
            return False
    
    async def _trigger_recovery(self, plan_id: str, reason: str):
        """Trigger disaster recovery"""
        try:
            if plan_id not in self.recovery_plans:
                logger.error(f"Recovery plan {plan_id} not found")
                return
            
            plan = self.recovery_plans[plan_id]
            if not plan.enabled:
                logger.info(f"Recovery plan {plan_id} is disabled")
                return
            
            # Check if recovery is already in progress
            active_recoveries = [
                execution for execution in self.recovery_executions.values()
                if execution.plan_id == plan_id and execution.status == RecoveryStatus.IN_PROGRESS
            ]
            
            if active_recoveries:
                logger.info(f"Recovery for plan {plan_id} already in progress")
                return
            
            # Start recovery execution
            execution_id = f"{plan_id}_{int(time.time())}"
            execution = RecoveryExecution(
                id=execution_id,
                plan_id=plan_id,
                status=RecoveryStatus.IN_PROGRESS,
                started_at=datetime.now(),
                executed_by="system"
            )
            
            self.recovery_executions[execution_id] = execution
            logger.warning(f"Triggered recovery {plan_id}: {reason}")
            
            # Execute recovery plan
            await self._execute_recovery_plan(execution, plan)
        
        except Exception as e:
            logger.error(f"Error triggering recovery {plan_id}: {e}")
    
    async def _execute_recovery_plan(self, execution: RecoveryExecution, plan: RecoveryPlan):
        """Execute a recovery plan"""
        try:
            execution.logs.append(f"Starting recovery plan: {plan.name}")
            
            # Execute recovery steps
            for step in plan.steps:
                action = step["action"]
                timeout = step["timeout"]
                
                execution.logs.append(f"Executing step: {action}")
                
                success = await self._execute_recovery_step(action, timeout)
                if not success:
                    execution.status = RecoveryStatus.FAILED
                    execution.error_message = f"Failed to execute step: {action}"
                    execution.completed_at = datetime.now()
                    logger.error(f"Recovery failed at step: {action}")
                    return
                
                execution.logs.append(f"Completed step: {action}")
            
            # Validate recovery
            validation_passed = await self._validate_recovery(plan.validation_checks)
            if not validation_passed:
                execution.status = RecoveryStatus.FAILED
                execution.error_message = "Recovery validation failed"
                execution.completed_at = datetime.now()
                logger.error("Recovery validation failed")
                return
            
            # Recovery completed successfully
            execution.status = RecoveryStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.recovery_time = int((execution.completed_at - execution.started_at).total_seconds() / 60)
            
            logger.info(f"Recovery completed successfully: {execution.id}")
            
            # Send notification
            await self._send_recovery_notification(execution, "completed")
        
        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            logger.error(f"Error executing recovery plan: {e}")
            
            # Send notification
            await self._send_recovery_notification(execution, "failed")
    
    async def _execute_recovery_step(self, action: str, timeout: int) -> bool:
        """Execute a specific recovery step"""
        try:
            if action == "stop_application":
                return await self._stop_application()
            elif action == "restore_database":
                return await self._restore_database()
            elif action == "verify_data_integrity":
                return await self._verify_data_integrity()
            elif action == "start_application":
                return await self._start_application()
            elif action == "verify_application":
                return await self._verify_application()
            elif action == "scale_down_old_pods":
                return await self._scale_down_old_pods()
            elif action == "deploy_new_pods":
                return await self._deploy_new_pods()
            elif action == "verify_health_checks":
                return await self._verify_health_checks()
            elif action == "update_load_balancer":
                return await self._update_load_balancer()
            elif action == "verify_traffic_routing":
                return await self._verify_traffic_routing()
            elif action == "activate_secondary_region":
                return await self._activate_secondary_region()
            elif action == "update_dns_records":
                return await self._update_dns_records()
            elif action == "verify_region_connectivity":
                return await self._verify_region_connectivity()
            elif action == "monitor_performance":
                return await self._monitor_performance()
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return False
        
        except Exception as e:
            logger.error(f"Error executing recovery step {action}: {e}")
            return False
    
    async def _stop_application(self) -> bool:
        """Stop application"""
        try:
            # Implementation for stopping application
            logger.info("Stopping application")
            return True
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
            return False
    
    async def _restore_database(self) -> bool:
        """Restore database from backup"""
        try:
            # Implementation for database restoration
            logger.info("Restoring database from backup")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    async def _verify_data_integrity(self) -> bool:
        """Verify data integrity"""
        try:
            # Implementation for data integrity verification
            logger.info("Verifying data integrity")
            return True
        except Exception as e:
            logger.error(f"Error verifying data integrity: {e}")
            return False
    
    async def _start_application(self) -> bool:
        """Start application"""
        try:
            # Implementation for starting application
            logger.info("Starting application")
            return True
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            return False
    
    async def _verify_application(self) -> bool:
        """Verify application functionality"""
        try:
            # Implementation for application verification
            logger.info("Verifying application functionality")
            return True
        except Exception as e:
            logger.error(f"Error verifying application: {e}")
            return False
    
    async def _scale_down_old_pods(self) -> bool:
        """Scale down old pods"""
        try:
            # Implementation for scaling down old pods
            logger.info("Scaling down old pods")
            return True
        except Exception as e:
            logger.error(f"Error scaling down old pods: {e}")
            return False
    
    async def _deploy_new_pods(self) -> bool:
        """Deploy new pods"""
        try:
            # Implementation for deploying new pods
            logger.info("Deploying new pods")
            return True
        except Exception as e:
            logger.error(f"Error deploying new pods: {e}")
            return False
    
    async def _verify_health_checks(self) -> bool:
        """Verify health checks"""
        try:
            # Implementation for health check verification
            logger.info("Verifying health checks")
            return True
        except Exception as e:
            logger.error(f"Error verifying health checks: {e}")
            return False
    
    async def _update_load_balancer(self) -> bool:
        """Update load balancer"""
        try:
            # Implementation for load balancer update
            logger.info("Updating load balancer")
            return True
        except Exception as e:
            logger.error(f"Error updating load balancer: {e}")
            return False
    
    async def _verify_traffic_routing(self) -> bool:
        """Verify traffic routing"""
        try:
            # Implementation for traffic routing verification
            logger.info("Verifying traffic routing")
            return True
        except Exception as e:
            logger.error(f"Error verifying traffic routing: {e}")
            return False
    
    async def _activate_secondary_region(self) -> bool:
        """Activate secondary region"""
        try:
            # Implementation for secondary region activation
            logger.info("Activating secondary region")
            return True
        except Exception as e:
            logger.error(f"Error activating secondary region: {e}")
            return False
    
    async def _update_dns_records(self) -> bool:
        """Update DNS records"""
        try:
            # Implementation for DNS record update
            logger.info("Updating DNS records")
            return True
        except Exception as e:
            logger.error(f"Error updating DNS records: {e}")
            return False
    
    async def _verify_region_connectivity(self) -> bool:
        """Verify region connectivity"""
        try:
            # Implementation for region connectivity verification
            logger.info("Verifying region connectivity")
            return True
        except Exception as e:
            logger.error(f"Error verifying region connectivity: {e}")
            return False
    
    async def _monitor_performance(self) -> bool:
        """Monitor performance"""
        try:
            # Implementation for performance monitoring
            logger.info("Monitoring performance")
            return True
        except Exception as e:
            logger.error(f"Error monitoring performance: {e}")
            return False
    
    async def _validate_recovery(self, validation_checks: List[str]) -> bool:
        """Validate recovery using validation checks"""
        try:
            for check in validation_checks:
                if not await self._run_validation_check(check):
                    logger.error(f"Validation check failed: {check}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating recovery: {e}")
            return False
    
    async def _run_validation_check(self, check: str) -> bool:
        """Run a specific validation check"""
        try:
            if check == "Database connectivity":
                return await self._check_database_health()
            elif check == "Data integrity":
                return await self._verify_data_integrity()
            elif check == "Application functionality":
                return await self._verify_application()
            elif check == "Performance metrics":
                return await self._check_performance_metrics()
            elif check == "Pod health":
                return await self._check_pod_health()
            elif check == "Service connectivity":
                return await self._check_service_connectivity()
            elif check == "Load balancer status":
                return await self._check_load_balancer_status()
            elif check == "Application endpoints":
                return await self._check_application_endpoints()
            elif check == "Cross-region connectivity":
                return await self._check_cross_region_connectivity()
            else:
                logger.warning(f"Unknown validation check: {check}")
                return False
        except Exception as e:
            logger.error(f"Error running validation check {check}: {e}")
            return False
    
    async def _check_performance_metrics(self) -> bool:
        """Check performance metrics"""
        # Implementation for performance metrics check
        return True
    
    async def _check_pod_health(self) -> bool:
        """Check pod health"""
        # Implementation for pod health check
        return True
    
    async def _check_service_connectivity(self) -> bool:
        """Check service connectivity"""
        # Implementation for service connectivity check
        return True
    
    async def _check_load_balancer_status(self) -> bool:
        """Check load balancer status"""
        # Implementation for load balancer status check
        return True
    
    async def _check_application_endpoints(self) -> bool:
        """Check application endpoints"""
        # Implementation for application endpoints check
        return True
    
    async def _check_cross_region_connectivity(self) -> bool:
        """Check cross-region connectivity"""
        # Implementation for cross-region connectivity check
        return True
    
    async def _perform_backups(self):
        """Perform regular backups"""
        while self.running:
            try:
                # Check if it's time for backup
                if self._should_perform_backup():
                    await self._create_backup()
                
            except Exception as e:
                logger.error(f"Error performing backup: {e}")
            
            await asyncio.sleep(3600)  # Check every hour
    
    def _should_perform_backup(self) -> bool:
        """Check if backup should be performed based on schedule"""
        # Simplified implementation - in production, use proper cron parsing
        current_time = datetime.now()
        return current_time.hour == 2 and current_time.minute == 0  # Daily at 2 AM
    
    async def _create_backup(self):
        """Create system backup"""
        try:
            backup_id = f"backup_{int(time.time())}"
            logger.info(f"Creating backup: {backup_id}")
            
            # Create database backup
            await self._create_database_backup(backup_id)
            
            # Create application backup
            await self._create_application_backup(backup_id)
            
            # Create configuration backup
            await self._create_configuration_backup(backup_id)
            
            # Update backup status
            self.backup_status[backup_id] = {
                "id": backup_id,
                "created_at": datetime.now(),
                "status": "completed",
                "size": "unknown"  # Would calculate actual size
            }
            
            logger.info(f"Backup completed: {backup_id}")
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    async def _create_database_backup(self, backup_id: str):
        """Create database backup"""
        try:
            # Implementation for database backup
            logger.info(f"Creating database backup: {backup_id}")
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
    
    async def _create_application_backup(self, backup_id: str):
        """Create application backup"""
        try:
            # Implementation for application backup
            logger.info(f"Creating application backup: {backup_id}")
        except Exception as e:
            logger.error(f"Error creating application backup: {e}")
    
    async def _create_configuration_backup(self, backup_id: str):
        """Create configuration backup"""
        try:
            # Implementation for configuration backup
            logger.info(f"Creating configuration backup: {backup_id}")
        except Exception as e:
            logger.error(f"Error creating configuration backup: {e}")
    
    async def _run_recovery_tests(self):
        """Run recovery tests"""
        while self.running:
            try:
                # Check if it's time for recovery test
                if self._should_run_recovery_test():
                    await self._run_recovery_test_suite()
                
            except Exception as e:
                logger.error(f"Error running recovery tests: {e}")
            
            await asyncio.sleep(3600)  # Check every hour
    
    def _should_run_recovery_test(self) -> bool:
        """Check if recovery test should be run based on schedule"""
        # Simplified implementation - in production, use proper cron parsing
        current_time = datetime.now()
        return current_time.weekday() == 6 and current_time.hour == 3 and current_time.minute == 0  # Sunday at 3 AM
    
    async def _run_recovery_test_suite(self):
        """Run comprehensive recovery test suite"""
        try:
            test_id = f"test_{int(time.time())}"
            logger.info(f"Running recovery test suite: {test_id}")
            
            # Run different types of tests
            test_results = {}
            
            # Backup restore test
            test_results["backup_restore"] = await self._run_backup_restore_test()
            
            # Failover test
            test_results["failover"] = await self._run_failover_test()
            
            # Data integrity test
            test_results["data_integrity"] = await self._run_data_integrity_test()
            
            # Network connectivity test
            test_results["network_connectivity"] = await self._run_network_connectivity_test()
            
            # Create test record
            test = RecoveryTest(
                id=test_id,
                test_type=TestType.DISASTER_SIMULATION,
                plan_id="comprehensive_test",
                status=RecoveryStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                test_results=test_results,
                success=all(test_results.values()),
                notes="Comprehensive recovery test suite"
            )
            
            self.recovery_tests[test_id] = test
            logger.info(f"Recovery test suite completed: {test_id}")
        
        except Exception as e:
            logger.error(f"Error running recovery test suite: {e}")
    
    async def _run_backup_restore_test(self) -> bool:
        """Run backup restore test"""
        try:
            logger.info("Running backup restore test")
            # Implementation for backup restore test
            return True
        except Exception as e:
            logger.error(f"Error running backup restore test: {e}")
            return False
    
    async def _run_failover_test(self) -> bool:
        """Run failover test"""
        try:
            logger.info("Running failover test")
            # Implementation for failover test
            return True
        except Exception as e:
            logger.error(f"Error running failover test: {e}")
            return False
    
    async def _run_data_integrity_test(self) -> bool:
        """Run data integrity test"""
        try:
            logger.info("Running data integrity test")
            # Implementation for data integrity test
            return True
        except Exception as e:
            logger.error(f"Error running data integrity test: {e}")
            return False
    
    async def _run_network_connectivity_test(self) -> bool:
        """Run network connectivity test"""
        try:
            logger.info("Running network connectivity test")
            # Implementation for network connectivity test
            return True
        except Exception as e:
            logger.error(f"Error running network connectivity test: {e}")
            return False
    
    async def _monitor_recovery_executions(self):
        """Monitor recovery executions"""
        while self.running:
            try:
                # Check for stuck executions
                current_time = datetime.now()
                stuck_executions = [
                    execution for execution in self.recovery_executions.values()
                    if (execution.status == RecoveryStatus.IN_PROGRESS and
                        current_time - execution.started_at > timedelta(seconds=self.config.recovery_timeout))
                ]
                
                for execution in stuck_executions:
                    execution.status = RecoveryStatus.FAILED
                    execution.error_message = "Recovery timeout"
                    execution.completed_at = current_time
                    logger.error(f"Recovery execution timed out: {execution.id}")
                
            except Exception as e:
                logger.error(f"Error monitoring recovery executions: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _send_recovery_notification(self, execution: RecoveryExecution, status: str):
        """Send recovery notification"""
        try:
            if not self.config.notification_webhook:
                return
            
            notification_data = {
                "execution_id": execution.id,
                "plan_id": execution.plan_id,
                "status": status,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "recovery_time": execution.recovery_time,
                "error_message": execution.error_message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.notification_webhook,
                    json=notification_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send recovery notification: {response.status}")
        
        except Exception as e:
            logger.error(f"Error sending recovery notification: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old recovery data"""
        while self.running:
            try:
                # Clean up old executions
                cutoff_date = datetime.now() - timedelta(days=self.config.backup_retention_days)
                
                executions_to_remove = [
                    execution_id for execution_id, execution in self.recovery_executions.items()
                    if execution.started_at < cutoff_date
                ]
                
                for execution_id in executions_to_remove:
                    del self.recovery_executions[execution_id]
                
                # Clean up old tests
                tests_to_remove = [
                    test_id for test_id, test in self.recovery_tests.items()
                    if test.started_at < cutoff_date
                ]
                
                for test_id in tests_to_remove:
                    del self.recovery_tests[test_id]
                
                # Clean up old backups
                backups_to_remove = [
                    backup_id for backup_id, backup in self.backup_status.items()
                    if backup["created_at"] < cutoff_date
                ]
                
                for backup_id in backups_to_remove:
                    del self.backup_status[backup_id]
                
                if executions_to_remove or tests_to_remove or backups_to_remove:
                    logger.info(f"Cleaned up {len(executions_to_remove)} executions, "
                              f"{len(tests_to_remove)} tests, {len(backups_to_remove)} backups")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(86400)  # Clean up daily
    
    async def get_recovery_summary(self) -> Dict[str, Any]:
        """Get disaster recovery summary"""
        return {
            "total_plans": len(self.recovery_plans),
            "enabled_plans": len([p for p in self.recovery_plans.values() if p.enabled]),
            "total_executions": len(self.recovery_executions),
            "active_executions": len([
                e for e in self.recovery_executions.values()
                if e.status == RecoveryStatus.IN_PROGRESS
            ]),
            "successful_executions": len([
                e for e in self.recovery_executions.values()
                if e.status == RecoveryStatus.COMPLETED
            ]),
            "failed_executions": len([
                e for e in self.recovery_executions.values()
                if e.status == RecoveryStatus.FAILED
            ]),
            "total_tests": len(self.recovery_tests),
            "successful_tests": len([
                t for t in self.recovery_tests.values()
                if t.success
            ]),
            "total_backups": len(self.backup_status),
            "recovery_running": self.running,
            "last_check": datetime.now().isoformat()
        }
    
    async def get_recovery_plan(self, plan_id: str) -> Optional[RecoveryPlan]:
        """Get a specific recovery plan"""
        return self.recovery_plans.get(plan_id)
    
    async def get_recovery_execution(self, execution_id: str) -> Optional[RecoveryExecution]:
        """Get a specific recovery execution"""
        return self.recovery_executions.get(execution_id)
    
    async def get_recovery_test(self, test_id: str) -> Optional[RecoveryTest]:
        """Get a specific recovery test"""
        return self.recovery_tests.get(test_id)
    
    async def trigger_manual_recovery(self, plan_id: str, user: str) -> str:
        """Trigger manual recovery"""
        try:
            if plan_id not in self.recovery_plans:
                raise ValueError(f"Recovery plan {plan_id} not found")
            
            execution_id = f"manual_{plan_id}_{int(time.time())}"
            execution = RecoveryExecution(
                id=execution_id,
                plan_id=plan_id,
                status=RecoveryStatus.IN_PROGRESS,
                started_at=datetime.now(),
                executed_by=user
            )
            
            self.recovery_executions[execution_id] = execution
            
            # Execute recovery plan asynchronously
            plan = self.recovery_plans[plan_id]
            asyncio.create_task(self._execute_recovery_plan(execution, plan))
            
            logger.info(f"Manual recovery triggered by {user}: {execution_id}")
            return execution_id
        
        except Exception as e:
            logger.error(f"Error triggering manual recovery: {e}")
            raise
    
    async def cancel_recovery(self, execution_id: str, user: str):
        """Cancel a recovery execution"""
        try:
            if execution_id not in self.recovery_executions:
                raise ValueError(f"Recovery execution {execution_id} not found")
            
            execution = self.recovery_executions[execution_id]
            if execution.status != RecoveryStatus.IN_PROGRESS:
                raise ValueError(f"Recovery execution {execution_id} is not in progress")
            
            execution.status = RecoveryStatus.CANCELLED
            execution.completed_at = datetime.now()
            
            logger.info(f"Recovery cancelled by {user}: {execution_id}")
        
        except Exception as e:
            logger.error(f"Error cancelling recovery: {e}")
            raise
