# SPIDER Framework Examples

This directory contains comprehensive examples demonstrating various features and capabilities of the SPIDER framework.

## Examples Overview

### 1. Basic Scraping (`basic_scraping.py`)
Demonstrates basic web scraping functionality including:
- Simple scraper configuration
- Basic data extraction
- Result storage and retrieval
- Monitoring and analytics

**Usage:**
```bash
python examples/basic_scraping.py
```

### 2. Advanced Scraping (`advanced_scraping.py`)
Demonstrates advanced scraping features including:
- Dynamic content scraping
- Anti-bot protection
- Data processing and AI analysis
- Custom plugins
- Error handling and retry logic

**Usage:**
```bash
python examples/advanced_scraping.py
```

### 3. AI Analysis (`ai_analysis.py`)
Demonstrates AI-powered data analysis including:
- Sentiment analysis
- Entity extraction
- Language detection
- Topic extraction
- Text classification
- Text summarization
- Text translation
- Text generation
- Text similarity
- Text clustering
- Anomaly detection
- Trend analysis
- Text prediction

**Usage:**
```bash
python examples/ai_analysis.py
```

### 4. Monitoring Dashboard (`monitoring_dashboard.py`)
Demonstrates monitoring and analytics including:
- Real-time metrics collection
- Performance monitoring
- Error tracking
- Resource usage monitoring
- Alert management
- Health status monitoring
- Dashboard data generation

**Usage:**
```bash
python examples/monitoring_dashboard.py
```

### 5. Plugin Development (`plugin_development.py`)
Demonstrates custom plugin development including:
- Custom data processors
- Custom analyzers
- Custom exporters
- Plugin registration and management
- Error handling
- Data format conversion

**Usage:**
```bash
python examples/plugin_development.py
```

### 6. Enterprise Features (`enterprise_features.py`)
Demonstrates enterprise features including:
- Multi-tenancy
- Advanced security
- Compliance reporting
- User management
- Audit logging
- Data retention
- Security scanning
- Backup and recovery

**Usage:**
```bash
python examples/enterprise_features.py
```

## Plugin Examples

### Simple HTML Extractor (`plugins/simple_html_extractor.py`)
A basic plugin for extracting HTML content and converting it to structured data.

## Prerequisites

Before running the examples, ensure you have:

1. **Python 3.8+** installed
2. **Required dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration file** set up:
   ```bash
   cp config/spider.yaml.example config/spider.yaml
   ```
4. **Database** configured and running
5. **Redis** server running (for caching and queuing)
6. **Required services** running (if applicable)

## Configuration

Each example uses the main SPIDER configuration file (`config/spider.yaml`). You can customize the configuration for your specific needs.

### Example Configuration

```yaml
# Database configuration
database:
  url: "sqlite:///spider.db"
  pool_size: 20
  max_overflow: 30

# Redis configuration
redis:
  url: "redis://localhost:6379"
  cluster_mode: false

# AI configuration
ai:
  enabled: true
  models:
    sentiment: "distilbert-base-uncased-finetuned-sst-2-english"
    entity: "dbmdz/bert-large-cased-finetuned-conll03-english"
    language: "papluca/xlm-roberta-base-language-detection"

# Monitoring configuration
monitoring:
  enabled: true
  metrics_interval: 30
  alert_thresholds:
    cpu_usage: 80
    memory_usage: 85
    error_rate: 5

# Security configuration
security:
  encryption_key: "your-encryption-key-here"
  jwt_secret: "your-jwt-secret-here"
  password_min_length: 8
  session_timeout: 3600
```

## Running Examples

### Individual Examples

Run a specific example:
```bash
python examples/basic_scraping.py
```

### All Examples

Run all examples in sequence:
```bash
python examples/run_all_examples.py
```

### With Custom Configuration

Run an example with a custom configuration:
```bash
SPIDER_CONFIG_PATH=/path/to/custom/config.yaml python examples/basic_scraping.py
```

## Example Outputs

Each example generates output files in the current directory:

- `scraping_results_YYYYMMDD_HHMMSS.json` - Scraping results
- `ai_analysis_results_YYYYMMDD_HHMMSS.json` - AI analysis results
- `monitoring_data_YYYYMMDD_HHMMSS.json` - Monitoring data
- `enterprise_data_YYYYMMDD_HHMMSS.json` - Enterprise features data

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in your Python path
2. **Configuration Errors**: Check that `config/spider.yaml` exists and is valid
3. **Database Errors**: Ensure the database is running and accessible
4. **Redis Errors**: Ensure Redis is running and accessible
5. **Permission Errors**: Check file permissions for output directories

### Debug Mode

Run examples in debug mode for detailed logging:
```bash
SPIDER_LOG_LEVEL=DEBUG python examples/basic_scraping.py
```

### Verbose Output

Enable verbose output for more detailed information:
```bash
SPIDER_VERBOSE=true python examples/basic_scraping.py
```

## Customization

### Adding New Examples

1. Create a new Python file in the `examples/` directory
2. Follow the existing example structure
3. Import required SPIDER components
4. Implement your example logic
5. Add error handling and logging
6. Update this README with your example

### Example Template

```python
#!/usr/bin/env python3
"""
SPIDER Framework - Your Example Name

Description of what this example demonstrates.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spider.core.config import Config
from spider.core.logger import Logger

async def main():
    """Main function demonstrating your feature."""
    
    # Initialize configuration
    config = Config()
    config.load_from_file('config/spider.yaml')
    
    # Initialize logger
    logger = Logger(config)
    logger.info("Starting your example")
    
    try:
        # Your example logic here
        
        logger.info("Your example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in your example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing

When adding new examples:

1. Follow the existing code style and structure
2. Include comprehensive error handling
3. Add detailed logging
4. Include configuration examples
5. Update documentation
6. Test thoroughly
7. Add to the examples list in this README

## Support

For questions or issues with the examples:

1. Check the troubleshooting section
2. Review the main SPIDER documentation
3. Check the GitHub issues
4. Create a new issue if needed

## License

These examples are part of the SPIDER framework and are subject to the same license terms.
