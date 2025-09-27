#!/usr/bin/env python3
"""
SPIDER Framework - Enterprise Features Example

This example demonstrates enterprise features including:
- Multi-tenancy
- Advanced security
- Compliance reporting
- User management
- Audit logging
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.config import Config
from spider.core.logger import Logger
from spider.core.storage import Storage
from spider.core.security import SecurityManager
from spider.core.monitor import Monitor
from spider.core.analytics import Analytics
from spider.core.compliance import ComplianceManager
from spider.core.audit import AuditLogger
from spider.core.user_manager import UserManager
from spider.core.tenant_manager import TenantManager

async def main():
    """Main function demonstrating enterprise features."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting enterprise features example")
    
    try:
        # Initialize components
        storage = Storage(config)
        security = SecurityManager(config)
        monitor = Monitor(config)
        analytics = Analytics(config)
        compliance = ComplianceManager(config)
        audit = AuditLogger(config)
        user_manager = UserManager(config)
        tenant_manager = TenantManager(config)
        
        # Start components
        await monitor.start()
        await analytics.start()
        await compliance.start()
        await audit.start()
        
        # Create tenants
        logger.info("Creating tenants...")
        tenant1 = await tenant_manager.create_tenant({
            'name': 'Acme Corporation',
            'domain': 'acme.com',
            'plan': 'enterprise',
            'settings': {
                'max_scrapers': 100,
                'max_users': 50,
                'data_retention_days': 365
            }
        })
        logger.info(f"Created tenant: {tenant1['id']}")
        
        tenant2 = await tenant_manager.create_tenant({
            'name': 'Tech Startup Inc',
            'domain': 'techstartup.com',
            'plan': 'professional',
            'settings': {
                'max_scrapers': 25,
                'max_users': 10,
                'data_retention_days': 90
            }
        })
        logger.info(f"Created tenant: {tenant2['id']}")
        
        # Create users
        logger.info("Creating users...")
        user1 = await user_manager.create_user({
            'username': 'admin@acme.com',
            'email': 'admin@acme.com',
            'password': 'SecurePassword123!',
            'role': 'admin',
            'tenant_id': tenant1['id'],
            'permissions': ['scraping:all', 'user:all', 'system:all']
        })
        logger.info(f"Created user: {user1['id']}")
        
        user2 = await user_manager.create_user({
            'username': 'user@acme.com',
            'email': 'user@acme.com',
            'password': 'UserPassword123!',
            'role': 'user',
            'tenant_id': tenant1['id'],
            'permissions': ['scraping:read', 'scraping:create']
        })
        logger.info(f"Created user: {user2['id']}")
        
        user3 = await user_manager.create_user({
            'username': 'admin@techstartup.com',
            'email': 'admin@techstartup.com',
            'password': 'StartupPassword123!',
            'role': 'admin',
            'tenant_id': tenant2['id'],
            'permissions': ['scraping:all', 'user:read']
        })
        logger.info(f"Created user: {user3['id']}")
        
        # Test authentication
        logger.info("Testing authentication...")
        auth_result1 = await security.authenticate_user('admin@acme.com', 'SecurePassword123!')
        logger.info(f"Authentication result 1: {auth_result1['success']}")
        
        auth_result2 = await security.authenticate_user('user@acme.com', 'UserPassword123!')
        logger.info(f"Authentication result 2: {auth_result2['success']}")
        
        # Test authorization
        logger.info("Testing authorization...")
        authz_result1 = await security.authorize_user(user1['id'], 'scraping:create')
        logger.info(f"Authorization result 1: {authz_result1}")
        
        authz_result2 = await security.authorize_user(user2['id'], 'user:delete')
        logger.info(f"Authorization result 2: {authz_result2}")
        
        # Test tenant isolation
        logger.info("Testing tenant isolation...")
        tenant1_users = await user_manager.get_users_by_tenant(tenant1['id'])
        tenant2_users = await user_manager.get_users_by_tenant(tenant2['id'])
        logger.info(f"Tenant 1 users: {len(tenant1_users)}")
        logger.info(f"Tenant 2 users: {len(tenant2_users)}")
        
        # Test audit logging
        logger.info("Testing audit logging...")
        await audit.log_event({
            'user_id': user1['id'],
            'tenant_id': tenant1['id'],
            'action': 'user_login',
            'resource': 'authentication',
            'details': {'ip_address': '192.168.1.100'}
        })
        
        await audit.log_event({
            'user_id': user1['id'],
            'tenant_id': tenant1['id'],
            'action': 'scraper_create',
            'resource': 'scraper',
            'details': {'scraper_name': 'example_scraper'}
        })
        
        # Get audit logs
        audit_logs = await audit.get_audit_logs(tenant_id=tenant1['id'])
        logger.info(f"Audit logs for tenant 1: {len(audit_logs)}")
        
        # Test compliance reporting
        logger.info("Testing compliance reporting...")
        compliance_report = await compliance.generate_report(tenant1['id'])
        logger.info(f"Compliance report: {json.dumps(compliance_report, indent=2)}")
        
        # Test monitoring
        logger.info("Testing monitoring...")
        await monitor.record_metric('enterprise_users', 3)
        await monitor.record_metric('enterprise_tenants', 2)
        await monitor.record_metric('enterprise_scrapers', 5)
        
        metrics = await monitor.get_metrics()
        logger.info(f"Enterprise metrics: {json.dumps(metrics, indent=2)}")
        
        # Test analytics
        logger.info("Testing analytics...")
        await analytics.record_event({
            'event_type': 'user_activity',
            'tenant_id': tenant1['id'],
            'user_id': user1['id'],
            'data': {'action': 'login', 'timestamp': datetime.now().isoformat()}
        })
        
        analytics_data = await analytics.get_analytics()
        logger.info(f"Analytics data: {json.dumps(analytics_data, indent=2)}")
        
        # Test data retention
        logger.info("Testing data retention...")
        retention_result = await compliance.enforce_data_retention()
        logger.info(f"Data retention result: {retention_result}")
        
        # Test security scanning
        logger.info("Testing security scanning...")
        security_scan = await security.perform_security_scan()
        logger.info(f"Security scan result: {json.dumps(security_scan, indent=2)}")
        
        # Test backup and recovery
        logger.info("Testing backup and recovery...")
        backup_result = await storage.create_backup()
        logger.info(f"Backup created: {backup_result['backup_id']}")
        
        # Test disaster recovery
        logger.info("Testing disaster recovery...")
        recovery_result = await storage.test_disaster_recovery()
        logger.info(f"Disaster recovery test: {recovery_result}")
        
        # Export enterprise data
        export_data = {
            'tenants': [tenant1, tenant2],
            'users': [user1, user2, user3],
            'audit_logs': audit_logs,
            'compliance_report': compliance_report,
            'metrics': metrics,
            'analytics': analytics_data,
            'security_scan': security_scan,
            'backup_result': backup_result,
            'recovery_result': recovery_result,
            'export_timestamp': datetime.now().isoformat()
        }
        
        export_file = f"enterprise_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Enterprise data exported to: {export_file}")
        
        # Stop components
        await monitor.stop()
        await analytics.stop()
        await compliance.stop()
        await audit.stop()
        
        logger.info("Enterprise features example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in enterprise features example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
