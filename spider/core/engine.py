"""Engine system for SPIDER framework."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from .exceptions import EngineError
from .logger import get_logger


class EngineType(Enum):
    """Available engine types."""
    SCRAPY = "scrapy"
    PLAYWRIGHT = "playwright"
    HTTPX = "httpx"


@dataclass
class ScrapingRequest:
    """Request object for scraping operations."""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    timeout: Optional[int] = None
    retries: int = 3
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ScrapingResponse:
    """Response object from scraping operations."""
    url: str
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    cookies: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None


class BaseEngine(ABC):
    """Base class for all scraping engines."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize engine with configuration.
        
        Args:
            config: Engine-specific configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the engine."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup engine resources."""
        pass
    
    @abstractmethod
    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        """Scrape a single URL.
        
        Args:
            request: Scraping request
            
        Returns:
            Scraping response
        """
        pass
    
    @abstractmethod
    async def scrape_batch(
        self, 
        requests: List[ScrapingRequest]
    ) -> List[ScrapingResponse]:
        """Scrape multiple URLs in batch.
        
        Args:
            requests: List of scraping requests
            
        Returns:
            List of scraping responses
        """
        pass
    
    @abstractmethod
    async def scrape_stream(
        self, 
        requests: AsyncGenerator[ScrapingRequest, None]
    ) -> AsyncGenerator[ScrapingResponse, None]:
        """Scrape URLs from a stream.
        
        Args:
            requests: Async generator of scraping requests
            
        Yields:
            Scraping responses
        """
        pass
    
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


