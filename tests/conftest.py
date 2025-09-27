"""Pytest configuration and fixtures for SPIDER tests."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from spider.core.config import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        environment="test",
        debug=True,
        max_concurrent_requests=4,
        request_delay=0.1,
        request_timeout=10,
        database__url="sqlite:///:memory:",
        redis__url="redis://localhost:6379",
        proxy__enabled=False,
        captcha__enabled=False,
        monitoring__enabled=False
    )


@pytest.fixture
def production_config():
    """Create production configuration."""
    return Config(
        environment="production",
        debug=False,
        max_concurrent_requests=16,
        request_delay=1.0,
        request_timeout=30,
        database__url="postgresql://user:pass@localhost/spider",
        redis__url="redis://localhost:6379",
        proxy__enabled=True,
        captcha__enabled=True,
        monitoring__enabled=True
    )


@pytest.fixture
def mock_engine():
    """Create mock engine for testing."""
    engine = AsyncMock()
    engine.initialize = AsyncMock()
    engine.cleanup = AsyncMock()
    return engine


@pytest.fixture
def mock_proxy_manager():
    """Create mock proxy manager for testing."""
    manager = AsyncMock()
    manager.initialize = AsyncMock()
    manager.get_proxy = AsyncMock(return_value=None)
    manager.report_proxy_result = AsyncMock()
    return manager


@pytest.fixture
def mock_captcha_manager():
    """Create mock CAPTCHA manager for testing."""
    manager = Mock()
    manager.solve_captcha = AsyncMock(return_value="test_solution")
    return manager


@pytest.fixture
def mock_extractor():
    """Create mock extractor for testing."""
    extractor = Mock()
    extractor.extract = Mock(return_value={"title": "Test Page"})
    return extractor


@pytest.fixture
def mock_transformer():
    """Create mock transformer for testing."""
    transformer = Mock()
    transformer.transform = Mock(side_effect=lambda x: x)
    return transformer


@pytest.fixture
def mock_storage():
    """Create mock storage for testing."""
    storage = AsyncMock()
    storage.save = AsyncMock()
    storage.load = AsyncMock(return_value=[])
    storage.exists = AsyncMock(return_value=False)
    return storage


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing."""
    return """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>Test paragraph</p>
            <a href="/link1">Link 1</a>
            <a href="/link2">Link 2</a>
            <img src="/image1.jpg" alt="Image 1">
        </body>
    </html>
    """


@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return {
        "id": 1,
        "name": "Test Item",
        "description": "Test description",
        "price": 19.99,
        "status": "active",
        "tags": ["test", "example"]
    }


@pytest.fixture
def sample_xml_content():
    """Sample XML content for testing."""
    return """
    <?xml version="1.0" encoding="UTF-8"?>
    <root>
        <item id="1">
            <name>Test Item</name>
            <price>19.99</price>
        </item>
        <item id="2">
            <name>Another Item</name>
            <price>29.99</price>
        </item>
    </root>
    """


@pytest.fixture
def sample_scraping_request():
    """Sample scraping request for testing."""
    from spider.core.engine import ScrapingRequest
    
    return ScrapingRequest(
        url="https://example.com",
        method="GET",
        headers={"User-Agent": "SPIDER/1.0"},
        timeout=30,
        retries=3
    )


@pytest.fixture
def sample_scraping_response():
    """Sample scraping response for testing."""
    from spider.core.engine import ScrapingResponse
    
    return ScrapingResponse(
        url="https://example.com",
        status_code=200,
        headers={"content-type": "text/html"},
        content=b"<html>Test</html>",
        text="<html>Test</html>",
        cookies={"session": "abc123"}
    )


@pytest.fixture
def sample_proxy_info():
    """Sample proxy info for testing."""
    from spider.infrastructure.proxy import ProxyInfo, ProxyStatus
    
    return ProxyInfo(
        host="proxy.example.com",
        port=8080,
        username="user",
        password="pass",
        protocol="http",
        country="US",
        status=ProxyStatus.HEALTHY,
        success_rate=0.9
    )


@pytest.fixture
def sample_captcha_task():
    """Sample CAPTCHA task for testing."""
    from spider.infrastructure.captcha import CAPTCHATask, CAPTCHAType
    
    return CAPTCHATask(
        task_id="task123",
        captcha_type=CAPTCHAType.IMAGE,
        image_data=b"fake_image_data"
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "proxy: marks tests that require proxy services"
    )
    config.addinivalue_line(
        "markers", "captcha: marks tests that require CAPTCHA services"
    )
    config.addinivalue_line(
        "markers", "aws: marks tests that require AWS services"
    )
    config.addinivalue_line(
        "markers", "apify: marks tests that require Apify services"
    )
    config.addinivalue_line(
        "markers", "docker: marks tests that require Docker"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Add markers based on test names
    for item in items:
        if "test_integration" in item.name:
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in item.name:
            item.add_marker(pytest.mark.e2e)
        elif "test_performance" in item.name:
            item.add_marker(pytest.mark.slow)
        elif "test_proxy" in item.name:
            item.add_marker(pytest.mark.proxy)
        elif "test_captcha" in item.name:
            item.add_marker(pytest.mark.captcha)
        elif "test_aws" in item.name:
            item.add_marker(pytest.mark.aws)
        elif "test_apify" in item.name:
            item.add_marker(pytest.mark.apify)
        elif "test_docker" in item.name:
            item.add_marker(pytest.mark.docker)
        elif "test_network" in item.name:
            item.add_marker(pytest.mark.network)
        else:
            item.add_marker(pytest.mark.unit)


# Async test utilities
@pytest.fixture
def async_test():
    """Decorator for async tests."""
    def decorator(func):
        return pytest.mark.asyncio(func)
    return decorator


# Test data generators
@pytest.fixture
def url_generator():
    """Generate test URLs."""
    def _generate_urls(count=10, domain="example.com"):
        return [f"https://{domain}/page{i}" for i in range(count)]
    return _generate_urls


@pytest.fixture
def data_generator():
    """Generate test data."""
    def _generate_data(count=10):
        return [
            {
                "id": i,
                "name": f"Item {i}",
                "value": i * 10,
                "active": i % 2 == 0
            }
            for i in range(count)
        ]
    return _generate_data


# Mock external services
@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock()
    redis.expire = AsyncMock()
    return redis


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Cleanup utilities
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test."""
    yield
    # Cleanup logic can be added here if needed
    pass
