"""Tests for SPIDER main application."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from spider.main import Spider
from spider.core.config import Config
from spider.core.engine import ScrapingRequest, ScrapingResponse
from spider.core.exceptions import SpiderError


class TestSpider:
    """Test main SPIDER application class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            environment="test",
            debug=True,
            max_concurrent_requests=4,
            request_delay=0.1,
            request_timeout=10
        )
    
    @pytest.fixture
    def spider(self, config):
        """Create SPIDER instance for testing."""
        return Spider(config)
    
    @pytest.mark.asyncio
    async def test_spider_initialization(self, spider):
        """Test SPIDER initialization."""
        assert spider.config is not None
        assert spider.engine is None
        assert spider.proxy_manager is None
        assert spider.captcha_manager is None
        assert spider.extractors == {}
        assert spider.transformers == []
        assert spider.storage is None
        assert spider._initialized is False
    
    @pytest.mark.asyncio
    async def test_spider_initialize(self, spider):
        """Test SPIDER initialization process."""
        # Mock the components
        with patch('spider.main.ProxyManager') as mock_proxy_manager, \
             patch('spider.main.CAPTCHAManager') as mock_captcha_manager, \
             patch('spider.main.HTMLExtractor') as mock_html_extractor, \
             patch('spider.main.JSONExtractor') as mock_json_extractor, \
             patch('spider.main.DataCleaner') as mock_cleaner, \
             patch('spider.main.DataNormalizer') as mock_normalizer, \
             patch('spider.main.FileStorage') as mock_storage:
            
            # Setup mocks
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            await spider.initialize()
            
            assert spider._initialized is True
            assert spider.proxy_manager is not None
            assert spider.captcha_manager is not None
            assert len(spider.extractors) == 2
            assert len(spider.transformers) == 2
            assert spider.storage is not None
    
    @pytest.mark.asyncio
    async def test_scrape_urls_success(self, spider):
        """Test successful URL scraping."""
        # Mock initialization
        spider._initialized = True
        spider.engine = AsyncMock()
        spider.proxy_manager = AsyncMock()
        spider.extractors = {'html': Mock()}
        spider.transformers = [Mock(), Mock()]
        
        # Mock engine response
        mock_response = ScrapingResponse(
            url="https://example.com",
            status_code=200,
            headers={"content-type": "text/html"},
            content=b"<html>Test</html>",
            text="<html>Test</html>",
            cookies={}
        )
        spider.engine.scrape.return_value = mock_response
        
        # Mock extractor
        spider.extractors['html'].extract.return_value = {"title": "Test Page"}
        
        # Mock transformers
        for transformer in spider.transformers:
            transformer.transform.return_value = {"title": "Test Page"}
        
        # Mock proxy manager
        spider.proxy_manager.get_proxy.return_value = None
        
        urls = ["https://example.com"]
        results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
        
        assert len(results) == 1
        assert results[0]['url'] == "https://example.com"
        assert results[0]['success'] is True
        assert results[0]['status_code'] == 200
        assert 'extracted_data' in results[0]
    
    @pytest.mark.asyncio
    async def test_scrape_urls_failure(self, spider):
        """Test URL scraping with failures."""
        # Mock initialization
        spider._initialized = True
        spider.engine = AsyncMock()
        spider.proxy_manager = AsyncMock()
        
        # Mock engine response with failure
        mock_response = ScrapingResponse(
            url="https://example.com",
            status_code=500,
            headers={},
            content=b"",
            text="",
            cookies={},
            success=False,
            error="Server error"
        )
        spider.engine.scrape.return_value = mock_response
        
        # Mock proxy manager
        spider.proxy_manager.get_proxy.return_value = None
        
        urls = ["https://example.com"]
        results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=False)
        
        assert len(results) == 1
        assert results[0]['url'] == "https://example.com"
        assert results[0]['success'] is False
        assert results[0]['error'] == "Server error"
    
    @pytest.mark.asyncio
    async def test_scrape_urls_with_proxy(self, spider):
        """Test URL scraping with proxy."""
        # Mock initialization
        spider._initialized = True
        spider.engine = AsyncMock()
        spider.proxy_manager = AsyncMock()
        
        # Mock proxy
        mock_proxy = Mock()
        mock_proxy.url = "http://proxy:8080"
        spider.proxy_manager.get_proxy.return_value = mock_proxy
        
        # Mock engine response
        mock_response = ScrapingResponse(
            url="https://example.com",
            status_code=200,
            headers={},
            content=b"<html>Test</html>",
            text="<html>Test</html>",
            cookies={}
        )
        spider.engine.scrape.return_value = mock_response
        
        urls = ["https://example.com"]
        results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=False)
        
        # Verify proxy was used
        spider.engine.scrape.assert_called_once()
        call_args = spider.engine.scrape.call_args[0][0]
        assert call_args.proxy == "http://proxy:8080"
    
    @pytest.mark.asyncio
    async def test_scrape_urls_not_initialized(self, spider):
        """Test URL scraping when not initialized."""
        with pytest.raises(AttributeError):
            await spider.scrape_urls(["https://example.com"])
    
    @pytest.mark.asyncio
    async def test_extract_data_html(self, spider):
        """Test HTML data extraction."""
        spider.extractors = {
            'html': Mock(),
            'json': Mock()
        }
        spider.transformers = [Mock(), Mock()]
        
        # Mock HTML extractor
        spider.extractors['html'].extract.return_value = {"title": "Test Page"}
        
        # Mock transformers
        for transformer in spider.transformers:
            transformer.transform.return_value = {"title": "Test Page"}
        
        content = "<html><title>Test Page</title></html>"
        headers = {"content-type": "text/html"}
        
        result = await spider._extract_data(content, headers)
        
        assert result["title"] == "Test Page"
        spider.extractors['html'].extract.assert_called_once_with(content)
    
    @pytest.mark.asyncio
    async def test_extract_data_json(self, spider):
        """Test JSON data extraction."""
        spider.extractors = {
            'html': Mock(),
            'json': Mock()
        }
        spider.transformers = [Mock(), Mock()]
        
        # Mock JSON extractor
        spider.extractors['json'].extract.return_value = {"name": "Test"}
        
        # Mock transformers
        for transformer in spider.transformers:
            transformer.transform.return_value = {"name": "Test"}
        
        content = '{"name": "Test"}'
        headers = {"content-type": "application/json"}
        
        result = await spider._extract_data(content, headers)
        
        assert result["name"] == "Test"
        spider.extractors['json'].extract.assert_called_once_with(content)
    
    @pytest.mark.asyncio
    async def test_extract_data_default_html(self, spider):
        """Test default HTML extraction for unknown content type."""
        spider.extractors = {
            'html': Mock(),
            'json': Mock()
        }
        spider.transformers = [Mock(), Mock()]
        
        # Mock HTML extractor
        spider.extractors['html'].extract.return_value = {"title": "Test Page"}
        
        # Mock transformers
        for transformer in spider.transformers:
            transformer.transform.return_value = {"title": "Test Page"}
        
        content = "<html><title>Test Page</title></html>"
        headers = {"content-type": "unknown/type"}
        
        result = await spider._extract_data(content, headers)
        
        assert result["title"] == "Test Page"
        spider.extractors['html'].extract.assert_called_once_with(content)
    
    @pytest.mark.asyncio
    async def test_extract_data_error(self, spider):
        """Test data extraction with error."""
        spider.extractors = {
            'html': Mock(),
            'json': Mock()
        }
        spider.transformers = [Mock(), Mock()]
        
        # Mock extractor to raise exception
        spider.extractors['html'].extract.side_effect = Exception("Extraction failed")
        
        content = "<html>Test</html>"
        headers = {"content-type": "text/html"}
        
        result = await spider._extract_data(content, headers)
        
        # Should return empty dict on error
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_save_results_with_storage(self, spider):
        """Test saving results with storage handler."""
        spider.storage = AsyncMock()
        
        results = [{"url": "https://example.com", "success": True}]
        output_path = "test_output.json"
        
        await spider.save_results(results, output_path)
        
        spider.storage.save.assert_called_once_with(results, output_path)
    
    @pytest.mark.asyncio
    async def test_save_results_without_storage(self, spider):
        """Test saving results without storage handler."""
        spider.storage = None
        
        results = [{"url": "https://example.com", "success": True}]
        output_path = "test_output.json"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output.json")
            
            await spider.save_results(results, output_path)
            
            # Check if file was created
            assert os.path.exists(output_path)
            
            # Check file content
            import json
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == results
    
    @pytest.mark.asyncio
    async def test_cleanup(self, spider):
        """Test SPIDER cleanup."""
        spider.engine = AsyncMock()
        spider.proxy_manager = AsyncMock()
        
        await spider.cleanup()
        
        spider.engine.cleanup.assert_called_once()