class ScrapyEngine(BaseEngine):
    """Scrapy-based scraping engine."""
    
    async def initialize(self) -> None:
        """Initialize Scrapy engine."""
        try:
            # Import Scrapy components
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings
            
            self.logger.info("Initializing Scrapy engine")
            
            # Setup Scrapy settings
            settings = get_project_settings()
            settings.update(self.config)
            
            self.process = CrawlerProcess(settings)
            self._initialized = True
            
            self.logger.info("Scrapy engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Scrapy engine: {e}")
            raise EngineError(f"Scrapy initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup Scrapy engine."""
        if hasattr(self, 'process'):
            self.process.stop()
        self._initialized = False
        self.logger.info("Scrapy engine cleaned up")
    
    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        """Scrape a single URL using Scrapy."""
        if not self._initialized:
            raise EngineError("Engine not initialized")
        
        try:
            # This is a simplified implementation
            # In practice, you'd use Scrapy's async capabilities
            self.logger.info(f"Scraping URL: {request.url}")
            
            # Placeholder implementation
            response = ScrapingResponse(
                url=request.url,
                status_code=200,
                headers={},
                content=b"",
                text="",
                cookies={}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Scraping failed for {request.url}: {e}")
            return ScrapingResponse(
                url=request.url,
                status_code=0,
                headers={},
                content=b"",
                text="",
                cookies={},
                success=False,
                error=str(e)
            )
    
    async def scrape_batch(
        self, 
        requests: List[ScrapingRequest]
    ) -> List[ScrapingResponse]:
        """Scrape multiple URLs using Scrapy."""
        responses = []
        for request in requests:
            response = await self.scrape(request)
            responses.append(response)
        return responses
    
    async def scrape_stream(
        self, 
        requests: AsyncGenerator[ScrapingRequest, None]
    ) -> AsyncGenerator[ScrapingResponse, None]:
        """Scrape URLs from stream using Scrapy."""
        async for request in requests:
            response = await self.scrape(request)
            yield response


class PlaywrightEngine(BaseEngine):
    """Playwright-based scraping engine for dynamic content."""
    
    async def initialize(self) -> None:
        """Initialize Playwright engine."""
        try:
            from playwright.async_api import async_playwright
            
            self.logger.info("Initializing Playwright engine")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                **self.config.get('browser_options', {})
            )
            
            self._initialized = True
            self.logger.info("Playwright engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright engine: {e}")
            raise EngineError(f"Playwright initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup Playwright engine."""
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        self._initialized = False
        self.logger.info("Playwright engine cleaned up")
    
    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        """Scrape a single URL using Playwright."""
        if not self._initialized:
            raise EngineError("Engine not initialized")
        
        try:
            self.logger.info(f"Scraping URL with Playwright: {request.url}")
            
            page = await self.browser.new_page()
            
            # Set headers if provided
            if request.headers:
                await page.set_extra_http_headers(request.headers)
            
            # Set cookies if provided
            if request.cookies:
                await page.context.add_cookies([
                    {"name": k, "value": v, "url": request.url}
                    for k, v in request.cookies.items()
                ])
            
            # Navigate to URL
            response = await page.goto(
                request.url,
                timeout=request.timeout or self.config.get('timeout', 30000)
            )
            
            # Get content
            content = await page.content()
            
            # Get cookies
            cookies = {}
            for cookie in await page.context.cookies():
                cookies[cookie['name']] = cookie['value']
            
            await page.close()
            
            return ScrapingResponse(
                url=request.url,
                status_code=response.status if response else 0,
                headers=response.headers if response else {},
                content=content.encode('utf-8'),
                text=content,
                cookies=cookies
            )
            
        except Exception as e:
            self.logger.error(f"Playwright scraping failed for {request.url}: {e}")
            return ScrapingResponse(
                url=request.url,
                status_code=0,
                headers={},
                content=b"",
                text="",
                cookies={},
                success=False,
                error=str(e)
            )
    
    async def scrape_batch(
        self, 
        requests: List[ScrapingRequest]
    ) -> List[ScrapingResponse]:
        """Scrape multiple URLs using Playwright."""
        responses = []
        for request in requests:
            response = await self.scrape(request)
            responses.append(response)
        return responses
    
    async def scrape_stream(
        self, 
        requests: AsyncGenerator[ScrapingRequest, None]
    ) -> AsyncGenerator[ScrapingResponse, None]:
        """Scrape URLs from stream using Playwright."""
        async for request in requests:
            response = await self.scrape(request)
            yield response


class HTTPXEngine(BaseEngine):
    """HTTPX-based scraping engine for lightweight requests."""
    
    async def initialize(self) -> None:
        """Initialize HTTPX engine."""
        try:
            import httpx
            
            self.logger.info("Initializing HTTPX engine")
            
            # Create HTTPX client with configuration
            client_config = {
                'timeout': self.config.get('timeout', 30.0),
                'limits': httpx.Limits(
                    max_keepalive_connections=self.config.get('max_keepalive', 20),
                    max_connections=self.config.get('max_connections', 100)
                ),
                'follow_redirects': self.config.get('follow_redirects', True)
            }
            
            self.client = httpx.AsyncClient(**client_config)
            self._initialized = True
            
            self.logger.info("HTTPX engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTPX engine: {e}")
            raise EngineError(f"HTTPX initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup HTTPX engine."""
        if hasattr(self, 'client'):
            await self.client.aclose()
        self._initialized = False
        self.logger.info("HTTPX engine cleaned up")
    
    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        """Scrape a single URL using HTTPX."""
        if not self._initialized:
            raise EngineError("Engine not initialized")
        
        try:
            self.logger.info(f"Scraping URL with HTTPX: {request.url}")
            
            # Prepare request parameters
            request_kwargs = {
                'method': request.method,
                'url': request.url,
                'headers': request.headers or {},
                'params': request.params,
                'timeout': request.timeout or self.config.get('timeout', 30.0)
            }
            
            if request.data:
                if request.method.upper() == 'POST':
                    request_kwargs['json'] = request.data
                else:
                    request_kwargs['params'] = request.data
            
            if request.cookies:
                request_kwargs['cookies'] = request.cookies
            
            if request.proxy:
                request_kwargs['proxies'] = request.proxy
            
            # Make request
            response = await self.client.request(**request_kwargs)
            
            return ScrapingResponse(
                url=str(response.url),
                status_code=response.status_code,
                headers=dict(response.headers),
                content=response.content,
                text=response.text,
                cookies=dict(response.cookies)
            )
            
        except Exception as e:
            self.logger.error(f"HTTPX scraping failed for {request.url}: {e}")
            return ScrapingResponse(
                url=request.url,
                status_code=0,
                headers={},
                content=b"",
                text="",
                cookies={},
                success=False,
                error=str(e)
            )
    
    async def scrape_batch(
        self, 
        requests: List[ScrapingRequest]
    ) -> List[ScrapingResponse]:
        """Scrape multiple URLs using HTTPX."""
        tasks = [self.scrape(request) for request in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append(ScrapingResponse(
                    url=requests[i].url,
                    status_code=0,
                    headers={},
                    content=b"",
                    text="",
                    cookies={},
                    success=False,
                    error=str(response)
                ))
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    async def scrape_stream(
        self, 
        requests: AsyncGenerator[ScrapingRequest, None]
    ) -> AsyncGenerator[ScrapingResponse, None]:
        """Scrape URLs from stream using HTTPX."""
        async for request in requests:
            response = await self.scrape(request)
            yield response


class EngineFactory:
    """Factory for creating scraping engines."""
    
    _engines = {
        EngineType.SCRAPY: ScrapyEngine,
        EngineType.PLAYWRIGHT: PlaywrightEngine,
        EngineType.HTTPX: HTTPXEngine,
    }
    
    @classmethod
    def create_engine(
        self, 
        engine_type: EngineType, 
        config: Dict[str, Any]
    ) -> BaseEngine:
        """Create an engine instance.
        
        Args:
            engine_type: Type of engine to create
            config: Engine configuration
            
        Returns:
            Engine instance
        """
        if engine_type not in self._engines:
            raise EngineError(f"Unknown engine type: {engine_type}")
        
        engine_class = self._engines[engine_type]
        return engine_class(config)
    
    @classmethod
    def get_available_engines(cls) -> List[EngineType]:
        """Get list of available engine types."""
        return list(cls._engines.keys())
