"""Tests for enterprise features."""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock

from spider.enterprise.multi_tenant import (
    TenantManager, TenantMiddleware, Tenant, TenantContext, TenantLimits, TenantUsage,
    TenantStatus, TenantTier, ResourceType
)
from spider.enterprise.security import (
    SecurityManager, PasswordValidator, EncryptionManager, JWTManager, SessionManager, AuditLogger,
    SecurityConfig, SecurityEvent, UserSession, SecurityLevel, EncryptionAlgorithm, HashAlgorithm
)
from spider.enterprise.dashboard import (
    DashboardManager, MetricCollector, ChartGenerator, AlertManager,
    Dashboard, WidgetConfig, MetricData, ChartData, AlertRule,
    DashboardType, WidgetType, ChartType
)


class TestMultiTenant:
    """Test multi-tenant functionality."""
    
    def test_tenant_manager_creation(self):
        """Test tenant manager creation."""
        manager = TenantManager()
        assert manager is not None
        assert len(manager.tenants) == 0
    
    def test_create_tenant(self):
        """Test tenant creation."""
        manager = TenantManager()
        
        tenant = manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.BASIC
        )
        
        assert tenant.name == "Test Company"
        assert tenant.domain == "test.com"
        assert tenant.tier == TenantTier.BASIC
        assert tenant.status == TenantStatus.PENDING
        assert tenant.tenant_id in manager.tenants
    
    def test_tenant_resource_limits(self):
        """Test tenant resource limits."""
        manager = TenantManager()
        
        # Create tenant with custom limits
        custom_limits = TenantLimits(
            max_scraping_jobs=50,
            max_data_storage_mb=5000,
            max_api_requests_per_hour=5000
        )
        
        tenant = manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.PROFESSIONAL,
            custom_limits=custom_limits
        )
        tenant.status = TenantStatus.ACTIVE
        
        # Check resource limits
        can_use, error = manager.check_resource_limit(
            tenant.tenant_id, ResourceType.SCRAPING_JOBS, 10
        )
        assert can_use is True
        
        can_use, error = manager.check_resource_limit(
            tenant.tenant_id, ResourceType.SCRAPING_JOBS, 100
        )
        assert can_use is False
        assert "limit exceeded" in error
    
    def test_tenant_resource_usage(self):
        """Test tenant resource usage tracking."""
        manager = TenantManager()
        
        tenant = manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.BASIC
        )
        tenant.status = TenantStatus.ACTIVE
        
        # Use resources
        success = manager.use_resource(tenant.tenant_id, ResourceType.SCRAPING_JOBS, 5)
        assert success is True
        
        # Check usage
        usage = manager.get_tenant_usage(tenant.tenant_id)
        assert usage["current_usage"]["scraping_jobs"] == 5
        
        # Release resources
        manager.release_resource(tenant.tenant_id, ResourceType.SCRAPING_JOBS, 2)
        
        usage = manager.get_tenant_usage(tenant.tenant_id)
        assert usage["current_usage"]["scraping_jobs"] == 3
    
    def test_tenant_context(self):
        """Test tenant context management."""
        manager = TenantManager()
        
        context = TenantContext(
            tenant_id="test-tenant",
            user_id="test-user",
            request_id="test-request"
        )
        
        manager.set_tenant_context(context)
        retrieved_context = manager.get_tenant_context("test-tenant")
        
        assert retrieved_context is not None
        assert retrieved_context.tenant_id == "test-tenant"
        assert retrieved_context.user_id == "test-user"
    
    def test_tenant_middleware(self):
        """Test tenant middleware."""
        manager = TenantManager()
        middleware = TenantMiddleware(manager)
        
        # Create tenant
        tenant = manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.BASIC
        )
        tenant.status = TenantStatus.ACTIVE
        
        # Test tenant resolution by ID
        headers = {"X-Tenant-ID": tenant.tenant_id}
        current_tenant = middleware.get_current_tenant(headers)
        assert current_tenant is not None
        assert current_tenant.tenant_id == tenant.tenant_id
        
        # Test tenant resolution by domain
        headers = {"Host": "test.com"}
        current_tenant = middleware.get_current_tenant(headers)
        assert current_tenant is not None
        assert current_tenant.domain == "test.com"
    
    def test_tenant_statistics(self):
        """Test tenant statistics."""
        manager = TenantManager()
        
        # Create multiple tenants
        for i in range(5):
            manager.create_tenant(
                name=f"Company {i}",
                domain=f"company{i}.com",
                tier=TenantTier.BASIC if i % 2 == 0 else TenantTier.PROFESSIONAL
            )
        
        stats = manager.get_tenant_statistics()
        assert stats["total_tenants"] == 5
        assert "tier_distribution" in stats
        assert stats["tier_distribution"]["basic"] == 3
        assert stats["tier_distribution"]["professional"] == 2


