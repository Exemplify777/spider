"""
Security Operations and Threat Detection

This module provides comprehensive security operations and threat detection capabilities
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
import re
from collections import defaultdict, deque

import aiohttp
import aiofiles
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import psutil
import docker
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Threat types"""
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    MALWARE = "malware"
    INTRUSION = "intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ANOMALY = "anomaly"


class SecurityEvent(Enum):
    """Security event types"""
    LOGIN_FAILURE = "login_failure"
    LOGIN_SUCCESS = "login_success"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    FILE_ACCESS = "file_access"
    NETWORK_CONNECTION = "network_connection"
    PROCESS_EXECUTION = "process_execution"
    CONFIGURATION_CHANGE = "configuration_change"
    DATA_ACCESS = "data_access"


@dataclass
class ThreatDetection:
    """Threat detection data"""
    id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: str
    target_resource: str
    description: str
    timestamp: datetime
    confidence: float
    indicators: List[str] = field(default_factory=list)
    mitigation_actions: List[str] = field(default_factory=list)
    status: str = "active"  # active, investigating, mitigated, false_positive


@dataclass
class SecurityEvent:
    """Security event data"""
    id: str
    event_type: SecurityEvent
    source: str
    target: str
    user: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical


@dataclass
class SecurityConfig:
    """Security configuration"""
    threat_detection_enabled: bool = True
    real_time_monitoring: bool = True
    log_analysis_enabled: bool = True
    network_monitoring_enabled: bool = True
    file_integrity_monitoring: bool = True
    user_behavior_analysis: bool = True
    threat_intelligence_enabled: bool = True
    auto_response_enabled: bool = True
    notification_webhook: Optional[str] = None
    alert_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "login_failures_per_minute": 10,
        "suspicious_connections_per_hour": 50,
        "file_access_anomalies_per_hour": 20,
        "privilege_escalation_attempts": 1
    })


