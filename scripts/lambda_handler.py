"""AWS Lambda handler for SPIDER framework."""

import json
import asyncio
import os
from typing import Dict, Any, List

from spider.main import Spider
from spider.core.config import Config
from spider.core.logger import setup_logging


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Lambda response
    """
    # Setup logging
    setup_logging(
        log_level="INFO",
        enable_console=True,
        enable_file=False
    )
    
    try:
        # Parse event
        urls = event.get('urls', [])
        engine = event.get('engine', 'httpx')
        extract_data = event.get('extract_data', True)
        config_path = event.get('config_path', 'config/spider.yaml')
        
        if not urls:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No URLs provided',
                    'message': 'Please provide URLs to scrape in the event data'
                })
            }
        
        # Load configuration
        try:
            config = Config.from_file(config_path)
        except FileNotFoundError:
            # Use default configuration for Lambda
            config = Config(
                environment="production",
                debug=False,
                max_concurrent_requests=10,  # Lower for Lambda
                request_delay=1.0,
                request_timeout=30
            )
        
        # Create SPIDER instance
        spider = Spider(config)
        
        # Run scraping
        results = asyncio.run(spider.scrape_urls(
            urls=urls,
            engine_type=engine,
            extract_data=extract_data
        ))
        
        # Calculate statistics
        successful = len([r for r in results if r.get('success', False)])
        failed = len([r for r in results if not r.get('success', False)])
        
        # Prepare response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Scraping completed successfully',
                'statistics': {
                    'total_urls': len(urls),
                    'successful': successful,
                    'failed': failed,
                    'success_rate': successful / len(urls) if urls else 0
                },
                'results': results
            })
        }
        
        return response
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    finally:
        # Cleanup
        try:
            asyncio.run(spider.cleanup())
        except:
            pass


# For testing locally
if __name__ == "__main__":
    # Test event
    test_event = {
        "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
        "engine": "httpx",
        "extract_data": True
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "spider-test"
            self.function_version = "1"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:spider-test"
            self.memory_limit_in_mb = 1024
            self.remaining_time_in_millis = 300000
    
    context = MockContext()
    
    # Run handler
    result = lambda_handler(test_event, context)
    print(json.dumps(result, indent=2))