class TestSecurity:
    """Test security features."""
    
    def test_security_config(self):
        """Test security configuration."""
        config = SecurityConfig(
            encryption_algorithm=EncryptionAlgorithm.FERNET,
            hash_algorithm=HashAlgorithm.SHA_256,
            password_min_length=12,
            enable_2fa=True
        )
        
        assert config.encryption_algorithm == EncryptionAlgorithm.FERNET
        assert config.hash_algorithm == HashAlgorithm.SHA_256
        assert config.password_min_length == 12
        assert config.enable_2fa is True
    
    def test_password_validator(self):
        """Test password validation."""
        config = SecurityConfig(password_min_length=8)
        validator = PasswordValidator(config)
        
        # Test valid password
        is_valid, errors = validator.validate_password("StrongPass123!")
        assert is_valid is True
        assert len(errors) == 0
        
        # Test invalid password
        is_valid, errors = validator.validate_password("weak")
        assert is_valid is False
        assert len(errors) > 0
        
        # Test password hashing
        password = "testpassword"
        hashed = validator.hash_password(password)
        assert hashed != password
        assert validator.verify_password(password, hashed) is True
    
    def test_encryption_manager(self):
        """Test encryption manager."""
        config = SecurityConfig(encryption_algorithm=EncryptionAlgorithm.FERNET)
        manager = EncryptionManager(config)
        
        # Test encryption/decryption
        data = "sensitive data"
        encrypted = manager.encrypt(data)
        assert encrypted != data
        
        decrypted = manager.decrypt(encrypted)
        assert decrypted == data
    
    def test_jwt_manager(self):
        """Test JWT token management."""
        config = SecurityConfig(jwt_expiry_hours=1)
        manager = JWTManager(config)
        
        # Create token
        token = manager.create_token("user123", "tenant456", additional_claims={"role": "admin"})
        assert token is not None
        
        # Verify token
        payload = manager.verify_token(token)
        assert payload["user_id"] == "user123"
        assert payload["tenant_id"] == "tenant456"
        assert payload["role"] == "admin"
        
        # Test token refresh
        new_token = manager.refresh_token(token)
        assert new_token != token
        
        new_payload = manager.verify_token(new_token)
        assert new_payload["user_id"] == "user123"
        assert new_payload["tenant_id"] == "tenant456"
    
    def test_session_manager(self):
        """Test session management."""
        config = SecurityConfig(session_timeout_minutes=60)
        manager = SessionManager(config)
        
        # Create session
        session = manager.create_session(
            user_id="user123",
            tenant_id="tenant456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert session.user_id == "user123"
        assert session.tenant_id == "tenant456"
        assert session.is_active is True
        
        # Get session
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        
        # Update activity
        success = manager.update_session_activity(session.session_id)
        assert success is True
        
        # Invalidate session
        success = manager.invalidate_session(session.session_id)
        assert success is True
        
        # Session should be inactive
        retrieved = manager.get_session(session.session_id)
        assert retrieved is None
    
    def test_audit_logger(self):
        """Test audit logging."""
        config = SecurityConfig(enable_audit_logging=True)
        logger = AuditLogger(config)
        
        # Log security event
        logger.log_event(
            event_type="login_success",
            user_id="user123",
            tenant_id="tenant456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            severity=SecurityLevel.MEDIUM,
            description="User logged in successfully"
        )
        
        # Get events
        events = logger.get_events(event_type="login_success")
        assert len(events) == 1
        assert events[0].user_id == "user123"
        assert events[0].event_type == "login_success"
        
        # Get statistics
        stats = logger.get_security_statistics()
        assert stats["total_events"] == 1
        assert "events_by_type" in stats
        assert "events_by_severity" in stats
    
    def test_security_manager(self):
        """Test main security manager."""
        config = SecurityConfig()
        manager = SecurityManager(config)
        
        # Test password validation
        is_valid, errors = manager.validate_password("StrongPass123!")
        assert is_valid is True
        
        # Test password hashing
        password = "testpassword"
        hashed = manager.hash_password(password)
        assert manager.verify_password(password, hashed) is True
        
        # Test encryption
        data = "sensitive data"
        encrypted = manager.encrypt_data(data)
        decrypted = manager.decrypt_data(encrypted)
        assert decrypted == data
        
        # Test JWT
        token = manager.create_token("user123", "tenant456")
        payload = manager.verify_token(token)
        assert payload["user_id"] == "user123"
        
        # Test session
        session = manager.create_session(
            "user123", "tenant456", "192.168.1.1", "Mozilla/5.0"
        )
        assert session.user_id == "user123"
        
        # Test login attempts
        can_login = manager.check_login_attempts("user123", "192.168.1.1")
        assert can_login is True
        
        # Record failed attempt
        manager.record_login_attempt("user123", "192.168.1.1", False)
        
        # Should still be able to login (under limit)
        can_login = manager.check_login_attempts("user123", "192.168.1.1")
        assert can_login is True


class TestDashboard:
    """Test dashboard functionality."""
    
    def test_metric_collector(self):
        """Test metric collection."""
        collector = MetricCollector()
        
        # Record metrics
        collector.record_metric("requests_total", 100, {"endpoint": "/api"})
        collector.record_metric("requests_total", 150, {"endpoint": "/api"})
        collector.record_metric("requests_total", 200, {"endpoint": "/api"})
        
        # Get metric data
        data = collector.get_metric_data("requests_total")
        assert len(data) == 3
        assert data[-1].value == 200
        
        # Get summary
        summary = collector.get_metric_summary("requests_total")
        assert summary["count"] == 3
        assert summary["latest_value"] == 200
        assert "avg" in summary
        assert "trend" in summary
    
    def test_chart_generator(self):
        """Test chart generation."""
        collector = MetricCollector()
        generator = ChartGenerator(collector)
        
        # Record some data
        for i in range(10):
            collector.record_metric("cpu_usage", 50 + i)
        
        # Generate line chart
        chart_data = generator.generate_line_chart("cpu_usage")
        assert hasattr(chart_data, 'labels')
        assert hasattr(chart_data, 'datasets')
        assert len(chart_data.datasets) > 0
        
        # Generate bar chart
        chart_data = generator.generate_bar_chart("cpu_usage")
        assert hasattr(chart_data, 'labels')
        assert hasattr(chart_data, 'datasets')
        
        # Generate pie chart
        collector.record_metric("status_codes", 100, {"code": "200"})
        collector.record_metric("status_codes", 50, {"code": "404"})
        collector.record_metric("status_codes", 25, {"code": "500"})
        
        chart_data = generator.generate_pie_chart("status_codes", "code")
        assert hasattr(chart_data, 'labels')
        assert hasattr(chart_data, 'datasets')
    
    def test_alert_manager(self):
        """Test alert management."""
        manager = AlertManager()
        
        # Add alert rule
        rule = AlertRule(
            rule_id="high_cpu",
            name="High CPU Usage",
            metric="cpu_usage",
            condition="value > threshold",
            threshold=80.0,
            severity="warning"
        )
        manager.add_alert_rule(rule)
        
        # Check alerts
        alerts = manager.check_alerts("cpu_usage", 90.0)
        assert len(alerts) == 1
        assert alerts[0]["rule_name"] == "High CPU Usage"
        assert alerts[0]["severity"] == "warning"
        
        # Get active alerts
        active_alerts = manager.get_active_alerts()
        assert len(active_alerts) == 1
        
        # Clear alert
        alert_id = alerts[0]["alert_id"]
        success = manager.clear_alert(alert_id)
        assert success is True
        
        # Should be no active alerts
        active_alerts = manager.get_active_alerts()
        assert len(active_alerts) == 0
    
    def test_dashboard_manager(self):
        """Test dashboard management."""
        manager = DashboardManager()
        
        # Create dashboard
        dashboard = manager.create_dashboard(
            name="Test Dashboard",
            dashboard_type=DashboardType.CUSTOM,
            description="Test dashboard for testing"
        )
        
        assert dashboard.name == "Test Dashboard"
        assert dashboard.dashboard_type == DashboardType.CUSTOM
        
        # Add widget
        widget = WidgetConfig(
            widget_id="test_widget",
            widget_type=WidgetType.METRIC,
            title="Test Metric",
            position=(0, 0),
            size=(2, 2),
            config={"metric": "test_metric"}
        )
        
        success = manager.add_widget(dashboard.dashboard_id, widget)
        assert success is True
        
        # Record some metrics
        manager.record_metric("test_metric", 100)
        manager.record_metric("test_metric", 150)
        manager.record_metric("test_metric", 200)
        
        # Get dashboard data
        dashboard_data = manager.get_dashboard_data(dashboard.dashboard_id)
        assert dashboard_data["name"] == "Test Dashboard"
        assert len(dashboard_data["widgets"]) == 1
        
        # Get dashboard list
        dashboards = manager.get_dashboard_list()
        assert len(dashboards) >= 1  # At least the default overview dashboard
    
    def test_dashboard_widget_types(self):
        """Test different widget types."""
        manager = DashboardManager()
        
        # Create dashboard
        dashboard = manager.create_dashboard(
            name="Widget Test Dashboard",
            dashboard_type=DashboardType.CUSTOM
        )
        
        # Add different widget types
        widgets = [
            WidgetConfig(
                widget_id="metric_widget",
                widget_type=WidgetType.METRIC,
                title="Metric Widget",
                position=(0, 0),
                size=(2, 2),
                config={"metric": "test_metric"}
            ),
            WidgetConfig(
                widget_id="chart_widget",
                widget_type=WidgetType.CHART,
                title="Chart Widget",
                position=(2, 0),
                size=(4, 4),
                config={"metric": "test_metric", "chart_type": "line"}
            ),
            WidgetConfig(
                widget_id="alert_widget",
                widget_type=WidgetType.ALERT,
                title="Alert Widget",
                position=(0, 2),
                size=(2, 2)
            )
        ]
        
        for widget in widgets:
            success = manager.add_widget(dashboard.dashboard_id, widget)
            assert success is True
        
        # Record metrics and create alerts
        manager.record_metric("test_metric", 100)
        
        # Add alert rule
        rule = AlertRule(
            rule_id="test_alert",
            name="Test Alert",
            metric="test_metric",
            condition="value > threshold",
            threshold=50.0
        )
        manager.add_alert_rule(rule)
        
        # Get dashboard data
        dashboard_data = manager.get_dashboard_data(dashboard.dashboard_id)
        assert len(dashboard_data["widgets"]) == 3
        
        # Check widget data
        for widget_data in dashboard_data["widgets"]:
            assert "data" in widget_data
            assert widget_data["type"] in ["metric", "chart", "alert"]


class TestIntegration:
    """Test integration between enterprise components."""
    
    def test_tenant_security_integration(self):
        """Test integration between tenant and security features."""
        # Create tenant manager
        tenant_manager = TenantManager()
        tenant = tenant_manager.create_tenant(
            name="Secure Company",
            domain="secure.com",
            tier=TenantTier.ENTERPRISE
        )
        tenant.status = TenantStatus.ACTIVE
        
        # Create security manager
        security_config = SecurityConfig()
        security_manager = SecurityManager(security_config)
        
        # Create user session
        session = security_manager.create_session(
            user_id="user123",
            tenant_id=tenant.tenant_id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Verify session belongs to tenant
        assert session.tenant_id == tenant.tenant_id
        
        # Create JWT token
        token = security_manager.create_token(
            user_id="user123",
            tenant_id=tenant.tenant_id,
            role="admin"
        )
        
        # Verify token
        payload = security_manager.verify_token(token)
        assert payload["tenant_id"] == tenant.tenant_id
        
        # Test resource access
        can_use, error = tenant_manager.check_resource_limit(
            tenant.tenant_id, ResourceType.SCRAPING_JOBS, 10
        )
        assert can_use is True
    
    def test_dashboard_tenant_integration(self):
        """Test integration between dashboard and tenant features."""
        # Create tenant manager
        tenant_manager = TenantManager()
        tenant = tenant_manager.create_tenant(
            name="Dashboard Company",
            domain="dashboard.com",
            tier=TenantTier.PROFESSIONAL
        )
        
        # Create dashboard manager
        dashboard_manager = DashboardManager()
        
        # Create tenant-specific dashboard
        dashboard = dashboard_manager.create_dashboard(
            name="Tenant Dashboard",
            dashboard_type=DashboardType.CUSTOM,
            tenant_id=tenant.tenant_id
        )
        
        # Record tenant-specific metrics
        dashboard_manager.record_metric(
            "tenant_requests",
            100,
            labels={"tenant_id": tenant.tenant_id}
        )
        
        # Get tenant dashboards
        tenant_dashboards = dashboard_manager.get_dashboard_list(tenant_id=tenant.tenant_id)
        assert len(tenant_dashboards) == 1
        assert tenant_dashboards[0]["name"] == "Tenant Dashboard"
    
    def test_security_dashboard_integration(self):
        """Test integration between security and dashboard features."""
        # Create security manager
        security_config = SecurityConfig(enable_audit_logging=True)
        security_manager = SecurityManager(security_config)
        
        # Create dashboard manager
        dashboard_manager = DashboardManager()
        
        # Log security events
        security_manager.log_security_event(
            event_type="login_success",
            user_id="user123",
            tenant_id="tenant456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            severity=SecurityLevel.MEDIUM,
            description="User logged in"
        )
        
        security_manager.log_security_event(
            event_type="login_failed",
            user_id="user456",
            tenant_id="tenant456",
            ip_address="192.168.1.2",
            user_agent="Mozilla/5.0",
            severity=SecurityLevel.HIGH,
            description="Failed login attempt"
        )
        
        # Record security metrics
        dashboard_manager.record_metric("security_events", 1, {"type": "login_success"})
        dashboard_manager.record_metric("security_events", 1, {"type": "login_failed"})
        
        # Create security dashboard
        dashboard = dashboard_manager.create_dashboard(
            name="Security Dashboard",
            dashboard_type=DashboardType.SECURITY
        )
        
        # Add security widgets
        security_widget = WidgetConfig(
            widget_id="security_events",
            widget_type=WidgetType.CHART,
            title="Security Events",
            position=(0, 0),
            size=(6, 4),
            config={"metric": "security_events", "chart_type": "pie"}
        )
        
        dashboard_manager.add_widget(dashboard.dashboard_id, security_widget)
        
        # Get dashboard data
        dashboard_data = dashboard_manager.get_dashboard_data(dashboard.dashboard_id)
        assert dashboard_data["name"] == "Security Dashboard"
        assert len(dashboard_data["widgets"]) == 1
    
    def test_end_to_end_enterprise_workflow(self):
        """Test complete enterprise workflow."""
        # 1. Create tenant
        tenant_manager = TenantManager()
        tenant = tenant_manager.create_tenant(
            name="Enterprise Corp",
            domain="enterprise.com",
            tier=TenantTier.ENTERPRISE
        )
        tenant.status = TenantStatus.ACTIVE
        
        # 2. Setup security
        security_config = SecurityConfig(enable_audit_logging=True)
        security_manager = SecurityManager(security_config)
        
        # 3. User authentication
        password = "SecurePass123!"
        hashed_password = security_manager.hash_password(password)
        
        # 4. Create session
        session = security_manager.create_session(
            user_id="admin",
            tenant_id=tenant.tenant_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        # 5. Create JWT token
        token = security_manager.create_token(
            user_id="admin",
            tenant_id=tenant.tenant_id,
            role="admin"
        )
        
        # 6. Setup dashboard
        dashboard_manager = DashboardManager()
        dashboard = dashboard_manager.create_dashboard(
            name="Enterprise Dashboard",
            dashboard_type=DashboardType.OVERVIEW,
            tenant_id=tenant.tenant_id
        )
        
        # 7. Record metrics
        dashboard_manager.record_metric("scraping_jobs", 5, {"tenant_id": tenant.tenant_id})
        dashboard_manager.record_metric("data_processed", 1000, {"tenant_id": tenant.tenant_id})
        
        # 8. Check resource usage
        can_use, error = tenant_manager.check_resource_limit(
            tenant.tenant_id, ResourceType.SCRAPING_JOBS, 1
        )
        assert can_use is True
        
        # 9. Use resources
        success = tenant_manager.use_resource(tenant.tenant_id, ResourceType.SCRAPING_JOBS, 1)
        assert success is True
        
        # 10. Log security event
        security_manager.log_security_event(
            event_type="resource_used",
            user_id="admin",
            tenant_id=tenant.tenant_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            severity=SecurityLevel.LOW,
            description="Scraping job started"
        )
        
        # 11. Get dashboard data
        dashboard_data = dashboard_manager.get_dashboard_data(dashboard.dashboard_id)
        assert dashboard_data["name"] == "Enterprise Dashboard"
        
        # 12. Verify everything is working
        assert session.tenant_id == tenant.tenant_id
        assert security_manager.verify_password(password, hashed_password) is True
        
        payload = security_manager.verify_token(token)
        assert payload["tenant_id"] == tenant.tenant_id
        
        usage = tenant_manager.get_tenant_usage(tenant.tenant_id)
        assert usage["current_usage"]["scraping_jobs"] == 1
