"""Comprehensive test coverage for all SPIDER components."""

import pytest
import asyncio
import time
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Core components
from spider.core.config import Config
from spider.core.engine import EngineFactory
from spider.core.logger import get_logger
from spider.core.exceptions import SpiderError, ValidationError, SecurityError

# Infrastructure components
from spider.infrastructure.proxy import ProxyManager, ProxyProvider, ProxyPool
from spider.infrastructure.captcha import CAPTCHAManager, CAPTCHAProvider
from spider.infrastructure.rate_limiter import RateLimiter, AdaptiveRateLimiter
from spider.infrastructure.session import SessionManager, CookieManager
from spider.infrastructure.behavior_simulation import BehaviorSimulator, BehaviorManager
from spider.infrastructure.cache import CacheManager, MemoryCache, DiskCache
from spider.infrastructure.load_balancer import LoadBalancer, Server
from spider.infrastructure.autoscaler import AutoScaler, ScalingConfig

# Monitoring components
from spider.monitoring.metrics import MetricsCollector, PrometheusMetrics
from spider.monitoring.health import HealthChecker, SystemHealth
from spider.monitoring.recovery import RecoveryManager, RecoveryRule
from spider.monitoring.alerts import AlertManager, AlertRule
from spider.monitoring.performance import PerformanceMonitor, PerformanceProfiler

# Processing components
from spider.processors.extractors import HTMLExtractor, JSONExtractor, XMLExtractor
from spider.processors.transformers import DataCleaner, DataNormalizer, DataEnricher
from spider.processors.validators import DataValidator, SchemaValidator
from spider.processors.storage import FileStorage, DatabaseStorage
from spider.processors.ml_extractor import MLExtractionManager, RuleBasedExtractor
from spider.processors.intelligent_validator import IntelligentValidator, FormatValidator
from spider.processors.transformation_pipeline import TransformationPipeline, PipelineConfig
from spider.processors.realtime_processor import StreamProcessor, ProcessingConfig
from spider.processors.quality_scorer import DataQualityScorer, CompletenessScorer

# Enterprise components
from spider.enterprise.multi_tenant import TenantManager, Tenant, TenantTier
from spider.enterprise.security import SecurityManager, SecurityConfig
from spider.enterprise.dashboard import DashboardManager, MetricCollector


