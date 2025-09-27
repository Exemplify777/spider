"""End-to-end tests for SPIDER framework."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from spider.main import Spider
from spider.core.config import Config
from spider.core.engine import ScrapingRequest, ScrapingResponse


@pytest.mark.e2e
class TestSpiderE2E:
    """End-to-end tests for SPIDER framework."""
    
    @pytest.fixture
    def e2e_config(self):
        """Create E2E test configuration."""
        return Config(
            environment="test",
            debug=True,
            max_concurrent_requests=2,
            request_delay=0.1,
            request_timeout=10,
            database__url="sqlite:///:memory:",
            redis__url="redis://localhost:6379",
            proxy__enabled=False,
            captcha__enabled=False,
            monitoring__enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self, e2e_config):
        """Test complete scraping workflow from start to finish."""
        spider = Spider(e2e_config)
        
        # Mock all external dependencies
        with patch('spider.main.ProxyManager') as mock_proxy_manager, \
             patch('spider.main.CAPTCHAManager') as mock_captcha_manager, \
             patch('spider.main.HTMLExtractor') as mock_html_extractor, \
             patch('spider.main.JSONExtractor') as mock_json_extractor, \
             patch('spider.main.DataCleaner') as mock_cleaner, \
             patch('spider.main.DataNormalizer') as mock_normalizer, \
             patch('spider.main.FileStorage') as mock_storage, \
             patch('spider.main.EngineFactory') as mock_engine_factory:
            
            # Setup mocks
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine responses
            mock_responses = [
                ScrapingResponse(
                    url="https://httpbin.org/html",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    content=b"<html><title>Test Page</title></html>",
                    text="<html><title>Test Page</title></html>",
                    cookies={}
                ),
                ScrapingResponse(
                    url="https://httpbin.org/json",
                    status_code=200,
                    headers={"content-type": "application/json"},
                    content=b'{"name": "Test", "value": 123}',
                    text='{"name": "Test", "value": 123}',
                    cookies={}
                )
            ]
            mock_engine.scrape.side_effect = mock_responses
            
            # Mock extractors
            mock_html_extractor.return_value.extract.return_value = {"title": "Test Page"}
            mock_json_extractor.return_value.extract.return_value = {"name": "Test", "value": 123}
            
            # Mock transformers
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html", "https://httpbin.org/json"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify results
            assert len(results) == 2
            assert all(result['success'] for result in results)
            assert all('extracted_data' in result for result in results)
            
            # Verify engine was called correctly
            assert mock_engine.scrape.call_count == 2
            
            # Test saving results
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "results.json")
                await spider.save_results(results, output_path)
                
                # Verify file was created
                assert os.path.exists(output_path)
                
                # Verify file content
                import json
                with open(output_path, 'r') as f:
                    saved_data = json.load(f)
                
                assert len(saved_data) == 2
                assert all(item['success'] for item in saved_data)
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, e2e_config):
        """Test error handling in complete workflow."""
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine to return mixed results
            mock_responses = [
                ScrapingResponse(
                    url="https://httpbin.org/html",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    content=b"<html><title>Success</title></html>",
                    text="<html><title>Success</title></html>",
                    cookies={}
                ),
                ScrapingResponse(
                    url="https://httpbin.org/error",
                    status_code=500,
                    headers={},
                    content=b"",
                    text="",
                    cookies={},
                    success=False,
                    error="Server error"
                )
            ]
            mock_engine.scrape.side_effect = mock_responses
            
            # Mock extractor
            mock_html_extractor.return_value.extract.return_value = {"title": "Success"}
            
            # Mock transformers
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html", "https://httpbin.org/error"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify mixed results
            assert len(results) == 2
            assert results[0]['success'] is True
            assert results[1]['success'] is False
            assert 'error' in results[1]
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_proxy_integration_workflow(self, e2e_config):
        """Test proxy integration in complete workflow."""
        # Enable proxy in config
        e2e_config.proxy.enabled = True
        e2e_config.proxy.providers = ["test_provider"]
        
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            # Mock proxy
            from spider.infrastructure.proxy import ProxyInfo, ProxyStatus
            mock_proxy = ProxyInfo(
                host="proxy.test.com",
                port=8080,
                status=ProxyStatus.HEALTHY,
                success_rate=0.9
            )
            mock_proxy_instance.get_proxy.return_value = mock_proxy
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://httpbin.org/html",
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
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify results
            assert len(results) == 1
            assert results[0]['success'] is True
            
            # Verify proxy was used
            mock_proxy_instance.get_proxy.assert_called()
            mock_proxy_instance.report_proxy_result.assert_called()
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_captcha_integration_workflow(self, e2e_config):
        """Test CAPTCHA integration in complete workflow."""
        # Enable CAPTCHA in config
        e2e_config.captcha.enabled = True
        e2e_config.captcha.providers = ["test_provider"]
        
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://httpbin.org/html",
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
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify results
            assert len(results) == 1
            assert results[0]['success'] is True
            
            # Verify CAPTCHA manager was initialized
            mock_captcha_manager.assert_called_once()
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_data_processing_pipeline(self, e2e_config):
        """Test complete data processing pipeline."""
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://httpbin.org/html",
                status_code=200,
                headers={"content-type": "text/html"},
                content=b"<html><title>  Test Page  </title></html>",
                text="<html><title>  Test Page  </title></html>",
                cookies={}
            )
            mock_engine.scrape.return_value = mock_response
            
            # Mock extractor to return dirty data
            mock_html_extractor.return_value.extract.return_value = {
                "title": "  Test Page  ",
                "description": "Test &amp; Description"
            }
            
            # Mock transformers to clean and normalize data
            def mock_cleaner_transform(data):
                return {
                    "title": "Test Page",
                    "description": "Test & Description"
                }
            
            def mock_normalizer_transform(data):
                return {
                    "title": "test page",
                    "description": "test & description"
                }
            
            mock_cleaner.return_value.transform.side_effect = mock_cleaner_transform
            mock_normalizer.return_value.transform.side_effect = mock_normalizer_transform
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Verify results
            assert len(results) == 1
            assert results[0]['success'] is True
            assert 'extracted_data' in results[0]
            
            # Verify data processing pipeline
            extracted_data = results[0]['extracted_data']
            assert extracted_data['title'] == 'test page'  # Normalized
            assert extracted_data['description'] == 'test & description'  # Cleaned and normalized
            
            # Verify transformers were called
            mock_cleaner.return_value.transform.assert_called()
            mock_normalizer.return_value.transform.assert_called()
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_storage_integration(self, e2e_config):
        """Test storage integration in complete workflow."""
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine response
            mock_response = ScrapingResponse(
                url="https://httpbin.org/html",
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
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Mock storage
            mock_storage_instance = AsyncMock()
            mock_storage.return_value = mock_storage_instance
            
            # Initialize and run
            await spider.initialize()
            
            urls = ["https://httpbin.org/html"]
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=True)
            
            # Test saving results
            await spider.save_results(results, "test_output.json")
            
            # Verify storage was called
            mock_storage_instance.save.assert_called_once_with(results, "test_output.json")
            
            # Cleanup
            await spider.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping(self, e2e_config):
        """Test concurrent scraping with multiple URLs."""
        spider = Spider(e2e_config)
        
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
            mock_engine = Mock()
            mock_engine.__aenter__ = AsyncMock(return_value=mock_engine)
            mock_engine.__aexit__ = AsyncMock(return_value=None)
            mock_engine.scrape = AsyncMock()
            mock_engine_factory.create_engine.return_value = mock_engine
            
            mock_proxy_instance = AsyncMock()
            mock_proxy_manager.return_value = mock_proxy_instance
            
            mock_captcha_instance = Mock()
            mock_captcha_manager.return_value = mock_captcha_instance
            
            # Mock engine responses for multiple URLs
            mock_responses = [
                ScrapingResponse(
                    url=f"https://httpbin.org/html?page={i}",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    content=f"<html><title>Page {i}</title></html>".encode(),
                    text=f"<html><title>Page {i}</title></html>",
                    cookies={}
                )
                for i in range(5)
            ]
            mock_engine.scrape.side_effect = mock_responses
            
            # Mock extractor
            mock_html_extractor.return_value.extract.return_value = {"title": "Test Page"}
            
            # Mock transformers
            mock_cleaner.return_value.transform.side_effect = lambda x: x
            mock_normalizer.return_value.transform.side_effect = lambda x: x
            
            # Initialize and run
            await spider.initialize()
            
            urls = [f"https://httpbin.org/html?page={i}" for i in range(5)]
            start_time = asyncio.get_event_loop().time()
            
            results = await spider.scrape_urls(urls, engine_type="httpx", extract_data=False)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Verify results
            assert len(results) == 5
            assert all(result['success'] for result in results)
            
            # Verify concurrency (should be faster than sequential)
            # With 2 concurrent requests and 5 URLs, should take less than 1 second
            assert duration < 1.0
            
            # Verify all URLs were processed
            processed_urls = [result['url'] for result in results]
            assert set(processed_urls) == set(urls)
            
            # Cleanup
            await spider.cleanup()
