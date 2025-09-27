"""Tests for SPIDER core modules."""

import pytest
import tempfile
import os
from pathlib import Path

from spider.core.config import Config
from spider.core.exceptions import ConfigurationError, SpiderError
from spider.core.engine import EngineFactory, EngineType, ScrapingRequest, ScrapingResponse
from spider.core.logger import setup_logging, get_logger


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config()
        
        assert config.environment == "development"
        assert config.debug is False
        assert config.max_concurrent_requests == 16
        assert config.request_delay == 1.0
        assert config.request_timeout == 30
    
    def test_config_from_file(self):
        """Test configuration loading from file."""
        # Create temporary config file
        config_data = """
environment: production
debug: true
max_concurrent_requests: 32
request_delay: 0.5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            config_path = f.name
        
        try:
            config = Config.from_file(config_path)
            
            assert config.environment == "production"
            assert config.debug is True
            assert config.max_concurrent_requests == 32
            assert config.request_delay == 0.5
        finally:
            os.unlink(config_path)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid environment
        with pytest.raises(ValueError):
            Config(environment="invalid")
        
        # Test invalid log level
        with pytest.raises(ValueError):
            Config(monitoring__log_level="invalid")
    
    def test_config_to_file(self):
        """Test configuration saving to file."""
        config = Config(environment="test", debug=True)
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            config.to_file(config_path)
            
            # Load and verify
            loaded_config = Config.from_file(config_path)
            assert loaded_config.environment == "test"
            assert loaded_config.debug is True
        finally:
            os.unlink(config_path)
    
    def test_engine_config(self):
        """Test engine configuration retrieval."""
        config = Config()
        engine_config = config.get_engine_config("httpx")
        
        assert isinstance(engine_config, dict)
        
        # Test invalid engine
        with pytest.raises(ValueError):
            config.get_engine_config("invalid_engine")
    
    def test_environment_checks(self):
        """Test environment check methods."""
        prod_config = Config(environment="production")
        dev_config = Config(environment="development")
        
        assert prod_config.is_production() is True
        assert prod_config.is_development() is False
        assert dev_config.is_production() is False
        assert dev_config.is_development() is True


class TestEngineFactory:
    """Test engine factory."""
    
    def test_create_engine(self):
        """Test engine creation."""
        # Test HTTPX engine
        engine = EngineFactory.create_engine(EngineType.HTTPX, {})
        assert engine is not None
        assert engine.__class__.__name__ == "HTTPXEngine"
        
        # Test Scrapy engine
        engine = EngineFactory.create_engine(EngineType.SCRAPY, {})
        assert engine is not None
        assert engine.__class__.__name__ == "ScrapyEngine"
        
        # Test Playwright engine
        engine = EngineFactory.create_engine(EngineType.PLAYWRIGHT, {})
        assert engine is not None
        assert engine.__class__.__name__ == "PlaywrightEngine"
    
    def test_invalid_engine_type(self):
        """Test invalid engine type handling."""
        with pytest.raises(Exception):  # Should raise EngineError
            EngineFactory.create_engine("invalid", {})
    
    def test_get_available_engines(self):
        """Test getting available engine types."""
        engines = EngineFactory.get_available_engines()
        
        assert EngineType.HTTPX in engines
        assert EngineType.SCRAPY in engines
        assert EngineType.PLAYWRIGHT in engines


class TestScrapingRequest:
    """Test scraping request."""
    
    def test_request_creation(self):
        """Test request creation."""
        request = ScrapingRequest(url="https://example.com")
        
        assert request.url == "https://example.com"
        assert request.method == "GET"
        assert request.headers is None
        assert request.data is None
        assert request.params is None
        assert request.cookies is None
        assert request.proxy is None
        assert request.timeout is None
        assert request.retries == 3
        assert request.priority == 0
        assert request.metadata is None
    
    def test_request_with_options(self):
        """Test request with all options."""
        request = ScrapingRequest(
            url="https://example.com",
            method="POST",
            headers={"User-Agent": "Test"},
            data={"key": "value"},
            params={"param": "value"},
            cookies={"session": "abc123"},
            proxy="http://proxy:8080",
            timeout=30,
            retries=5,
            priority=1,
            metadata={"test": True}
        )
        
        assert request.url == "https://example.com"
        assert request.method == "POST"
        assert request.headers == {"User-Agent": "Test"}
        assert request.data == {"key": "value"}
        assert request.params == {"param": "value"}
        assert request.cookies == {"session": "abc123"}
        assert request.proxy == "http://proxy:8080"
        assert request.timeout == 30
        assert request.retries == 5
        assert request.priority == 1
        assert request.metadata == {"test": True}


class TestScrapingResponse:
    """Test scraping response."""
    
    def test_response_creation(self):
        """Test response creation."""
        response = ScrapingResponse(
            url="https://example.com",
            status_code=200,
            headers={"Content-Type": "text/html"},
            content=b"<html>Test</html>",
            text="<html>Test</html>",
            cookies={"session": "abc123"}
        )
        
        assert response.url == "https://example.com"
        assert response.status_code == 200
        assert response.headers == {"Content-Type": "text/html"}
        assert response.content == b"<html>Test</html>"
        assert response.text == "<html>Test</html>"
        assert response.cookies == {"session": "abc123"}
        assert response.metadata is None
        assert response.success is True
        assert response.error is None
    
    def test_response_with_error(self):
        """Test response with error."""
        response = ScrapingResponse(
            url="https://example.com",
            status_code=500,
            headers={},
            content=b"",
            text="",
            cookies={},
            success=False,
            error="Server error"
        )
        
        assert response.success is False
        assert response.error == "Server error"


class TestLogger:
    """Test logging functionality."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        # This should not raise an exception
        setup_logging(
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test.module")
        assert logger is not None
        assert logger.name == "test.module"


class TestExceptions:
    """Test custom exceptions."""
    
    def test_spider_error(self):
        """Test base SpiderError."""
        with pytest.raises(SpiderError):
            raise SpiderError("Test error")
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")
        
        # Should be instance of SpiderError
        try:
            raise ConfigurationError("Config error")
        except SpiderError:
            pass
        else:
            pytest.fail("ConfigurationError should inherit from SpiderError")
