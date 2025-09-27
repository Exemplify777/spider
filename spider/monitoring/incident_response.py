"""
Automated Incident Response Module

This module implements intelligent incident response systems that can:
- Automatically detect and classify incidents
- Execute predefined response procedures
- Escalate incidents based on severity and impact
- Coordinate multi-step response workflows
- Learn from incident patterns to improve responses
- Integrate with external systems and tools

Author: SPIDER Development Team
Version: 1.0.0
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import uuid
import traceback

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status states"""
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class ResponseActionType(Enum):
    """Types of response actions"""
    RESTART_SERVICE = "restart_service"
    SCALE_RESOURCES = "scale_resources"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    ENABLE_CIRCUIT_BREAKER = "enable_circuit_breaker"
    SEND_ALERT = "send_alert"
    EXECUTE_SCRIPT = "execute_script"
    UPDATE_CONFIGURATION = "update_configuration"
    ISOLATE_SYSTEM = "isolate_system"
    BACKUP_DATA = "backup_data"
    NOTIFY_TEAM = "notify_team"


class ActionStatus(Enum):
    """Action execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class Incident:
    """Incident representation"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    impact_score: float = 0.0
    urgency_score: float = 0.0
    priority_score: float = 0.0


@dataclass
class ResponseAction:
    """Response action definition"""
    id: str
    name: str
    action_type: ResponseActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 30  # seconds
    conditions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ActionExecution:
    """Action execution record"""
    id: str
    action_id: str
    incident_id: str
    status: ActionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    retry_count: int = 0
    execution_time: Optional[float] = None


@dataclass
class ResponseWorkflow:
    """Response workflow definition"""
    id: str
    name: str
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    actions: List[ResponseAction] = field(default_factory=list)
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    timeout: int = 3600  # 1 hour
    enabled: bool = True
    priority: int = 1


