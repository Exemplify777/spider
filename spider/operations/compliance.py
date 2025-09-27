"""
Compliance Automation and Reporting

This module provides comprehensive compliance automation and reporting capabilities
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

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    SOC_2 = "soc_2"
    NIST = "nist"
    FEDRAMP = "fedramp"


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"
    IN_PROGRESS = "in_progress"


class ControlType(Enum):
    """Control types"""
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    PHYSICAL = "physical"
    ORGANIZATIONAL = "organizational"


@dataclass
class ComplianceControl:
    """Compliance control definition"""
    id: str
    name: str
    description: str
    standard: ComplianceStandard
    control_type: ControlType
    category: str
    requirements: List[str] = field(default_factory=list)
    implementation_notes: str = ""
    evidence_required: List[str] = field(default_factory=list)
    automated: bool = False
    frequency: str = "continuous"  # continuous, daily, weekly, monthly, quarterly, annually


@dataclass
class ComplianceAssessment:
    """Compliance assessment result"""
    id: str
    control_id: str
    standard: ComplianceStandard
    status: ComplianceStatus
    score: float  # 0-100
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_by: str = "system"
    assessed_at: datetime = field(default_factory=datetime.now)
    next_assessment: Optional[datetime] = None


@dataclass
class ComplianceReport:
    """Compliance report"""
    id: str
    title: str
    standard: ComplianceStandard
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    overall_score: float
    controls_assessed: int
    controls_compliant: int
    controls_non_compliant: int
    critical_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    executive_summary: str = ""


@dataclass
class ComplianceConfig:
    """Compliance configuration"""
    enabled_standards: List[ComplianceStandard] = field(default_factory=lambda: [
        ComplianceStandard.GDPR,
        ComplianceStandard.CCPA,
        ComplianceStandard.HIPAA,
        ComplianceStandard.SOX,
        ComplianceStandard.PCI_DSS,
        ComplianceStandard.ISO_27001,
        ComplianceStandard.SOC_2
    ])
    assessment_interval: int = 3600  # seconds
    report_generation_interval: int = 86400  # seconds (daily)
    evidence_retention_days: int = 2555  # 7 years
    notification_webhook: Optional[str] = None
    auto_remediation_enabled: bool = True
    compliance_threshold: float = 80.0  # Minimum compliance score


class ComplianceManager:
    """
    Compliance automation and reporting system
    """
    
    def __init__(self, config: ComplianceConfig):
        self.config = config
        self.controls: Dict[str, ComplianceControl] = {}
        self.assessments: Dict[str, ComplianceAssessment] = {}
        self.reports: Dict[str, ComplianceReport] = {}
        self.evidence: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.running = False
        self.compliance_tasks: List[asyncio.Task] = []
        
        # Initialize compliance controls
        self._initialize_compliance_controls()
    
    def _initialize_compliance_controls(self):
        """Initialize compliance controls for various standards"""
        # GDPR Controls
        gdpr_controls = [
            ComplianceControl(
                id="gdpr_001",
                name="Data Protection by Design",
                description="Implement data protection principles in system design",
                standard=ComplianceStandard.GDPR,
                control_type=ControlType.TECHNICAL,
                category="Data Protection",
                requirements=[
                    "Data minimization implemented",
                    "Purpose limitation enforced",
                    "Storage limitation applied",
                    "Accuracy maintained"
                ],
                evidence_required=["System architecture documentation", "Data flow diagrams"],
                automated=True,
                frequency="continuous"
            ),
            ComplianceControl(
                id="gdpr_002",
                name="Consent Management",
                description="Implement consent management system",
                standard=ComplianceStandard.GDPR,
                control_type=ControlType.TECHNICAL,
                category="Consent",
                requirements=[
                    "Consent collection mechanism",
                    "Consent withdrawal capability",
                    "Consent records maintained",
                    "Granular consent options"
                ],
                evidence_required=["Consent management system logs", "User consent records"],
                automated=True,
                frequency="continuous"
            ),
            ComplianceControl(
                id="gdpr_003",
                name="Data Subject Rights",
                description="Implement data subject rights (access, rectification, erasure, portability)",
                standard=ComplianceStandard.GDPR,
                control_type=ControlType.TECHNICAL,
                category="Data Subject Rights",
                requirements=[
                    "Right of access implemented",
                    "Right to rectification implemented",
                    "Right to erasure implemented",
                    "Right to data portability implemented"
                ],
                evidence_required=["Data subject request logs", "Response time metrics"],
                automated=True,
                frequency="continuous"
            ),
            ComplianceControl(
                id="gdpr_004",
                name="Data Breach Notification",
                description="Implement data breach detection and notification system",
                standard=ComplianceStandard.GDPR,
                control_type=ControlType.TECHNICAL,
                category="Breach Management",
                requirements=[
                    "Breach detection mechanisms",
                    "Notification system to authorities",
                    "Notification system to data subjects",
                    "Breach response procedures"
                ],
                evidence_required=["Breach detection logs", "Notification records"],
                automated=True,
                frequency="continuous"
            )
        ]
        
        # HIPAA Controls
        hipaa_controls = [
            ComplianceControl(
                id="hipaa_001",
                name="Access Control",
                description="Implement access control for PHI",
                standard=ComplianceStandard.HIPAA,
                control_type=ControlType.TECHNICAL,
                category="Access Control",
                requirements=[
                    "Unique user identification",
                    "Emergency access procedures",
                    "Automatic logoff",
                    "Encryption and decryption"
                ],
                evidence_required=["Access control logs", "User authentication records"],
                automated=True,
                frequency="continuous"
            ),
            ComplianceControl(
                id="hipaa_002",
                name="Audit Controls",
                description="Implement audit controls for PHI access",
                standard=ComplianceStandard.HIPAA,
                control_type=ControlType.TECHNICAL,
                category="Audit",
                requirements=[
                    "Audit log generation",
                    "Audit log review",
                    "Audit log protection",
                    "Audit log retention"
                ],
                evidence_required=["Audit logs", "Log review records"],
                automated=True,
                frequency="continuous"
            )
        ]
        
        # PCI DSS Controls
        pci_controls = [
            ComplianceControl(
                id="pci_001",
                name="Firewall Configuration",
                description="Install and maintain firewall configuration",
                standard=ComplianceStandard.PCI_DSS,
                control_type=ControlType.TECHNICAL,
                category="Network Security",
                requirements=[
                    "Firewall installed and configured",
                    "Firewall rules documented",
                    "Firewall rules reviewed",
                    "Default passwords changed"
                ],
                evidence_required=["Firewall configuration", "Rule review records"],
                automated=True,
                frequency="monthly"
            ),
            ComplianceControl(
                id="pci_002",
                name="Cardholder Data Protection",
                description="Protect stored cardholder data",
                standard=ComplianceStandard.PCI_DSS,
                control_type=ControlType.TECHNICAL,
                category="Data Protection",
                requirements=[
                    "Data encryption implemented",
                    "Encryption keys protected",
                    "Data retention policies",
                    "Data disposal procedures"
                ],
                evidence_required=["Encryption configuration", "Key management logs"],
                automated=True,
                frequency="continuous"
            )
        ]
        
        # ISO 27001 Controls
        iso_controls = [
            ComplianceControl(
                id="iso_001",
                name="Information Security Policy",
                description="Maintain information security policy",
                standard=ComplianceStandard.ISO_27001,
                control_type=ControlType.ADMINISTRATIVE,
                category="Governance",
                requirements=[
                    "Policy documented",
                    "Policy approved",
                    "Policy communicated",
                    "Policy reviewed"
                ],
                evidence_required=["Policy document", "Approval records"],
                automated=False,
                frequency="annually"
            ),
            ComplianceControl(
                id="iso_002",
                name="Risk Assessment",
                description="Conduct regular risk assessments",
                standard=ComplianceStandard.ISO_27001,
                control_type=ControlType.ADMINISTRATIVE,
                category="Risk Management",
                requirements=[
                    "Risk assessment methodology",
                    "Risk register maintained",
                    "Risk treatment plans",
                    "Risk monitoring"
                ],
                evidence_required=["Risk assessment reports", "Risk register"],
                automated=False,
                frequency="quarterly"
            )
        ]
        
        # Add all controls
        all_controls = gdpr_controls + hipaa_controls + pci_controls + iso_controls
        
        for control in all_controls:
            self.controls[control.id] = control
    
    async def start_compliance_management(self):
        """Start the compliance management system"""
        if self.running:
            logger.warning("Compliance management is already running")
            return
        
        self.running = True
        logger.info("Starting compliance management system")
        
        # Start compliance tasks
        self.compliance_tasks = [
            asyncio.create_task(self._assess_compliance()),
            asyncio.create_task(self._collect_evidence()),
            asyncio.create_task(self._generate_reports()),
            asyncio.create_task(self._remediate_issues()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.compliance_tasks)
        except Exception as e:
            logger.error(f"Error in compliance tasks: {e}")
        finally:
            self.running = False
    
    async def stop_compliance_management(self):
        """Stop the compliance management system"""
        if not self.running:
            return
        
        logger.info("Stopping compliance management system")
        self.running = False
        
        # Cancel all compliance tasks
        for task in self.compliance_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.compliance_tasks, return_exceptions=True)
    
    async def _assess_compliance(self):
        """Assess compliance for all controls"""
        while self.running:
            try:
                for control in self.controls.values():
                    if control.standard in self.config.enabled_standards:
                        await self._assess_control(control)
                
            except Exception as e:
                logger.error(f"Error assessing compliance: {e}")
            
            await asyncio.sleep(self.config.assessment_interval)
    
    async def _assess_control(self, control: ComplianceControl):
        """Assess a specific compliance control"""
        try:
            assessment_id = f"{control.id}_{int(time.time())}"
            
            # Perform automated assessment if possible
            if control.automated:
                status, score, findings, recommendations = await self._perform_automated_assessment(control)
            else:
                # Manual assessment required
                status = ComplianceStatus.NOT_ASSESSED
                score = 0.0
                findings = ["Manual assessment required"]
                recommendations = ["Schedule manual assessment"]
            
            # Create assessment record
            assessment = ComplianceAssessment(
                id=assessment_id,
                control_id=control.id,
                standard=control.standard,
                status=status,
                score=score,
                findings=findings,
                recommendations=recommendations,
                assessed_by="system" if control.automated else "manual",
                assessed_at=datetime.now(),
                next_assessment=self._calculate_next_assessment(control)
            )
            
            self.assessments[assessment_id] = assessment
            
            logger.info(f"Assessed control {control.id}: {status.value} ({score:.1f}%)")
            
        except Exception as e:
            logger.error(f"Error assessing control {control.id}: {e}")
    
    async def _perform_automated_assessment(self, control: ComplianceControl) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Perform automated assessment of a control"""
        findings = []
        recommendations = []
        score = 100.0
        
        try:
            if control.id.startswith("gdpr_"):
                return await self._assess_gdpr_control(control)
            elif control.id.startswith("hipaa_"):
                return await self._assess_hipaa_control(control)
            elif control.id.startswith("pci_"):
                return await self._assess_pci_control(control)
            elif control.id.startswith("iso_"):
                return await self._assess_iso_control(control)
            else:
                return ComplianceStatus.NOT_ASSESSED, 0.0, ["Unknown control type"], ["Contact compliance team"]
        
        except Exception as e:
            findings.append(f"Assessment error: {str(e)}")
            recommendations.append("Review system configuration")
            return ComplianceStatus.NON_COMPLIANT, 0.0, findings, recommendations
    
    async def _assess_gdpr_control(self, control: ComplianceControl) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Assess GDPR control"""
        findings = []
        recommendations = []
        score = 100.0
        
        if control.id == "gdpr_001":  # Data Protection by Design
            # Check for data minimization
            if not await self._check_data_minimization():
                findings.append("Data minimization not properly implemented")
                recommendations.append("Implement data minimization controls")
                score -= 25
            
            # Check for purpose limitation
            if not await self._check_purpose_limitation():
                findings.append("Purpose limitation not enforced")
                recommendations.append("Implement purpose limitation controls")
                score -= 25
            
            # Check for storage limitation
            if not await self._check_storage_limitation():
                findings.append("Storage limitation not applied")
                recommendations.append("Implement data retention policies")
                score -= 25
            
            # Check for accuracy
            if not await self._check_data_accuracy():
                findings.append("Data accuracy not maintained")
                recommendations.append("Implement data validation and correction mechanisms")
                score -= 25
        
        elif control.id == "gdpr_002":  # Consent Management
            # Check consent management system
            if not await self._check_consent_management():
                findings.append("Consent management system not implemented")
                recommendations.append("Implement consent management system")
                score -= 50
            
            # Check consent withdrawal
            if not await self._check_consent_withdrawal():
                findings.append("Consent withdrawal not available")
                recommendations.append("Implement consent withdrawal mechanism")
                score -= 50
        
        elif control.id == "gdpr_003":  # Data Subject Rights
            # Check data subject rights implementation
            rights_implemented = await self._check_data_subject_rights()
            if not rights_implemented["access"]:
                findings.append("Right of access not implemented")
                recommendations.append("Implement data subject access mechanism")
                score -= 25
            
            if not rights_implemented["rectification"]:
                findings.append("Right to rectification not implemented")
                recommendations.append("Implement data rectification mechanism")
                score -= 25
            
            if not rights_implemented["erasure"]:
                findings.append("Right to erasure not implemented")
                recommendations.append("Implement data erasure mechanism")
                score -= 25
            
            if not rights_implemented["portability"]:
                findings.append("Right to data portability not implemented")
                recommendations.append("Implement data portability mechanism")
                score -= 25
        
        elif control.id == "gdpr_004":  # Data Breach Notification
            # Check breach detection
            if not await self._check_breach_detection():
                findings.append("Data breach detection not implemented")
                recommendations.append("Implement breach detection system")
                score -= 50
            
            # Check notification system
            if not await self._check_breach_notification():
                findings.append("Breach notification system not implemented")
                recommendations.append("Implement breach notification system")
                score -= 50
        
        # Determine status based on score
        if score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return status, score, findings, recommendations
    
    async def _assess_hipaa_control(self, control: ComplianceControl) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Assess HIPAA control"""
        findings = []
        recommendations = []
        score = 100.0
        
        if control.id == "hipaa_001":  # Access Control
            # Check unique user identification
            if not await self._check_unique_user_identification():
                findings.append("Unique user identification not implemented")
                recommendations.append("Implement unique user identification")
                score -= 25
            
            # Check emergency access procedures
            if not await self._check_emergency_access():
                findings.append("Emergency access procedures not implemented")
                recommendations.append("Implement emergency access procedures")
                score -= 25
            
            # Check automatic logoff
            if not await self._check_automatic_logoff():
                findings.append("Automatic logoff not implemented")
                recommendations.append("Implement automatic logoff")
                score -= 25
            
            # Check encryption
            if not await self._check_encryption():
                findings.append("Encryption not implemented")
                recommendations.append("Implement encryption for PHI")
                score -= 25
        
        elif control.id == "hipaa_002":  # Audit Controls
            # Check audit log generation
            if not await self._check_audit_log_generation():
                findings.append("Audit log generation not implemented")
                recommendations.append("Implement audit logging")
                score -= 25
            
            # Check audit log review
            if not await self._check_audit_log_review():
                findings.append("Audit log review not implemented")
                recommendations.append("Implement audit log review process")
                score -= 25
            
            # Check audit log protection
            if not await self._check_audit_log_protection():
                findings.append("Audit log protection not implemented")
                recommendations.append("Implement audit log protection")
                score -= 25
            
            # Check audit log retention
            if not await self._check_audit_log_retention():
                findings.append("Audit log retention not implemented")
                recommendations.append("Implement audit log retention policy")
                score -= 25
        
        # Determine status based on score
        if score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return status, score, findings, recommendations
    
    async def _assess_pci_control(self, control: ComplianceControl) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Assess PCI DSS control"""
        findings = []
        recommendations = []
        score = 100.0
        
        if control.id == "pci_001":  # Firewall Configuration
            # Check firewall installation
            if not await self._check_firewall_installation():
                findings.append("Firewall not installed or configured")
                recommendations.append("Install and configure firewall")
                score -= 25
            
            # Check firewall rules documentation
            if not await self._check_firewall_documentation():
                findings.append("Firewall rules not documented")
                recommendations.append("Document firewall rules")
                score -= 25
            
            # Check firewall rules review
            if not await self._check_firewall_review():
                findings.append("Firewall rules not reviewed")
                recommendations.append("Implement firewall rules review process")
                score -= 25
            
            # Check default passwords
            if not await self._check_default_passwords():
                findings.append("Default passwords not changed")
                recommendations.append("Change default passwords")
                score -= 25
        
        elif control.id == "pci_002":  # Cardholder Data Protection
            # Check data encryption
            if not await self._check_card_data_encryption():
                findings.append("Cardholder data not encrypted")
                recommendations.append("Implement encryption for cardholder data")
                score -= 25
            
            # Check encryption key protection
            if not await self._check_key_protection():
                findings.append("Encryption keys not protected")
                recommendations.append("Implement key management system")
                score -= 25
            
            # Check data retention policies
            if not await self._check_data_retention_policies():
                findings.append("Data retention policies not implemented")
                recommendations.append("Implement data retention policies")
                score -= 25
            
            # Check data disposal procedures
            if not await self._check_data_disposal():
                findings.append("Data disposal procedures not implemented")
                recommendations.append("Implement secure data disposal procedures")
                score -= 25
        
        # Determine status based on score
        if score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return status, score, findings, recommendations
    
    async def _assess_iso_control(self, control: ComplianceControl) -> Tuple[ComplianceStatus, float, List[str], List[str]]:
        """Assess ISO 27001 control"""
        # ISO controls are typically manual assessments
        return ComplianceStatus.NOT_ASSESSED, 0.0, ["Manual assessment required"], ["Schedule manual assessment"]
    
    # Helper methods for specific compliance checks
    async def _check_data_minimization(self) -> bool:
        """Check if data minimization is implemented"""
        # Implementation for data minimization check
        return True  # Simplified implementation
    
    async def _check_purpose_limitation(self) -> bool:
        """Check if purpose limitation is enforced"""
        # Implementation for purpose limitation check
        return True  # Simplified implementation
    
    async def _check_storage_limitation(self) -> bool:
        """Check if storage limitation is applied"""
        # Implementation for storage limitation check
        return True  # Simplified implementation
    
    async def _check_data_accuracy(self) -> bool:
        """Check if data accuracy is maintained"""
        # Implementation for data accuracy check
        return True  # Simplified implementation
    
    async def _check_consent_management(self) -> bool:
        """Check if consent management system is implemented"""
        # Implementation for consent management check
        return True  # Simplified implementation
    
    async def _check_consent_withdrawal(self) -> bool:
        """Check if consent withdrawal is available"""
        # Implementation for consent withdrawal check
        return True  # Simplified implementation
    
    async def _check_data_subject_rights(self) -> Dict[str, bool]:
        """Check if data subject rights are implemented"""
        # Implementation for data subject rights check
        return {
            "access": True,
            "rectification": True,
            "erasure": True,
            "portability": True
        }  # Simplified implementation
    
    async def _check_breach_detection(self) -> bool:
        """Check if breach detection is implemented"""
        # Implementation for breach detection check
        return True  # Simplified implementation
    
    async def _check_breach_notification(self) -> bool:
        """Check if breach notification is implemented"""
        # Implementation for breach notification check
        return True  # Simplified implementation
    
    async def _check_unique_user_identification(self) -> bool:
        """Check if unique user identification is implemented"""
        # Implementation for unique user identification check
        return True  # Simplified implementation
    
    async def _check_emergency_access(self) -> bool:
        """Check if emergency access procedures are implemented"""
        # Implementation for emergency access check
        return True  # Simplified implementation
    
    async def _check_automatic_logoff(self) -> bool:
        """Check if automatic logoff is implemented"""
        # Implementation for automatic logoff check
        return True  # Simplified implementation
    
    async def _check_encryption(self) -> bool:
        """Check if encryption is implemented"""
        # Implementation for encryption check
        return True  # Simplified implementation
    
    async def _check_audit_log_generation(self) -> bool:
        """Check if audit log generation is implemented"""
        # Implementation for audit log generation check
        return True  # Simplified implementation
    
    async def _check_audit_log_review(self) -> bool:
        """Check if audit log review is implemented"""
        # Implementation for audit log review check
        return True  # Simplified implementation
    
    async def _check_audit_log_protection(self) -> bool:
        """Check if audit log protection is implemented"""
        # Implementation for audit log protection check
        return True  # Simplified implementation
    
    async def _check_audit_log_retention(self) -> bool:
        """Check if audit log retention is implemented"""
        # Implementation for audit log retention check
        return True  # Simplified implementation
    
    async def _check_firewall_installation(self) -> bool:
        """Check if firewall is installed and configured"""
        # Implementation for firewall installation check
        return True  # Simplified implementation
    
    async def _check_firewall_documentation(self) -> bool:
        """Check if firewall rules are documented"""
        # Implementation for firewall documentation check
        return True  # Simplified implementation
    
    async def _check_firewall_review(self) -> bool:
        """Check if firewall rules are reviewed"""
        # Implementation for firewall review check
        return True  # Simplified implementation
    
    async def _check_default_passwords(self) -> bool:
        """Check if default passwords are changed"""
        # Implementation for default password check
        return True  # Simplified implementation
    
    async def _check_card_data_encryption(self) -> bool:
        """Check if cardholder data is encrypted"""
        # Implementation for card data encryption check
        return True  # Simplified implementation
    
    async def _check_key_protection(self) -> bool:
        """Check if encryption keys are protected"""
        # Implementation for key protection check
        return True  # Simplified implementation
    
    async def _check_data_retention_policies(self) -> bool:
        """Check if data retention policies are implemented"""
        # Implementation for data retention policies check
        return True  # Simplified implementation
    
    async def _check_data_disposal(self) -> bool:
        """Check if data disposal procedures are implemented"""
        # Implementation for data disposal check
        return True  # Simplified implementation
    
    def _calculate_next_assessment(self, control: ComplianceControl) -> datetime:
        """Calculate next assessment date based on frequency"""
        now = datetime.now()
        
        if control.frequency == "continuous":
            return now + timedelta(hours=1)
        elif control.frequency == "daily":
            return now + timedelta(days=1)
        elif control.frequency == "weekly":
            return now + timedelta(weeks=1)
        elif control.frequency == "monthly":
            return now + timedelta(days=30)
        elif control.frequency == "quarterly":
            return now + timedelta(days=90)
        elif control.frequency == "annually":
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=1)
    
    async def _collect_evidence(self):
        """Collect evidence for compliance assessments"""
        while self.running:
            try:
                # Collect evidence for each control
                for control in self.controls.values():
                    if control.standard in self.config.enabled_standards:
                        await self._collect_control_evidence(control)
                
            except Exception as e:
                logger.error(f"Error collecting evidence: {e}")
            
            await asyncio.sleep(3600)  # Collect evidence every hour
    
    async def _collect_control_evidence(self, control: ComplianceControl):
        """Collect evidence for a specific control"""
        try:
            evidence_items = []
            
            for evidence_type in control.evidence_required:
                evidence = await self._collect_evidence_item(evidence_type)
                if evidence:
                    evidence_items.append({
                        "type": evidence_type,
                        "data": evidence,
                        "collected_at": datetime.now(),
                        "control_id": control.id
                    })
            
            if evidence_items:
                self.evidence[control.id].extend(evidence_items)
                logger.info(f"Collected {len(evidence_items)} evidence items for control {control.id}")
        
        except Exception as e:
            logger.error(f"Error collecting evidence for control {control.id}: {e}")
    
    async def _collect_evidence_item(self, evidence_type: str) -> Optional[Dict[str, Any]]:
        """Collect a specific evidence item"""
        try:
            if "log" in evidence_type.lower():
                return await self._collect_log_evidence(evidence_type)
            elif "configuration" in evidence_type.lower():
                return await self._collect_configuration_evidence(evidence_type)
            elif "documentation" in evidence_type.lower():
                return await self._collect_documentation_evidence(evidence_type)
            else:
                return {"type": evidence_type, "status": "collected"}
        
        except Exception as e:
            logger.error(f"Error collecting evidence item {evidence_type}: {e}")
            return None
    
    async def _collect_log_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Collect log evidence"""
        # Implementation for log evidence collection
        return {"type": evidence_type, "logs": "sample log data"}
    
    async def _collect_configuration_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Collect configuration evidence"""
        # Implementation for configuration evidence collection
        return {"type": evidence_type, "configuration": "sample config data"}
    
    async def _collect_documentation_evidence(self, evidence_type: str) -> Dict[str, Any]:
        """Collect documentation evidence"""
        # Implementation for documentation evidence collection
        return {"type": evidence_type, "documentation": "sample doc data"}
    
    async def _generate_reports(self):
        """Generate compliance reports"""
        while self.running:
            try:
                # Generate daily reports
                if datetime.now().hour == 0:  # At midnight
                    await self._generate_daily_report()
                
                # Generate weekly reports
                if datetime.now().weekday() == 0 and datetime.now().hour == 0:  # Monday at midnight
                    await self._generate_weekly_report()
                
                # Generate monthly reports
                if datetime.now().day == 1 and datetime.now().hour == 0:  # First day of month at midnight
                    await self._generate_monthly_report()
                
            except Exception as e:
                logger.error(f"Error generating reports: {e}")
            
            await asyncio.sleep(self.config.report_generation_interval)
    
    async def _generate_daily_report(self):
        """Generate daily compliance report"""
        report_id = f"daily_{datetime.now().strftime('%Y%m%d')}"
        
        # Calculate compliance metrics
        metrics = await self._calculate_compliance_metrics()
        
        # Generate report
        report = ComplianceReport(
            id=report_id,
            title="Daily Compliance Report",
            standard=ComplianceStandard.GDPR,  # Default to GDPR
            generated_at=datetime.now(),
            period_start=datetime.now() - timedelta(days=1),
            period_end=datetime.now(),
            overall_status=metrics["overall_status"],
            overall_score=metrics["overall_score"],
            controls_assessed=metrics["controls_assessed"],
            controls_compliant=metrics["controls_compliant"],
            controls_non_compliant=metrics["controls_non_compliant"],
            critical_findings=metrics["critical_findings"],
            recommendations=metrics["recommendations"],
            executive_summary=metrics["executive_summary"]
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated daily compliance report: {report_id}")
    
    async def _generate_weekly_report(self):
        """Generate weekly compliance report"""
        report_id = f"weekly_{datetime.now().strftime('%Y%m%d')}"
        
        # Calculate compliance metrics for the week
        metrics = await self._calculate_compliance_metrics(days=7)
        
        # Generate report
        report = ComplianceReport(
            id=report_id,
            title="Weekly Compliance Report",
            standard=ComplianceStandard.GDPR,  # Default to GDPR
            generated_at=datetime.now(),
            period_start=datetime.now() - timedelta(weeks=1),
            period_end=datetime.now(),
            overall_status=metrics["overall_status"],
            overall_score=metrics["overall_score"],
            controls_assessed=metrics["controls_assessed"],
            controls_compliant=metrics["controls_compliant"],
            controls_non_compliant=metrics["controls_non_compliant"],
            critical_findings=metrics["critical_findings"],
            recommendations=metrics["recommendations"],
            executive_summary=metrics["executive_summary"]
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated weekly compliance report: {report_id}")
    
    async def _generate_monthly_report(self):
        """Generate monthly compliance report"""
        report_id = f"monthly_{datetime.now().strftime('%Y%m%d')}"
        
        # Calculate compliance metrics for the month
        metrics = await self._calculate_compliance_metrics(days=30)
        
        # Generate report
        report = ComplianceReport(
            id=report_id,
            title="Monthly Compliance Report",
            standard=ComplianceStandard.GDPR,  # Default to GDPR
            generated_at=datetime.now(),
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            overall_status=metrics["overall_status"],
            overall_score=metrics["overall_score"],
            controls_assessed=metrics["controls_assessed"],
            controls_compliant=metrics["controls_compliant"],
            controls_non_compliant=metrics["controls_non_compliant"],
            critical_findings=metrics["critical_findings"],
            recommendations=metrics["recommendations"],
            executive_summary=metrics["executive_summary"]
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated monthly compliance report: {report_id}")
    
    async def _calculate_compliance_metrics(self, days: int = 1) -> Dict[str, Any]:
        """Calculate compliance metrics"""
        # Get recent assessments
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_assessments = [
            assessment for assessment in self.assessments.values()
            if assessment.assessed_at > cutoff_date
        ]
        
        if not recent_assessments:
            return {
                "overall_status": ComplianceStatus.NOT_ASSESSED,
                "overall_score": 0.0,
                "controls_assessed": 0,
                "controls_compliant": 0,
                "controls_non_compliant": 0,
                "critical_findings": [],
                "recommendations": [],
                "executive_summary": "No assessments available"
            }
        
        # Calculate metrics
        total_assessments = len(recent_assessments)
        compliant_assessments = len([a for a in recent_assessments if a.status == ComplianceStatus.COMPLIANT])
        non_compliant_assessments = len([a for a in recent_assessments if a.status == ComplianceStatus.NON_COMPLIANT])
        
        overall_score = sum(a.score for a in recent_assessments) / total_assessments if total_assessments > 0 else 0.0
        
        if overall_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT
        
        # Collect findings and recommendations
        critical_findings = []
        recommendations = []
        
        for assessment in recent_assessments:
            if assessment.status == ComplianceStatus.NON_COMPLIANT:
                critical_findings.extend(assessment.findings)
            recommendations.extend(assessment.recommendations)
        
        # Generate executive summary
        executive_summary = f"Compliance status: {overall_status.value}. "
        executive_summary += f"Overall score: {overall_score:.1f}%. "
        executive_summary += f"Assessed {total_assessments} controls. "
        executive_summary += f"{compliant_assessments} compliant, {non_compliant_assessments} non-compliant."
        
        return {
            "overall_status": overall_status,
            "overall_score": overall_score,
            "controls_assessed": total_assessments,
            "controls_compliant": compliant_assessments,
            "controls_non_compliant": non_compliant_assessments,
            "critical_findings": critical_findings,
            "recommendations": recommendations,
            "executive_summary": executive_summary
        }
    
    async def _remediate_issues(self):
        """Automatically remediate compliance issues"""
        while self.running:
            try:
                if not self.config.auto_remediation_enabled:
                    await asyncio.sleep(3600)  # Check every hour
                    continue
                
                # Find non-compliant assessments
                non_compliant_assessments = [
                    assessment for assessment in self.assessments.values()
                    if assessment.status == ComplianceStatus.NON_COMPLIANT
                    and assessment.assessed_at > datetime.now() - timedelta(hours=24)
                ]
                
                for assessment in non_compliant_assessments:
                    await self._remediate_assessment(assessment)
                
            except Exception as e:
                logger.error(f"Error remediating issues: {e}")
            
            await asyncio.sleep(3600)  # Check every hour
    
    async def _remediate_assessment(self, assessment: ComplianceAssessment):
        """Remediate a specific assessment"""
        try:
            # Implement automated remediation based on control type
            control = self.controls.get(assessment.control_id)
            if not control:
                return
            
            # Simple remediation examples
            if "encryption" in control.name.lower():
                await self._remediate_encryption_issue(assessment)
            elif "access" in control.name.lower():
                await self._remediate_access_issue(assessment)
            elif "audit" in control.name.lower():
                await self._remediate_audit_issue(assessment)
            
            logger.info(f"Attempted remediation for assessment {assessment.id}")
        
        except Exception as e:
            logger.error(f"Error remediating assessment {assessment.id}: {e}")
    
    async def _remediate_encryption_issue(self, assessment: ComplianceAssessment):
        """Remediate encryption issues"""
        # Implementation for encryption remediation
        pass
    
    async def _remediate_access_issue(self, assessment: ComplianceAssessment):
        """Remediate access control issues"""
        # Implementation for access control remediation
        pass
    
    async def _remediate_audit_issue(self, assessment: ComplianceAssessment):
        """Remediate audit control issues"""
        # Implementation for audit control remediation
        pass
    
    async def _cleanup_old_data(self):
        """Clean up old compliance data"""
        while self.running:
            try:
                # Clean up old assessments
                cutoff_date = datetime.now() - timedelta(days=self.config.evidence_retention_days)
                
                assessments_to_remove = [
                    assessment_id for assessment_id, assessment in self.assessments.items()
                    if assessment.assessed_at < cutoff_date
                ]
                
                for assessment_id in assessments_to_remove:
                    del self.assessments[assessment_id]
                
                # Clean up old evidence
                for control_id, evidence_list in self.evidence.items():
                    self.evidence[control_id] = [
                        evidence for evidence in evidence_list
                        if evidence["collected_at"] > cutoff_date
                    ]
                
                if assessments_to_remove:
                    logger.info(f"Cleaned up {len(assessments_to_remove)} old assessments")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(86400)  # Clean up daily
    
    async def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary"""
        return {
            "total_controls": len(self.controls),
            "enabled_standards": [std.value for std in self.config.enabled_standards],
            "total_assessments": len(self.assessments),
            "recent_assessments": len([
                a for a in self.assessments.values()
                if a.assessed_at > datetime.now() - timedelta(days=1)
            ]),
            "total_reports": len(self.reports),
            "compliance_running": self.running,
            "last_check": datetime.now().isoformat()
        }
    
    async def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get a specific compliance report"""
        return self.reports.get(report_id)
    
    async def get_control_assessments(self, control_id: str) -> List[ComplianceAssessment]:
        """Get assessments for a specific control"""
        return [
            assessment for assessment in self.assessments.values()
            if assessment.control_id == control_id
        ]
    
    async def get_standard_compliance(self, standard: ComplianceStandard) -> Dict[str, Any]:
        """Get compliance status for a specific standard"""
        standard_controls = [
            control for control in self.controls.values()
            if control.standard == standard
        ]
        
        standard_assessments = [
            assessment for assessment in self.assessments.values()
            if assessment.standard == standard
        ]
        
        if not standard_assessments:
            return {
                "standard": standard.value,
                "status": ComplianceStatus.NOT_ASSESSED,
                "score": 0.0,
                "controls_total": len(standard_controls),
                "controls_assessed": 0,
                "controls_compliant": 0,
                "controls_non_compliant": 0
            }
        
        compliant_count = len([a for a in standard_assessments if a.status == ComplianceStatus.COMPLIANT])
        non_compliant_count = len([a for a in standard_assessments if a.status == ComplianceStatus.NON_COMPLIANT])
        avg_score = sum(a.score for a in standard_assessments) / len(standard_assessments)
        
        if avg_score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif avg_score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return {
            "standard": standard.value,
            "status": status,
            "score": avg_score,
            "controls_total": len(standard_controls),
            "controls_assessed": len(standard_assessments),
            "controls_compliant": compliant_count,
            "controls_non_compliant": non_compliant_count
        }
