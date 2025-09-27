"""
Tests for automated health recovery mechanisms.

This module tests the health recovery functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.health_recovery import (
    HealthMonitor, RecoveryManager, HealthRecoverySystem,
    HealthMetric, FailureEvent, RecoveryPlan, RecoveryResult,
    HealthStatus, RecoveryAction, FailureType
)


class TestHealthMetric:
    """Test HealthMetric data structure."""
    
    def test_health_metric_creation(self):
        """Test creating a health metric."""
        metric = HealthMetric(
            name="cpu_usage",
            value=75.5,
            threshold_warning=70.0,
            threshold_critical=90.0,
            unit="percent",
            timestamp=time.time(),
            metadata={"source": "system"}
        )
        
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.threshold_warning == 70.0
        assert metric.threshold_critical == 90.0
        assert metric.unit == "percent"
        assert metric.metadata["source"] == "system"


class TestFailureEvent:
    """Test FailureEvent data structure."""
    
    def test_failure_event_creation(self):
        """Test creating a failure event."""
        event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="Connection timeout",
            stack_trace="Traceback...",
            context={"url": "https://example.com", "timeout": 30}
        )
        
        assert event.failure_type == FailureType.CONNECTION_ERROR
        assert event.severity == "high"
        assert event.component == "scraper"
        assert event.message == "Connection timeout"
        assert event.context["url"] == "https://example.com"


class TestRecoveryPlan:
    """Test RecoveryPlan data structure."""
    
    def test_recovery_plan_creation(self):
        """Test creating a recovery plan."""
        plan = RecoveryPlan(
            plan_id="test_plan",
            failure_type=FailureType.CONNECTION_ERROR,
            actions=[RecoveryAction.RETRY, RecoveryAction.RESTART],
            priority=1,
            timeout_seconds=300,
            retry_count=3,
            success_criteria=[lambda x: True],
            rollback_actions=[RecoveryAction.ESCALATE],
            metadata={"description": "Test recovery plan"}
        )
        
        assert plan.plan_id == "test_plan"
        assert plan.failure_type == FailureType.CONNECTION_ERROR
        assert len(plan.actions) == 2
        assert plan.priority == 1
        assert plan.timeout_seconds == 300
        assert plan.retry_count == 3


class TestRecoveryResult:
    """Test RecoveryResult data structure."""
    
    def test_recovery_result_creation(self):
        """Test creating a recovery result."""
        result = RecoveryResult(
            success=True,
            actions_taken=[RecoveryAction.RETRY, RecoveryAction.RESTART],
            duration_seconds=45.5,
            error_message=None,
            metrics_improved=["cpu_usage", "memory_usage"],
            rollback_performed=False
        )
        
        assert result.success is True
        assert len(result.actions_taken) == 2
        assert result.duration_seconds == 45.5
        assert result.error_message is None
        assert len(result.metrics_improved) == 2
        assert result.rollback_performed is False


class TestHealthMonitor:
    """Test health monitor functionality."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = HealthMonitor(check_interval=10.0)
        
        assert monitor.check_interval == 10.0
        assert len(monitor.metrics) == 0
        assert len(monitor.failure_events) == 0
        assert len(monitor.health_callbacks) == 0
        assert monitor.is_monitoring is False
        assert monitor.monitor_task is None
    
    def test_add_health_callback(self):
        """Test adding health callbacks."""
        monitor = HealthMonitor()
        callback = Mock()
        
        monitor.add_health_callback(callback)
        
        assert len(monitor.health_callbacks) == 1
        assert callback in monitor.health_callbacks
    
    def test_record_failure(self):
        """Test recording failure events."""
        monitor = HealthMonitor()
        
        event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="Connection failed"
        )
        
        monitor.record_failure(event)
        
        assert len(monitor.failure_events) == 1
        assert monitor.failure_events[0] == event
    
    def test_get_health_status(self):
        """Test getting health status."""
        monitor = HealthMonitor()
        
        # Add some metrics
        monitor.metrics['cpu_usage'] = HealthMetric(
            name='cpu_usage',
            value=50.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
            unit='percent',
            timestamp=time.time()
        )
        
        status = monitor.get_health_status()
        
        assert status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]
    
    def test_get_metrics(self):
        """Test getting metrics."""
        monitor = HealthMonitor()
        
        # Add a metric
        metric = HealthMetric(
            name='cpu_usage',
            value=75.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
            unit='percent',
            timestamp=time.time()
        )
        monitor.metrics['cpu_usage'] = metric
        
        metrics = monitor.get_metrics()
        
        assert len(metrics) == 1
        assert 'cpu_usage' in metrics
        assert metrics['cpu_usage'] == metric
    
    def test_get_recent_failures(self):
        """Test getting recent failures."""
        monitor = HealthMonitor()
        
        # Add old failure
        old_event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time() - 86400,  # 24 hours ago
            component="scraper",
            message="Old failure"
        )
        monitor.record_failure(old_event)
        
        # Add recent failure
        recent_event = FailureEvent(
            failure_type=FailureType.TIMEOUT_ERROR,
            severity="medium",
            timestamp=time.time(),
            component="scraper",
            message="Recent failure"
        )
        monitor.record_failure(recent_event)
        
        recent_failures = monitor.get_recent_failures(hours=12)
        
        assert len(recent_failures) == 1
        assert recent_failures[0] == recent_event
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = HealthMonitor(check_interval=0.1)  # Very fast for testing
        
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True
        assert monitor.monitor_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False
        # Task should be cancelled or finished
        assert monitor.monitor_task is None or monitor.monitor_task.cancelled() or monitor.monitor_task.done()
    
    @pytest.mark.asyncio
    async def test_health_callback_notification(self):
        """Test health callback notification."""
        monitor = HealthMonitor(check_interval=0.1)
        callback = AsyncMock()
        
        monitor.add_health_callback(callback)
        await monitor.start_monitoring()
        
        # Let it run briefly to trigger callbacks
        await asyncio.sleep(0.2)
        
        await monitor.stop_monitoring()
        
        # Callback should have been called
        assert callback.call_count > 0


