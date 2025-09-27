#!/usr/bin/env python3
"""
SPIDER Framework - Advanced Scraping Example

This example demonstrates advanced web scraping features including:
- Dynamic content scraping
- Anti-bot protection
- Data processing and AI analysis
- Custom plugins
- Error handling and retry logic
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

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
from spider.core.anti_bot import AntiBotProtection
from spider.core.data_processor import DataProcessor
from spider.core.plugin_manager import PluginManager

async def main():
    """Main function demonstrating advanced scraping."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting advanced scraping example")
    
    try:
        # Initialize components
        storage = Storage(config)
        security = SecurityManager(config)
        ai_processor = AIProcessor(config)
        analytics = Analytics(config)
        monitor = Monitor(config)
        scheduler = Scheduler(config)
        anti_bot = AntiBotProtection(config)
        data_processor = DataProcessor(config)
        plugin_manager = PluginManager(config)
        
        # Load custom plugins
        await plugin_manager.load_plugins('plugins/')
        
        # Create advanced scraper configuration
        scraper_config = {
            'name': 'advanced_scraper',
            'url': 'https://quotes.toscrape.com',
            'selectors': {
                'quotes': '.quote',
                'quote_text': '.text',
                'quote_author': '.author',
                'quote_tags': '.tag',
                'next_page': '.next a'
            },
            'delay': 2.0,
            'max_pages': 10,
            'respect_robots': True,
            'user_agent': 'SPIDER Bot 1.0',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            'cookies': {},
            'timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 5.0,
            'anti_bot_protection': True,
            'data_processing': True,
            'ai_analysis': True,
            'custom_plugins': ['simple_html_extractor']
        }
        
        # Create scraper with anti-bot protection
        scraper = Scraper(scraper_config, config)
        scraper.set_anti_bot_protection(anti_bot)
        scraper.set_data_processor(data_processor)
        scraper.set_ai_processor(ai_processor)
        
        # Add custom data processing rules
        processing_rules = {
            'clean_text': True,
            'extract_entities': True,
            'sentiment_analysis': True,
            'language_detection': True,
            'duplicate_removal': True,
            'data_validation': True
        }
        scraper.set_processing_rules(processing_rules)
        
        # Add scraper to engine
        engine = ScrapingEngine(config, storage, security, ai_processor, analytics, monitor)
        engine.add_scraper(scraper)
        
        # Start all components
        await monitor.start()
        await analytics.start()
        await engine.start()
        
        # Schedule multiple scraping tasks
        tasks = []
        for i in range(3):
            task_id = await scheduler.schedule_task(
                scraper_id=scraper.id,
                schedule_time=datetime.now() + timedelta(seconds=i*10),
                priority=i+1
            )
            tasks.append(task_id)
            logger.info(f"Scheduled task {i+1}: {task_id}")
        
        # Wait for all tasks to complete
        await asyncio.sleep(60)
        
        # Get task statuses
        for i, task_id in enumerate(tasks):
            task_status = await scheduler.get_task_status(task_id)
            logger.info(f"Task {i+1} status: {task_status}")
        
        # Get scraping results
        results = await storage.get_scraping_results(scraper.id)
        logger.info(f"Scraped {len(results)} pages")
        
        # Process and analyze results
        processed_results = []
        for result in results:
            # Apply data processing
            processed_data = await data_processor.process_data(
                result.get('data', {}),
                processing_rules
            )
            
            # Apply AI analysis
            ai_analysis = await ai_processor.analyze_data(processed_data)
            
            processed_result = {
                'url': result.get('url'),
                'timestamp': result.get('timestamp'),
                'data': processed_data,
                'ai_analysis': ai_analysis
            }
            processed_results.append(processed_result)
        
        # Display processed results
        for i, result in enumerate(processed_results[:3]):  # Show first 3 results
            logger.info(f"Processed Result {i+1}:")
            logger.info(f"  URL: {result.get('url', 'N/A')}")
            logger.info(f"  Timestamp: {result.get('timestamp', 'N/A')}")
            
            data = result.get('data', {})
            logger.info(f"  Quotes found: {len(data.get('quotes', []))}")
            
            ai_analysis = result.get('ai_analysis', {})
            if ai_analysis:
                logger.info(f"  Sentiment: {ai_analysis.get('sentiment', 'N/A')}")
                logger.info(f"  Language: {ai_analysis.get('language', 'N/A')}")
                logger.info(f"  Entities: {len(ai_analysis.get('entities', []))}")
        
        # Get analytics data
        analytics_data = await analytics.get_analytics()
        logger.info(f"Analytics data: {analytics_data}")
        
        # Get monitoring data
        monitoring_data = await monitor.get_metrics()
        logger.info(f"Monitoring data: {monitoring_data}")
        
        # Export results
        export_data = {
            'scraper_id': scraper.id,
            'total_pages': len(results),
            'processed_results': processed_results,
            'analytics': analytics_data,
            'monitoring': monitoring_data,
            'export_timestamp': datetime.now().isoformat()
        }
        
        export_file = f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Results exported to: {export_file}")
        
        # Stop components
        await engine.stop()
        await analytics.stop()
        await monitor.stop()
        
        logger.info("Advanced scraping example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in advanced scraping example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
