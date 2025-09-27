"""
SPIDER Framework - Operations Module

This module provides comprehensive operational capabilities for the SPIDER Framework
in production environments, including monitoring, maintenance, analytics, and automation.

Features:
- Advanced operational monitoring and alerting
- Automated maintenance and operational procedures
- Performance analytics and reporting
- Cost optimization and resource management
- Security operations and threat detection
- Compliance automation and reporting
- Disaster recovery operations and testing
"""

from .monitoring import OperationalMonitor
from .maintenance import MaintenanceManager
from .analytics import PerformanceAnalytics
from .cost_optimization import CostOptimizer
from .security_ops import SecurityOperations
from .compliance import ComplianceManager
from .disaster_recovery import DisasterRecoveryManager

__all__ = [
    'OperationalMonitor',
    'MaintenanceManager', 
    'PerformanceAnalytics',
    'CostOptimizer',
    'SecurityOperations',
    'ComplianceManager',
    'DisasterRecoveryManager'
]

__version__ = '2.0.0'
__author__ = 'SPIDER Framework Team'
__email__ = 'team@example.com'
