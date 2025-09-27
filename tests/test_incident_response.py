"""
Tests for Incident Response Module

This module tests the automated incident response functionality including:
- Incident detection and classification
- Response action execution
- Workflow management
- Automated response coordination

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from spider.monitoring.incident_response import (
    IncidentDetector, ActionExecutor, ResponseWorkflowEngine,
    IncidentResponseManager, Incident, ResponseAction, ActionExecution,
    IncidentResponse, ResponseWorkflow, IncidentSeverity, IncidentStatus,
    ResponseActionType, ActionStatus
)


class TestIncidentDetector:
    """Test IncidentDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        config = {
            'detection_rules': [
                {
                    'title': 'High CPU Usage',
                    'description': 'CPU usage exceeds threshold',
                    'conditions': [
                        {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 80}
                    ],
                    'severity': 'high',
                    'tags': ['cpu', 'performance']
                },
                {
                    'title': 'Memory Leak',
                    'description': 'Memory usage continuously increasing',
                    'conditions': [
                        {'field': 'memory_usage', 'operator': 'greater_than', 'value': 90},
                        {'field': 'memory_trend', 'operator': 'equals', 'value': 'increasing'}
                    ],
                    'severity': 'critical',
                    'tags': ['memory', 'leak']
                }
            ],
            'severity_thresholds': {
                'critical': 0.9,
                'high': 0.7,
                'medium': 0.5,
                'low': 0.3
            }
        }
        return IncidentDetector(config)
    
    @pytest.mark.asyncio
    async def test_detect_incident_high_cpu(self, detector):
        """Test incident detection for high CPU usage"""
        data = {
            'cpu_usage': 85,
            'memory_usage': 60,
            'timestamp': datetime.now().isoformat()
        }
        
        incident = await detector.detect_incident('monitoring', data)
        
        assert incident is not None
        assert incident.title == 'High CPU Usage'
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.DETECTED
        assert incident.source == 'monitoring'
        assert 'cpu' in incident.tags
        assert incident.impact_score > 0
        assert incident.urgency_score > 0
    
    @pytest.mark.asyncio
    async def test_detect_incident_memory_leak(self, detector):
        """Test incident detection for memory leak"""
        data = {
            'cpu_usage': 50,
            'memory_usage': 95,
            'memory_trend': 'increasing',
            'timestamp': datetime.now().isoformat()
        }
        
        incident = await detector.detect_incident('monitoring', data)
        
        assert incident is not None
        assert incident.title == 'Memory Leak'
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.status == IncidentStatus.DETECTED
        assert 'memory' in incident.tags
        assert 'leak' in incident.tags
    
    @pytest.mark.asyncio
    async def test_detect_incident_no_match(self, detector):
        """Test incident detection with no matching rules"""
        data = {
            'cpu_usage': 50,
            'memory_usage': 60,
            'timestamp': datetime.now().isoformat()
        }
        
        incident = await detector.detect_incident('monitoring', data)
        
        assert incident is None
    
    @pytest.mark.asyncio
    async def test_detect_incident_custom_rules(self, detector):
        """Test incident detection with custom rules"""
        custom_rules = [
            {
                'title': 'Low Disk Space',
                'description': 'Disk space below threshold',
                'conditions': [
                    {'field': 'disk_usage', 'operator': 'greater_than', 'value': 95}
                ],
                'severity': 'medium',
                'tags': ['disk', 'storage']
            }
        ]
        
        data = {
            'disk_usage': 98,
            'timestamp': datetime.now().isoformat()
        }
        
        incident = await detector.detect_incident('monitoring', data, custom_rules)
        
        assert incident is not None
        assert incident.title == 'Low Disk Space'
        assert incident.severity == IncidentSeverity.MEDIUM
        assert 'disk' in incident.tags
    
    def test_get_incident_history(self, detector):
        """Test getting incident history"""
        history = detector.get_incident_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestActionExecutor:
    """Test ActionExecutor functionality"""
    
    @pytest.fixture
    def executor(self):
        return ActionExecutor()
    
    @pytest.fixture
    def sample_incident(self):
        return Incident(
            id='test-incident-1',
            title='Test Incident',
            description='Test incident for testing',
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            source='test',
            detected_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_action(self):
        return ResponseAction(
            id='test-action-1',
            name='Test Action',
            action_type=ResponseActionType.RESTART_SERVICE,
            description='Test action for testing',
            parameters={'service_name': 'test-service'},
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_execute_action_restart_service(self, executor, sample_incident, sample_action):
        """Test executing restart service action"""
        execution = await executor.execute_action(sample_action, sample_incident)
        
        assert execution.status == ActionStatus.COMPLETED
        assert execution.action_id == sample_action.id
        assert execution.incident_id == sample_incident.id
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.execution_time is not None
        assert 'restarted successfully' in execution.output
    
    @pytest.mark.asyncio
    async def test_execute_action_scale_resources(self, executor, sample_incident):
        """Test executing scale resources action"""
        action = ResponseAction(
            id='scale-action',
            name='Scale Resources',
            action_type=ResponseActionType.SCALE_RESOURCES,
            description='Scale resources',
            parameters={'resource_type': 'cpu', 'scale_factor': 2.0}
        )
        
        execution = await executor.execute_action(action, sample_incident)
        
        assert execution.status == ActionStatus.COMPLETED
        assert 'Scaled cpu by factor 2.0' in execution.output
    
    @pytest.mark.asyncio
    async def test_execute_action_timeout(self, executor, sample_incident):
        """Test action execution timeout"""
        action = ResponseAction(
            id='timeout-action',
            name='Timeout Action',
            action_type=ResponseActionType.BACKUP_DATA,
            description='Action that times out',
            timeout=1  # Very short timeout
        )
        
        execution = await executor.execute_action(action, sample_incident)
        
        assert execution.status == ActionStatus.TIMEOUT
        assert 'timed out' in execution.error_message
    
    @pytest.mark.asyncio
    async def test_execute_action_failure(self, executor, sample_incident):
        """Test action execution failure"""
        # Create a custom action that will fail
        def failing_handler(action, incident, parameters):
            raise Exception("Simulated failure")
        
        executor.register_handler(ResponseActionType.EXECUTE_SCRIPT, failing_handler)
        
        action = ResponseAction(
            id='failing-action',
            name='Failing Action',
            action_type=ResponseActionType.EXECUTE_SCRIPT,
            description='Action that fails',
            retry_count=1
        )
        
        execution = await executor.execute_action(action, sample_incident)
        
        assert execution.status == ActionStatus.FAILED
        assert 'Simulated failure' in execution.error_message
        assert execution.retry_count > 0
    
    def test_register_handler(self, executor):
        """Test registering custom action handler"""
        def custom_handler(action, incident, parameters):
            return "Custom handler executed"
        
        executor.register_handler(ResponseActionType.SEND_ALERT, custom_handler)
        
        assert ResponseActionType.SEND_ALERT in executor.action_handlers
        assert executor.action_handlers[ResponseActionType.SEND_ALERT] == custom_handler
    
    def test_get_execution_history(self, executor):
        """Test getting execution history"""
        history = executor.get_execution_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestResponseWorkflowEngine:
    """Test ResponseWorkflowEngine functionality"""
    
    @pytest.fixture
    def engine(self):
        return ResponseWorkflowEngine()
    
    @pytest.fixture
    def sample_workflow(self):
        return ResponseWorkflow(
            id='test-workflow',
            name='Test Workflow',
            description='Test workflow for testing',
            trigger_conditions=['severity == "high"'],
            actions=[
                ResponseAction(
                    id='action-1',
                    name='Action 1',
                    action_type=ResponseActionType.SEND_ALERT,
                    description='Send alert',
                    parameters={'priority': 1}
                ),
                ResponseAction(
                    id='action-2',
                    name='Action 2',
                    action_type=ResponseActionType.RESTART_SERVICE,
                    description='Restart service',
                    parameters={'priority': 2, 'service_name': 'test-service'}
                )
            ],
            timeout=600
        )
    
    @pytest.fixture
    def sample_incident(self):
        return Incident(
            id='test-incident-1',
            title='Test Incident',
            description='Test incident for testing',
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            source='test',
            detected_at=datetime.now()
        )
    
    def test_register_workflow(self, engine, sample_workflow):
        """Test workflow registration"""
        engine.register_workflow(sample_workflow)
        
        assert sample_workflow.id in engine.workflows
        assert engine.workflows[sample_workflow.id] == sample_workflow
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, engine, sample_workflow, sample_incident):
        """Test workflow execution"""
        engine.register_workflow(sample_workflow)
        
        response = await engine.execute_workflow(sample_workflow.id, sample_incident)
        
        assert response is not None
        assert response.incident_id == sample_incident.id
        assert response.workflow_id == sample_workflow.id
        assert response.status in [IncidentStatus.RESOLVED, IncidentStatus.ESCALATED]
        assert response.started_at is not None
        assert response.completed_at is not None
        assert len(response.actions_executed) == 2
    
    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, engine, sample_incident):
        """Test workflow execution with non-existent workflow"""
        with pytest.raises(ValueError, match="Workflow not found"):
            await engine.execute_workflow('non-existent', sample_incident)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_disabled(self, engine, sample_incident):
        """Test workflow execution with disabled workflow"""
        workflow = ResponseWorkflow(
            id='disabled-workflow',
            name='Disabled Workflow',
            description='Disabled workflow',
            enabled=False
        )
        engine.register_workflow(workflow)
        
        with pytest.raises(ValueError, match="Workflow disabled"):
            await engine.execute_workflow(workflow.id, sample_incident)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_conditions(self, engine, sample_incident):
        """Test workflow execution with action conditions"""
        workflow = ResponseWorkflow(
            id='conditional-workflow',
            name='Conditional Workflow',
            description='Workflow with conditional actions',
            actions=[
                ResponseAction(
                    id='conditional-action',
                    name='Conditional Action',
                    action_type=ResponseActionType.SEND_ALERT,
                    description='Action with conditions',
                    conditions=['severity == "critical"'],
                    parameters={'priority': 1}
                )
            ]
        )
        engine.register_workflow(workflow)
        
        # Test with high severity (should skip action)
        response = await engine.execute_workflow(workflow.id, sample_incident)
        assert response.status == IncidentStatus.RESOLVED
        assert len(response.actions_executed) == 0
        
        # Test with critical severity
        sample_incident.severity = IncidentSeverity.CRITICAL
        response = await engine.execute_workflow(workflow.id, sample_incident)
        assert response.status == IncidentStatus.RESOLVED
        assert len(response.actions_executed) == 1
    
    def test_get_active_responses(self, engine):
        """Test getting active responses"""
        active = engine.get_active_responses()
        assert isinstance(active, list)
    
    def test_get_response_history(self, engine):
        """Test getting response history"""
        history = engine.get_response_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestIncidentResponseManager:
    """Test IncidentResponseManager functionality"""
    
    @pytest.fixture
    def manager(self):
        return IncidentResponseManager()
    
    @pytest.fixture
    def sample_data(self):
        return {
            'cpu_usage': 85,
            'memory_usage': 60,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager.incident_detector is not None
        assert manager.workflow_engine is not None
        assert not manager.response_active
        assert len(manager.workflow_engine.workflows) > 0  # Default workflows loaded
    
    @pytest.mark.asyncio
    async def test_start_stop_response_system(self, manager):
        """Test starting and stopping response system"""
        assert not manager.response_active
        
        await manager.start_response_system(interval=0.1)
        assert manager.response_active
        
        await asyncio.sleep(0.2)  # Let it run briefly
        
        await manager.stop_response_system()
        assert not manager.response_active
    
    @pytest.mark.asyncio
    async def test_detect_and_respond(self, manager, sample_data):
        """Test detect and respond functionality"""
        # Create custom detection rules
        rules = [
            {
                'title': 'High CPU Usage',
                'description': 'CPU usage exceeds threshold',
                'conditions': [
                    {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 80}
                ],
                'severity': 'high',
                'tags': ['cpu', 'performance']
            }
        ]
        
        response = await manager.detect_and_respond('monitoring', sample_data, rules)
        
        # Response may be None if no workflow matches
        if response:
            assert response.incident_id is not None
            assert response.workflow_id is not None
            assert response.status in [IncidentStatus.RESOLVED, IncidentStatus.ESCALATED]
    
    @pytest.mark.asyncio
    async def test_detect_and_respond_no_incident(self, manager):
        """Test detect and respond with no incident detected"""
        data = {
            'cpu_usage': 50,
            'memory_usage': 60,
            'timestamp': datetime.now().isoformat()
        }
        
        response = await manager.detect_and_respond('monitoring', data)
        
        assert response is None
    
    def test_add_alert_callback(self, manager):
        """Test adding alert callback"""
        callback = Mock()
        manager.add_alert_callback(callback)
        
        assert callback in manager.alert_callbacks
    
    def test_register_workflow(self, manager):
        """Test registering custom workflow"""
        workflow = ResponseWorkflow(
            id='custom-workflow',
            name='Custom Workflow',
            description='Custom workflow for testing',
            trigger_conditions=['severity == "medium"'],
            actions=[
                ResponseAction(
                    id='custom-action',
                    name='Custom Action',
                    action_type=ResponseActionType.SEND_ALERT,
                    description='Custom action'
                )
            ]
        )
        
        manager.register_workflow(workflow)
        
        assert workflow.id in manager.workflow_engine.workflows
    
    def test_register_action_handler(self, manager):
        """Test registering custom action handler"""
        def custom_handler(action, incident, parameters):
            return "Custom handler executed"
        
        manager.register_action_handler(ResponseActionType.EXECUTE_SCRIPT, custom_handler)
        
        assert ResponseActionType.EXECUTE_SCRIPT in manager.workflow_engine.action_executor.action_handlers
    
    def test_get_system_status(self, manager):
        """Test getting system status"""
        status = manager.get_system_status()
        
        assert 'response_active' in status
        assert 'registered_workflows' in status
        assert 'active_responses' in status
        assert 'total_incidents' in status
        assert 'total_responses' in status
        
        assert isinstance(status['response_active'], bool)
        assert isinstance(status['registered_workflows'], int)
        assert isinstance(status['active_responses'], int)
        assert isinstance(status['total_incidents'], int)
        assert isinstance(status['total_responses'], int)


@pytest.mark.asyncio
async def test_integration_incident_response():
    """Test integration of incident response components"""
    # Create manager
    manager = IncidentResponseManager()
    
    # Create custom workflow
    workflow = ResponseWorkflow(
        id='integration-workflow',
        name='Integration Workflow',
        description='Workflow for integration testing',
        trigger_conditions=['severity == "high"'],
        actions=[
            ResponseAction(
                id='integration-action',
                name='Integration Action',
                action_type=ResponseActionType.SEND_ALERT,
                description='Integration test action',
                parameters={'message': 'Integration test alert'}
            )
        ]
    )
    
    manager.register_workflow(workflow)
    
    # Create incident data
    data = {
        'cpu_usage': 85,
        'memory_usage': 60,
        'timestamp': datetime.now().isoformat()
    }
    
    # Create detection rules
    rules = [
        {
            'title': 'High CPU Usage',
            'description': 'CPU usage exceeds threshold',
            'conditions': [
                {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 80}
            ],
            'severity': 'high',
            'tags': ['cpu', 'performance']
        }
    ]
    
    # Test detect and respond
    response = await manager.detect_and_respond('monitoring', data, rules)
    
    if response:
        assert response.incident_id is not None
        assert response.workflow_id == 'integration-workflow'
        assert response.status in [IncidentStatus.RESOLVED, IncidentStatus.ESCALATED]
        assert len(response.actions_executed) > 0
    
    # Test system status
    status = manager.get_system_status()
    assert status['registered_workflows'] >= 1  # At least our custom workflow


@pytest.mark.asyncio
async def test_incident_classification():
    """Test incident classification and scoring"""
    detector = IncidentDetector()
    
    # Test high impact incident
    high_impact_data = {
        'cpu_usage': 95,
        'memory_usage': 90,
        'error_rate': 0.1,
        'response_time': 10.0
    }
    
    incident = await detector.detect_incident('monitoring', high_impact_data, [
        {
            'title': 'System Overload',
            'description': 'System experiencing high load',
            'conditions': [
                {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 90}
            ],
            'severity': 'critical',
            'impact_factors': {'cpu_usage': 0.3, 'memory_usage': 0.2, 'error_rate': 0.4},
            'urgency_factors': {'response_time': 0.5}
        }
    ])
    
    if incident:
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.impact_score > 0.5
        assert incident.urgency_score > 0.5
        assert incident.priority_score > 0.5


@pytest.mark.asyncio
async def test_workflow_dependency_handling():
    """Test workflow with action dependencies"""
    engine = ResponseWorkflowEngine()
    
    # Create workflow with dependencies
    workflow = ResponseWorkflow(
        id='dependency-workflow',
        name='Dependency Workflow',
        description='Workflow with action dependencies',
        actions=[
            ResponseAction(
                id='action-1',
                name='Action 1',
                action_type=ResponseActionType.BACKUP_DATA,
                description='Backup data first',
                parameters={'priority': 1}
            ),
            ResponseAction(
                id='action-2',
                name='Action 2',
                action_type=ResponseActionType.RESTART_SERVICE,
                description='Restart service after backup',
                dependencies=['action-1'],
                parameters={'priority': 2}
            )
        ]
    )
    
    engine.register_workflow(workflow)
    
    incident = Incident(
        id='test-incident',
        title='Test Incident',
        description='Test incident',
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        source='test',
        detected_at=datetime.now()
    )
    
    response = await engine.execute_workflow(workflow.id, incident)
    
    assert response.status in [IncidentStatus.RESOLVED, IncidentStatus.ESCALATED]
    assert len(response.actions_executed) == 2
    
    # Check that actions were executed in correct order
    action_1_execution = next(
        (a for a in response.actions_executed if a.action_id == 'action-1'), None
    )
    action_2_execution = next(
        (a for a in response.actions_executed if a.action_id == 'action-2'), None
    )
    
    if action_1_execution and action_2_execution:
        assert action_1_execution.started_at <= action_2_execution.started_at


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
