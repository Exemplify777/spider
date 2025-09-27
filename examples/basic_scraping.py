#!/usr/bin/env python3
"""
SPIDER Framework - Basic Scraping Example

This example demonstrates basic web scraping using the SPIDER framework.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.scraper import Scraper
from spider.core.engine import ScrapingEngine
from spider.core.scheduler import Scheduler
from spider.core.monitor import Monitor
from spider.core.storage import Storage
from spider.core.ai import AIProcessor
from spider.core.analytics import Analytics
from spider.core.security import SecurityManager
from spider.core.config import Config
from spider.core.logger import Logger

async def main():
    """Main function demonstrating basic scraping."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting basic scraping example")
    
    try:
        # Initialize components
        storage = Storage(config)
        security = SecurityManager(config)
        ai_processor = AIProcessor(config)
        analytics = Analytics(config)
        monitor = Monitor(config)
        scheduler = Scheduler(config)
        engine = ScrapingEngine(config, storage, security, ai_processor, analytics, monitor)
        
        # Create a simple scraper configuration
        scraper_config = {
            'name': 'example_scraper',
            'url': 'https://example.com',
            'selectors': {
                'title': 'h1',
                'content': '.content',
                'links': 'a[href]'
            },
            'delay': 1.0,
            'max_pages': 5,
            'respect_robots': True,
            'user_agent': 'SPIDER Bot 1.0'
        }
        
        # Create scraper
        scraper = Scraper(scraper_config, config)
        
        # Add scraper to engine
        engine.add_scraper(scraper)
        
        # Start monitoring
        await monitor.start()
        
        # Start analytics
        await analytics.start()
        
        # Start engine
        await engine.start()
        
        # Schedule scraping task
        task_id = await scheduler.schedule_task(
            scraper_id=scraper.id,
            schedule_time=None,  # Run immediately
            priority=1
        )
        
        logger.info(f"Scheduled scraping task: {task_id}")
        
        # Wait for task to complete
        await asyncio.sleep(10)
        
        # Get task status
        task_status = await scheduler.get_task_status(task_id)
        logger.info(f"Task status: {task_status}")
        
        # Get scraping results
        results = await storage.get_scraping_results(scraper.id)
        logger.info(f"Scraped {len(results)} pages")
        
        # Display results
        for i, result in enumerate(results[:3]):  # Show first 3 results
            logger.info(f"Result {i+1}:")
            logger.info(f"  URL: {result.get('url', 'N/A')}")
            logger.info(f"  Title: {result.get('data', {}).get('title', 'N/A')}")
            logger.info(f"  Content length: {len(result.get('data', {}).get('content', ''))}")
            logger.info(f"  Links found: {len(result.get('data', {}).get('links', []))}")
        
        # Get analytics data
        analytics_data = await analytics.get_analytics()
        logger.info(f"Analytics data: {analytics_data}")
        
        # Get monitoring data
        monitoring_data = await monitor.get_metrics()
        logger.info(f"Monitoring data: {monitoring_data}")
        
        # Stop components
        await engine.stop()
        await analytics.stop()
        await monitor.stop()
        
        logger.info("Basic scraping example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in basic scraping example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
