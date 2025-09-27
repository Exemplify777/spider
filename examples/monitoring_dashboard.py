#!/usr/bin/env python3
"""
SPIDER Framework - Monitoring Dashboard Example

This example demonstrates monitoring and analytics using the SPIDER framework.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.monitor import Monitor
from spider.core.analytics import Analytics
from spider.core.config import Config
from spider.core.logger import Logger
from spider.core.storage import Storage

async def main():
    """Main function demonstrating monitoring dashboard."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting monitoring dashboard example")
    
    try:
        # Initialize components
        storage = Storage(config)
        monitor = Monitor(config)
        analytics = Analytics(config)
        
        # Start monitoring
        await monitor.start()
        await analytics.start()
        
        # Simulate some scraping activity
        logger.info("Simulating scraping activity...")
        for i in range(10):
            # Simulate scraping metrics
            await monitor.record_metric('scraping_requests', 1)
            await monitor.record_metric('scraping_success', 1)
            await monitor.record_metric('scraping_duration', 2.5)
            await monitor.record_metric('scraping_pages', 5)
            
            # Simulate system metrics
            await monitor.record_metric('cpu_usage', 45.2)
            await monitor.record_metric('memory_usage', 67.8)
            await monitor.record_metric('disk_usage', 23.4)
            await monitor.record_metric('network_usage', 12.1)
            
            # Simulate error metrics
            if i % 3 == 0:
                await monitor.record_metric('scraping_errors', 1)
                await monitor.record_metric('scraping_retries', 1)
            
            await asyncio.sleep(1)
        
        # Get monitoring metrics
        logger.info("Getting monitoring metrics...")
        metrics = await monitor.get_metrics()
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        # Get analytics data
        logger.info("Getting analytics data...")
        analytics_data = await analytics.get_analytics()
        logger.info(f"Analytics: {json.dumps(analytics_data, indent=2)}")
        
        # Get performance metrics
        logger.info("Getting performance metrics...")
        performance = await monitor.get_performance_metrics()
        logger.info(f"Performance: {json.dumps(performance, indent=2)}")
        
        # Get error metrics
        logger.info("Getting error metrics...")
        errors = await monitor.get_error_metrics()
        logger.info(f"Errors: {json.dumps(errors, indent=2)}")
        
        # Get resource usage
        logger.info("Getting resource usage...")
        resources = await monitor.get_resource_usage()
        logger.info(f"Resources: {json.dumps(resources, indent=2)}")
        
        # Get alerts
        logger.info("Getting alerts...")
        alerts = await monitor.get_alerts()
        logger.info(f"Alerts: {json.dumps(alerts, indent=2)}")
        
        # Get health status
        logger.info("Getting health status...")
        health = await monitor.get_health_status()
        logger.info(f"Health: {json.dumps(health, indent=2)}")
        
        # Get dashboard data
        logger.info("Getting dashboard data...")
        dashboard = await monitor.get_dashboard_data()
        logger.info(f"Dashboard: {json.dumps(dashboard, indent=2)}")
        
        # Export monitoring data
        export_data = {
            'metrics': metrics,
            'analytics': analytics_data,
            'performance': performance,
            'errors': errors,
            'resources': resources,
            'alerts': alerts,
            'health': health,
            'dashboard': dashboard,
            'export_timestamp': datetime.now().isoformat()
        }
        
        export_file = f"monitoring_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Monitoring data exported to: {export_file}")
        
        # Stop monitoring
        await monitor.stop()
        await analytics.stop()
        
        logger.info("Monitoring dashboard example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in monitoring dashboard example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
