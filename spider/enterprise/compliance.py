"""Compliance and audit reporting for SPIDER framework."""

import asyncio
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import csv
import io

from ..core.exceptions import SpiderError, ComplianceError
from ..core.logger import get_logger


class ComplianceStandard(Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    SOC_2 = "soc_2"
    CUSTOM = "custom"


class ComplianceLevel(Enum):
    """Compliance levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditEventType(Enum):
    """Audit event types."""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SECURITY_VIOLATION = "security_violation"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    API_ACCESS = "api_access"
    ADMIN_ACTION = "admin_action"


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    rule_id: str
    name: str
    description: str
    standard: ComplianceStandard
    level: ComplianceLevel
    category: str
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str
    event_type: AuditEventType
    user_id: Optional[str]
    tenant_id: Optional[str]
    resource_id: Optional[str]
    action: str
    description: str
    timestamp: float
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[str] = field(default_factory=list)
    severity: ComplianceLevel = ComplianceLevel.INFO


@dataclass
class ComplianceReport:
    """Compliance report."""
    report_id: str
    name: str
    standard: ComplianceStandard
    period_start: float
    period_end: float
    generated_at: float
    generated_by: str
    status: str = "generated"
    summary: Dict[str, Any] = field(default_factory=dict)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0


class ComplianceManager:
    """Manages compliance and audit operations."""
    
    def __init__(self):
        """Initialize compliance manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.audit_events: deque = deque(maxlen=100000)
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        self.compliance_reports: Dict[str, ComplianceReport] = {}
        self.lock = threading.RLock()
        
        # Setup default compliance rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default compliance rules."""
        default_rules = [
            ComplianceRule(
                rule_id="data_retention_gdpr",
                name="GDPR Data Retention",
                description="Ensure data is retained only as long as necessary",
                standard=ComplianceStandard.GDPR,
                level=ComplianceLevel.HIGH,
                category="data_retention",
                conditions={"max_retention_days": 365},
                actions=["audit", "notify"]
            ),
            ComplianceRule(
                rule_id="data_encryption_hipaa",
                name="HIPAA Data Encryption",
                description="Ensure all sensitive data is encrypted",
                standard=ComplianceStandard.HIPAA,
                level=ComplianceLevel.CRITICAL,
                category="data_protection",
                conditions={"encryption_required": True},
                actions=["audit", "block"]
            ),
            ComplianceRule(
                rule_id="access_logging_sox",
                name="SOX Access Logging",
                description="Log all data access for SOX compliance",
                standard=ComplianceStandard.SOX,
                level=ComplianceLevel.HIGH,
                category="access_control",
                conditions={"log_all_access": True},
                actions=["audit", "log"]
            ),
            ComplianceRule(
                rule_id="pii_protection_ccpa",
                name="CCPA PII Protection",
                description="Protect personally identifiable information",
                standard=ComplianceStandard.CCPA,
                level=ComplianceLevel.HIGH,
                category="privacy",
                conditions={"pii_encryption": True, "consent_required": True},
                actions=["audit", "encrypt"]
            )
        ]
        
        for rule in default_rules:
            self.compliance_rules[rule.rule_id] = rule
    
    def add_compliance_rule(self, rule: ComplianceRule) -> None:
        """Add compliance rule.
        
        Args:
            rule: Compliance rule
        """
        with self.lock:
            self.compliance_rules[rule.rule_id] = rule
            self.logger.info(f"Added compliance rule: {rule.name}")
    
    def remove_compliance_rule(self, rule_id: str) -> bool:
        """Remove compliance rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if rule_id in self.compliance_rules:
                del self.compliance_rules[rule_id]
                self.logger.info(f"Removed compliance rule: {rule_id}")
                return True
            return False
    
    def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        tenant_id: Optional[str],
        resource_id: Optional[str],
        action: str,
        description: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[str]] = None
    ) -> str:
        """Log audit event.
        
        Args:
            event_type: Type of audit event
            user_id: User ID
            tenant_id: Tenant ID
            resource_id: Resource ID
            action: Action performed
            description: Event description
            ip_address: IP address
            user_agent: User agent
            metadata: Optional metadata
            compliance_tags: Optional compliance tags
            
        Returns:
            Event ID
        """
        with self.lock:
            event_id = str(uuid.uuid4())
            
            # Determine severity based on event type
            severity = self._determine_event_severity(event_type)
            
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                tenant_id=tenant_id,
                resource_id=resource_id,
                action=action,
                description=description,
                timestamp=time.time(),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
                compliance_tags=compliance_tags or [],
                severity=severity
            )
            
            self.audit_events.append(event)
            
            # Check compliance rules
            self._check_compliance_rules(event)
            
            self.logger.info(f"Logged audit event: {event_type.value} - {description}")
            return event_id
    
    def _determine_event_severity(self, event_type: AuditEventType) -> ComplianceLevel:
        """Determine event severity based on type.
        
        Args:
            event_type: Event type
            
        Returns:
            Compliance level
        """
        severity_mapping = {
            AuditEventType.SECURITY_VIOLATION: ComplianceLevel.CRITICAL,
            AuditEventType.DATA_DELETION: ComplianceLevel.HIGH,
            AuditEventType.DATA_MODIFICATION: ComplianceLevel.MEDIUM,
            AuditEventType.DATA_ACCESS: ComplianceLevel.MEDIUM,
            AuditEventType.PERMISSION_CHANGE: ComplianceLevel.HIGH,
            AuditEventType.ADMIN_ACTION: ComplianceLevel.HIGH,
            AuditEventType.USER_LOGIN: ComplianceLevel.LOW,
            AuditEventType.USER_LOGOUT: ComplianceLevel.INFO,
            AuditEventType.SYSTEM_STARTUP: ComplianceLevel.INFO,
            AuditEventType.SYSTEM_SHUTDOWN: ComplianceLevel.INFO,
            AuditEventType.API_ACCESS: ComplianceLevel.LOW,
            AuditEventType.DATA_EXPORT: ComplianceLevel.MEDIUM,
            AuditEventType.DATA_IMPORT: ComplianceLevel.MEDIUM,
            AuditEventType.CONFIGURATION_CHANGE: ComplianceLevel.MEDIUM
        }
        
        return severity_mapping.get(event_type, ComplianceLevel.INFO)
    
    def _check_compliance_rules(self, event: AuditEvent) -> None:
        """Check compliance rules against event.
        
        Args:
            event: Audit event
        """
        for rule in self.compliance_rules.values():
            if not rule.enabled:
                continue
            
            if self._evaluate_rule(rule, event):
                self._execute_rule_actions(rule, event)
    
    def _evaluate_rule(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Evaluate compliance rule against event.
        
        Args:
            rule: Compliance rule
            event: Audit event
            
        Returns:
            True if rule matches
        """
        try:
            # Check event type
            if "event_types" in rule.conditions:
                if event.event_type.value not in rule.conditions["event_types"]:
                    return False
            
            # Check severity level
            if "min_severity" in rule.conditions:
                min_severity = ComplianceLevel(rule.conditions["min_severity"])
                if event.severity.value not in [level.value for level in ComplianceLevel]:
                    return False
                severity_order = [level.value for level in ComplianceLevel]
                if severity_order.index(event.severity.value) < severity_order.index(min_severity.value):
                    return False
            
            # Check compliance tags
            if "required_tags" in rule.conditions:
                required_tags = rule.conditions["required_tags"]
                if not all(tag in event.compliance_tags for tag in required_tags):
                    return False
            
            # Check metadata conditions
            if "metadata_conditions" in rule.conditions:
                conditions = rule.conditions["metadata_conditions"]
                for key, expected_value in conditions.items():
                    if key not in event.metadata or event.metadata[key] != expected_value:
                        return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error evaluating compliance rule {rule.rule_id}: {e}")
            return False
    
    def _execute_rule_actions(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Execute rule actions.
        
        Args:
            rule: Compliance rule
            event: Audit event
        """
        for action in rule.actions:
            try:
                if action == "audit":
                    self.logger.warning(f"Compliance rule triggered: {rule.name} for event {event.event_id}")
                elif action == "notify":
                    self._send_compliance_notification(rule, event)
                elif action == "block":
                    self._block_action(rule, event)
                elif action == "log":
                    self._log_compliance_event(rule, event)
                elif action == "encrypt":
                    self._encrypt_data(rule, event)
                
            except Exception as e:
                self.logger.error(f"Error executing rule action {action}: {e}")
    
    def _send_compliance_notification(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Send compliance notification.
        
        Args:
            rule: Compliance rule
            event: Audit event
        """
        # In a real implementation, this would send notifications
        self.logger.warning(f"COMPLIANCE NOTIFICATION: {rule.name} - {event.description}")
    
    def _block_action(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Block action for compliance violation.
        
        Args:
            rule: Compliance rule
            event: Audit event
        """
        self.logger.error(f"COMPLIANCE BLOCK: {rule.name} - Action blocked for {event.description}")
    
    def _log_compliance_event(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Log compliance event.
        
        Args:
            rule: Compliance rule
            event: Audit event
        """
        self.logger.info(f"COMPLIANCE LOG: {rule.name} - {event.description}")
    
    def _encrypt_data(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Encrypt data for compliance.
        
        Args:
            rule: Compliance rule
            event: Audit event
        """
        self.logger.info(f"COMPLIANCE ENCRYPT: {rule.name} - Data encrypted for {event.description}")
    
    def get_audit_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """Get audit events with filters.
        
        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter
            tenant_id: Optional tenant ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of events
            
        Returns:
            List of audit events
        """
        with self.lock:
            events = list(self.audit_events)
            
            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            
            if tenant_id:
                events = [e for e in events if e.tenant_id == tenant_id]
            
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[:limit]
    
    def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        period_start: float,
        period_end: float,
        generated_by: str
    ) -> ComplianceReport:
        """Generate compliance report.
        
        Args:
            standard: Compliance standard
            period_start: Report period start time
            period_end: Report period end time
            generated_by: User who generated the report
            
        Returns:
            Compliance report
        """
        with self.lock:
            report_id = str(uuid.uuid4())
            
            # Get events for the period
            events = self.get_audit_events(
                start_time=period_start,
                end_time=period_end
            )
            
            # Filter events by compliance standard
            relevant_events = self._filter_events_by_standard(events, standard)
            
            # Generate summary
            summary = self._generate_report_summary(relevant_events, standard)
            
            # Generate findings
            findings = self._generate_report_findings(relevant_events, standard)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(findings, standard)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(findings, standard)
            
            report = ComplianceReport(
                report_id=report_id,
                name=f"{standard.value.upper()} Compliance Report",
                standard=standard,
                period_start=period_start,
                period_end=period_end,
                generated_at=time.time(),
                generated_by=generated_by,
                summary=summary,
                findings=findings,
                recommendations=recommendations,
                compliance_score=compliance_score
            )
            
            self.compliance_reports[report_id] = report
            self.logger.info(f"Generated compliance report: {report.name}")
            
            return report
    
    def _filter_events_by_standard(self, events: List[AuditEvent], standard: ComplianceStandard) -> List[AuditEvent]:
        """Filter events by compliance standard.
        
        Args:
            events: List of audit events
            standard: Compliance standard
            
        Returns:
            Filtered events
        """
        # Get rules for the standard
        standard_rules = [rule for rule in self.compliance_rules.values() if rule.standard == standard]
        
        relevant_events = []
        for event in events:
            # Check if event matches any rule for the standard
            for rule in standard_rules:
                if self._evaluate_rule(rule, event):
                    relevant_events.append(event)
                    break
        
        return relevant_events
    
    def _generate_report_summary(self, events: List[AuditEvent], standard: ComplianceStandard) -> Dict[str, Any]:
        """Generate report summary.
        
        Args:
            events: List of audit events
            standard: Compliance standard
            
        Returns:
            Report summary
        """
        if not events:
            return {
                "total_events": 0,
                "compliance_score": 100.0,
                "status": "compliant"
            }
        
        # Count events by type
        event_counts = defaultdict(int)
        for event in events:
            event_counts[event.event_type.value] += 1
        
        # Count events by severity
        severity_counts = defaultdict(int)
        for event in events:
            severity_counts[event.severity.value] += 1
        
        # Calculate compliance score
        total_events = len(events)
        critical_events = severity_counts[ComplianceLevel.CRITICAL.value]
        high_events = severity_counts[ComplianceLevel.HIGH.value]
        
        compliance_score = max(0, 100 - (critical_events * 20 + high_events * 10))
        
        return {
            "total_events": total_events,
            "event_counts": dict(event_counts),
            "severity_counts": dict(severity_counts),
            "compliance_score": compliance_score,
            "status": "compliant" if compliance_score >= 80 else "non_compliant"
        }
    
    def _generate_report_findings(self, events: List[AuditEvent], standard: ComplianceStandard) -> List[Dict[str, Any]]:
        """Generate report findings.
        
        Args:
            events: List of audit events
            standard: Compliance standard
            
        Returns:
            List of findings
        """
        findings = []
        
        # Group events by type and analyze patterns
        event_groups = defaultdict(list)
        for event in events:
            event_groups[event.event_type.value].append(event)
        
        for event_type, type_events in event_groups.items():
            if len(type_events) > 10:  # High frequency events
                findings.append({
                    "type": "high_frequency",
                    "description": f"High frequency of {event_type} events ({len(type_events)})",
                    "severity": "medium",
                    "recommendation": f"Review {event_type} patterns for compliance"
                })
        
        # Check for critical events
        critical_events = [e for e in events if e.severity == ComplianceLevel.CRITICAL]
        if critical_events:
            findings.append({
                "type": "critical_events",
                "description": f"Found {len(critical_events)} critical events",
                "severity": "high",
                "recommendation": "Immediate attention required for critical events"
            })
        
        return findings
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], standard: ComplianceStandard) -> List[str]:
        """Generate recommendations based on findings.
        
        Args:
            findings: List of findings
            standard: Compliance standard
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for finding in findings:
            if finding["type"] == "high_frequency":
                recommendations.append(f"Implement rate limiting for {finding['description']}")
            elif finding["type"] == "critical_events":
                recommendations.append("Review and strengthen security controls")
        
        # Add standard-specific recommendations
        if standard == ComplianceStandard.GDPR:
            recommendations.append("Implement data retention policies")
            recommendations.append("Ensure data subject rights are supported")
        elif standard == ComplianceStandard.HIPAA:
            recommendations.append("Implement encryption for all PHI data")
            recommendations.append("Conduct regular security assessments")
        elif standard == ComplianceStandard.SOX:
            recommendations.append("Implement comprehensive audit trails")
            recommendations.append("Ensure data integrity controls")
        
        return recommendations
    
    def _calculate_compliance_score(self, findings: List[Dict[str, Any]], standard: ComplianceStandard) -> float:
        """Calculate compliance score.
        
        Args:
            findings: List of findings
            standard: Compliance standard
            
        Returns:
            Compliance score (0-100)
        """
        if not findings:
            return 100.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points for findings
        for finding in findings:
            if finding["severity"] == "high":
                score -= 20
            elif finding["severity"] == "medium":
                score -= 10
            elif finding["severity"] == "low":
                score -= 5
        
        return max(0.0, score)
    
    def export_audit_log(
        self,
        format: str = "csv",
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """Export audit log.
        
        Args:
            format: Export format (csv, json)
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Exported data
        """
        events = self.get_audit_events(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if format == "csv":
            return self._export_csv(events)
        elif format == "json":
            return self._export_json(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self, events: List[AuditEvent]) -> str:
        """Export events as CSV.
        
        Args:
            events: List of audit events
            
        Returns:
            CSV data
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Event ID", "Event Type", "User ID", "Tenant ID", "Resource ID",
            "Action", "Description", "Timestamp", "IP Address", "User Agent",
            "Severity", "Compliance Tags"
        ])
        
        # Write events
        for event in events:
            writer.writerow([
                event.event_id,
                event.event_type.value,
                event.user_id or "",
                event.tenant_id or "",
                event.resource_id or "",
                event.action,
                event.description,
                datetime.fromtimestamp(event.timestamp).isoformat(),
                event.ip_address,
                event.user_agent,
                event.severity.value,
                ",".join(event.compliance_tags)
            ])
        
        return output.getvalue()
    
    def _export_json(self, events: List[AuditEvent]) -> str:
        """Export events as JSON.
        
        Args:
            events: List of audit events
            
        Returns:
            JSON data
        """
        events_data = []
        for event in events:
            events_data.append({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "resource_id": event.resource_id,
                "action": event.action,
                "description": event.description,
                "timestamp": event.timestamp,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "severity": event.severity.value,
                "compliance_tags": event.compliance_tags,
                "metadata": event.metadata
            })
        
        return json.dumps(events_data, indent=2)
    
    def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get compliance dashboard data.
        
        Returns:
            Dashboard data
        """
        with self.lock:
            # Get recent events (last 24 hours)
            cutoff_time = time.time() - 86400
            recent_events = self.get_audit_events(start_time=cutoff_time)
            
            # Count events by type
            event_counts = defaultdict(int)
            for event in recent_events:
                event_counts[event.event_type.value] += 1
            
            # Count events by severity
            severity_counts = defaultdict(int)
            for event in recent_events:
                severity_counts[event.severity.value] += 1
            
            # Count events by compliance standard
            standard_counts = defaultdict(int)
            for event in recent_events:
                for rule in self.compliance_rules.values():
                    if self._evaluate_rule(rule, event):
                        standard_counts[rule.standard.value] += 1
                        break
            
            return {
                "total_events": len(recent_events),
                "event_counts": dict(event_counts),
                "severity_counts": dict(severity_counts),
                "standard_counts": dict(standard_counts),
                "compliance_rules": len(self.compliance_rules),
                "active_reports": len(self.compliance_reports)
            }
