"""
Automated health recovery mechanisms for web scraping.

This module provides intelligent health monitoring and automated recovery
systems that can detect and respond to various failure scenarios.
"""

import asyncio
import time
import logging
import random
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import hashlib
from datetime import datetime, timedelta


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Types of recovery actions."""
    RESTART = "restart"
    RESET = "reset"
    ROTATE = "rotate"
    SCALE = "scale"
    FALLBACK = "fallback"
    RETRY = "retry"
    ESCALATE = "escalate"
    IGNORE = "ignore"


class FailureType(Enum):
    """Types of failures that can occur."""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT = "rate_limit"
    CAPTCHA_BLOCK = "captcha_block"
    IP_BLOCK = "ip_block"
    PROXY_FAILURE = "proxy_failure"
    MEMORY_ERROR = "memory_error"
    DISK_ERROR = "disk_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class HealthMetric:
    """Represents a health metric."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureEvent:
    """Represents a failure event."""
    failure_type: FailureType
    severity: str
    timestamp: float
    component: str
    message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False


@dataclass
class RecoveryPlan:
    """Represents a recovery plan."""
    plan_id: str
    failure_type: FailureType
    actions: List[RecoveryAction]
    priority: int
    timeout_seconds: int
    retry_count: int
    success_criteria: List[Callable]
    rollback_actions: List[RecoveryAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Represents the result of a recovery attempt."""
    success: bool
    actions_taken: List[RecoveryAction]
    duration_seconds: float
    error_message: Optional[str] = None
    metrics_improved: List[str] = field(default_factory=list)
    rollback_performed: bool = False


class HealthMonitor:
    """Monitors system health and detects issues."""
    
    def __init__(self, check_interval: float = 30.0):
        """Initialize the health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self.metrics: Dict[str, HealthMetric] = {}
        self.failure_events: deque = deque(maxlen=1000)
        self.health_callbacks: List[Callable] = []
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Health thresholds
        self.thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0},
            'response_time': {'warning': 5.0, 'critical': 10.0},
            'error_rate': {'warning': 5.0, 'critical': 15.0},
            'success_rate': {'warning': 90.0, 'critical': 80.0}
        }
    
    async def start_monitoring(self):
        """Start the health monitoring process."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logging.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring process."""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logging.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_health(self):
        """Perform health checks."""
        # Collect system metrics
        await self._collect_metrics()
        
        # Analyze health status
        health_status = self._analyze_health()
        
        # Notify callbacks if health degraded
        if health_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
            await self._notify_health_callbacks(health_status)
    
    async def _collect_metrics(self):
        """Collect system metrics."""
        # CPU usage (simulated)
        cpu_usage = random.uniform(10.0, 100.0)
        self.metrics['cpu_usage'] = HealthMetric(
            name='cpu_usage',
            value=cpu_usage,
            threshold_warning=self.thresholds['cpu_usage']['warning'],
            threshold_critical=self.thresholds['cpu_usage']['critical'],
            unit='percent',
            timestamp=time.time()
        )
        
        # Memory usage (simulated)
        memory_usage = random.uniform(20.0, 100.0)
        self.metrics['memory_usage'] = HealthMetric(
            name='memory_usage',
            value=memory_usage,
            threshold_warning=self.thresholds['memory_usage']['warning'],
            threshold_critical=self.thresholds['memory_usage']['critical'],
            unit='percent',
            timestamp=time.time()
        )
        
        # Disk usage (simulated)
        disk_usage = random.uniform(30.0, 100.0)
        self.metrics['disk_usage'] = HealthMetric(
            name='disk_usage',
            value=disk_usage,
            threshold_warning=self.thresholds['disk_usage']['warning'],
            threshold_critical=self.thresholds['disk_usage']['critical'],
            unit='percent',
            timestamp=time.time()
        )
        
        # Response time (simulated)
        response_time = random.uniform(0.1, 15.0)
        self.metrics['response_time'] = HealthMetric(
            name='response_time',
            value=response_time,
            threshold_warning=self.thresholds['response_time']['warning'],
            threshold_critical=self.thresholds['response_time']['critical'],
            unit='seconds',
            timestamp=time.time()
        )
        
        # Error rate (simulated)
        error_rate = random.uniform(0.0, 20.0)
        self.metrics['error_rate'] = HealthMetric(
            name='error_rate',
            value=error_rate,
            threshold_warning=self.thresholds['error_rate']['warning'],
            threshold_critical=self.thresholds['error_rate']['critical'],
            unit='percent',
            timestamp=time.time()
        )
        
        # Success rate (simulated)
        success_rate = random.uniform(60.0, 100.0)
        self.metrics['success_rate'] = HealthMetric(
            name='success_rate',
            value=success_rate,
            threshold_warning=self.thresholds['success_rate']['warning'],
            threshold_critical=self.thresholds['success_rate']['critical'],
            unit='percent',
            timestamp=time.time()
        )
    
    def _analyze_health(self) -> HealthStatus:
        """Analyze collected metrics to determine health status."""
        critical_count = 0
        warning_count = 0
        
        for metric in self.metrics.values():
            if metric.value >= metric.threshold_critical:
                critical_count += 1
            elif metric.value >= metric.threshold_warning:
                warning_count += 1
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 2:
            return HealthStatus.UNHEALTHY
        elif warning_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    async def _notify_health_callbacks(self, health_status: HealthStatus):
        """Notify registered callbacks about health status changes."""
        for callback in self.health_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(health_status, self.metrics)
                else:
                    callback(health_status, self.metrics)
            except Exception as e:
                logging.error(f"Error in health callback: {e}")
    
    def add_health_callback(self, callback: Callable):
        """Add a health status callback.
        
        Args:
            callback: Function to call when health status changes
        """
        self.health_callbacks.append(callback)
    
    def record_failure(self, failure_event: FailureEvent):
        """Record a failure event.
        
        Args:
            failure_event: Failure event to record
        """
        self.failure_events.append(failure_event)
        logging.warning(f"Failure recorded: {failure_event.failure_type.value} - {failure_event.message}")
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status."""
        return self._analyze_health()
    
    def get_metrics(self) -> Dict[str, HealthMetric]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_recent_failures(self, hours: int = 24) -> List[FailureEvent]:
        """Get recent failure events.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent failure events
        """
        cutoff_time = time.time() - (hours * 3600)
        return [event for event in self.failure_events if event.timestamp > cutoff_time]


class RecoveryManager:
    """Manages automated recovery from failures."""
    
    def __init__(self):
        """Initialize the recovery manager."""
        self.recovery_plans: Dict[FailureType, RecoveryPlan] = {}
        self.recovery_history: List[RecoveryResult] = []
        self.active_recoveries: Dict[str, asyncio.Task] = {}
        self.recovery_callbacks: List[Callable] = []
        
        # Initialize default recovery plans
        self._initialize_default_plans()
    
    def _initialize_default_plans(self):
        """Initialize default recovery plans for common failure types."""
        # Connection error recovery
        self.recovery_plans[FailureType.CONNECTION_ERROR] = RecoveryPlan(
            plan_id="connection_error_recovery",
            failure_type=FailureType.CONNECTION_ERROR,
            actions=[RecoveryAction.RETRY, RecoveryAction.ROTATE, RecoveryAction.RESTART],
            priority=1,
            timeout_seconds=300,
            retry_count=3,
            success_criteria=[self._check_connection_restored],
            rollback_actions=[RecoveryAction.ESCALATE]
        )
        
        # Rate limit recovery
        self.recovery_plans[FailureType.RATE_LIMIT] = RecoveryPlan(
            plan_id="rate_limit_recovery",
            failure_type=FailureType.RATE_LIMIT,
            actions=[RecoveryAction.RETRY, RecoveryAction.ROTATE, RecoveryAction.SCALE],
            priority=2,
            timeout_seconds=600,
            retry_count=5,
            success_criteria=[self._check_rate_limit_cleared],
            rollback_actions=[RecoveryAction.FALLBACK]
        )
        
        # CAPTCHA block recovery
        self.recovery_plans[FailureType.CAPTCHA_BLOCK] = RecoveryPlan(
            plan_id="captcha_block_recovery",
            failure_type=FailureType.CAPTCHA_BLOCK,
            actions=[RecoveryAction.ROTATE, RecoveryAction.RETRY, RecoveryAction.FALLBACK],
            priority=1,
            timeout_seconds=180,
            retry_count=2,
            success_criteria=[self._check_captcha_bypassed],
            rollback_actions=[RecoveryAction.ESCALATE]
        )
        
        # IP block recovery
        self.recovery_plans[FailureType.IP_BLOCK] = RecoveryPlan(
            plan_id="ip_block_recovery",
            failure_type=FailureType.IP_BLOCK,
            actions=[RecoveryAction.ROTATE, RecoveryAction.RESET, RecoveryAction.RESTART],
            priority=1,
            timeout_seconds=300,
            retry_count=2,
            success_criteria=[self._check_ip_unblocked],
            rollback_actions=[RecoveryAction.ESCALATE]
        )
        
        # Memory error recovery
        self.recovery_plans[FailureType.MEMORY_ERROR] = RecoveryPlan(
            plan_id="memory_error_recovery",
            failure_type=FailureType.MEMORY_ERROR,
            actions=[RecoveryAction.RESTART, RecoveryAction.SCALE, RecoveryAction.RESET],
            priority=0,
            timeout_seconds=120,
            retry_count=1,
            success_criteria=[self._check_memory_available],
            rollback_actions=[RecoveryAction.ESCALATE]
        )
    
    async def recover_from_failure(self, failure_event: FailureEvent) -> RecoveryResult:
        """Attempt to recover from a failure.
        
        Args:
            failure_event: Failure event to recover from
            
        Returns:
            Recovery result
        """
        recovery_id = f"recovery_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Get recovery plan for this failure type
        plan = self.recovery_plans.get(failure_event.failure_type)
        if not plan:
            return RecoveryResult(
                success=False,
                actions_taken=[],
                duration_seconds=0.0,
                error_message=f"No recovery plan for {failure_event.failure_type.value}"
            )
        
        start_time = time.time()
        actions_taken = []
        error_message = None
        
        try:
            # Execute recovery actions
            for action in plan.actions:
                try:
                    success = await self._execute_recovery_action(action, failure_event)
                    actions_taken.append(action)
                    
                    if success:
                        # Check if recovery was successful
                        if await self._check_recovery_success(plan, failure_event):
                            duration = time.time() - start_time
                            result = RecoveryResult(
                                success=True,
                                actions_taken=actions_taken,
                                duration_seconds=duration,
                                metrics_improved=self._get_improved_metrics()
                            )
                            
                            # Record successful recovery
                            self.recovery_history.append(result)
                            await self._notify_recovery_callbacks(result, failure_event)
                            
                            return result
                    
                    # Wait before next action
                    await asyncio.sleep(2.0)
                    
                except Exception as e:
                    error_message = f"Error executing {action.value}: {str(e)}"
                    logging.error(error_message)
                    continue
            
            # If we get here, recovery failed
            duration = time.time() - start_time
            result = RecoveryResult(
                success=False,
                actions_taken=actions_taken,
                duration_seconds=duration,
                error_message=error_message or "All recovery actions failed"
            )
            
            # Try rollback actions
            if plan.rollback_actions:
                await self._execute_rollback_actions(plan.rollback_actions, failure_event)
                result.rollback_performed = True
            
            self.recovery_history.append(result)
            await self._notify_recovery_callbacks(result, failure_event)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = RecoveryResult(
                success=False,
                actions_taken=actions_taken,
                duration_seconds=duration,
                error_message=f"Recovery failed with exception: {str(e)}"
            )
            
            self.recovery_history.append(result)
            await self._notify_recovery_callbacks(result, failure_event)
            
            return result
    
    async def _execute_recovery_action(self, action: RecoveryAction, failure_event: FailureEvent) -> bool:
        """Execute a specific recovery action.
        
        Args:
            action: Recovery action to execute
            failure_event: Original failure event
            
        Returns:
            True if action was successful
        """
        try:
            if action == RecoveryAction.RESTART:
                return await self._restart_component(failure_event.component)
            
            elif action == RecoveryAction.RESET:
                return await self._reset_component(failure_event.component)
            
            elif action == RecoveryAction.ROTATE:
                return await self._rotate_resources(failure_event.component)
            
            elif action == RecoveryAction.SCALE:
                return await self._scale_component(failure_event.component)
            
            elif action == RecoveryAction.FALLBACK:
                return await self._fallback_to_alternative(failure_event.component)
            
            elif action == RecoveryAction.RETRY:
                return await self._retry_operation(failure_event.component)
            
            elif action == RecoveryAction.ESCALATE:
                return await self._escalate_issue(failure_event)
            
            else:
                logging.warning(f"Unknown recovery action: {action.value}")
                return False
                
        except Exception as e:
            logging.error(f"Error executing recovery action {action.value}: {e}")
            return False
    
    async def _restart_component(self, component: str) -> bool:
        """Restart a component.
        
        Args:
            component: Component to restart
            
        Returns:
            True if restart was successful
        """
        logging.info(f"Restarting component: {component}")
        # Simulate restart process
        await asyncio.sleep(random.uniform(1.0, 3.0))
        return random.choice([True, True, True, False])  # 75% success rate
    
    async def _reset_component(self, component: str) -> bool:
        """Reset a component to default state.
        
        Args:
            component: Component to reset
            
        Returns:
            True if reset was successful
        """
        logging.info(f"Resetting component: {component}")
        # Simulate reset process
        await asyncio.sleep(random.uniform(0.5, 2.0))
        return random.choice([True, True, False])  # 67% success rate
    
    async def _rotate_resources(self, component: str) -> bool:
        """Rotate resources (proxies, IPs, etc.).
        
        Args:
            component: Component to rotate resources for
            
        Returns:
            True if rotation was successful
        """
        logging.info(f"Rotating resources for component: {component}")
        # Simulate resource rotation
        await asyncio.sleep(random.uniform(0.2, 1.0))
        return random.choice([True, True, True, True, False])  # 80% success rate
    
    async def _scale_component(self, component: str) -> bool:
        """Scale a component up or down.
        
        Args:
            component: Component to scale
            
        Returns:
            True if scaling was successful
        """
        logging.info(f"Scaling component: {component}")
        # Simulate scaling process
        await asyncio.sleep(random.uniform(2.0, 5.0))
        return random.choice([True, True, False])  # 67% success rate
    
    async def _fallback_to_alternative(self, component: str) -> bool:
        """Fallback to alternative implementation.
        
        Args:
            component: Component to fallback for
            
        Returns:
            True if fallback was successful
        """
        logging.info(f"Falling back to alternative for component: {component}")
        # Simulate fallback process
        await asyncio.sleep(random.uniform(1.0, 3.0))
        return random.choice([True, True, True, False])  # 75% success rate
    
    async def _retry_operation(self, component: str) -> bool:
        """Retry the failed operation.
        
        Args:
            component: Component to retry operation for
            
        Returns:
            True if retry was successful
        """
        logging.info(f"Retrying operation for component: {component}")
        # Simulate retry process
        await asyncio.sleep(random.uniform(0.5, 2.0))
        return random.choice([True, True, True, True, False])  # 80% success rate
    
    async def _escalate_issue(self, failure_event: FailureEvent) -> bool:
        """Escalate the issue to human operators.
        
        Args:
            failure_event: Failure event to escalate
            
        Returns:
            True if escalation was successful
        """
        logging.critical(f"Escalating issue: {failure_event.failure_type.value} - {failure_event.message}")
        # Simulate escalation process
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return True  # Escalation always "succeeds"
    
    async def _check_recovery_success(self, plan: RecoveryPlan, failure_event: FailureEvent) -> bool:
        """Check if recovery was successful.
        
        Args:
            plan: Recovery plan that was executed
            failure_event: Original failure event
            
        Returns:
            True if recovery was successful
        """
        for criteria in plan.success_criteria:
            if not await criteria(failure_event):
                return False
        return True
    
    async def _check_connection_restored(self, failure_event: FailureEvent) -> bool:
        """Check if connection has been restored."""
        # Simulate connection check
        await asyncio.sleep(0.1)
        return random.choice([True, True, True, False])  # 75% success rate
    
    async def _check_rate_limit_cleared(self, failure_event: FailureEvent) -> bool:
        """Check if rate limit has been cleared."""
        # Simulate rate limit check
        await asyncio.sleep(0.1)
        return random.choice([True, True, False])  # 67% success rate
    
    async def _check_captcha_bypassed(self, failure_event: FailureEvent) -> bool:
        """Check if CAPTCHA has been bypassed."""
        # Simulate CAPTCHA check
        await asyncio.sleep(0.1)
        return random.choice([True, True, True, False])  # 75% success rate
    
    async def _check_ip_unblocked(self, failure_event: FailureEvent) -> bool:
        """Check if IP has been unblocked."""
        # Simulate IP check
        await asyncio.sleep(0.1)
        return random.choice([True, True, False])  # 67% success rate
    
    async def _check_memory_available(self, failure_event: FailureEvent) -> bool:
        """Check if memory is available."""
        # Simulate memory check
        await asyncio.sleep(0.1)
        return random.choice([True, True, True, True, False])  # 80% success rate
    
    def _get_improved_metrics(self) -> List[str]:
        """Get list of metrics that improved after recovery."""
        return random.sample(['cpu_usage', 'memory_usage', 'response_time', 'error_rate'], 
                           random.randint(1, 3))
    
    async def _execute_rollback_actions(self, rollback_actions: List[RecoveryAction], 
                                      failure_event: FailureEvent):
        """Execute rollback actions.
        
        Args:
            rollback_actions: List of rollback actions to execute
            failure_event: Original failure event
        """
        for action in rollback_actions:
            try:
                await self._execute_recovery_action(action, failure_event)
            except Exception as e:
                logging.error(f"Error executing rollback action {action.value}: {e}")
    
    async def _notify_recovery_callbacks(self, result: RecoveryResult, failure_event: FailureEvent):
        """Notify registered callbacks about recovery results.
        
        Args:
            result: Recovery result
            failure_event: Original failure event
        """
        for callback in self.recovery_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result, failure_event)
                else:
                    callback(result, failure_event)
            except Exception as e:
                logging.error(f"Error in recovery callback: {e}")
    
    def add_recovery_callback(self, callback: Callable):
        """Add a recovery result callback.
        
        Args:
            callback: Function to call when recovery completes
        """
        self.recovery_callbacks.append(callback)
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics.
        
        Returns:
            Dictionary with recovery statistics
        """
        if not self.recovery_history:
            return {
                'total_recoveries': 0,
                'successful_recoveries': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'common_actions': {}
            }
        
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r.success)
        success_rate = successful_recoveries / total_recoveries
        average_duration = sum(r.duration_seconds for r in self.recovery_history) / total_recoveries
        
        # Count common actions
        action_counts = defaultdict(int)
        for result in self.recovery_history:
            for action in result.actions_taken:
                action_counts[action.value] += 1
        
        return {
            'total_recoveries': total_recoveries,
            'successful_recoveries': successful_recoveries,
            'success_rate': success_rate,
            'average_duration': average_duration,
            'common_actions': dict(action_counts)
        }


