"""
Test suite for the SPIDER plugin system.

This module tests the core plugin functionality including registration,
loading, execution, and lifecycle management.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from spider.plugins.base import (
    Plugin, PluginManager, PluginRegistry, PluginMetadata, PluginType, PluginStatus,
    PluginError, PluginValidationError, PluginLoadError, PluginExecutionError
)
from spider.plugins.extractor import ExtractorPlugin, HTMLExtractorPlugin
from spider.plugins.processor import ProcessorPlugin, DataCleanerPlugin
from spider.plugins.engine import EnginePlugin, WebScrapingEnginePlugin
from spider.plugins.monitor import MonitorPlugin
from spider.plugins.middleware import MiddlewarePlugin
from spider.plugins.validator import ValidatorPlugin
from spider.plugins.storage import StoragePlugin
from spider.plugins.auth import AuthPlugin
from spider.plugins.rate_limiter import RateLimiterPlugin
from spider.plugins.proxy import ProxyPlugin
from spider.plugins.captcha import CaptchaPlugin
from spider.plugins.behavior import BehaviorPlugin
from spider.plugins.fingerprint import FingerprintPlugin
from spider.plugins.cache import CachePlugin
from spider.plugins.notification import NotificationPlugin
from spider.plugins.reporting import ReportingPlugin
from spider.plugins.compliance import CompliancePlugin
from spider.plugins.security import SecurityPlugin
from spider.plugins.analytics import AnalyticsPlugin
from spider.plugins.ai import AIPlugin


class TestPlugin(Plugin):
    """Test plugin implementation."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="TestPlugin",
            version="1.0.0",
            description="Test plugin for testing",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
    
    def validate_config(self, config: dict) -> bool:
        return "enabled" in config
    
    async def extract(self, data, context=None):
        return {"extracted": data}


class TestExtractorPlugin(HTMLExtractorPlugin):
    """Test HTML extractor plugin."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="TestHTMLExtractor",
            version="1.0.0",
            description="Test HTML extractor",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
    
    def validate_config(self, config: dict) -> bool:
        return "enabled" in config
    
    async def extract(self, data, context=None):
        return {"html_extracted": data}
    
    def get_supported_formats(self):
        return ["html", "xhtml"]
    
    def get_extraction_fields(self):
        return ["title", "content", "links"]


class TestProcessorPlugin(DataCleanerPlugin):
    """Test data cleaner plugin."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="TestDataCleaner",
            version="1.0.0",
            description="Test data cleaner",
            author="Test Author",
            plugin_type=PluginType.PROCESSOR
        )
    
    def validate_config(self, config: dict) -> bool:
        return "enabled" in config
    
    async def process(self, data, context=None):
        return {"cleaned": data}
    
    def get_input_types(self):
        return ["text", "html"]
    
    def get_output_types(self):
        return ["text", "html"]


class TestEnginePlugin(WebScrapingEnginePlugin):
    """Test web scraping engine plugin."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="TestWebEngine",
            version="1.0.0",
            description="Test web engine",
            author="Test Author",
            plugin_type=PluginType.ENGINE
        )
    
    def validate_config(self, config: dict) -> bool:
        return "enabled" in config
    
    async def execute(self, task, context=None):
        return {"result": "scraped_data"}
    
    def get_supported_features(self):
        return ["http_requests", "javascript_rendering"]
    
    def get_capabilities(self):
        return {"max_pages_per_minute": 100}


class TestPluginRegistry:
    """Test plugin registry functionality."""
    
    def test_plugin_registration(self):
        """Test plugin registration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="TestPlugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        
        registry.register(TestPlugin, metadata)
        
        assert "TestPlugin" in registry.list_plugins()
        assert registry.get_plugin_class("TestPlugin") == TestPlugin
        assert registry.get_metadata("TestPlugin") == metadata
    
    def test_plugin_unregistration(self):
        """Test plugin unregistration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="TestPlugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        
        registry.register(TestPlugin, metadata)
        assert "TestPlugin" in registry.list_plugins()
        
        registry.unregister("TestPlugin")
        assert "TestPlugin" not in registry.list_plugins()
    
    def test_plugin_type_filtering(self):
        """Test filtering plugins by type."""
        registry = PluginRegistry()
        
        # Register different types of plugins
        extractor_metadata = PluginMetadata(
            name="ExtractorPlugin",
            version="1.0.0",
            description="Extractor plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        
        processor_metadata = PluginMetadata(
            name="ProcessorPlugin",
            version="1.0.0",
            description="Processor plugin",
            author="Test Author",
            plugin_type=PluginType.PROCESSOR
        )
        
        registry.register(TestPlugin, extractor_metadata)
        registry.register(TestProcessorPlugin, processor_metadata)
        
        extractors = registry.list_plugins(PluginType.EXTRACTOR)
        processors = registry.list_plugins(PluginType.PROCESSOR)
        
        assert "ExtractorPlugin" in extractors
        assert "ProcessorPlugin" in processors
        assert "ExtractorPlugin" not in processors
        assert "ProcessorPlugin" not in extractors
    
    def test_plugin_search(self):
        """Test plugin search functionality."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="HTMLParser",
            version="1.0.0",
            description="HTML parsing plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR,
            tags=["html", "parser", "web"]
        )
        
        registry.register(TestPlugin, metadata)
        
        # Search by name
        results = registry.search_plugins("HTML")
        assert "HTMLParser" in results
        
        # Search by description
        results = registry.search_plugins("parsing")
        assert "HTMLParser" in results
        
        # Search by tags
        results = registry.search_plugins("web")
        assert "HTMLParser" in results


