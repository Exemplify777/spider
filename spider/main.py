"""Main entry point for SPIDER framework."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from .core.config import Config
from .core.logger import setup_logging, get_logger
from .core.engine import EngineFactory, EngineType, ScrapingRequest, ScrapingResponse
from .infrastructure.proxy import ProxyManager
from .infrastructure.captcha import CAPTCHAManager
from .processors.extractors import HTMLExtractor, JSONExtractor
from .processors.transformers import DataCleaner, DataNormalizer
from .processors.storage import FileStorage


class Spider:
    """Main SPIDER application class."""
    
    def __init__(self, config: Config):
        """Initialize SPIDER with configuration.
        
        Args:
            config: SPIDER configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize components
        self.engine = None
        self.proxy_manager = None
        self.captcha_manager = None
        self.extractors = {}
        self.transformers = []
        self.storage = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize SPIDER components."""
        if self._initialized:
            return
        
        self.logger.info("Initializing SPIDER...")
        
        # Setup logging
        setup_logging(
            log_level=self.config.monitoring.log_level,
            log_dir=self.config.log_dir,
            enable_console=True,
            enable_file=True
        )
        
        # Initialize proxy manager
        if self.config.proxy.enabled:
            self.proxy_manager = ProxyManager(self.config.proxy.dict())
            await self.proxy_manager.initialize()
            self.logger.info("Proxy manager initialized")
        
        # Initialize CAPTCHA manager
        if self.config.captcha.enabled:
            self.captcha_manager = CAPTCHAManager(self.config.captcha.dict())
            self.logger.info("CAPTCHA manager initialized")
        
        # Initialize extractors
        self.extractors = {
            'html': HTMLExtractor(self.config.engines.scrapy.get('extractors', {}).get('html', {})),
            'json': JSONExtractor(self.config.engines.scrapy.get('extractors', {}).get('json', {}))
        }
        
        # Initialize transformers
        self.transformers = [
            DataCleaner(self.config.get('transformers', {}).get('cleaner', {})),
            DataNormalizer(self.config.get('transformers', {}).get('normalizer', {}))
        ]
        
        # Initialize storage
        self.storage = FileStorage({
            'data_dir': self.config.data_dir,
            'format': 'json'
        })
        
        self._initialized = True
        self.logger.info("SPIDER initialized successfully")
    
    async def scrape_urls(
        self, 
        urls: list[str], 
        engine_type: str = "httpx",
        extract_data: bool = True
    ) -> list[dict]:
        """Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            engine_type: Scraping engine to use
            extract_data: Whether to extract and process data
            
        Returns:
            List of scraping results
        """
        if not self._initialized:
            await self.initialize()
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs with {engine_type} engine")
        
        # Create engine
        engine_enum = EngineType(engine_type)
        engine_config = self.config.get_engine_config(engine_type)
        self.engine = EngineFactory.create_engine(engine_enum, engine_config)
        
        results = []
        
        async with self.engine:
            for url in urls:
                try:
                    self.logger.info(f"Scraping URL: {url}")
                    
                    # Create request
                    request = ScrapingRequest(url=url)
                    
                    # Get proxy if available
                    if self.proxy_manager:
                        proxy = await self.proxy_manager.get_proxy()
                        if proxy:
                            request.proxy = proxy.url
                    
                    # Scrape URL
                    response = await self.engine.scrape(request)
                    
                    if response.success:
                        result = {
                            'url': url,
                            'status_code': response.status_code,
                            'content_length': len(response.content),
                            'headers': response.headers,
                            'success': True
                        }
                        
                        # Extract data if requested
                        if extract_data and response.content:
                            try:
                                extracted_data = await self._extract_data(response.text, response.headers)
                                result['extracted_data'] = extracted_data
                            except Exception as e:
                                self.logger.warning(f"Data extraction failed for {url}: {e}")
                                result['extraction_error'] = str(e)
                        
                        # Report proxy success
                        if self.proxy_manager and request.proxy:
                            await self.proxy_manager.report_proxy_result(
                                proxy, True, 0.0  # Response time not available
                            )
                    else:
                        result = {
                            'url': url,
                            'status_code': response.status_code,
                            'success': False,
                            'error': response.error
                        }
                        
                        # Report proxy failure
                        if self.proxy_manager and request.proxy:
                            await self.proxy_manager.report_proxy_result(
                                proxy, False, 0.0
                            )
                    
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Failed to scrape {url}: {e}")
                    results.append({
                        'url': url,
                        'success': False,
                        'error': str(e)
                    })
        
        self.logger.info(f"Scraping completed. {len([r for r in results if r['success']])} successful, {len([r for r in results if not r['success']])} failed")
        
        return results
    
    async def _extract_data(self, content: str, headers: dict) -> dict:
        """Extract data from content.
        
        Args:
            content: Content to extract from
            headers: Response headers
            
        Returns:
            Extracted data
        """
        # Determine content type
        content_type = headers.get('content-type', '').lower()
        
        if 'html' in content_type:
            extractor = self.extractors['html']
        elif 'json' in content_type:
            extractor = self.extractors['json']
        else:
            # Default to HTML
            extractor = self.extractors['html']
        
        # Extract data
        extracted_data = extractor.extract(content)
        
        # Apply transformers
        for transformer in self.transformers:
            extracted_data = transformer.transform(extracted_data)
        
        return extracted_data
    
    async def save_results(self, results: list[dict], output_path: str) -> None:
        """Save scraping results to file.
        
        Args:
            results: Results to save
            output_path: Output file path
        """
        if self.storage:
            await self.storage.save(results, output_path)
        else:
            # Fallback to direct file writing
            import json
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to {output_path}")
    
    async def cleanup(self) -> None:
        """Cleanup SPIDER resources."""
        if self.engine:
            await self.engine.cleanup()
        
        if self.proxy_manager:
            # Cleanup proxy manager if needed
            pass
        
        self.logger.info("SPIDER cleanup completed")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SPIDER - Web Scraping Framework")
    parser.add_argument("--config", "-c", default="config/spider.yaml", help="Configuration file")
    parser.add_argument("--urls", "-u", nargs="+", help="URLs to scrape")
    parser.add_argument("--engine", "-e", default="httpx", choices=["scrapy", "playwright", "httpx"], help="Scraping engine")
    parser.add_argument("--output", "-o", default="data/results.json", help="Output file")
    parser.add_argument("--extract", action="store_true", help="Extract and process data")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config.from_file(args.config)
    except FileNotFoundError:
        print(f"Configuration file not found: {args.config}")
        print("Run 'spider init' to create a default configuration.")
        sys.exit(1)
    
    # Create SPIDER instance
    spider = Spider(config)
    
    try:
        # Initialize
        await spider.initialize()
        
        # Get URLs
        if args.urls:
            urls = args.urls
        else:
            # Default test URLs
            urls = [
                "https://httpbin.org/html",
                "https://httpbin.org/json",
                "https://httpbin.org/xml"
            ]
        
        # Scrape URLs
        results = await spider.scrape_urls(
            urls=urls,
            engine_type=args.engine,
            extract_data=args.extract
        )
        
        # Save results
        await spider.save_results(results, args.output)
        
        # Print summary
        successful = len([r for r in results if r['success']])
        failed = len([r for r in results if not r['success']])
        
        print(f"\nScraping completed:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await spider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