class TestCoreComponents:
    """Test core framework components."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = Config()
        assert config is not None
        assert hasattr(config, 'scraping')
        assert hasattr(config, 'storage')
        assert hasattr(config, 'monitoring')
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        config = Config()
        engine = SpiderEngine(config)
        assert engine is not None
        assert engine.config == config
    
    def test_logger_functionality(self):
        """Test logger functionality."""
        logger = get_logger("test_logger")
        assert logger is not None
        
        # Test logging levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_exception_hierarchy(self):
        """Test exception hierarchy."""
        # Test base exception
        with pytest.raises(SpiderError):
            raise SpiderError("Test error")
        
        # Test validation error
        with pytest.raises(ValidationError):
            raise ValidationError("Validation failed")
        
        # Test security error
        with pytest.raises(SecurityError):
            raise SecurityError("Security violation")


class TestInfrastructureComponents:
    """Test infrastructure components."""
    
    def test_proxy_management(self):
        """Test proxy management."""
        manager = ProxyManager()
        
        # Add proxy
        success = manager.add_proxy("http://proxy1:8080", "username", "password")
        assert success is True
        
        # Get proxy
        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.url == "http://proxy1:8080"
        
        # Test proxy pool
        pool = ProxyPool(max_size=10)
        pool.add_proxy("http://proxy1:8080")
        pool.add_proxy("http://proxy2:8080")
        
        assert pool.size() == 2
        proxy = pool.get_proxy()
        assert proxy is not None
    
    def test_captcha_management(self):
        """Test CAPTCHA management."""
        manager = CAPTCHAManager()
        
        # Test CAPTCHA solving (mock)
        with patch.object(manager, '_solve_captcha') as mock_solve:
            mock_solve.return_value = "solved_text"
            
            result = asyncio.run(manager.solve_captcha("image_data", "image_captcha"))
            assert result == "solved_text"
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        limiter = RateLimiter(requests_per_second=10)
        
        # Test rate limiting
        for i in range(5):
            can_proceed = asyncio.run(limiter.acquire())
            assert can_proceed is True
        
        # Test adaptive rate limiter
        adaptive_limiter = AdaptiveRateLimiter(
            initial_rate=10,
            min_rate=1,
            max_rate=100
        )
        
        can_proceed = asyncio.run(adaptive_limiter.acquire())
        assert can_proceed is True
    
    def test_session_management(self):
        """Test session management."""
        manager = SessionManager()
        
        # Create session
        session = manager.create_session("session1")
        assert session is not None
        assert session.session_id == "session1"
        
        # Add cookie
        manager.add_cookie("session1", "test.com", "cookie1", "value1")
        
        # Get cookies
        cookies = manager.get_cookies("session1", "test.com")
        assert len(cookies) == 1
        assert cookies[0].name == "cookie1"
    
    def test_behavior_simulation(self):
        """Test behavior simulation."""
        simulator = BehaviorSimulator()
        
        # Test mouse movement
        movement = simulator.generate_mouse_movement(100, 200, 300, 400)
        assert len(movement) > 0
        assert movement[0] == (100, 200)
        assert movement[-1] == (300, 400)
        
        # Test scroll behavior
        scroll = simulator.generate_scroll_behavior(0, 1000)
        assert len(scroll) > 0
    
    def test_caching_system(self):
        """Test caching system."""
        manager = CacheManager()
        
        # Test memory cache
        memory_cache = MemoryCache(max_size=100)
        memory_cache.set("key1", "value1", ttl=60)
        
        value = memory_cache.get("key1")
        assert value == "value1"
        
        # Test cache manager
        manager.add_cache("memory", memory_cache)
        manager.set("key2", "value2", cache_name="memory")
        
        value = manager.get("key2", cache_name="memory")
        assert value == "value2"
    
    def test_load_balancing(self):
        """Test load balancing."""
        balancer = LoadBalancer()
        
        # Add servers
        balancer.add_server("server1", "http://server1:8080")
        balancer.add_server("server2", "http://server2:8080")
        
        # Get server
        server = balancer.get_server()
        assert server is not None
        assert server.name in ["server1", "server2"]
        
        # Test health checking
        balancer.check_health()
        stats = balancer.get_stats()
        assert stats is not None
    
    def test_auto_scaling(self):
        """Test auto-scaling."""
        config = ScalingConfig(
            min_instances=1,
            max_instances=10,
            target_instances=5
        )
        
        scaler = AutoScaler(config)
        
        # Test scaling decision
        decision = scaler.make_scaling_decision(
            current_instances=3,
            cpu_usage=0.8,
            memory_usage=0.7
        )
        
        assert decision is not None
        assert hasattr(decision, 'action')


class TestMonitoringComponents:
    """Test monitoring components."""
    
    def test_metrics_collection(self):
        """Test metrics collection."""
        collector = MetricsCollector()
        
        # Record metrics
        collector.record_counter("requests_total", 1, {"endpoint": "/api"})
        collector.record_histogram("response_time", 0.5, {"endpoint": "/api"})
        collector.record_gauge("active_connections", 10)
        
        # Get metrics
        metrics = collector.get_metrics()
        assert len(metrics) > 0
        
        # Test Prometheus metrics
        prom_metrics = PrometheusMetrics()
        prom_metrics.record_counter("test_counter", 1)
        
        metrics_text = prom_metrics.get_metrics_text()
        assert "test_counter" in metrics_text
    
    def test_health_checking(self):
        """Test health checking."""
        checker = HealthChecker()
        
        # Add health check
        def test_check():
            return True, "OK"
        
        checker.add_check("test_service", test_check)
        
        # Run health checks
        health = checker.check_health()
        assert health is not None
        assert health.overall_status == "healthy"
    
    def test_recovery_management(self):
        """Test recovery management."""
        manager = RecoveryManager()
        
        # Add recovery rule
        rule = RecoveryRule(
            name="restart_service",
            condition="service_down",
            action="restart",
            max_attempts=3
        )
        
        manager.add_rule(rule)
        
        # Test recovery
        success = asyncio.run(manager.attempt_recovery("service_down"))
        assert success is True
    
    def test_alert_management(self):
        """Test alert management."""
        manager = AlertManager()
        
        # Add alert rule
        rule = AlertRule(
            name="high_cpu",
            condition="cpu_usage > 80",
            severity="warning"
        )
        
        manager.add_rule(rule)
        
        # Check alerts
        alerts = manager.check_alerts({"cpu_usage": 90})
        assert len(alerts) > 0
        assert alerts[0].rule_name == "high_cpu"
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        
        # Start monitoring
        monitor.start_monitoring("test_operation")
        
        # Simulate some work
        time.sleep(0.1)
        
        # Stop monitoring
        result = monitor.stop_monitoring("test_operation")
        assert result is not None
        assert result.duration > 0


class TestProcessingComponents:
    """Test data processing components."""
    
    def test_data_extraction(self):
        """Test data extraction."""
        # HTML extraction
        html_extractor = HTMLExtractor()
        html_data = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        
        results = asyncio.run(html_extractor.extract(html_data, {"title": "h1", "content": "p"}))
        assert len(results) > 0
        
        # JSON extraction
        json_extractor = JSONExtractor()
        json_data = '{"name": "John", "age": 30}'
        
        results = asyncio.run(json_extractor.extract(json_data, {"name": "name", "age": "age"}))
        assert len(results) > 0
        
        # XML extraction
        xml_extractor = XMLExtractor()
        xml_data = "<root><name>John</name><age>30</age></root>"
        
        results = asyncio.run(xml_extractor.extract(xml_data, {"name": "name", "age": "age"}))
        assert len(results) > 0
    
    def test_data_transformation(self):
        """Test data transformation."""
        # Data cleaning
        cleaner = DataCleaner()
        cleaned = cleaner.clean_text("  Hello   World  ", remove_whitespace=True)
        assert cleaned == "Hello World"
        
        # Data normalization
        normalizer = DataNormalizer()
        normalized = normalizer.normalize_text("Hello World", case="lower")
        assert normalized == "hello world"
        
        # Data enrichment
        enricher = DataEnricher()
        enriched = asyncio.run(enricher.enrich_with_sentiment("This is great!"))
        assert "sentiment" in enriched
    
    def test_data_validation(self):
        """Test data validation."""
        validator = DataValidator()
        
        # Test validation
        is_valid, errors = validator.validate({"name": "John", "age": 30}, {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True, "min": 0}
        })
        
        assert is_valid is True
        assert len(errors) == 0
        
        # Test schema validation
        schema_validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        
        is_valid, errors = schema_validator.validate({"name": "John", "age": 30}, schema)
        assert is_valid is True
    
    def test_data_storage(self):
        """Test data storage."""
        # File storage
        with tempfile.TemporaryDirectory() as temp_dir:
            file_storage = FileStorage(base_path=temp_dir)
            
            # Store data
            success = asyncio.run(file_storage.store("test.json", {"name": "John"}))
            assert success is True
            
            # Retrieve data
            data = asyncio.run(file_storage.retrieve("test.json"))
            assert data is not None
            assert data["name"] == "John"
        
        # Database storage (mock)
        db_storage = DatabaseStorage("sqlite:///:memory:")
        success = asyncio.run(db_storage.store("test_table", {"name": "John"}))
        assert success is True
    
    def test_ml_extraction(self):
        """Test ML-based extraction."""
        manager = MLExtractionManager()
        
        # Test extraction
        text = "Contact us at john@example.com or call (555) 123-4567"
        results = asyncio.run(manager.extract_data(text, "contact_info"))
        
        assert len(results) > 0
        assert any("john@example.com" in str(r.value) for r in results)
    
    def test_intelligent_validation(self):
        """Test intelligent validation."""
        validator = IntelligentValidator()
        
        # Add validation rule
        from spider.processors.intelligent_validator import ValidationRule, ValidationType
        rule = ValidationRule(
            name="email_rule",
            validation_type=ValidationType.FORMAT,
            rule="email"
        )
        validator.add_rule("email", rule)
        
        # Test validation
        report = asyncio.run(validator.validate_field("email", "test@example.com"))
        assert report.field_name == "email"
        assert report.value == "test@example.com"
    
    def test_transformation_pipeline(self):
        """Test transformation pipeline."""
        config = PipelineConfig(name="test_pipeline")
        pipeline = TransformationPipeline(config)
        
        # Add transformation step
        from spider.processors.transformation_pipeline import TransformationStep, TransformationType
        step = TransformationStep(
            name="clean_data",
            transformation_type=TransformationType.CLEAN,
            function=lambda x: x
        )
        pipeline.add_step(step)
        
        # Test pipeline execution
        data = [{"text": "  Hello World  "}]
        result = asyncio.run(pipeline.execute(data))
        
        assert result.success is True
        assert result.input_count == 1
        assert result.output_count == 1
    
    def test_realtime_processing(self):
        """Test real-time processing."""
        config = ProcessingConfig(mode="streaming")
        processor = StreamProcessor(config)
        
        # Add processor
        def simple_processor(data):
            return f"processed_{data}"
        
        processor.add_processor(simple_processor)
        
        # Test adding event
        success = processor.add_event("test_data", "test_1")
        assert success is True
        
        # Test getting status
        status = processor.get_status()
        assert status["status"] == "stopped"
        assert status["buffer_size"] == 1
    
    def test_quality_scoring(self):
        """Test data quality scoring."""
        scorer = DataQualityScorer()
        
        data = [
            {"name": "John", "email": "john@example.com", "age": 30},
            {"name": "Jane", "email": "jane@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 35}
        ]
        
        required_fields = ["name", "email", "age"]
        validation_rules = {"email": "email", "age": "number"}
        consistency_rules = {"name": ["case_consistent"]}
        unique_fields = ["email"]
        
        score = asyncio.run(scorer.calculate_quality_score(
            data, required_fields, validation_rules, consistency_rules, unique_fields
        ))
        
        assert score.total_score >= 0
        assert score.level in ["excellent", "good", "fair", "poor", "critical"]


class TestEnterpriseComponents:
    """Test enterprise components."""
    
    def test_multi_tenant(self):
        """Test multi-tenant functionality."""
        manager = TenantManager()
        
        # Create tenant
        tenant = manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.PROFESSIONAL
        )
        
        assert tenant.name == "Test Company"
        assert tenant.tier == TenantTier.PROFESSIONAL
        
        # Test resource limits
        can_use, error = manager.check_resource_limit(
            tenant.tenant_id, "scraping_jobs", 10
        )
        assert can_use is True
    
    def test_security_features(self):
        """Test security features."""
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
    
    def test_dashboard_functionality(self):
        """Test dashboard functionality."""
        manager = DashboardManager()
        
        # Create dashboard
        dashboard = manager.create_dashboard(
            name="Test Dashboard",
            dashboard_type="custom"
        )
        
        assert dashboard.name == "Test Dashboard"
        
        # Record metrics
        manager.record_metric("test_metric", 100)
        manager.record_metric("test_metric", 150)
        
        # Get dashboard data
        dashboard_data = manager.get_dashboard_data(dashboard.dashboard_id)
        assert dashboard_data["name"] == "Test Dashboard"


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    def test_complete_scraping_workflow(self):
        """Test complete scraping workflow."""
        # 1. Setup configuration
        config = Config()
        
        # 2. Initialize engine
        engine = SpiderEngine(config)
        
        # 3. Setup monitoring
        metrics = MetricsCollector()
        health = HealthChecker()
        
        # 4. Setup processing
        extractor = HTMLExtractor()
        cleaner = DataCleaner()
        validator = DataValidator()
        
        # 5. Setup storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(base_path=temp_dir)
            
            # 6. Simulate scraping workflow
            url = "https://example.com"
            
            # Record metrics
            metrics.record_counter("scraping_requests", 1)
            
            # Simulate data extraction
            html_data = "<html><body><h1>Title</h1><p>Content</p></body></html>"
            results = asyncio.run(extractor.extract(html_data, {"title": "h1", "content": "p"}))
            
            # Clean data
            cleaned_data = {}
            for result in results:
                cleaned_data[result.field] = cleaner.clean_text(str(result.value))
            
            # Validate data
            is_valid, errors = validator.validate(cleaned_data, {
                "title": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            })
            
            assert is_valid is True
            
            # Store data
            success = asyncio.run(storage.store("scraped_data.json", cleaned_data))
            assert success is True
            
            # Verify stored data
            stored_data = asyncio.run(storage.retrieve("scraped_data.json"))
            assert stored_data is not None
            assert "title" in stored_data
            assert "content" in stored_data
    
    def test_enterprise_workflow(self):
        """Test enterprise workflow with multi-tenancy and security."""
        # 1. Setup tenant
        tenant_manager = TenantManager()
        tenant = tenant_manager.create_tenant(
            name="Enterprise Corp",
            domain="enterprise.com",
            tier=TenantTier.ENTERPRISE
        )
        tenant.status = "active"
        
        # 2. Setup security
        security_config = SecurityConfig()
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
        
        # 5. Setup dashboard
        dashboard_manager = DashboardManager()
        dashboard = dashboard_manager.create_dashboard(
            name="Enterprise Dashboard",
            dashboard_type="overview",
            tenant_id=tenant.tenant_id
        )
        
        # 6. Record metrics
        dashboard_manager.record_metric("scraping_jobs", 5, {"tenant_id": tenant.tenant_id})
        
        # 7. Check resource usage
        can_use, error = tenant_manager.check_resource_limit(
            tenant.tenant_id, "scraping_jobs", 1
        )
        assert can_use is True
        
        # 8. Use resources
        success = tenant_manager.use_resource(tenant.tenant_id, "scraping_jobs", 1)
        assert success is True
        
        # 9. Verify everything is working
        assert session.tenant_id == tenant.tenant_id
        assert security_manager.verify_password(password, hashed_password) is True
        
        usage = tenant_manager.get_tenant_usage(tenant.tenant_id)
        assert usage["current_usage"]["scraping_jobs"] == 1


class TestPerformanceAndReliability:
    """Test performance and reliability."""
    
    def test_concurrent_operations(self):
        """Test concurrent operations."""
        async def concurrent_task(task_id):
            # Simulate some work
            await asyncio.sleep(0.01)
            return f"task_{task_id}_completed"
        
        # Run concurrent tasks
        tasks = [concurrent_task(i) for i in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        assert len(results) == 10
        assert all("completed" in result for result in results)
    
    def test_error_handling(self):
        """Test error handling and recovery."""
        # Test exception handling
        with pytest.raises(SpiderError):
            raise SpiderError("Test error")
        
        # Test recovery mechanisms
        recovery_manager = RecoveryManager()
        
        rule = RecoveryRule(
            name="test_recovery",
            condition="test_failure",
            action="retry",
            max_attempts=3
        )
        
        recovery_manager.add_rule(rule)
        
        # Test recovery
        success = asyncio.run(recovery_manager.attempt_recovery("test_failure"))
        assert success is True
    
    def test_memory_management(self):
        """Test memory management."""
        # Test cache memory limits
        cache = MemoryCache(max_size=100)
        
        # Add items until limit
        for i in range(150):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Check that old items were evicted
        assert cache.get("key_0") is None
        assert cache.get("key_149") is not None
    
    def test_data_persistence(self):
        """Test data persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(base_path=temp_dir)
            
            # Store data
            test_data = {"key": "value", "number": 42}
            success = asyncio.run(storage.store("test.json", test_data))
            assert success is True
            
            # Verify persistence
            stored_data = asyncio.run(storage.retrieve("test.json"))
            assert stored_data == test_data
            
            # Test file exists
            file_path = Path(temp_dir) / "test.json"
            assert file_path.exists()
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        config = Config()
        
        # Test valid configuration
        assert config.scraping is not None
        assert config.storage is not None
        assert config.monitoring is not None
        
        # Test configuration access
        assert hasattr(config.scraping, 'max_workers')
        assert hasattr(config.storage, 'type')
        assert hasattr(config.monitoring, 'enabled')


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        extractor = HTMLExtractor()
        
        # Test empty HTML
        results = asyncio.run(extractor.extract("", {"title": "h1"}))
        assert len(results) == 0
        
        # Test None data
        results = asyncio.run(extractor.extract(None, {"title": "h1"}))
        assert len(results) == 0
    
    def test_invalid_input_handling(self):
        """Test handling of invalid input."""
        validator = DataValidator()
        
        # Test invalid data type
        is_valid, errors = validator.validate("not_a_dict", {})
        assert is_valid is False
        assert len(errors) > 0
        
        # Test missing required fields
        is_valid, errors = validator.validate({}, {"name": {"required": True}})
        assert is_valid is False
        assert len(errors) > 0
    
    def test_resource_exhaustion(self):
        """Test resource exhaustion scenarios."""
        # Test cache size limits
        cache = MemoryCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
    
    def test_network_failure_simulation(self):
        """Test network failure simulation."""
        # Test proxy failure handling
        manager = ProxyManager()
        manager.add_proxy("http://invalid-proxy:8080")
        
        # Simulate proxy failure
        with patch.object(manager, '_test_proxy') as mock_test:
            mock_test.return_value = False
            
            # Should handle proxy failure gracefully
            proxy = manager.get_proxy()
            # Implementation should handle failures appropriately
    
    def test_concurrent_access(self):
        """Test concurrent access scenarios."""
        import threading
        import time
        
        # Test thread-safe operations
        cache = MemoryCache(max_size=100)
        results = []
        
        def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.set(key, value)
                results.append(cache.get(key))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 50
        assert all(result is not None for result in results)