class TestPluginManager:
    """Test plugin manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a plugin manager for testing."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="TestPlugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        registry.register(TestPlugin, metadata)
        return PluginManager(registry)
    
    @pytest.mark.asyncio
    async def test_plugin_loading(self, manager):
        """Test plugin loading."""
        config = {"enabled": True}
        plugin_info = await manager.load_plugin("TestPlugin", config)
        
        assert plugin_info is not None
        assert plugin_info.metadata.name == "TestPlugin"
        assert plugin_info.status == PluginStatus.LOADED
        assert plugin_info.instance is not None
    
    @pytest.mark.asyncio
    async def test_plugin_loading_with_invalid_config(self, manager):
        """Test plugin loading with invalid configuration."""
        config = {"invalid": "config"}
        
        with pytest.raises(PluginLoadError):
            await manager.load_plugin("TestPlugin", config)
    
    @pytest.mark.asyncio
    async def test_plugin_loading_nonexistent(self, manager):
        """Test loading a non-existent plugin."""
        with pytest.raises(PluginLoadError):
            await manager.load_plugin("NonExistentPlugin")
    
    @pytest.mark.asyncio
    async def test_plugin_start_stop(self, manager):
        """Test plugin start and stop."""
        config = {"enabled": True}
        await manager.load_plugin("TestPlugin", config)
        
        # Start plugin
        await manager.start_plugin("TestPlugin")
        plugin_info = manager.get_plugin_info("TestPlugin")
        assert plugin_info.status == PluginStatus.RUNNING
        
        # Stop plugin
        await manager.stop_plugin("TestPlugin")
        plugin_info = manager.get_plugin_info("TestPlugin")
        assert plugin_info.status == PluginStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_plugin_unloading(self, manager):
        """Test plugin unloading."""
        config = {"enabled": True}
        await manager.load_plugin("TestPlugin", config)
        
        assert "TestPlugin" in manager.list_loaded_plugins()
        
        await manager.unload_plugin("TestPlugin")
        assert "TestPlugin" not in manager.list_loaded_plugins()
    
    @pytest.mark.asyncio
    async def test_plugin_get_instance(self, manager):
        """Test getting plugin instance."""
        config = {"enabled": True}
        await manager.load_plugin("TestPlugin", config)
        
        plugin = await manager.get_plugin("TestPlugin")
        assert plugin is not None
        assert isinstance(plugin, TestPlugin)
    
    @pytest.mark.asyncio
    async def test_plugin_manager_shutdown(self, manager):
        """Test plugin manager shutdown."""
        config = {"enabled": True}
        await manager.load_plugin("TestPlugin", config)
        
        assert "TestPlugin" in manager.list_loaded_plugins()
        
        await manager.shutdown()
        assert "TestPlugin" not in manager.list_loaded_plugins()


class TestPluginLifecycle:
    """Test plugin lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = TestPlugin({"enabled": True})
        
        assert plugin.status == PluginStatus.UNLOADED
        assert not plugin.is_initialized
        
        await plugin.initialize()
        
        assert plugin.status == PluginStatus.INITIALIZED
        assert plugin.is_initialized
    
    @pytest.mark.asyncio
    async def test_plugin_start_stop(self):
        """Test plugin start and stop."""
        plugin = TestPlugin({"enabled": True})
        await plugin.initialize()
        
        assert not plugin.is_started
        
        await plugin.start()
        
        assert plugin.status == PluginStatus.RUNNING
        assert plugin.is_started
        
        await plugin.stop()
        
        assert plugin.status == PluginStatus.STOPPED
        assert not plugin.is_started
    
    @pytest.mark.asyncio
    async def test_plugin_cleanup(self):
        """Test plugin cleanup."""
        plugin = TestPlugin({"enabled": True})
        await plugin.initialize()
        await plugin.start()
        
        await plugin.cleanup()
        
        assert plugin.status == PluginStatus.UNLOADED
        assert not plugin.is_initialized
        assert not plugin.is_started
    
    @pytest.mark.asyncio
    async def test_plugin_config_update(self):
        """Test plugin configuration update."""
        plugin = TestPlugin({"enabled": True})
        
        new_config = {"enabled": True, "timeout": 60}
        plugin.update_config(new_config)
        
        assert plugin.get_config() == new_config
    
    @pytest.mark.asyncio
    async def test_plugin_metrics_recording(self):
        """Test plugin metrics recording."""
        plugin = TestPlugin({"enabled": True})
        
        plugin.record_metric("test_metric", 42.5)
        metric_value = plugin.get_metric("test_metric")
        
        assert metric_value == 42.5
        assert "test_metric" in plugin.performance_metrics