class TestSpiderIntegration:
    """Test SPIDER integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete scraping workflow."""
        config = Config(
            environment="test",
            debug=True,
            max_concurrent_requests=2,
            request_delay=0.1
        )
        
        spider = Spider(config)
        
        # Mock all dependencies
        with patch('spider.main.ProxyManager') as mock_proxy_manager, \
             patch('spider.main.CAPTCHAManager') as mock_captcha_manager, \
             patch('spider.main.HTMLExtractor') as mock_html_extractor, \
             patch('spider.main.JSONExtractor') as mock_json_extractor, \
             patch('spider.main.DataCleaner') as mock_cleaner, \
             patch('spider.main.DataNormalizer') as mock_normalizer, \
             patch('spider.main.FileStorage') as mock_storage, \
             patch('spider.main.EngineFactory') as mock_engine_factory:
            
            # Setup mocks
            mock_engine = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://example.com",
                status_code=200,
                headers={"content-type": "text/html"},
                content=b"<html><title>Test</title></html>",
                text="<html><title>Test</title></html>",
                cookies={}
            )
            mock_engine.scrape.return_value = mock_response
            
            # Mock extractor
            mock_html_extractor.return_value.extract.return_value = {"title": "Test"}
            
            # Mock transformers
            mock_cleaner.return_value.transform.return_value = {"title": "Test"}
            mock_normalizer.return_value.transform.return_value = {"title": "Test"}
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://example.com", "https://test.com"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify results
            assert len(results) == 2
            for result in results:
                assert result['success'] is True
                assert 'extracted_data' in result
            
            # Verify engine was called
            assert mock_engine.scrape.call_count == 2
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in scraping workflow."""
        config = Config(
            environment="test",
            debug=True,
            max_concurrent_requests=1,
            request_delay=0.1
        )
        
        spider = Spider(config)
        
        # Mock dependencies
        with patch('spider.main.ProxyManager') as mock_proxy_manager, \
             patch('spider.main.CAPTCHAManager') as mock_captcha_manager, \
             patch('spider.main.HTMLExtractor') as mock_html_extractor, \
             patch('spider.main.JSONExtractor') as mock_json_extractor, \
             patch('spider.main.DataCleaner') as mock_cleaner, \
             patch('spider.main.DataNormalizer') as mock_normalizer, \
             patch('spider.main.FileStorage') as mock_storage, \
             patch('spider.main.EngineFactory') as mock_engine_factory:
            
            # Setup mocks
            mock_engine = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine to raise exception
            mock_engine.scrape.side_effect = Exception("Engine error")
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://example.com"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=False)
            
            # Verify error handling
            assert len(results) == 1
            assert results[0]['success'] is False
            assert 'error' in results[0]
            assert "Engine error" in results[0]['error']
            
            # Cleanup
            await spider.cleanup()


# Performance tests
class TestSpiderPerformance:
    """Test SPIDER performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping(self):
        """Test concurrent URL scraping."""
        config = Config(
            environment="test",
            debug=True,
            max_concurrent_requests=5,
            request_delay=0.01
        )
        
        spider = Spider(config)
        
        # Mock dependencies
        with patch('spider.main.ProxyManager') as mock_proxy_manager, \
             patch('spider.main.CAPTCHAManager') as mock_captcha_manager, \
             patch('spider.main.HTMLExtractor') as mock_html_extractor, \
             patch('spider.main.JSONExtractor') as mock_json_extractor, \
             patch('spider.main.DataCleaner') as mock_cleaner, \
             patch('spider.main.DataNormalizer') as mock_normalizer, \
             patch('spider.main.FileStorage') as mock_storage, \
             patch('spider.main.EngineFactory') as mock_engine_factory:
            
            # Setup mocks
            mock_engine = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://example.com",
                status_code=200,
                headers={},
                content=b"<html>Test</html>",
                text="<html>Test</html>",
                cookies={}
            )
            mock_engine.scrape.return_value = mock_response
            
            # Initialize and run
            await spider.initialize()
            
            # Test with multiple URLs
            urls = [f"https://example{i}.com" for i in range(10)]
            start_time = asyncio.get_event_loop().time()
            
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=False)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Verify results
            assert len(results) == 10
            assert all(result['success'] for result in results)
            
            # Verify concurrency (should be faster than sequential)
            # With 5 concurrent requests and 10 URLs, should take less than 2 seconds
            assert duration < 2.0
            
            # Cleanup
            await spider.cleanup()
