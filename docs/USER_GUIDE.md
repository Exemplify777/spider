# SPIDER Framework - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Features](#core-features)
4. [Web Interface](#web-interface)
5. [API Usage](#api-usage)
6. [Configuration](#configuration)
7. [Data Processing](#data-processing)
8. [AI/ML Features](#aiml-features)
9. [Monitoring & Analytics](#monitoring--analytics)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

## Introduction

SPIDER is an enterprise-grade web scraping framework that provides powerful, scalable, and intelligent data extraction capabilities. This guide will help you get started with SPIDER and make the most of its features.

### What is SPIDER?

SPIDER is a comprehensive web scraping platform that combines:
- **Multi-Engine Scraping**: Scrapy, Playwright, and HTTPX
- **AI-Powered Processing**: Machine learning for data extraction and validation
- **Enterprise Features**: Multi-tenancy, security, compliance, and monitoring
- **Cloud-Native**: Deploy anywhere from local development to Kubernetes clusters

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ (for web interface)
- Docker (optional, for containerized deployment)
- 4GB+ RAM recommended

### Installation

#### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/Exemplify777/spider.git
cd spider

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for web interface)
cd web/dashboard
npm install
cd ../..

# Run the application
python -m spider.main --config config/local.yaml
```

#### Option 2: Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:3000
```

### First Steps

1. **Access the Web Interface**: Navigate to `http://localhost:3000`
2. **Create an Account**: Register a new user account
3. **Configure Your First Scraper**: Use the guided setup wizard
4. **Run a Test Scrape**: Execute your first scraping job

## Core Features

### Web Scraping Engines

SPIDER supports three powerful scraping engines:

#### Scrapy Engine
- **Best for**: Large-scale crawling, structured data extraction
- **Features**: Built-in scheduling, duplicate detection, auto-throttling
- **Use cases**: E-commerce sites, news aggregation, content management

```python
from spider.engines.scrapy_engine import ScrapyEngine

engine = ScrapyEngine()
result = await engine.scrape({
    "url": "https://example.com",
    "selectors": {
        "title": "h1::text",
        "price": ".price::text"
    }
})
```

#### Playwright Engine
- **Best for**: JavaScript-heavy sites, dynamic content
- **Features**: Full browser automation, screenshot capture, PDF generation
- **Use cases**: Single-page applications, interactive websites

```python
from spider.engines.playwright_engine import PlaywrightEngine

engine = PlaywrightEngine()
result = await engine.scrape({
    "url": "https://spa-example.com",
    "wait_for": ".dynamic-content",
    "actions": ["click_button", "scroll_to_bottom"]
})
```

#### HTTPX Engine
- **Best for**: High-performance API calls, simple HTTP requests
- **Features**: Async/await support, connection pooling, retry logic
- **Use cases**: REST APIs, lightweight scraping

```python
from spider.engines.httpx_engine import HTTPXEngine

engine = HTTPXEngine()
result = await engine.scrape({
    "url": "https://api.example.com/data",
    "headers": {"Authorization": "Bearer token"}
})
```

### Data Processing Pipeline

```mermaid
graph TD
    A[Raw HTML/JSON] --> B[Content Extraction]
    B --> C[Data Validation]
    C --> D[AI Processing]
    D --> E[Data Transformation]
    E --> F[Quality Scoring]
    F --> G[Storage/Export]
    
    B --> H[CSS Selectors]
    B --> I[XPath]
    B --> J[Regex Patterns]
    B --> K[AI Extractors]
    
    D --> L[Sentiment Analysis]
    D --> M[Entity Recognition]
    D --> N[Text Classification]
    D --> O[Image Processing]
```

### Proxy Management

SPIDER includes intelligent proxy management:

```python
# Configure proxy settings
proxy_config = {
    "enabled": True,
    "rotation_strategy": "round_robin",
    "health_check_interval": 300,
    "proxies": [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080"
    ]
}
```

### Rate Limiting

Adaptive rate limiting prevents overwhelming target websites:

```python
rate_limit_config = {
    "requests_per_second": 2,
    "burst_size": 10,
    "backoff_strategy": "exponential",
    "respect_robots_txt": True
}
```

## Web Interface

### Dashboard Overview

The SPIDER web interface provides a comprehensive dashboard with:

- **Real-time Metrics**: Active scrapers, data volume, success rates
- **Job Management**: Create, monitor, and manage scraping jobs
- **Data Visualization**: Charts and graphs of your scraping results
- **System Health**: Monitor system performance and resource usage

### Creating Your First Scraper

1. **Navigate to Scrapers**: Click "Scrapers" in the main menu
2. **Create New Scraper**: Click the "New Scraper" button
3. **Configure Basic Settings**:
   - Name: Give your scraper a descriptive name
   - URL: Target website URL
   - Engine: Choose Scrapy, Playwright, or HTTPX
4. **Define Data Selectors**:
   - Use the visual selector tool
   - Or manually enter CSS selectors/XPath
5. **Set Schedule**: Configure when to run the scraper
6. **Save and Test**: Save your configuration and run a test

### Data Management

#### Viewing Scraped Data
- **Data Explorer**: Browse and search through scraped data
- **Export Options**: Download data in CSV, JSON, or Excel format
- **Data Visualization**: Create charts and graphs from your data

#### Data Quality
- **Quality Scores**: See how clean and complete your data is
- **Validation Rules**: Set up custom validation rules
- **Error Handling**: Review and fix data extraction errors

## API Usage

### Authentication

All API requests require authentication. Include your API key in the header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.example.com/v1/scrapers
```

### Core API Endpoints

#### Scrapers

```bash
# List all scrapers
GET /api/v1/scrapers

# Create a new scraper
POST /api/v1/scrapers
{
  "name": "Product Scraper",
  "url": "https://shop.example.com",
  "engine": "scrapy",
  "selectors": {
    "title": "h1::text",
    "price": ".price::text"
  }
}

# Run a scraper
POST /api/v1/scrapers/{id}/run

# Get scraper results
GET /api/v1/scrapers/{id}/results
```

#### Data Processing

```bash
# Process raw data
POST /api/v1/process
{
  "data": [...],
  "processors": ["clean", "validate", "enrich"]
}

# Get processing status
GET /api/v1/process/{job_id}/status
```

#### AI/ML Features

```bash
# Analyze text sentiment
POST /api/v1/ai/sentiment
{
  "text": "This product is amazing!"
}

# Extract entities
POST /api/v1/ai/entities
{
  "text": "Apple Inc. was founded by Steve Jobs in 1976."
}

# Classify content
POST /api/v1/ai/classify
{
  "text": "Breaking news: New technology announced",
  "categories": ["news", "technology", "business"]
}
```

### WebSocket API

For real-time updates:

```javascript
const ws = new WebSocket('wss://api.example.com/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

## Configuration

### Environment Variables

```bash
# Database
SPIDER_DATABASE_URL=postgresql://user:pass@localhost/spider

# Redis
SPIDER_REDIS_URL=redis://localhost:6379

# Security
SPIDER_SECRET_KEY=your-secret-key
SPIDER_JWT_SECRET=your-jwt-secret

# Monitoring
SPIDER_PROMETHEUS_ENABLED=true
SPIDER_GRAFANA_URL=http://localhost:3001
```

### Configuration Files

#### Local Development (`config/local.yaml`)

```yaml
database:
  url: "sqlite:///spider.db"
  echo: true

redis:
  url: "redis://localhost:6379"

scraping:
  default_engine: "scrapy"
  rate_limit:
    requests_per_second: 1
    burst_size: 5

ai:
  enabled: true
  models:
    sentiment: "distilbert-base-uncased"
    entities: "en_core_web_sm"
```

#### Production (`config/production.yaml`)

```yaml
database:
  url: "${SPIDER_DATABASE_URL}"
  pool_size: 20
  max_overflow: 30

redis:
  url: "${SPIDER_REDIS_URL}"
  cluster_mode: true

scraping:
  default_engine: "scrapy"
  rate_limit:
    requests_per_second: 10
    burst_size: 50

monitoring:
  prometheus:
    enabled: true
    port: 9090
  grafana:
    enabled: true
    url: "${SPIDER_GRAFANA_URL}"

security:
  jwt_secret: "${SPIDER_JWT_SECRET}"
  session_timeout: 3600
  rate_limiting:
    enabled: true
    requests_per_minute: 100
```

## Data Processing

### Extractors

SPIDER provides multiple data extraction methods:

#### CSS Selectors
```python
selectors = {
    "title": "h1::text",
    "price": ".price::text",
    "description": ".description p::text"
}
```

#### XPath
```python
xpath_selectors = {
    "title": "//h1/text()",
    "price": "//span[@class='price']/text()",
    "rating": "//div[@class='rating']/@data-value"
}
```

#### AI Extractors
```python
ai_extractors = {
    "sentiment": "analyze_sentiment",
    "entities": "extract_entities",
    "categories": "classify_content"
}
```

### Data Validation

Set up validation rules to ensure data quality:

```python
validation_rules = {
    "price": {
        "type": "number",
        "min": 0,
        "required": True
    },
    "title": {
        "type": "string",
        "min_length": 5,
        "max_length": 200,
        "required": True
    },
    "email": {
        "type": "email",
        "required": False
    }
}
```

### Data Transformation

Transform your data using built-in processors:

```python
transformers = [
    "clean_whitespace",
    "normalize_phone",
    "extract_domain",
    "format_date",
    "calculate_sentiment"
]
```

## AI/ML Features

### Natural Language Processing

#### Sentiment Analysis
```python
from spider.ai.nlp import SentimentAnalyzer

analyzer = SentimentAnalyzer()
sentiment = await analyzer.analyze("This product is amazing!")
# Returns: {"sentiment": "positive", "confidence": 0.95}
```

#### Entity Recognition
```python
from spider.ai.nlp import EntityRecognizer

recognizer = EntityRecognizer()
entities = await recognizer.extract("Apple Inc. was founded by Steve Jobs.")
# Returns: [{"text": "Apple Inc.", "label": "ORG"}, {"text": "Steve Jobs", "label": "PERSON"}]
```

#### Text Classification
```python
from spider.ai.nlp import TextClassifier

classifier = TextClassifier()
category = await classifier.classify("Breaking news: New technology announced")
# Returns: {"category": "news", "confidence": 0.89}
```

### Computer Vision

#### Image Processing
```python
from spider.ai.vision import ImageProcessor

processor = ImageProcessor()
result = await processor.process_image("image.jpg", {
    "extract_text": True,
    "detect_objects": True,
    "classify_content": True
})
```

#### OCR (Optical Character Recognition)
```python
from spider.ai.vision import OCRProcessor

ocr = OCRProcessor()
text = await ocr.extract_text("document.png")
```

### Predictive Analytics

#### Forecasting
```python
from spider.ai.predictive import ForecastingEngine

forecaster = ForecastingEngine()
forecast = await forecaster.forecast(data, {
    "horizon": 30,
    "frequency": "daily",
    "model": "arima"
})
```

#### Anomaly Detection
```python
from spider.ai.predictive import AnomalyDetector

detector = AnomalyDetector()
anomalies = await detector.detect(data, {
    "method": "isolation_forest",
    "contamination": 0.1
})
```

## Monitoring & Analytics

### Real-time Monitoring

The SPIDER dashboard provides real-time monitoring of:

- **Active Scrapers**: Number of running scrapers
- **Data Volume**: Amount of data being processed
- **Success Rate**: Percentage of successful scraping jobs
- **Error Rate**: Number and types of errors
- **Performance Metrics**: Response times, throughput

### Analytics Dashboard

#### Key Metrics
- **Scraping Performance**: Success rates, error rates, response times
- **Data Quality**: Validation scores, completeness metrics
- **System Health**: CPU, memory, disk usage
- **User Activity**: Login patterns, feature usage

#### Custom Reports
Create custom reports and dashboards:

```python
from spider.analytics import ReportBuilder

report = ReportBuilder()
report.add_metric("scraping_success_rate")
report.add_metric("data_quality_score")
report.add_filter("date_range", "last_30_days")
report.add_grouping("scraper_type")
dashboard = await report.build()
```

### Alerts and Notifications

Configure alerts for important events:

```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.1"
    channels: ["email", "slack"]
    recipients: ["admin@example.com"]
  
  - name: "Low Data Quality"
    condition: "quality_score < 0.8"
    channels: ["webhook"]
    webhook_url: "https://hooks.slack.com/..."
```

## Troubleshooting

### Common Issues

#### Scraping Failures

**Problem**: Scraper returns empty results
**Solutions**:
1. Check if the website structure has changed
2. Verify selectors are correct
3. Try a different scraping engine
4. Check if the site requires JavaScript

**Problem**: Rate limiting errors
**Solutions**:
1. Increase delays between requests
2. Use proxy rotation
3. Implement exponential backoff
4. Respect robots.txt

#### Performance Issues

**Problem**: Slow scraping performance
**Solutions**:
1. Use HTTPX engine for simple requests
2. Enable connection pooling
3. Optimize selectors
4. Use parallel processing

**Problem**: High memory usage
**Solutions**:
1. Enable data streaming
2. Use pagination for large datasets
3. Implement data cleanup
4. Monitor memory limits

#### Authentication Issues

**Problem**: API authentication fails
**Solutions**:
1. Check API key validity
2. Verify token expiration
3. Ensure proper header format
4. Check user permissions

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set environment variable
export SPIDER_DEBUG=true

# Or use command line flag
python -m spider.main --debug
```

### Log Analysis

View and analyze logs:

```bash
# View recent logs
tail -f logs/spider.log

# Search for errors
grep "ERROR" logs/spider.log

# Analyze performance
grep "PERFORMANCE" logs/spider.log | jq
```

## Best Practices

### Scraping Best Practices

1. **Respect robots.txt**: Always check and respect robots.txt files
2. **Use appropriate delays**: Don't overwhelm target websites
3. **Implement error handling**: Handle network errors gracefully
4. **Monitor for changes**: Websites change, monitor your scrapers
5. **Use appropriate engines**: Choose the right engine for the job

### Data Quality

1. **Validate early**: Implement validation rules from the start
2. **Clean data**: Use data cleaning processors
3. **Monitor quality**: Track data quality metrics
4. **Handle errors**: Implement proper error handling
5. **Test regularly**: Run validation tests frequently

### Performance Optimization

1. **Choose the right engine**: Scrapy for large-scale, Playwright for dynamic content
2. **Use caching**: Enable Redis caching for repeated requests
3. **Optimize selectors**: Use efficient CSS selectors or XPath
4. **Parallel processing**: Use multiple workers for large jobs
5. **Monitor resources**: Keep an eye on CPU and memory usage

### Security

1. **Use HTTPS**: Always use secure connections
2. **Rotate proxies**: Use proxy rotation for anonymity
3. **Validate inputs**: Sanitize all user inputs
4. **Monitor access**: Track and log all access attempts
5. **Keep updated**: Regularly update dependencies

### Maintenance

1. **Regular testing**: Run tests after any changes
2. **Monitor logs**: Check logs regularly for issues
3. **Update dependencies**: Keep all packages updated
4. **Backup data**: Regular backups of important data
5. **Document changes**: Document any configuration changes

---

## Support

### Getting Help

- **Documentation**: Check this guide and other documentation
- **Community Forum**: Join our community forum
- **GitHub Issues**: Report bugs and request features
### Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### License

SPIDER is licensed under the MIT License. See [LICENSE](LICENSE) for details.