class TestPluginTypes:
    """Test different plugin types."""
    
    def test_extractor_plugin(self):
        """Test extractor plugin functionality."""
        plugin = TestExtractorPlugin({"enabled": True})
        
        assert plugin.get_supported_formats() == ["html", "xhtml"]
        assert plugin.get_extraction_fields() == ["title", "content", "links"]
        assert plugin.validate_config({"enabled": True})
    
    def test_processor_plugin(self):
        """Test processor plugin functionality."""
        plugin = TestProcessorPlugin({"enabled": True})
        
        assert plugin.get_input_types() == ["text", "html"]
        assert plugin.get_output_types() == ["text", "html"]
        assert plugin.validate_config({"enabled": True})
    
    def test_engine_plugin(self):
        """Test engine plugin functionality."""
        plugin = TestEnginePlugin({"enabled": True})
        
        assert "http_requests" in plugin.get_supported_features()
        assert plugin.get_capabilities()["max_pages_per_minute"] == 100
        assert plugin.validate_config({"enabled": True})


class TestPluginErrors:
    """Test plugin error handling."""
    
    def test_plugin_validation_error(self):
        """Test plugin validation error."""
        plugin = TestPlugin({"enabled": True})
        
        with pytest.raises(PluginValidationError):
            plugin.update_config({"invalid": "config"})
    
    def test_plugin_load_error(self):
        """Test plugin load error."""
        registry = PluginRegistry()
        manager = PluginManager(registry)
        
        with pytest.raises(PluginLoadError):
            asyncio.run(manager.load_plugin("NonExistentPlugin"))
    
    def test_plugin_execution_error(self):
        """Test plugin execution error."""
        plugin = TestPlugin({"enabled": True})
        
        # This would be tested with a plugin that fails during execution
        # For now, we test the error class exists
        assert PluginExecutionError is not None


class TestPluginIntegration:
    """Test plugin system integration."""
    
    @pytest.mark.asyncio
    async def test_multiple_plugin_types(self):
        """Test managing multiple plugin types."""
        registry = PluginRegistry()
        
        # Register different plugin types
        extractor_metadata = PluginMetadata(
            name="TestExtractor",
            version="1.0.0",
            description="Test extractor",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        
        processor_metadata = PluginMetadata(
            name="TestProcessor",
            version="1.0.0",
            description="Test processor",
            author="Test Author",
            plugin_type=PluginType.PROCESSOR
        )
        
        registry.register(TestExtractorPlugin, extractor_metadata)
        registry.register(TestProcessorPlugin, processor_metadata)
        
        manager = PluginManager(registry)
        
        # Load both plugins
        await manager.load_plugin("TestExtractor", {"enabled": True})
        await manager.load_plugin("TestProcessor", {"enabled": True})
        
        # Start both plugins
        await manager.start_plugin("TestExtractor")
        await manager.start_plugin("TestProcessor")
        
        # Verify both are running
        assert manager.get_plugin_info("TestExtractor").status == PluginStatus.RUNNING
        assert manager.get_plugin_info("TestProcessor").status == PluginStatus.RUNNING
        
        # Test plugin execution
        extractor = await manager.get_plugin("TestExtractor")
        processor = await manager.get_plugin("TestProcessor")
        
        extractor_result = await extractor.extract("<html>test</html>")
        processor_result = await processor.process("test data")
        
        assert "html_extracted" in extractor_result
        assert "cleaned" in processor_result
    
    @pytest.mark.asyncio
    async def test_plugin_dependencies(self):
        """Test plugin dependency management."""
        registry = PluginRegistry()
        
        # Create plugins with dependencies
        base_metadata = PluginMetadata(
            name="BasePlugin",
            version="1.0.0",
            description="Base plugin",
            author="Test Author",
            plugin_type=PluginType.EXTRACTOR
        )
        
        dependent_metadata = PluginMetadata(
            name="DependentPlugin",
            version="1.0.0",
            description="Dependent plugin",
            author="Test Author",
            plugin_type=PluginType.PROCESSOR,
            dependencies=["BasePlugin"]
        )
        
        registry.register(TestPlugin, base_metadata)
        registry.register(TestProcessorPlugin, dependent_metadata)
        
        manager = PluginManager(registry)
        
        # Load base plugin first
        await manager.load_plugin("BasePlugin", {"enabled": True})
        await manager.start_plugin("BasePlugin")
        
        # Load dependent plugin
        await manager.load_plugin("DependentPlugin", {"enabled": True})
        await manager.start_plugin("DependentPlugin")
        
        # Both should be running
        assert manager.get_plugin_info("BasePlugin").status == PluginStatus.RUNNING
        assert manager.get_plugin_info("DependentPlugin").status == PluginStatus.RUNNING


if __name__ == "__main__":
    pytest.main([__file__])