class HealthRecoverySystem:
    """Main health recovery system that coordinates monitoring and recovery."""
    
    def __init__(self, check_interval: float = 30.0):
        """Initialize the health recovery system.
        
        Args:
            check_interval: Interval between health checks in seconds
        """
        self.health_monitor = HealthMonitor(check_interval)
        self.recovery_manager = RecoveryManager()
        self.is_running = False
        
        # Register health monitor callback
        self.health_monitor.add_health_callback(self._on_health_change)
    
    async def start(self):
        """Start the health recovery system."""
        if self.is_running:
            return
        
        self.is_running = True
        await self.health_monitor.start_monitoring()
        logging.info("Health recovery system started")
    
    async def stop(self):
        """Stop the health recovery system."""
        if not self.is_running:
            return
        
        self.is_running = False
        await self.health_monitor.stop_monitoring()
        logging.info("Health recovery system stopped")
    
    async def _on_health_change(self, health_status: HealthStatus, metrics: Dict[str, HealthMetric]):
        """Handle health status changes.
        
        Args:
            health_status: Current health status
            metrics: Current metrics
        """
        if health_status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
            # Create failure event based on health status
            failure_type = self._determine_failure_type(metrics)
            failure_event = FailureEvent(
                failure_type=failure_type,
                severity=health_status.value,
                timestamp=time.time(),
                component="system",
                message=f"Health degraded to {health_status.value}",
                context={"metrics": {k: v.value for k, v in metrics.items()}}
            )
            
            # Record failure
            self.health_monitor.record_failure(failure_event)
            
            # Attempt recovery
            recovery_result = await self.recovery_manager.recover_from_failure(failure_event)
            
            if recovery_result.success:
                logging.info(f"Successfully recovered from {failure_type.value}")
            else:
                logging.error(f"Failed to recover from {failure_type.value}: {recovery_result.error_message}")
    
    def _determine_failure_type(self, metrics: Dict[str, HealthMetric]) -> FailureType:
        """Determine failure type based on metrics.
        
        Args:
            metrics: Current metrics
            
        Returns:
            Determined failure type
        """
        # Check for specific metric issues
        if 'cpu_usage' in metrics and metrics['cpu_usage'].value >= 90:
            return FailureType.RESOURCE_EXHAUSTION
        elif 'memory_usage' in metrics and metrics['memory_usage'].value >= 95:
            return FailureType.MEMORY_ERROR
        elif 'response_time' in metrics and metrics['response_time'].value >= 10:
            return FailureType.TIMEOUT_ERROR
        elif 'error_rate' in metrics and metrics['error_rate'].value >= 15:
            return FailureType.CONNECTION_ERROR
        else:
            return FailureType.UNKNOWN_ERROR
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status.
        
        Returns:
            Dictionary with system status information
        """
        return {
            'is_running': self.is_running,
            'health_status': self.health_monitor.get_health_status().value,
            'metrics': {k: v.value for k, v in self.health_monitor.get_metrics().items()},
            'recovery_stats': self.recovery_manager.get_recovery_statistics(),
            'recent_failures': len(self.health_monitor.get_recent_failures(1))  # Last hour
        }
    
    def add_health_callback(self, callback: Callable):
        """Add a health status callback.
        
        Args:
            callback: Function to call when health status changes
        """
        self.health_monitor.add_health_callback(callback)
    
    def add_recovery_callback(self, callback: Callable):
        """Add a recovery result callback.
        
        Args:
            callback: Function to call when recovery completes
        """
        self.recovery_manager.add_recovery_callback(callback)