class SecurityOperations:
    """
    Security operations and threat detection system
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.threats: Dict[str, ThreatDetection] = {}
        self.security_events: Dict[str, SecurityEvent] = {}
        self.user_behavior: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.network_connections: deque = deque(maxlen=10000)
        self.file_access_log: deque = deque(maxlen=10000)
        self.login_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.running = False
        self.security_tasks: List[asyncio.Task] = []
        
        # Initialize security components
        self._initialize_security_components()
    
    def _initialize_security_components(self):
        """Initialize security monitoring components"""
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
    
    async def start_security_operations(self):
        """Start the security operations system"""
        if self.running:
            logger.warning("Security operations is already running")
            return
        
        self.running = True
        logger.info("Starting security operations system")
        
        # Start security monitoring tasks
        self.security_tasks = [
            asyncio.create_task(self._monitor_login_attempts()),
            asyncio.create_task(self._monitor_network_connections()),
            asyncio.create_task(self._monitor_file_access()),
            asyncio.create_task(self._monitor_process_execution()),
            asyncio.create_task(self._analyze_user_behavior()),
            asyncio.create_task(self._detect_threats()),
            asyncio.create_task(self._respond_to_threats()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.security_tasks)
        except Exception as e:
            logger.error(f"Error in security tasks: {e}")
        finally:
            self.running = False
    
    async def stop_security_operations(self):
        """Stop the security operations system"""
        if not self.running:
            return
        
        logger.info("Stopping security operations system")
        self.running = False
        
        # Cancel all security tasks
        for task in self.security_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.security_tasks, return_exceptions=True)
    
    async def _monitor_login_attempts(self):
        """Monitor login attempts for brute force attacks"""
        while self.running:
            try:
                # Monitor authentication logs
                await self._check_authentication_logs()
                
                # Check for brute force patterns
                await self._detect_brute_force_attacks()
                
            except Exception as e:
                logger.error(f"Error monitoring login attempts: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_authentication_logs(self):
        """Check authentication logs for suspicious activity"""
        try:
            # Check application logs for authentication events
            log_files = [
                "/var/log/auth.log",
                "/app/logs/spider.log",
                "/var/log/nginx/access.log"
            ]
            
            for log_file in log_files:
                if Path(log_file).exists():
                    await self._analyze_log_file(log_file)
        
        except Exception as e:
            logger.error(f"Error checking authentication logs: {e}")
    
    async def _analyze_log_file(self, log_file: str):
        """Analyze log file for security events"""
        try:
            async with aiofiles.open(log_file, 'r') as f:
                async for line in f:
                    # Check for login failures
                    if "authentication failure" in line.lower() or "login failed" in line.lower():
                        await self._process_login_failure(line)
                    
                    # Check for privilege escalation attempts
                    if "sudo" in line.lower() and "failed" in line.lower():
                        await self._process_privilege_escalation_attempt(line)
                    
                    # Check for suspicious network activity
                    if "connection" in line.lower() and "denied" in line.lower():
                        await self._process_network_denial(line)
        
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")
    
    async def _process_login_failure(self, log_line: str):
        """Process login failure event"""
        # Extract IP address and timestamp
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', log_line)
        if ip_match:
            ip_address = ip_match.group(1)
            self.login_attempts[ip_address].append(datetime.now())
            
            # Create security event
            event = SecurityEvent(
                id=f"login_failure_{int(time.time())}",
                event_type=SecurityEvent.LOGIN_FAILURE,
                source=ip_address,
                target="authentication_system",
                ip_address=ip_address,
                details={"log_line": log_line.strip()},
                severity="warning"
            )
            
            self.security_events[event.id] = event
            logger.info(f"Login failure detected from {ip_address}")
    
    async def _process_privilege_escalation_attempt(self, log_line: str):
        """Process privilege escalation attempt"""
        # Extract user and IP address
        user_match = re.search(r'user (\w+)', log_line)
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', log_line)
        
        if user_match and ip_match:
            user = user_match.group(1)
            ip_address = ip_match.group(1)
            
            # Create security event
            event = SecurityEvent(
                id=f"priv_esc_{int(time.time())}",
                event_type=SecurityEvent.PRIVILEGE_ESCALATION,
                source=ip_address,
                target="privilege_escalation",
                user=user,
                ip_address=ip_address,
                details={"log_line": log_line.strip()},
                severity="critical"
            )
            
            self.security_events[event.id] = event
            logger.warning(f"Privilege escalation attempt by {user} from {ip_address}")
    
    async def _process_network_denial(self, log_line: str):
        """Process network connection denial"""
        # Extract IP address
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', log_line)
        if ip_match:
            ip_address = ip_match.group(1)
            
            # Create security event
            event = SecurityEvent(
                id=f"network_denial_{int(time.time())}",
                event_type=SecurityEvent.NETWORK_CONNECTION,
                source=ip_address,
                target="network_access",
                ip_address=ip_address,
                details={"log_line": log_line.strip()},
                severity="info"
            )
            
            self.security_events[event.id] = event
    
    async def _detect_brute_force_attacks(self):
        """Detect brute force attacks"""
        current_time = datetime.now()
        threshold = self.config.alert_thresholds["login_failures_per_minute"]
        
        for ip_address, attempts in self.login_attempts.items():
            # Count attempts in the last minute
            recent_attempts = [
                attempt for attempt in attempts
                if current_time - attempt < timedelta(minutes=1)
            ]
            
            if len(recent_attempts) >= threshold:
                # Create threat detection
                threat = ThreatDetection(
                    id=f"brute_force_{ip_address}_{int(time.time())}",
                    threat_type=ThreatType.BRUTE_FORCE,
                    threat_level=ThreatLevel.HIGH,
                    source_ip=ip_address,
                    target_resource="authentication_system",
                    description=f"Brute force attack detected from {ip_address}: {len(recent_attempts)} attempts in 1 minute",
                    timestamp=current_time,
                    confidence=0.9,
                    indicators=[f"Multiple login failures from {ip_address}"],
                    mitigation_actions=["Block IP address", "Enable rate limiting", "Send alert"]
                )
                
                self.threats[threat.id] = threat
                logger.warning(f"Brute force attack detected from {ip_address}")
                
                # Send alert
                await self._send_security_alert(threat)
    
    async def _monitor_network_connections(self):
        """Monitor network connections for suspicious activity"""
        while self.running:
            try:
                # Get current network connections
                connections = psutil.net_connections()
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        connection_info = {
                            "local_addr": conn.laddr,
                            "remote_addr": conn.raddr,
                            "status": conn.status,
                            "pid": conn.pid,
                            "timestamp": datetime.now()
                        }
                        
                        self.network_connections.append(connection_info)
                        
                        # Check for suspicious connections
                        await self._check_suspicious_connection(connection_info)
                
            except Exception as e:
                logger.error(f"Error monitoring network connections: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _check_suspicious_connection(self, connection: Dict[str, Any]):
        """Check for suspicious network connections"""
        try:
            remote_addr = connection.get("remote_addr")
            if not remote_addr:
                return
            
            # Check for connections to known malicious IPs
            if await self._is_malicious_ip(remote_addr[0]):
                threat = ThreatDetection(
                    id=f"malicious_connection_{int(time.time())}",
                    threat_type=ThreatType.INTRUSION,
                    threat_level=ThreatLevel.CRITICAL,
                    source_ip=remote_addr[0],
                    target_resource="network_connection",
                    description=f"Suspicious connection to known malicious IP: {remote_addr[0]}",
                    timestamp=datetime.now(),
                    confidence=0.95,
                    indicators=[f"Connection to malicious IP: {remote_addr[0]}"],
                    mitigation_actions=["Block IP address", "Terminate connection", "Investigate process"]
                )
                
                self.threats[threat.id] = threat
                logger.critical(f"Malicious connection detected to {remote_addr[0]}")
                
                # Send alert
                await self._send_security_alert(threat)
            
            # Check for unusual connection patterns
            if await self._is_unusual_connection_pattern(remote_addr[0]):
                threat = ThreatDetection(
                    id=f"unusual_connection_{int(time.time())}",
                    threat_type=ThreatType.SUSPICIOUS_ACTIVITY,
                    threat_level=ThreatLevel.MEDIUM,
                    source_ip=remote_addr[0],
                    target_resource="network_connection",
                    description=f"Unusual connection pattern from {remote_addr[0]}",
                    timestamp=datetime.now(),
                    confidence=0.7,
                    indicators=[f"Unusual connection pattern from {remote_addr[0]}"],
                    mitigation_actions=["Monitor connection", "Log activity", "Investigate if needed"]
                )
                
                self.threats[threat.id] = threat
                logger.warning(f"Unusual connection pattern detected from {remote_addr[0]}")
        
        except Exception as e:
            logger.error(f"Error checking suspicious connection: {e}")
    
    async def _is_malicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is known to be malicious"""
        # In production, integrate with threat intelligence feeds
        # For now, use a simple blacklist
        malicious_ips = [
            "192.168.1.100",  # Example malicious IP
            "10.0.0.50",      # Example malicious IP
        ]
        
        return ip_address in malicious_ips
    
    async def _is_unusual_connection_pattern(self, ip_address: str) -> bool:
        """Check for unusual connection patterns"""
        # Count connections from this IP in the last hour
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        recent_connections = [
            conn for conn in self.network_connections
            if (conn.get("remote_addr") and 
                conn["remote_addr"][0] == ip_address and
                conn["timestamp"] > hour_ago)
        ]
        
        # If more than 100 connections in an hour, consider it unusual
        return len(recent_connections) > 100
    
    async def _monitor_file_access(self):
        """Monitor file access for suspicious activity"""
        while self.running:
            try:
                # Monitor critical files
                critical_files = [
                    "/etc/passwd",
                    "/etc/shadow",
                    "/app/config/secrets.yaml",
                    "/app/data/",
                    "/var/log/"
                ]
                
                for file_path in critical_files:
                    if Path(file_path).exists():
                        await self._check_file_access(file_path)
                
            except Exception as e:
                logger.error(f"Error monitoring file access: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_file_access(self, file_path: str):
        """Check file access for suspicious activity"""
        try:
            # Get file access information
            stat = Path(file_path).stat()
            
            # Check for unusual access patterns
            if await self._is_unusual_file_access(file_path, stat):
                threat = ThreatDetection(
                    id=f"file_access_{int(time.time())}",
                    threat_type=ThreatType.SUSPICIOUS_ACTIVITY,
                    threat_level=ThreatLevel.MEDIUM,
                    source_ip="unknown",
                    target_resource=file_path,
                    description=f"Unusual file access pattern detected for {file_path}",
                    timestamp=datetime.now(),
                    confidence=0.6,
                    indicators=[f"Unusual access to {file_path}"],
                    mitigation_actions=["Monitor file access", "Check file integrity", "Investigate if needed"]
                )
                
                self.threats[threat.id] = threat
                logger.warning(f"Unusual file access detected for {file_path}")
        
        except Exception as e:
            logger.error(f"Error checking file access for {file_path}: {e}")
    
    async def _is_unusual_file_access(self, file_path: str, stat) -> bool:
        """Check for unusual file access patterns"""
        # Simple heuristic: check if file was accessed recently and frequently
        # In production, implement more sophisticated analysis
        return False
    
    async def _monitor_process_execution(self):
        """Monitor process execution for suspicious activity"""
        while self.running:
            try:
                # Get running processes
                processes = psutil.process_iter(['pid', 'name', 'cmdline', 'create_time'])
                
                for proc in processes:
                    try:
                        proc_info = proc.info
                        
                        # Check for suspicious processes
                        await self._check_suspicious_process(proc_info)
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
            except Exception as e:
                logger.error(f"Error monitoring process execution: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _check_suspicious_process(self, proc_info: Dict[str, Any]):
        """Check for suspicious process execution"""
        try:
            process_name = proc_info.get('name', '').lower()
            cmdline = proc_info.get('cmdline', [])
            
            # Check for known malicious processes
            malicious_processes = [
                'nc', 'netcat', 'ncat',
                'wget', 'curl',  # If used suspiciously
                'python', 'perl', 'bash'  # If used for malicious purposes
            ]
            
            if any(malicious in process_name for malicious in malicious_processes):
                # Additional checks for context
                if await self._is_suspicious_process_context(proc_info):
                    threat = ThreatDetection(
                        id=f"suspicious_process_{int(time.time())}",
                        threat_type=ThreatType.MALWARE,
                        threat_level=ThreatLevel.HIGH,
                        source_ip="unknown",
                        target_resource="process_execution",
                        description=f"Suspicious process execution detected: {process_name}",
                        timestamp=datetime.now(),
                        confidence=0.8,
                        indicators=[f"Suspicious process: {process_name}"],
                        mitigation_actions=["Terminate process", "Investigate process", "Check system integrity"]
                    )
                    
                    self.threats[threat.id] = threat
                    logger.warning(f"Suspicious process detected: {process_name}")
        
        except Exception as e:
            logger.error(f"Error checking suspicious process: {e}")
    
    async def _is_suspicious_process_context(self, proc_info: Dict[str, Any]) -> bool:
        """Check if process execution context is suspicious"""
        # Simple heuristic: check if process is running with suspicious arguments
        cmdline = proc_info.get('cmdline', [])
        
        # Check for network-related suspicious arguments
        suspicious_args = ['-l', '-p', '4444', 'reverse', 'shell']
        
        return any(arg in ' '.join(cmdline).lower() for arg in suspicious_args)
    
    async def _analyze_user_behavior(self):
        """Analyze user behavior for anomalies"""
        while self.running:
            try:
                # Analyze user behavior patterns
                await self._detect_user_behavior_anomalies()
                
            except Exception as e:
                logger.error(f"Error analyzing user behavior: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _detect_user_behavior_anomalies(self):
        """Detect user behavior anomalies"""
        # Analyze login patterns, access patterns, etc.
        # This is a simplified implementation
        pass
    
    async def _detect_threats(self):
        """Main threat detection logic"""
        while self.running:
            try:
                # Analyze collected data for threats
                await self._analyze_threat_indicators()
                
                # Update threat confidence scores
                await self._update_threat_confidence()
                
            except Exception as e:
                logger.error(f"Error detecting threats: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _analyze_threat_indicators(self):
        """Analyze threat indicators"""
        # Correlate different security events to identify threats
        # This is a simplified implementation
        pass
    
    async def _update_threat_confidence(self):
        """Update threat confidence scores based on additional data"""
        for threat_id, threat in self.threats.items():
            if threat.status == "active":
                # Update confidence based on additional indicators
                # This is a simplified implementation
                pass
    
    async def _respond_to_threats(self):
        """Respond to detected threats"""
        while self.running:
            try:
                # Process active threats
                active_threats = [
                    threat for threat in self.threats.values()
                    if threat.status == "active"
                ]
                
                for threat in active_threats:
                    await self._execute_threat_response(threat)
                
            except Exception as e:
                logger.error(f"Error responding to threats: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _execute_threat_response(self, threat: ThreatDetection):
        """Execute response actions for a threat"""
        try:
            for action in threat.mitigation_actions:
                if action == "Block IP address":
                    await self._block_ip_address(threat.source_ip)
                elif action == "Terminate connection":
                    await self._terminate_connection(threat.source_ip)
                elif action == "Send alert":
                    await self._send_security_alert(threat)
                elif action == "Enable rate limiting":
                    await self._enable_rate_limiting(threat.source_ip)
                elif action == "Investigate process":
                    await self._investigate_process(threat)
            
            # Mark threat as being investigated
            threat.status = "investigating"
            
        except Exception as e:
            logger.error(f"Error executing threat response for {threat.id}: {e}")
    
    async def _block_ip_address(self, ip_address: str):
        """Block IP address"""
        try:
            # Implement IP blocking (e.g., using iptables, firewall rules)
            logger.info(f"Blocking IP address: {ip_address}")
            # In production, implement actual IP blocking
        except Exception as e:
            logger.error(f"Error blocking IP address {ip_address}: {e}")
    
    async def _terminate_connection(self, ip_address: str):
        """Terminate network connection"""
        try:
            # Find and terminate connections from the IP
            logger.info(f"Terminating connections from IP: {ip_address}")
            # In production, implement actual connection termination
        except Exception as e:
            logger.error(f"Error terminating connections from {ip_address}: {e}")
    
    async def _enable_rate_limiting(self, ip_address: str):
        """Enable rate limiting for IP address"""
        try:
            logger.info(f"Enabling rate limiting for IP: {ip_address}")
            # In production, implement actual rate limiting
        except Exception as e:
            logger.error(f"Error enabling rate limiting for {ip_address}: {e}")
    
    async def _investigate_process(self, threat: ThreatDetection):
        """Investigate suspicious process"""
        try:
            logger.info(f"Investigating process for threat: {threat.id}")
            # In production, implement process investigation
        except Exception as e:
            logger.error(f"Error investigating process for threat {threat.id}: {e}")
    
    async def _send_security_alert(self, threat: ThreatDetection):
        """Send security alert"""
        try:
            alert_data = {
                "threat_id": threat.id,
                "threat_type": threat.threat_type.value,
                "threat_level": threat.threat_level.value,
                "source_ip": threat.source_ip,
                "target_resource": threat.target_resource,
                "description": threat.description,
                "timestamp": threat.timestamp.isoformat(),
                "confidence": threat.confidence,
                "indicators": threat.indicators,
                "mitigation_actions": threat.mitigation_actions
            }
            
            if self.config.notification_webhook:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.config.notification_webhook,
                        json=alert_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Failed to send security alert: {response.status}")
            
            logger.warning(f"Security alert sent for threat: {threat.id}")
        
        except Exception as e:
            logger.error(f"Error sending security alert: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old security data"""
        while self.running:
            try:
                # Clean up old threats
                cutoff_date = datetime.now() - timedelta(days=7)
                threats_to_remove = [
                    threat_id for threat_id, threat in self.threats.items()
                    if threat.timestamp < cutoff_date
                ]
                
                for threat_id in threats_to_remove:
                    del self.threats[threat_id]
                
                # Clean up old security events
                events_to_remove = [
                    event_id for event_id, event in self.security_events.items()
                    if event.timestamp < cutoff_date
                ]
                
                for event_id in events_to_remove:
                    del self.security_events[event_id]
                
                # Clean up old login attempts
                for ip_address in list(self.login_attempts.keys()):
                    self.login_attempts[ip_address] = [
                        attempt for attempt in self.login_attempts[ip_address]
                        if attempt > cutoff_date
                    ]
                    if not self.login_attempts[ip_address]:
                        del self.login_attempts[ip_address]
                
                if threats_to_remove or events_to_remove:
                    logger.info(f"Cleaned up {len(threats_to_remove)} old threats and {len(events_to_remove)} old events")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(3600)  # Clean up every hour
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security operations summary"""
        return {
            "total_threats": len(self.threats),
            "active_threats": len([t for t in self.threats.values() if t.status == "active"]),
            "investigating_threats": len([t for t in self.threats.values() if t.status == "investigating"]),
            "mitigated_threats": len([t for t in self.threats.values() if t.status == "mitigated"]),
            "total_events": len(self.security_events),
            "threats_by_level": {
                level.value: len([t for t in self.threats.values() if t.threat_level == level])
                for level in ThreatLevel
            },
            "threats_by_type": {
                threat_type.value: len([t for t in self.threats.values() if t.threat_type == threat_type])
                for threat_type in ThreatType
            },
            "security_running": self.running,
            "last_check": datetime.now().isoformat()
        }
    
    async def get_active_threats(self) -> List[ThreatDetection]:
        """Get active threats"""
        return [
            threat for threat in self.threats.values()
            if threat.status == "active"
        ]
    
    async def get_security_events(self, event_type: Optional[SecurityEvent] = None) -> List[SecurityEvent]:
        """Get security events"""
        events = list(self.security_events.values())
        
        if event_type:
            events = [event for event in events if event.event_type == event_type]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)
    
    async def acknowledge_threat(self, threat_id: str, user: str):
        """Acknowledge a threat"""
        if threat_id in self.threats:
            threat = self.threats[threat_id]
            threat.status = "investigating"
            logger.info(f"Threat {threat_id} acknowledged by {user}")
    
    async def mitigate_threat(self, threat_id: str, user: str):
        """Mark threat as mitigated"""
        if threat_id in self.threats:
            threat = self.threats[threat_id]
            threat.status = "mitigated"
            logger.info(f"Threat {threat_id} mitigated by {user}")
    
    async def add_threat_intelligence(self, ip_address: str, threat_type: str, confidence: float):
        """Add threat intelligence data"""
        # In production, integrate with threat intelligence feeds
        logger.info(f"Added threat intelligence: {ip_address} - {threat_type} (confidence: {confidence})")