class TestRecoveryManager:
    """Test recovery manager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = RecoveryManager()
        
        assert len(manager.recovery_plans) > 0
        assert len(manager.recovery_history) == 0
        assert len(manager.active_recoveries) == 0
        assert len(manager.recovery_callbacks) == 0
        
        # Check that default plans are initialized
        assert FailureType.CONNECTION_ERROR in manager.recovery_plans
        assert FailureType.RATE_LIMIT in manager.recovery_plans
        assert FailureType.CAPTCHA_BLOCK in manager.recovery_plans
    
    def test_add_recovery_callback(self):
        """Test adding recovery callbacks."""
        manager = RecoveryManager()
        callback = Mock()
        
        manager.add_recovery_callback(callback)
        
        assert len(manager.recovery_callbacks) == 1
        assert callback in manager.recovery_callbacks
    
    @pytest.mark.asyncio
    async def test_recover_from_failure_connection_error(self):
        """Test recovery from connection error."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="Connection failed"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.duration_seconds > 0
        assert result.actions_taken[0] in [RecoveryAction.RETRY, RecoveryAction.ROTATE, RecoveryAction.RESTART]
    
    @pytest.mark.asyncio
    async def test_recover_from_failure_rate_limit(self):
        """Test recovery from rate limit."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.RATE_LIMIT,
            severity="medium",
            timestamp=time.time(),
            component="scraper",
            message="Rate limited"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.actions_taken[0] in [RecoveryAction.RETRY, RecoveryAction.ROTATE, RecoveryAction.SCALE]
    
    @pytest.mark.asyncio
    async def test_recover_from_failure_captcha_block(self):
        """Test recovery from CAPTCHA block."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.CAPTCHA_BLOCK,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="CAPTCHA blocked"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.actions_taken[0] in [RecoveryAction.ROTATE, RecoveryAction.RETRY, RecoveryAction.FALLBACK]
    
    @pytest.mark.asyncio
    async def test_recover_from_failure_ip_block(self):
        """Test recovery from IP block."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.IP_BLOCK,
            severity="critical",
            timestamp=time.time(),
            component="scraper",
            message="IP blocked"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.actions_taken[0] in [RecoveryAction.ROTATE, RecoveryAction.RESET, RecoveryAction.RESTART]
    
    @pytest.mark.asyncio
    async def test_recover_from_failure_memory_error(self):
        """Test recovery from memory error."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.MEMORY_ERROR,
            severity="critical",
            timestamp=time.time(),
            component="scraper",
            message="Out of memory"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.actions_taken[0] in [RecoveryAction.RESTART, RecoveryAction.SCALE, RecoveryAction.RESET]
    
    @pytest.mark.asyncio
    async def test_recover_from_unknown_failure(self):
        """Test recovery from unknown failure type."""
        manager = RecoveryManager()
        
        failure_event = FailureEvent(
            failure_type=FailureType.UNKNOWN_ERROR,
            severity="medium",
            timestamp=time.time(),
            component="scraper",
            message="Unknown error"
        )
        
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is False
        assert "No recovery plan" in result.error_message
    
    def test_get_recovery_statistics_empty(self):
        """Test getting recovery statistics when no recoveries have occurred."""
        manager = RecoveryManager()
        
        stats = manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 0
        assert stats['successful_recoveries'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_duration'] == 0.0
        assert len(stats['common_actions']) == 0
    
    def test_get_recovery_statistics_with_data(self):
        """Test getting recovery statistics with data."""
        manager = RecoveryManager()
        
        # Add some recovery results
        result1 = RecoveryResult(
            success=True,
            actions_taken=[RecoveryAction.RETRY, RecoveryAction.RESTART],
            duration_seconds=30.0,
            metrics_improved=["cpu_usage"]
        )
        result2 = RecoveryResult(
            success=False,
            actions_taken=[RecoveryAction.ROTATE],
            duration_seconds=20.0,
            error_message="Failed"
        )
        
        manager.recovery_history = [result1, result2]
        
        stats = manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 2
        assert stats['successful_recoveries'] == 1
        assert stats['success_rate'] == 0.5
        assert stats['average_duration'] == 25.0
        assert stats['common_actions']['retry'] == 1
        assert stats['common_actions']['restart'] == 1
        assert stats['common_actions']['rotate'] == 1


class TestHealthRecoverySystem:
    """Test health recovery system functionality."""
    
    def test_system_initialization(self):
        """Test system initialization."""
        system = HealthRecoverySystem(check_interval=15.0)
        
        assert system.health_monitor is not None
        assert system.recovery_manager is not None
        assert system.is_running is False
        assert system.health_monitor.check_interval == 15.0
    
    @pytest.mark.asyncio
    async def test_start_stop_system(self):
        """Test starting and stopping the system."""
        system = HealthRecoverySystem(check_interval=0.1)
        
        # Start system
        await system.start()
        assert system.is_running is True
        assert system.health_monitor.is_monitoring is True
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop system
        await system.stop()
        assert system.is_running is False
        assert system.health_monitor.is_monitoring is False
    
    def test_add_health_callback(self):
        """Test adding health callbacks."""
        system = HealthRecoverySystem()
        callback = Mock()
        
        system.add_health_callback(callback)
        
        assert callback in system.health_monitor.health_callbacks
    
    def test_add_recovery_callback(self):
        """Test adding recovery callbacks."""
        system = HealthRecoverySystem()
        callback = Mock()
        
        system.add_recovery_callback(callback)
        
        assert callback in system.recovery_manager.recovery_callbacks
    
    def test_get_system_status(self):
        """Test getting system status."""
        system = HealthRecoverySystem()
        
        status = system.get_system_status()
        
        assert 'is_running' in status
        assert 'health_status' in status
        assert 'metrics' in status
        assert 'recovery_stats' in status
        assert 'recent_failures' in status
        
        assert status['is_running'] is False
        assert isinstance(status['health_status'], str)
        assert isinstance(status['metrics'], dict)
        assert isinstance(status['recovery_stats'], dict)
        assert isinstance(status['recent_failures'], int)
    
    def test_determine_failure_type_cpu(self):
        """Test determining failure type from CPU metrics."""
        system = HealthRecoverySystem()
        
        metrics = {
            'cpu_usage': HealthMetric(
                name='cpu_usage',
                value=95.0,
                threshold_warning=70.0,
                threshold_critical=90.0,
                unit='percent',
                timestamp=time.time()
            )
        }
        
        failure_type = system._determine_failure_type(metrics)
        
        assert failure_type == FailureType.RESOURCE_EXHAUSTION
    
    def test_determine_failure_type_memory(self):
        """Test determining failure type from memory metrics."""
        system = HealthRecoverySystem()
        
        metrics = {
            'memory_usage': HealthMetric(
                name='memory_usage',
                value=98.0,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit='percent',
                timestamp=time.time()
            )
        }
        
        failure_type = system._determine_failure_type(metrics)
        
        assert failure_type == FailureType.MEMORY_ERROR
    
    def test_determine_failure_type_response_time(self):
        """Test determining failure type from response time metrics."""
        system = HealthRecoverySystem()
        
        metrics = {
            'response_time': HealthMetric(
                name='response_time',
                value=15.0,
                threshold_warning=5.0,
                threshold_critical=10.0,
                unit='seconds',
                timestamp=time.time()
            )
        }
        
        failure_type = system._determine_failure_type(metrics)
        
        assert failure_type == FailureType.TIMEOUT_ERROR
    
    def test_determine_failure_type_error_rate(self):
        """Test determining failure type from error rate metrics."""
        system = HealthRecoverySystem()
        
        metrics = {
            'error_rate': HealthMetric(
                name='error_rate',
                value=20.0,
                threshold_warning=5.0,
                threshold_critical=15.0,
                unit='percent',
                timestamp=time.time()
            )
        }
        
        failure_type = system._determine_failure_type(metrics)
        
        assert failure_type == FailureType.CONNECTION_ERROR
    
    def test_determine_failure_type_unknown(self):
        """Test determining failure type when no specific issues detected."""
        system = HealthRecoverySystem()
        
        metrics = {
            'cpu_usage': HealthMetric(
                name='cpu_usage',
                value=50.0,
                threshold_warning=70.0,
                threshold_critical=90.0,
                unit='percent',
                timestamp=time.time()
            )
        }
        
        failure_type = system._determine_failure_type(metrics)
        
        assert failure_type == FailureType.UNKNOWN_ERROR


class TestHealthRecoveryIntegration:
    """Integration tests for health recovery system."""
    
    @pytest.mark.asyncio
    async def test_complete_health_recovery_workflow(self):
        """Test complete health recovery workflow."""
        system = HealthRecoverySystem(check_interval=0.1)
        
        # Add callbacks to track events
        health_events = []
        recovery_events = []
        
        def health_callback(status, metrics):
            health_events.append((status, metrics))
        
        def recovery_callback(result, failure_event):
            recovery_events.append((result, failure_event))
        
        system.add_health_callback(health_callback)
        system.add_recovery_callback(recovery_callback)
        
        # Start system
        await system.start()
        
        # Let it run to collect metrics and potentially trigger recovery
        await asyncio.sleep(0.5)
        
        # Stop system
        await system.stop()
        
        # Should have collected some health events
        assert len(health_events) > 0
        
        # Check system status
        status = system.get_system_status()
        assert status['is_running'] is False
        assert 'health_status' in status
        assert 'metrics' in status
    
    @pytest.mark.asyncio
    async def test_manual_failure_recovery(self):
        """Test manual failure recovery."""
        system = HealthRecoverySystem()
        
        # Create a failure event
        failure_event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="Manual test failure"
        )
        
        # Record the failure
        system.health_monitor.record_failure(failure_event)
        
        # Attempt recovery
        result = await system.recovery_manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        assert result.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_recovery_plan_execution(self):
        """Test recovery plan execution."""
        manager = RecoveryManager()
        
        # Get a recovery plan
        plan = manager.recovery_plans[FailureType.CONNECTION_ERROR]
        
        # Create failure event
        failure_event = FailureEvent(
            failure_type=FailureType.CONNECTION_ERROR,
            severity="high",
            timestamp=time.time(),
            component="scraper",
            message="Test failure"
        )
        
        # Execute recovery
        result = await manager.recover_from_failure(failure_event)
        
        assert isinstance(result, RecoveryResult)
        assert len(result.actions_taken) > 0
        
        # Check that actions taken are from the plan
        for action in result.actions_taken:
            assert action in plan.actions
    
    def test_recovery_statistics_tracking(self):
        """Test recovery statistics tracking."""
        manager = RecoveryManager()
        
        # Simulate some recoveries
        results = [
            RecoveryResult(
                success=True,
                actions_taken=[RecoveryAction.RETRY],
                duration_seconds=10.0,
                metrics_improved=["cpu_usage"]
            ),
            RecoveryResult(
                success=False,
                actions_taken=[RecoveryAction.RESTART],
                duration_seconds=20.0,
                error_message="Failed"
            ),
            RecoveryResult(
                success=True,
                actions_taken=[RecoveryAction.ROTATE, RecoveryAction.RETRY],
                duration_seconds=15.0,
                metrics_improved=["memory_usage"]
            )
        ]
        
        manager.recovery_history = results
        
        stats = manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 3
        assert stats['successful_recoveries'] == 2
        assert stats['success_rate'] == 2/3
        assert stats['average_duration'] == 15.0
        assert stats['common_actions']['retry'] == 2
        assert stats['common_actions']['restart'] == 1
        assert stats['common_actions']['rotate'] == 1
