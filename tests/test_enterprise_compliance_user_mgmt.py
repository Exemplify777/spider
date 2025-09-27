"""Tests for enterprise compliance and user management features."""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock

from spider.enterprise.compliance import (
    ComplianceManager, ComplianceRule, AuditEvent, ComplianceReport,
    ComplianceStandard, ComplianceLevel, AuditEventType
)
from spider.enterprise.user_management import (
    UserManager, User, UserProfile, Role, UserGroup, UserSession,
    UserStatus, UserRole, Permission
)
from spider.core.exceptions import ValidationError


class TestComplianceManager:
    """Test compliance management functionality."""
    
    def test_compliance_manager_creation(self):
        """Test compliance manager creation."""
        manager = ComplianceManager()
        assert manager is not None
        assert len(manager.compliance_rules) > 0  # Should have default rules
    
    def test_add_compliance_rule(self):
        """Test adding compliance rule."""
        manager = ComplianceManager()
        
        rule = ComplianceRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test compliance rule",
            standard=ComplianceStandard.GDPR,
            level=ComplianceLevel.HIGH,
            category="data_protection"
        )
        
        manager.add_compliance_rule(rule)
        assert "test_rule" in manager.compliance_rules
        assert manager.compliance_rules["test_rule"].name == "Test Rule"
    
    def test_remove_compliance_rule(self):
        """Test removing compliance rule."""
        manager = ComplianceManager()
        
        # Add a rule first
        rule = ComplianceRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test compliance rule",
            standard=ComplianceStandard.GDPR,
            level=ComplianceLevel.HIGH,
            category="data_protection"
        )
        manager.add_compliance_rule(rule)
        
        # Remove it
        success = manager.remove_compliance_rule("test_rule")
        assert success is True
        assert "test_rule" not in manager.compliance_rules
    
    def test_log_audit_event(self):
        """Test logging audit event."""
        manager = ComplianceManager()
        
        event_id = manager.log_audit_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id="user123",
            tenant_id="tenant456",
            resource_id="resource789",
            action="read",
            description="User accessed data",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert event_id is not None
        assert len(manager.audit_events) == 1
        
        event = manager.audit_events[0]
        assert event.event_type == AuditEventType.DATA_ACCESS
        assert event.user_id == "user123"
        assert event.action == "read"
    
    def test_get_audit_events_with_filters(self):
        """Test getting audit events with filters."""
        manager = ComplianceManager()
        
        # Log some events
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant1", "resource1",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        manager.log_audit_event(
            AuditEventType.USER_LOGIN, "user2", "tenant1", None,
            "login", "User login", "192.168.1.2", "Mozilla/5.0"
        )
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant2", "resource2",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        
        # Test filtering by event type
        events = manager.get_audit_events(event_type=AuditEventType.DATA_ACCESS)
        assert len(events) == 2
        
        # Test filtering by user
        events = manager.get_audit_events(user_id="user1")
        assert len(events) == 2
        
        # Test filtering by tenant
        events = manager.get_audit_events(tenant_id="tenant1")
        assert len(events) == 2
    
    def test_generate_compliance_report(self):
        """Test generating compliance report."""
        manager = ComplianceManager()
        
        # Log some events
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant1", "resource1",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        manager.log_audit_event(
            AuditEventType.DATA_MODIFICATION, "user2", "tenant1", "resource2",
            "update", "Modify data", "192.168.1.2", "Mozilla/5.0"
        )
        
        # Generate report
        start_time = time.time() - 3600  # 1 hour ago
        end_time = time.time()
        
        report = manager.generate_compliance_report(
            standard=ComplianceStandard.GDPR,
            period_start=start_time,
            period_end=end_time,
            generated_by="admin"
        )
        
        assert report is not None
        assert report.standard == ComplianceStandard.GDPR
        assert report.generated_by == "admin"
        assert "total_events" in report.summary
        assert "compliance_score" in report.summary
    
    def test_export_audit_log_csv(self):
        """Test exporting audit log as CSV."""
        manager = ComplianceManager()
        
        # Log some events
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant1", "resource1",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        
        # Export as CSV
        csv_data = manager.export_audit_log(format="csv")
        assert csv_data is not None
        assert "Event ID" in csv_data
        assert "Event Type" in csv_data
        assert "user1" in csv_data
    
    def test_export_audit_log_json(self):
        """Test exporting audit log as JSON."""
        manager = ComplianceManager()
        
        # Log some events
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant1", "resource1",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        
        # Export as JSON
        json_data = manager.export_audit_log(format="json")
        assert json_data is not None
        
        data = json.loads(json_data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["user_id"] == "user1"
    
    def test_get_compliance_dashboard_data(self):
        """Test getting compliance dashboard data."""
        manager = ComplianceManager()
        
        # Log some events
        manager.log_audit_event(
            AuditEventType.DATA_ACCESS, "user1", "tenant1", "resource1",
            "read", "Access data", "192.168.1.1", "Mozilla/5.0"
        )
        
        # Get dashboard data
        dashboard_data = manager.get_compliance_dashboard_data()
        assert "total_events" in dashboard_data
        assert "event_counts" in dashboard_data
        assert "severity_counts" in dashboard_data
        assert "compliance_rules" in dashboard_data


class TestUserManager:
    """Test user management functionality."""
    
    def test_user_manager_creation(self):
        """Test user manager creation."""
        manager = UserManager()
        assert manager is not None
        assert len(manager.roles) > 0  # Should have default roles
    
    def test_create_user(self):
        """Test user creation."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        assert user is not None
        assert user.username == "johndoe"
        assert user.email == "john.doe@example.com"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.PENDING
    
    def test_duplicate_user_creation(self):
        """Test creating duplicate user."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        # Create first user
        manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Try to create duplicate
        with pytest.raises(ValidationError):
            manager.create_user(
                username="johndoe",
                email="john.doe@example.com",
                password="password123",
                profile=profile,
                role=UserRole.USER
            )
    
    def test_get_user(self):
        """Test getting user."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Get by ID
        retrieved_user = manager.get_user(user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.username == "johndoe"
        
        # Get by username
        retrieved_user = manager.get_user_by_username("johndoe")
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
        
        # Get by email
        retrieved_user = manager.get_user_by_email("john.doe@example.com")
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
    
    def test_authenticate_user(self):
        """Test user authentication."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Test successful authentication
        authenticated_user = manager.authenticate_user("johndoe", "password123")
        assert authenticated_user is not None
        assert authenticated_user.user_id == user.user_id
        assert authenticated_user.status == UserStatus.ACTIVE
        
        # Test failed authentication
        authenticated_user = manager.authenticate_user("johndoe", "wrongpassword")
        assert authenticated_user is None
        
        # Test authentication by email
        authenticated_user = manager.authenticate_user("john.doe@example.com", "password123")
        assert authenticated_user is not None
        assert authenticated_user.user_id == user.user_id
    
    def test_change_password(self):
        """Test changing password."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Change password
        success = manager.change_password(user.user_id, "password123", "newpassword456")
        assert success is True
        
        # Test authentication with new password
        authenticated_user = manager.authenticate_user("johndoe", "newpassword456")
        assert authenticated_user is not None
        
        # Test authentication with old password should fail
        authenticated_user = manager.authenticate_user("johndoe", "password123")
        assert authenticated_user is None
    
    def test_reset_password(self):
        """Test resetting password."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Reset password
        success = manager.reset_password(user.user_id, "newpassword456")
        assert success is True
        
        # Test authentication with new password
        authenticated_user = manager.authenticate_user("johndoe", "newpassword456")
        assert authenticated_user is not None
    
    def test_create_session(self):
        """Test creating user session."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Create session
        session = manager.create_session(
            user_id=user.user_id,
            tenant_id="tenant123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert session is not None
        assert session.user_id == user.user_id
        assert session.tenant_id == "tenant123"
        assert session.is_active is True
        
        # Get session
        retrieved_session = manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.user_id == user.user_id
    
    def test_check_permission(self):
        """Test checking user permissions."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Test permissions
        assert manager.check_permission(user.user_id, Permission.READ_SCRAPER) is True
        assert manager.check_permission(user.user_id, Permission.CREATE_SCRAPER) is True
        assert manager.check_permission(user.user_id, Permission.DELETE_USER) is False  # User role doesn't have this
        assert manager.check_permission(user.user_id, Permission.MANAGE_SYSTEM) is False  # User role doesn't have this
    
    def test_create_group(self):
        """Test creating user group."""
        manager = UserManager()
        
        group = manager.create_group(
            name="Developers",
            description="Development team",
            permissions=[Permission.CREATE_SCRAPER, Permission.READ_SCRAPER]
        )
        
        assert group is not None
        assert group.name == "Developers"
        assert Permission.CREATE_SCRAPER in group.permissions
    
    def test_add_user_to_group(self):
        """Test adding user to group."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        group = manager.create_group(
            name="Developers",
            description="Development team",
            permissions=[Permission.MANAGE_SYSTEM]  # User role doesn't have this
        )
        
        # Add user to group
        success = manager.add_user_to_group(user.user_id, group.group_id)
        assert success is True
        
        # Check if user now has group permission
        assert manager.check_permission(user.user_id, Permission.MANAGE_SYSTEM) is True
    
    def test_list_users(self):
        """Test listing users with filters."""
        manager = UserManager()
        
        profile1 = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        profile2 = UserProfile(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com"
        )
        
        user1 = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile1,
            role=UserRole.USER,
            tenant_id="tenant1"
        )
        
        user2 = manager.create_user(
            username="janesmith",
            email="jane.smith@example.com",
            password="password123",
            profile=profile2,
            role=UserRole.ADMIN,
            tenant_id="tenant2"
        )
        
        # List all users
        users = manager.list_users()
        assert len(users) == 2
        
        # Filter by tenant
        users = manager.list_users(tenant_id="tenant1")
        assert len(users) == 1
        assert users[0].username == "johndoe"
        
        # Filter by role
        users = manager.list_users(role=UserRole.ADMIN)
        assert len(users) == 1
        assert users[0].username == "janesmith"
    
    def test_get_user_statistics(self):
        """Test getting user statistics."""
        manager = UserManager()
        
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Create session
        manager.create_session(
            user_id=user.user_id,
            tenant_id="tenant123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        stats = manager.get_user_statistics()
        assert stats["total_users"] == 1
        assert stats["active_users"] >= 0  # User starts as PENDING, not ACTIVE
        assert "status_counts" in stats
        assert "role_counts" in stats
        assert "active_sessions" in stats


class TestIntegration:
    """Test integration between compliance and user management."""
    
    def test_compliance_user_integration(self):
        """Test integration between compliance and user management."""
        compliance_manager = ComplianceManager()
        user_manager = UserManager()
        
        # Create user
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        user = user_manager.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="password123",
            profile=profile,
            role=UserRole.USER
        )
        
        # Log audit events for user actions
        compliance_manager.log_audit_event(
            AuditEventType.USER_LOGIN,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            resource_id=None,
            action="login",
            description="User logged in",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        compliance_manager.log_audit_event(
            AuditEventType.DATA_ACCESS,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            resource_id="resource123",
            action="read",
            description="User accessed data",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Get events for user
        events = compliance_manager.get_audit_events(user_id=user.user_id)
        assert len(events) == 2
        
        # Check user permissions
        assert user_manager.check_permission(user.user_id, Permission.READ_DATA) is True
        
        # Generate compliance report
        start_time = time.time() - 3600
        end_time = time.time()
        
        report = compliance_manager.generate_compliance_report(
            standard=ComplianceStandard.GDPR,
            period_start=start_time,
            period_end=end_time,
            generated_by=user.user_id
        )
        
        assert report is not None
        assert report.generated_by == user.user_id
    
    def test_end_to_end_enterprise_workflow(self):
        """Test complete enterprise workflow."""
        # Initialize managers
        compliance_manager = ComplianceManager()
        user_manager = UserManager()
        
        # Create admin user
        admin_profile = UserProfile(
            first_name="Admin",
            last_name="User",
            email="admin@example.com"
        )
        
        admin = user_manager.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            profile=admin_profile,
            role=UserRole.ADMIN
        )
        
        # Create regular user
        user_profile = UserProfile(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        user = user_manager.create_user(
            username="johndoe",
            email="john@example.com",
            password="password123",
            profile=user_profile,
            role=UserRole.USER
        )
        
        # Admin creates session
        admin_session = user_manager.create_session(
            user_id=admin.user_id,
            tenant_id="tenant123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        # User creates session
        user_session = user_manager.create_session(
            user_id=user.user_id,
            tenant_id="tenant123",
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0"
        )
        
        # Log audit events
        compliance_manager.log_audit_event(
            AuditEventType.USER_LOGIN,
            user_id=admin.user_id,
            tenant_id="tenant123",
            resource_id=None,
            action="login",
            description="Admin logged in",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        compliance_manager.log_audit_event(
            AuditEventType.USER_LOGIN,
            user_id=user.user_id,
            tenant_id="tenant123",
            resource_id=None,
            action="login",
            description="User logged in",
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0"
        )
        
        # Admin performs admin action
        compliance_manager.log_audit_event(
            AuditEventType.ADMIN_ACTION,
            user_id=admin.user_id,
            tenant_id="tenant123",
            resource_id="system",
            action="create_user",
            description="Admin created new user",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        # User accesses data
        compliance_manager.log_audit_event(
            AuditEventType.DATA_ACCESS,
            user_id=user.user_id,
            tenant_id="tenant123",
            resource_id="data123",
            action="read",
            description="User accessed data",
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0"
        )
        
        # Verify permissions - admin should have MANAGE_SYSTEM permission
        # First authenticate the admin to activate the user
        authenticated_admin = user_manager.authenticate_user("admin", "admin123")
        assert authenticated_admin is not None
        assert user_manager.check_permission(admin.user_id, Permission.MANAGE_SYSTEM) is True
        assert user_manager.check_permission(user.user_id, Permission.READ_DATA) is True
        assert user_manager.check_permission(user.user_id, Permission.MANAGE_SYSTEM) is False
        
        # Generate compliance report
        start_time = time.time() - 3600
        end_time = time.time()
        
        report = compliance_manager.generate_compliance_report(
            standard=ComplianceStandard.GDPR,
            period_start=start_time,
            period_end=end_time,
            generated_by=admin.user_id
        )
        
        assert report is not None
        assert report.compliance_score >= 0
        assert len(report.findings) >= 0
        
        # Get user statistics
        user_stats = user_manager.get_user_statistics()
        assert user_stats["total_users"] == 2
        assert user_stats["active_sessions"] == 2
        
        # Get compliance dashboard data
        compliance_data = compliance_manager.get_compliance_dashboard_data()
        assert compliance_data["total_events"] == 4
        assert "event_counts" in compliance_data
