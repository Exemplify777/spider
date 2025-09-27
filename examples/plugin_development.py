#!/usr/bin/env python3
"""
SPIDER Framework - Plugin Development Example

This example demonstrates how to create and use custom plugins.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.plugin_manager import PluginManager
from spider.core.config import Config
from spider.core.logger import Logger

class CustomDataProcessor:
    """Custom data processor plugin."""
    
    def __init__(self, config):
        self.config = config
        self.name = "custom_data_processor"
        self.version = "1.0.0"
        self.description = "Custom data processor for text cleaning and formatting"
    
    async def process(self, data, context=None):
        """Process data with custom logic."""
        try:
            processed_data = {}
            
            for key, value in data.items():
                if isinstance(value, str):
                    # Clean and format text
                    processed_value = self._clean_text(value)
                    processed_data[key] = processed_value
                elif isinstance(value, list):
                    # Process list items
                    processed_list = []
                    for item in value:
                        if isinstance(item, str):
                            processed_list.append(self._clean_text(item))
                        else:
                            processed_list.append(item)
                    processed_data[key] = processed_list
                else:
                    processed_data[key] = value
            
            return processed_data
            
        except Exception as e:
            print(f"Error in custom data processor: {str(e)}")
            return data
    
    def _clean_text(self, text):
        """Clean and format text."""
        if not isinstance(text, str):
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters
        text = ''.join(char for char in text if char.isalnum() or char.isspace())
        
        # Convert to title case
        text = text.title()
        
        return text

class CustomAnalyzer:
    """Custom analyzer plugin."""
    
    def __init__(self, config):
        self.config = config
        self.name = "custom_analyzer"
        self.version = "1.0.0"
        self.description = "Custom analyzer for data insights and statistics"
    
    async def analyze(self, data, context=None):
        """Analyze data and return insights."""
        try:
            analysis = {
                'total_items': len(data) if isinstance(data, list) else 1,
                'data_types': {},
                'statistics': {},
                'insights': []
            }
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            data_type = type(value).__name__
                            if data_type not in analysis['data_types']:
                                analysis['data_types'][data_type] = 0
                            analysis['data_types'][data_type] += 1
                            
                            if isinstance(value, str):
                                if 'text_length' not in analysis['statistics']:
                                    analysis['statistics']['text_length'] = []
                                analysis['statistics']['text_length'].append(len(value))
            
            # Calculate insights
            if 'text_length' in analysis['statistics']:
                lengths = analysis['statistics']['text_length']
                analysis['insights'].append(f"Average text length: {sum(lengths) / len(lengths):.2f}")
                analysis['insights'].append(f"Shortest text: {min(lengths)} characters")
                analysis['insights'].append(f"Longest text: {max(lengths)} characters")
            
            return analysis
            
        except Exception as e:
            print(f"Error in custom analyzer: {str(e)}")
            return {'error': str(e)}

class CustomExporter:
    """Custom exporter plugin."""
    
    def __init__(self, config):
        self.config = config
        self.name = "custom_exporter"
        self.version = "1.0.0"
        self.description = "Custom exporter for data formatting and output"
    
    async def export(self, data, format='json', context=None):
        """Export data in custom format."""
        try:
            if format == 'json':
                return json.dumps(data, indent=2, default=str)
            elif format == 'csv':
                return self._to_csv(data)
            elif format == 'xml':
                return self._to_xml(data)
            else:
                return str(data)
                
        except Exception as e:
            print(f"Error in custom exporter: {str(e)}")
            return str(data)
    
    def _to_csv(self, data):
        """Convert data to CSV format."""
        if not isinstance(data, list) or not data:
            return ""
        
        # Get headers from first item
        headers = list(data[0].keys()) if data else []
        
        # Create CSV content
        csv_lines = [','.join(headers)]
        for item in data:
            row = []
            for header in headers:
                value = str(item.get(header, ''))
                # Escape commas and quotes
                value = value.replace('"', '""')
                if ',' in value or '"' in value:
                    value = f'"{value}"'
                row.append(value)
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)
    
    def _to_xml(self, data):
        """Convert data to XML format."""
        if not isinstance(data, list):
            data = [data]
        
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<data>']
        
        for i, item in enumerate(data):
            xml_lines.append(f'  <item id="{i}">')
            for key, value in item.items():
                xml_lines.append(f'    <{key}>{value}</{key}>')
            xml_lines.append('  </item>')
        
        xml_lines.append('</data>')
        return '\n'.join(xml_lines)

async def main():
    """Main function demonstrating plugin development."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting plugin development example")
    
    try:
        # Initialize plugin manager
        plugin_manager = PluginManager(config)
        
        # Register custom plugins
        plugin_manager.register_plugin('data_processor', CustomDataProcessor(config))
        plugin_manager.register_plugin('analyzer', CustomAnalyzer(config))
        plugin_manager.register_plugin('exporter', CustomExporter(config))
        
        # Load plugins
        await plugin_manager.load_plugins()
        
        # Sample data for processing
        sample_data = [
            {
                'title': '  Great Product!  ',
                'description': 'This is an amazing product with excellent quality.',
                'rating': 5,
                'tags': ['quality', 'amazing', 'excellent']
            },
            {
                'title': '  Average Item  ',
                'description': 'Nothing special, just average quality.',
                'rating': 3,
                'tags': ['average', 'nothing', 'special']
            },
            {
                'title': '  Poor Quality  ',
                'description': 'Very disappointed with this purchase.',
                'rating': 1,
                'tags': ['poor', 'disappointed', 'quality']
            }
        ]
        
        # Process data using custom data processor
        logger.info("Processing data with custom data processor...")
        processed_data = await plugin_manager.process_data('data_processor', sample_data)
        logger.info(f"Processed data: {json.dumps(processed_data, indent=2)}")
        
        # Analyze data using custom analyzer
        logger.info("Analyzing data with custom analyzer...")
        analysis = await plugin_manager.analyze_data('analyzer', processed_data)
        logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
        
        # Export data using custom exporter
        logger.info("Exporting data with custom exporter...")
        
        # Export as JSON
        json_export = await plugin_manager.export_data('exporter', processed_data, 'json')
        logger.info(f"JSON export:\n{json_export}")
        
        # Export as CSV
        csv_export = await plugin_manager.export_data('exporter', processed_data, 'csv')
        logger.info(f"CSV export:\n{csv_export}")
        
        # Export as XML
        xml_export = await plugin_manager.export_data('exporter', processed_data, 'xml')
        logger.info(f"XML export:\n{xml_export}")
        
        # Get plugin information
        logger.info("Getting plugin information...")
        plugins = plugin_manager.get_plugins()
        for plugin_name, plugin in plugins.items():
            logger.info(f"Plugin: {plugin_name}")
            logger.info(f"  Name: {plugin.name}")
            logger.info(f"  Version: {plugin.version}")
            logger.info(f"  Description: {plugin.description}")
        
        # Test plugin error handling
        logger.info("Testing plugin error handling...")
        try:
            await plugin_manager.process_data('nonexistent_plugin', sample_data)
        except Exception as e:
            logger.info(f"Expected error: {str(e)}")
        
        # Unload plugins
        await plugin_manager.unload_plugins()
        
        logger.info("Plugin development example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in plugin development example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