@dataclass
class IncidentResponse:
    """Incident response execution"""
    id: str
    incident_id: str
    workflow_id: str
    status: IncidentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions_executed: List[ActionExecution] = field(default_factory=list)
    current_action: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class IncidentDetector:
    """Detects and classifies incidents from various sources"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.detection_rules = self.config.get('detection_rules', [])
        self.severity_thresholds = self.config.get('severity_thresholds', {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        })
        self.incident_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    async def detect_incident(
        self,
        source: str,
        data: Dict[str, Any],
        rules: Optional[List[Dict]] = None
    ) -> Optional[Incident]:
        """Detect incident from source data"""
        try:
            rules = rules or self.detection_rules
            
            for rule in rules:
                if await self._matches_rule(data, rule):
                    incident = await self._create_incident(source, data, rule)
                    if incident:
                        with self.lock:
                            self.incident_history.append(incident)
                        return incident
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting incident: {e}")
            return None
    
    async def _matches_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if data matches detection rule"""
        try:
            conditions = rule.get('conditions', [])
            
            for condition in conditions:
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if not self._evaluate_condition(data.get(field), operator, value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return False
    
    def _evaluate_condition(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate a single condition"""
        try:
            if operator == 'equals':
                return field_value == expected_value
            elif operator == 'not_equals':
                return field_value != expected_value
            elif operator == 'greater_than':
                return float(field_value) > float(expected_value)
            elif operator == 'less_than':
                return float(field_value) < float(expected_value)
            elif operator == 'contains':
                return expected_value in str(field_value)
            elif operator == 'regex':
                import re
                return bool(re.search(expected_value, str(field_value)))
            elif operator == 'in':
                return field_value in expected_value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    async def _create_incident(
        self,
        source: str,
        data: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> Optional[Incident]:
        """Create incident from matched rule"""
        try:
            # Calculate severity based on data and rule
            severity = await self._calculate_severity(data, rule)
            
            # Calculate impact and urgency scores
            impact_score = await self._calculate_impact_score(data, rule)
            urgency_score = await self._calculate_urgency_score(data, rule)
            priority_score = (impact_score + urgency_score) / 2
            
            incident = Incident(
                id=str(uuid.uuid4()),
                title=rule.get('title', f"Incident from {source}"),
                description=rule.get('description', f"Incident detected: {data}"),
                severity=severity,
                status=IncidentStatus.DETECTED,
                source=source,
                detected_at=datetime.now(),
                tags=rule.get('tags', []),
                metadata=data,
                impact_score=impact_score,
                urgency_score=urgency_score,
                priority_score=priority_score
            )
            
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return None
    
    async def _calculate_severity(self, data: Dict[str, Any], rule: Dict[str, Any]) -> IncidentSeverity:
        """Calculate incident severity"""
        try:
            # Get severity from rule or calculate based on data
            if 'severity' in rule:
                return IncidentSeverity(rule['severity'])
            
            # Calculate based on impact and urgency
            impact_score = await self._calculate_impact_score(data, rule)
            urgency_score = await self._calculate_urgency_score(data, rule)
            combined_score = (impact_score + urgency_score) / 2
            
            if combined_score >= self.severity_thresholds['critical']:
                return IncidentSeverity.CRITICAL
            elif combined_score >= self.severity_thresholds['high']:
                return IncidentSeverity.HIGH
            elif combined_score >= self.severity_thresholds['medium']:
                return IncidentSeverity.MEDIUM
            else:
                return IncidentSeverity.LOW
                
        except Exception as e:
            logger.error(f"Error calculating severity: {e}")
            return IncidentSeverity.LOW
    
    async def _calculate_impact_score(self, data: Dict[str, Any], rule: Dict[str, Any]) -> float:
        """Calculate impact score (0.0 to 1.0)"""
        try:
            # Base impact from rule
            base_impact = rule.get('impact_score', 0.5)
            
            # Adjust based on data values
            impact_factors = rule.get('impact_factors', {})
            for factor, weight in impact_factors.items():
                if factor in data:
                    value = float(data[factor])
                    # Normalize value to 0-1 range
                    normalized_value = min(max(value / 100.0, 0.0), 1.0)
                    base_impact += normalized_value * weight
            
            return min(max(base_impact, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating impact score: {e}")
            return 0.5
    
    async def _calculate_urgency_score(self, data: Dict[str, Any], rule: Dict[str, Any]) -> float:
        """Calculate urgency score (0.0 to 1.0)"""
        try:
            # Base urgency from rule
            base_urgency = rule.get('urgency_score', 0.5)
            
            # Adjust based on time-sensitive factors
            urgency_factors = rule.get('urgency_factors', {})
            for factor, weight in urgency_factors.items():
                if factor in data:
                    value = float(data[factor])
                    # Higher values increase urgency
                    normalized_value = min(max(value / 100.0, 0.0), 1.0)
                    base_urgency += normalized_value * weight
            
            return min(max(base_urgency, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating urgency score: {e}")
            return 0.5
    
    def get_incident_history(self, limit: int = 100) -> List[Incident]:
        """Get recent incident history"""
        with self.lock:
            return list(self.incident_history)[-limit:]


class ActionExecutor:
    """Executes response actions"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.action_handlers = {}
        self.execution_history = deque(maxlen=1000)
        self.lock = threading.Lock()
        
        # Register default action handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default action handlers"""
        self.action_handlers = {
            ResponseActionType.RESTART_SERVICE: self._restart_service,
            ResponseActionType.SCALE_RESOURCES: self._scale_resources,
            ResponseActionType.ROLLBACK_DEPLOYMENT: self._rollback_deployment,
            ResponseActionType.ENABLE_CIRCUIT_BREAKER: self._enable_circuit_breaker,
            ResponseActionType.SEND_ALERT: self._send_alert,
            ResponseActionType.EXECUTE_SCRIPT: self._execute_script,
            ResponseActionType.UPDATE_CONFIGURATION: self._update_configuration,
            ResponseActionType.ISOLATE_SYSTEM: self._isolate_system,
            ResponseActionType.BACKUP_DATA: self._backup_data,
            ResponseActionType.NOTIFY_TEAM: self._notify_team
        }
    
    async def execute_action(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ActionExecution:
        """Execute a response action"""
        execution_id = str(uuid.uuid4())
        started_at = datetime.now()
        
        execution = ActionExecution(
            id=execution_id,
            action_id=action.id,
            incident_id=incident.id,
            status=ActionStatus.RUNNING,
            started_at=started_at
        )
        
        try:
            # Get action handler
            handler = self.action_handlers.get(action.action_type)
            if not handler:
                raise ValueError(f"No handler for action type: {action.action_type}")
            
            # Execute action with timeout
            result = await asyncio.wait_for(
                handler(action, incident, parameters or {}),
                timeout=action.timeout
            )
            
            execution.status = ActionStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.output = str(result)
            execution.execution_time = (execution.completed_at - started_at).total_seconds()
            
        except asyncio.TimeoutError:
            execution.status = ActionStatus.TIMEOUT
            execution.completed_at = datetime.now()
            execution.error_message = f"Action timed out after {action.timeout} seconds"
            execution.execution_time = action.timeout
            
        except Exception as e:
            execution.status = ActionStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error_message = str(e)
            execution.execution_time = (execution.completed_at - started_at).total_seconds()
            
            # Retry if configured
            if execution.retry_count < action.retry_count:
                execution.retry_count += 1
                await asyncio.sleep(action.retry_delay)
                return await self.execute_action(action, incident, parameters)
        
        # Store execution record
        with self.lock:
            self.execution_history.append(execution)
        
        return execution
    
    async def _restart_service(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Restart a service"""
        service_name = parameters.get('service_name', 'unknown')
        logger.info(f"Restarting service: {service_name}")
        
        # Simulate service restart
        await asyncio.sleep(2)
        
        return f"Service {service_name} restarted successfully"
    
    async def _scale_resources(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Scale resources"""
        resource_type = parameters.get('resource_type', 'cpu')
        scale_factor = parameters.get('scale_factor', 2.0)
        
        logger.info(f"Scaling {resource_type} by factor {scale_factor}")
        
        # Simulate resource scaling
        await asyncio.sleep(3)
        
        return f"Scaled {resource_type} by factor {scale_factor}"
    
    async def _rollback_deployment(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Rollback deployment"""
        version = parameters.get('version', 'previous')
        
        logger.info(f"Rolling back deployment to version: {version}")
        
        # Simulate rollback
        await asyncio.sleep(5)
        
        return f"Rolled back to version {version}"
    
    async def _enable_circuit_breaker(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Enable circuit breaker"""
        service_name = parameters.get('service_name', 'unknown')
        
        logger.info(f"Enabling circuit breaker for service: {service_name}")
        
        # Simulate circuit breaker enablement
        await asyncio.sleep(1)
        
        return f"Circuit breaker enabled for {service_name}"
    
    async def _send_alert(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Send alert notification"""
        message = parameters.get('message', incident.description)
        channel = parameters.get('channel', 'default')
        
        logger.info(f"Sending alert to {channel}: {message}")
        
        # Simulate alert sending
        await asyncio.sleep(1)
        
        return f"Alert sent to {channel}"
    
    async def _execute_script(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Execute custom script"""
        script_path = parameters.get('script_path', '')
        args = parameters.get('args', [])
        
        logger.info(f"Executing script: {script_path} with args: {args}")
        
        # Simulate script execution
        await asyncio.sleep(2)
        
        return f"Script {script_path} executed successfully"
    
    async def _update_configuration(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Update system configuration"""
        config_key = parameters.get('config_key', '')
        config_value = parameters.get('config_value', '')
        
        logger.info(f"Updating configuration: {config_key} = {config_value}")
        
        # Simulate configuration update
        await asyncio.sleep(1)
        
        return f"Configuration updated: {config_key} = {config_value}"
    
    async def _isolate_system(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Isolate system from network"""
        system_id = parameters.get('system_id', 'unknown')
        
        logger.info(f"Isolating system: {system_id}")
        
        # Simulate system isolation
        await asyncio.sleep(2)
        
        return f"System {system_id} isolated"
    
    async def _backup_data(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Backup critical data"""
        backup_path = parameters.get('backup_path', '/backup')
        
        logger.info(f"Backing up data to: {backup_path}")
        
        # Simulate data backup
        await asyncio.sleep(10)
        
        return f"Data backed up to {backup_path}"
    
    async def _notify_team(
        self,
        action: ResponseAction,
        incident: Incident,
        parameters: Dict[str, Any]
    ) -> str:
        """Notify team members"""
        team = parameters.get('team', 'oncall')
        message = parameters.get('message', incident.description)
        
        logger.info(f"Notifying team {team}: {message}")
        
        # Simulate team notification
        await asyncio.sleep(1)
        
        return f"Team {team} notified"
    
    def register_handler(self, action_type: ResponseAction, handler: Callable):
        """Register custom action handler"""
        self.action_handlers[action_type] = handler
    
    def get_execution_history(self, limit: int = 100) -> List[ActionExecution]:
        """Get recent execution history"""
        with self.lock:
            return list(self.execution_history)[-limit:]


class ResponseWorkflowEngine:
    """Manages and executes response workflows"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.workflows = {}
        self.active_responses = {}
        self.response_history = deque(maxlen=1000)
        self.action_executor = ActionExecutor(config)
        self.lock = threading.Lock()
    
    def register_workflow(self, workflow: ResponseWorkflow):
        """Register a response workflow"""
        with self.lock:
            self.workflows[workflow.id] = workflow
    
    async def execute_workflow(
        self,
        workflow_id: str,
        incident: Incident
    ) -> IncidentResponse:
        """Execute a response workflow for an incident"""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            if not workflow.enabled:
                raise ValueError(f"Workflow disabled: {workflow_id}")
            
            # Create response execution
            response_id = str(uuid.uuid4())
            response = IncidentResponse(
                id=response_id,
                incident_id=incident.id,
                workflow_id=workflow_id,
                status=IncidentStatus.INVESTIGATING,
                started_at=datetime.now()
            )
            
            # Store active response
            with self.lock:
                self.active_responses[response_id] = response
            
            # Execute workflow actions
            await self._execute_workflow_actions(workflow, incident, response)
            
            # Update response status
            if response.error_message:
                response.status = IncidentStatus.ESCALATED
            else:
                response.status = IncidentStatus.RESOLVED
            
            response.completed_at = datetime.now()
            
            # Store in history
            with self.lock:
                self.response_history.append(response)
                if response_id in self.active_responses:
                    del self.active_responses[response_id]
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            response.status = IncidentStatus.ESCALATED
            response.error_message = str(e)
            response.completed_at = datetime.now()
            
            with self.lock:
                self.response_history.append(response)
                if response_id in self.active_responses:
                    del self.active_responses[response_id]
            
            return response
    
    async def _execute_workflow_actions(
        self,
        workflow: ResponseWorkflow,
        incident: Incident,
        response: IncidentResponse
    ):
        """Execute all actions in a workflow"""
        try:
            # Sort actions by priority and dependencies
            sorted_actions = self._sort_actions(workflow.actions)
            
            for action in sorted_actions:
                if not action.enabled:
                    continue
                
                # Check if action conditions are met
                if not await self._check_action_conditions(action, incident):
                    logger.info(f"Skipping action {action.name} - conditions not met")
                    continue
                
                # Update current action
                response.current_action = action.id
                
                # Execute action
                execution = await self.action_executor.execute_action(
                    action, incident, action.parameters
                )
                
                response.actions_executed.append(execution)
                
                # Check if action failed and should stop workflow
                if execution.status == ActionStatus.FAILED:
                    if action.parameters.get('stop_on_failure', False):
                        response.error_message = f"Action {action.name} failed: {execution.error_message}"
                        break
                
                # Wait between actions if configured
                delay = action.parameters.get('delay_after', 0)
                if delay > 0:
                    await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error executing workflow actions: {e}")
            response.error_message = str(e)
    
    def _sort_actions(self, actions: List[ResponseAction]) -> List[ResponseAction]:
        """Sort actions by priority and dependencies"""
        # Simple topological sort for dependencies
        sorted_actions = []
        remaining_actions = actions.copy()
        
        while remaining_actions:
            # Find actions with no unmet dependencies
            ready_actions = []
            for action in remaining_actions:
                if not action.dependencies or all(
                    dep in [a.id for a in sorted_actions] for dep in action.dependencies
                ):
                    ready_actions.append(action)
            
            if not ready_actions:
                # Circular dependency or missing dependency
                break
            
            # Sort by priority (lower number = higher priority)
            ready_actions.sort(key=lambda a: a.parameters.get('priority', 999))
            sorted_actions.extend(ready_actions)
            
            # Remove from remaining
            for action in ready_actions:
                remaining_actions.remove(action)
        
        return sorted_actions
    
    async def _check_action_conditions(
        self,
        action: ResponseAction,
        incident: Incident
    ) -> bool:
        """Check if action conditions are met"""
        try:
            for condition in action.conditions:
                if not await self._evaluate_condition(condition, incident):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking action conditions: {e}")
            return False
    
    async def _evaluate_condition(self, condition: str, incident: Incident) -> bool:
        """Evaluate a single condition"""
        try:
            # Simple condition evaluation
            # In a real implementation, this would use a proper expression evaluator
            
            if 'severity' in condition:
                required_severity = condition.split('==')[1].strip().strip('"\'')
                return incident.severity.value == required_severity
            
            if 'impact_score' in condition:
                if '>' in condition:
                    threshold = float(condition.split('>')[1].strip())
                    return incident.impact_score > threshold
                elif '<' in condition:
                    threshold = float(condition.split('<')[1].strip())
                    return incident.impact_score < threshold
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def get_active_responses(self) -> List[IncidentResponse]:
        """Get currently active responses"""
        with self.lock:
            return list(self.active_responses.values())
    
    def get_response_history(self, limit: int = 100) -> List[IncidentResponse]:
        """Get response history"""
        with self.lock:
            return list(self.response_history)[-limit:]


class IncidentResponseManager:
    """Main incident response manager"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.incident_detector = IncidentDetector(config)
        self.workflow_engine = ResponseWorkflowEngine(config)
        self.response_active = False
        self.response_task = None
        self.alert_callbacks = []
        self.lock = threading.Lock()
        
        # Load default workflows
        self._load_default_workflows()
    
    def _load_default_workflows(self):
        """Load default response workflows"""
        # Critical incident workflow
        critical_workflow = ResponseWorkflow(
            id="critical_incident",
            name="Critical Incident Response",
            description="Response workflow for critical incidents",
            trigger_conditions=["severity == 'critical'"],
            actions=[
                ResponseAction(
                    id="notify_team",
                    name="Notify On-Call Team",
                    action_type=ResponseAction.NOTIFY_TEAM,
                    description="Immediately notify on-call team",
                    parameters={"team": "oncall", "priority": 1}
                ),
                ResponseAction(
                    id="isolate_system",
                    name="Isolate Affected System",
                    action_type=ResponseAction.ISOLATE_SYSTEM,
                    description="Isolate system to prevent further damage",
                    parameters={"priority": 2}
                ),
                ResponseAction(
                    id="backup_data",
                    name="Backup Critical Data",
                    action_type=ResponseAction.BACKUP_DATA,
                    description="Backup critical data before remediation",
                    parameters={"priority": 3}
                )
            ],
            timeout=1800,  # 30 minutes
            priority=1
        )
        
        # High severity workflow
        high_workflow = ResponseWorkflow(
            id="high_incident",
            name="High Severity Incident Response",
            description="Response workflow for high severity incidents",
            trigger_conditions=["severity == 'high'"],
            actions=[
                ResponseAction(
                    id="send_alert",
                    name="Send Alert",
                    action_type=ResponseAction.SEND_ALERT,
                    description="Send alert to monitoring team",
                    parameters={"priority": 1}
                ),
                ResponseAction(
                    id="restart_service",
                    name="Restart Service",
                    action_type=ResponseAction.RESTART_SERVICE,
                    description="Restart affected service",
                    parameters={"priority": 2}
                )
            ],
            timeout=900,  # 15 minutes
            priority=2
        )
        
        # Register workflows
        self.workflow_engine.register_workflow(critical_workflow)
        self.workflow_engine.register_workflow(high_workflow)
    
    async def start_response_system(self, interval: float = 30.0):
        """Start the incident response system"""
        if self.response_active:
            logger.warning("Response system already active")
            return
        
        self.response_active = True
        self.response_task = asyncio.create_task(
            self._response_loop(interval)
        )
        logger.info("Incident response system started")
    
    async def stop_response_system(self):
        """Stop the incident response system"""
        self.response_active = False
        if self.response_task:
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass
        logger.info("Incident response system stopped")
    
    async def _response_loop(self, interval: float):
        """Main response monitoring loop"""
        while self.response_active:
            try:
                await self._process_pending_incidents()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in response loop: {e}")
                await asyncio.sleep(interval)
    
    async def _process_pending_incidents(self):
        """Process pending incidents"""
        try:
            # Get recent incidents
            recent_incidents = self.incident_detector.get_incident_history(10)
            
            for incident in recent_incidents:
                if incident.status == IncidentStatus.DETECTED:
                    await self._handle_incident(incident)
            
        except Exception as e:
            logger.error(f"Error processing pending incidents: {e}")
    
    async def _handle_incident(self, incident: Incident):
        """Handle a detected incident"""
        try:
            logger.info(f"Handling incident: {incident.id} - {incident.title}")
            
            # Find appropriate workflow
            workflow_id = await self._select_workflow(incident)
            if not workflow_id:
                logger.warning(f"No workflow found for incident: {incident.id}")
                return
            
            # Execute workflow
            response = await self.workflow_engine.execute_workflow(workflow_id, incident)
            
            # Trigger alert callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback('incident_response', response)
                except Exception as e:
                    logger.error(f"Error in response callback: {e}")
            
        except Exception as e:
            logger.error(f"Error handling incident {incident.id}: {e}")
    
    async def _select_workflow(self, incident: Incident) -> Optional[str]:
        """Select appropriate workflow for incident"""
        try:
            # Find workflow that matches incident conditions
            for workflow in self.workflow_engine.workflows.values():
                if not workflow.enabled:
                    continue
                
                # Check trigger conditions
                if await self._matches_workflow_conditions(workflow, incident):
                    return workflow.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting workflow: {e}")
            return None
    
    async def _matches_workflow_conditions(
        self,
        workflow: ResponseWorkflow,
        incident: Incident
    ) -> bool:
        """Check if incident matches workflow conditions"""
        try:
            for condition in workflow.trigger_conditions:
                if not await self._evaluate_workflow_condition(condition, incident):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error evaluating workflow conditions: {e}")
            return False
    
    async def _evaluate_workflow_condition(self, condition: str, incident: Incident) -> bool:
        """Evaluate a workflow condition"""
        try:
            if 'severity' in condition:
                if '==' in condition:
                    required_severity = condition.split('==')[1].strip().strip('"\'')
                    return incident.severity.value == required_severity
                elif '>=' in condition:
                    severity_levels = ['low', 'medium', 'high', 'critical']
                    required_level = condition.split('>=')[1].strip().strip('"\'')
                    incident_level = incident.severity.value
                    return severity_levels.index(incident_level) >= severity_levels.index(required_level)
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating workflow condition: {e}")
            return False
    
    async def detect_and_respond(
        self,
        source: str,
        data: Dict[str, Any],
        rules: Optional[List[Dict]] = None
    ) -> Optional[IncidentResponse]:
        """Detect incident and trigger response"""
        try:
            # Detect incident
            incident = await self.incident_detector.detect_incident(source, data, rules)
            if not incident:
                return None
            
            # Handle incident
            await self._handle_incident(incident)
            
            # Return response if available
            active_responses = self.workflow_engine.get_active_responses()
            for response in active_responses:
                if response.incident_id == incident.id:
                    return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error in detect and respond: {e}")
            return None
    
    def add_alert_callback(self, callback):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def register_workflow(self, workflow: ResponseWorkflow):
        """Register a custom workflow"""
        self.workflow_engine.register_workflow(workflow)
    
    def register_action_handler(self, action_type: ResponseAction, handler: Callable):
        """Register custom action handler"""
        self.workflow_engine.action_executor.register_handler(action_type, handler)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get incident response system status"""
        return {
            'response_active': self.response_active,
            'registered_workflows': len(self.workflow_engine.workflows),
            'active_responses': len(self.workflow_engine.get_active_responses()),
            'total_incidents': len(self.incident_detector.get_incident_history()),
            'total_responses': len(self.workflow_engine.get_response_history())
        }
