"""Advanced alerting system for SPIDER framework."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.exceptions import SpiderError, MonitoringError
from ..core.logger import get_logger
from .health import HealthStatus, SystemHealth


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    CONSOLE = "console"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    condition: Callable[[SystemHealth], bool]
    severity: AlertSeverity
    message_template: str
    channels: List[NotificationChannel]
    cooldown: int = 300  # seconds
    escalation_delay: int = 1800  # seconds
    max_escalations: int = 3
    enabled: bool = True
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    status: AlertStatus
    created_at: float
    updated_at: float
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None
    escalation_count: int = 0
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationConfig:
    """Notification configuration."""
    email: Optional[Dict[str, Any]] = None
    slack: Optional[Dict[str, Any]] = None
    webhook: Optional[Dict[str, Any]] = None
    pagerduty: Optional[Dict[str, Any]] = None


class AlertManager:
    """Manages alerts and notifications for SPIDER framework."""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        """Initialize alert manager.
        
        Args:
            config: Notification configuration
        """
        self.config = config or NotificationConfig()
        self.logger = get_logger(self.__class__.__name__)
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, float] = {}
        self.escalation_tasks: Dict[str, asyncio.Task] = {}
        
        # Initialize default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default alert rules."""
        # Critical alerts
        self.add_rule(AlertRule(
            name="service_down",
            condition=lambda health: health.overall_status == HealthStatus.UNHEALTHY,
            severity=AlertSeverity.CRITICAL,
            message_template="SPIDER service is down: {overall_status}",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.PAGERDUTY],
            cooldown=60,
            escalation_delay=300,
            tags=["service", "critical"]
        ))
        
        self.add_rule(AlertRule(
            name="database_down",
            condition=lambda health: (
                health.components.get("database", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            severity=AlertSeverity.CRITICAL,
            message_template="Database connection failed: {database_status}",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            cooldown=120,
            escalation_delay=600,
            tags=["database", "critical"]
        ))
        
        # Error alerts
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda health: (
                health.business_metrics.get("error_rate", 0) > 10
            ),
            severity=AlertSeverity.ERROR,
            message_template="High error rate detected: {error_rate}%",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            cooldown=300,
            escalation_delay=1800,
            tags=["performance", "error"]
        ))
        
        self.add_rule(AlertRule(
            name="proxy_failure",
            condition=lambda health: (
                health.components.get("proxy", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            severity=AlertSeverity.ERROR,
            message_template="Proxy service failure: {proxy_status}",
            channels=[NotificationChannel.SLACK],
            cooldown=180,
            escalation_delay=900,
            tags=["proxy", "error"]
        ))
        
        # Warning alerts
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda health: (
                health.system_metrics.get("memory_usage_percent", 0) > 85
            ),
            severity=AlertSeverity.WARNING,
            message_template="High memory usage: {memory_usage_percent}%",
            channels=[NotificationChannel.SLACK],
            cooldown=600,
            escalation_delay=3600,
            tags=["system", "memory"]
        ))
        
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda health: (
                health.system_metrics.get("cpu_usage_percent", 0) > 90
            ),
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage: {cpu_usage_percent}%",
            channels=[NotificationChannel.SLACK],
            cooldown=600,
            escalation_delay=3600,
            tags=["system", "cpu"]
        ))
        
        self.add_rule(AlertRule(
            name="low_success_rate",
            condition=lambda health: (
                health.business_metrics.get("success_rate", 100) < 80
            ),
            severity=AlertSeverity.WARNING,
            message_template="Low success rate: {success_rate}%",
            channels=[NotificationChannel.SLACK],
            cooldown=900,
            escalation_delay=1800,
            tags=["business", "performance"]
        ))
        
        # Info alerts
        self.add_rule(AlertRule(
            name="service_recovered",
            condition=lambda health: (
                health.overall_status == HealthStatus.HEALTHY and
                any(alert.status == AlertStatus.ACTIVE for alert in self.active_alerts.values())
            ),
            severity=AlertSeverity.INFO,
            message_template="SPIDER service recovered: {overall_status}",
            channels=[NotificationChannel.SLACK],
            cooldown=60,
            tags=["service", "recovery"]
        ))
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule.
        
        Args:
            rule: Alert rule to add
        """
        self.rules.append(rule)
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                self.logger.info(f"Removed alert rule: {rule_name}")
                return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable an alert rule.
        
        Args:
            rule_name: Name of rule to enable
            
        Returns:
            True if rule was enabled, False if not found
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                self.logger.info(f"Enabled alert rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable an alert rule.
        
        Args:
            rule_name: Name of rule to disable
            
        Returns:
            True if rule was disabled, False if not found
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                self.logger.info(f"Disabled alert rule: {rule_name}")
                return True
        return False
    
    async def check_alerts(self, health: SystemHealth) -> None:
        """Check health status and trigger alerts.
        
        Args:
            health: Current health status
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                if rule.condition(health):
                    await self._trigger_alert(rule, health)
                else:
                    await self._resolve_alert(rule.name, health)
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, health: SystemHealth) -> None:
        """Trigger an alert for a rule.
        
        Args:
            rule: Alert rule
            health: Current health status
        """
        # Check cooldown
        last_alert = self.last_alert_times.get(rule.name, 0)
        if time.time() - last_alert < rule.cooldown:
            return
        
        # Check if alert already exists
        if rule.name in self.active_alerts:
            return
        
        # Create alert
        alert_id = f"{rule.name}_{int(time.time())}"
        message = self._format_message(rule.message_template, health)
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            status=AlertStatus.ACTIVE,
            created_at=time.time(),
            updated_at=time.time(),
            tags=rule.tags.copy(),
            metadata={"health": asdict(health)}
        )
        
        # Store alert
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        self.last_alert_times[rule.name] = time.time()
        
        # Send notifications
        await self._send_notifications(alert, rule.channels)
        
        # Schedule escalation
        if rule.escalation_delay > 0:
            self.escalation_tasks[rule.name] = asyncio.create_task(
                self._schedule_escalation(rule, alert)
            )
        
        self.logger.warning(f"Alert triggered: {rule.name} - {message}")
    
    async def _resolve_alert(self, rule_name: str, health: SystemHealth) -> None:
        """Resolve an alert if it exists.
        
        Args:
            rule_name: Name of the rule
            health: Current health status
        """
        if rule_name not in self.active_alerts:
            return
        
        alert = self.active_alerts[rule_name]
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = time.time()
            alert.updated_at = time.time()
            
            # Cancel escalation task
            if rule_name in self.escalation_tasks:
                self.escalation_tasks[rule_name].cancel()
                del self.escalation_tasks[rule_name]
            
            # Send resolution notification
            resolution_message = f"Alert resolved: {alert.message}"
            await self._send_notifications(
                alert, 
                [NotificationChannel.SLACK],
                message_override=resolution_message
            )
            
            self.logger.info(f"Alert resolved: {rule_name}")
    
    async def _schedule_escalation(self, rule: AlertRule, alert: Alert) -> None:
        """Schedule alert escalation.
        
        Args:
            rule: Alert rule
            alert: Alert instance
        """
        try:
            await asyncio.sleep(rule.escalation_delay)
            
            if rule.name in self.active_alerts:
                current_alert = self.active_alerts[rule.name]
                if current_alert.status == AlertStatus.ACTIVE:
                    current_alert.escalation_count += 1
                    current_alert.updated_at = time.time()
                    
                    if current_alert.escalation_count <= rule.max_escalations:
                        escalation_message = f"ESCALATED: {alert.message} (escalation {current_alert.escalation_count})"
                        await self._send_notifications(
                            current_alert,
                            rule.channels,
                            message_override=escalation_message
                        )
                        self.logger.warning(f"Alert escalated: {rule.name}")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in escalation for {rule.name}: {e}")
    
    async def _send_notifications(
        self, 
        alert: Alert, 
        channels: List[NotificationChannel],
        message_override: Optional[str] = None
    ) -> None:
        """Send notifications to specified channels.
        
        Args:
            alert: Alert instance
            channels: Notification channels
            message_override: Override message
        """
        message = message_override or alert.message
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email(alert, message)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack(alert, message)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook(alert, message)
                elif channel == NotificationChannel.PAGERDUTY:
                    await self._send_pagerduty(alert, message)
                elif channel == NotificationChannel.CONSOLE:
                    self._send_console(alert, message)
            except Exception as e:
                self.logger.error(f"Failed to send {channel.value} notification: {e}")
    
    async def _send_email(self, alert: Alert, message: str) -> None:
        """Send email notification."""
        if not self.config.email:
            return
        
        config = self.config.email
        msg = MIMEMultipart()
        msg['From'] = config['from']
        msg['To'] = ', '.join(config['to'])
        msg['Subject'] = f"[{alert.severity.value.upper()}] SPIDER Alert: {alert.rule_name}"
        
        body = f"""
Alert: {alert.rule_name}
Severity: {alert.severity.value.upper()}
Message: {message}
Time: {time.ctime(alert.created_at)}
Tags: {', '.join(alert.tags)}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (simplified - in production use proper email service)
        self.logger.info(f"Email notification sent: {alert.rule_name}")
    
    async def _send_slack(self, alert: Alert, message: str) -> None:
        """Send Slack notification."""
        if not self.config.slack:
            return
        
        config = self.config.slack
        webhook_url = config['webhook_url']
        
        payload = {
            "text": f"[{alert.severity.value.upper()}] SPIDER Alert",
            "attachments": [
                {
                    "color": self._get_severity_color(alert.severity),
                    "fields": [
                        {"title": "Rule", "value": alert.rule_name, "short": True},
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Message", "value": message, "short": False},
                        {"title": "Time", "value": time.ctime(alert.created_at), "short": True},
                        {"title": "Tags", "value": ', '.join(alert.tags), "short": True}
                    ]
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        self.logger.info(f"Slack notification sent: {alert.rule_name}")
    
    async def _send_webhook(self, alert: Alert, message: str) -> None:
        """Send webhook notification."""
        if not self.config.webhook:
            return
        
        config = self.config.webhook
        webhook_url = config['url']
        
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "message": message,
            "timestamp": alert.created_at,
            "tags": alert.tags,
            "metadata": alert.metadata
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        self.logger.info(f"Webhook notification sent: {alert.rule_name}")
    
    async def _send_pagerduty(self, alert: Alert, message: str) -> None:
        """Send PagerDuty notification."""
        if not self.config.pagerduty:
            return
        
        config = self.config.pagerduty
        integration_key = config['integration_key']
        
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": alert.rule_name,
            "payload": {
                "summary": f"SPIDER Alert: {alert.rule_name}",
                "source": "spider",
                "severity": alert.severity.value,
                "custom_details": {
                    "message": message,
                    "tags": alert.tags,
                    "metadata": alert.metadata
                }
            }
        }
        
        response = requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        self.logger.info(f"PagerDuty notification sent: {alert.rule_name}")
    
    def _send_console(self, alert: Alert, message: str) -> None:
        """Send console notification."""
        severity_color = self._get_severity_color(alert.severity)
        self.logger.warning(f"CONSOLE ALERT [{alert.severity.value.upper()}]: {message}")
    
    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level."""
        colors = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger"
        }
        return colors.get(severity, "good")
    
    def _format_message(self, template: str, health: SystemHealth) -> str:
        """Format alert message template.
        
        Args:
            template: Message template
            health: Health status
            
        Returns:
            Formatted message
        """
        # Flatten health data for template formatting
        data = {
            "overall_status": health.overall_status.value,
            "timestamp": health.timestamp,
            **health.system_metrics,
            **health.business_metrics
        }
        
        # Add component statuses
        for component, status in health.components.items():
            data[f"{component}_status"] = status.get("status", "unknown")
        
        return template.format(**data)
    
    def acknowledge_alert(self, rule_name: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert.
        
        Args:
            rule_name: Name of the rule
            acknowledged_by: Person acknowledging the alert
            
        Returns:
            True if alert was acknowledged, False if not found
        """
        if rule_name not in self.active_alerts:
            return False
        
        alert = self.active_alerts[rule_name]
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = time.time()
            alert.updated_at = time.time()
            
            # Cancel escalation task
            if rule_name in self.escalation_tasks:
                self.escalation_tasks[rule_name].cancel()
                del self.escalation_tasks[rule_name]
            
            self.logger.info(f"Alert acknowledged by {acknowledged_by}: {rule_name}")
            return True
        
        return False
    
    def suppress_alert(self, rule_name: str, duration: int = 3600) -> bool:
        """Suppress an alert for a duration.
        
        Args:
            rule_name: Name of the rule
            duration: Suppression duration in seconds
            
        Returns:
            True if alert was suppressed, False if not found
        """
        if rule_name not in self.active_alerts:
            return False
        
        alert = self.active_alerts[rule_name]
        alert.status = AlertStatus.SUPPRESSED
        alert.updated_at = time.time()
        alert.metadata["suppressed_until"] = time.time() + duration
        
        # Cancel escalation task
        if rule_name in self.escalation_tasks:
            self.escalation_tasks[rule_name].cancel()
            del self.escalation_tasks[rule_name]
        
        self.logger.info(f"Alert suppressed for {duration}s: {rule_name}")
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts.
        
        Returns:
            List of active alerts
        """
        return [alert for alert in self.active_alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of historical alerts
        """
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alert_history if alert.created_at > cutoff_time]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics.
        
        Returns:
            Alert statistics
        """
        total_alerts = len(self.alert_history)
        active_alerts = len(self.get_active_alerts())
        acknowledged_alerts = len([
            alert for alert in self.active_alerts.values() 
            if alert.status == AlertStatus.ACKNOWLEDGED
        ])
        
        # Severity breakdown
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Rule breakdown
        rule_counts = {}
        for alert in self.alert_history:
            rule_name = alert.rule_name
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "severity_breakdown": severity_counts,
            "rule_breakdown": rule_counts,
            "enabled_rules": len([r for r in self.rules if r.enabled])
        }
    
    def cleanup(self) -> None:
        """Cleanup alert manager."""
        # Cancel all escalation tasks
        for task in self.escalation_tasks.values():
            task.cancel()
        self.escalation_tasks.clear()
        
        # Clear old alerts (keep last 7 days)
        cutoff_time = time.time() - (7 * 24 * 3600)
        self.alert_history = [alert for alert in self.alert_history if alert.created_at > cutoff_time]
        
        self.logger.info("Alert manager cleaned up")
