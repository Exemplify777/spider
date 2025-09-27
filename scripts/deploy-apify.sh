#!/bin/bash

# SPIDER Apify Platform Deployment Script
# This script packages and deploys SPIDER to the Apify platform

set -e

echo "🕷️  SPIDER Apify Platform Deployment"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
ACTOR_NAME="spider-scraper"
ACTOR_VERSION="1.0.0"
APIFY_API_TOKEN="${APIFY_API_TOKEN}"
APIFY_USER_ID="${APIFY_USER_ID}"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Apify CLI is installed
    if ! command -v apify &> /dev/null; then
        print_error "Apify CLI is not installed. Please install it first:"
        echo "npm install -g @apify/cli"
        exit 1
    fi
    
    # Check if API token is provided
    if [ -z "$APIFY_API_TOKEN" ]; then
        print_error "APIFY_API_TOKEN environment variable is not set."
        echo "Please set your Apify API token:"
        echo "export APIFY_API_TOKEN=your_api_token"
        exit 1
    fi
    
    # Check if user ID is provided
    if [ -z "$APIFY_USER_ID" ]; then
        print_error "APIFY_USER_ID environment variable is not set."
        echo "Please set your Apify user ID:"
        echo "export APIFY_USER_ID=your_user_id"
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Create Apify actor structure
create_actor_structure() {
    print_status "Creating Apify actor structure..."
    
    # Create actor directory
    mkdir -p apify-actor
    
    # Create package.json
    cat > apify-actor/package.json << EOF
{
  "name": "spider-scraper",
  "version": "1.0.0",
  "description": "SPIDER - Scalable Python Integrated Data Extraction & Retrieval",
  "main": "main.py",
  "scripts": {
    "start": "python main.py",
    "test": "pytest tests/",
    "dev": "python main.py --config config/spider.yaml"
  },
  "dependencies": {
    "apify": "^3.0.0"
  },
  "apify": {
    "actorSpecification": 1,
    "name": "spider-scraper",
    "title": "SPIDER Web Scraper",
    "description": "A comprehensive web scraping framework for scalable data extraction",
    "version": "1.0.0",
    "input": "./input_schema.json",
    "dockerfile": "./Dockerfile"
  }
}
EOF
    
    # Create input schema
    cat > apify-actor/input_schema.json << EOF
{
  "title": "SPIDER Scraper Input",
  "type": "object",
  "schemaVersion": 1,
  "properties": {
    "urls": {
      "title": "URLs to scrape",
      "type": "array",
      "description": "List of URLs to scrape",
      "editor": "stringList",
      "isRequired": true
    },
    "engine": {
      "title": "Scraping Engine",
      "type": "string",
      "description": "Scraping engine to use",
      "enum": ["scrapy", "playwright", "httpx"],
      "default": "httpx"
    },
    "extractData": {
      "title": "Extract Data",
      "type": "boolean",
      "description": "Whether to extract and process data",
      "default": true
    },
    "maxConcurrent": {
      "title": "Max Concurrent Requests",
      "type": "integer",
      "description": "Maximum number of concurrent requests",
      "minimum": 1,
      "maximum": 100,
      "default": 16
    },
    "requestDelay": {
      "title": "Request Delay (seconds)",
      "type": "number",
      "description": "Delay between requests in seconds",
      "minimum": 0,
      "default": 1.0
    },
    "useProxy": {
      "title": "Use Proxy",
      "type": "boolean",
      "description": "Whether to use proxy rotation",
      "default": false
    },
    "solveCaptcha": {
      "title": "Solve CAPTCHA",
      "type": "boolean",
      "description": "Whether to solve CAPTCHAs automatically",
      "default": false
    }
  }
}
EOF
    
    # Create Dockerfile for Apify
    cat > apify-actor/Dockerfile << EOF
# SPIDER Apify Actor Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    wget \\
    gnupg \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \\
    pip install -r requirements.txt

# Install Playwright and browsers
RUN pip install playwright && \\
    playwright install chromium && \\
    playwright install-deps

# Create application directory
WORKDIR /app

# Copy application code
COPY spider/ ./spider/
COPY config/ ./config/
COPY main.py .
COPY apify_main.py .

# Create necessary directories
RUN mkdir -p data logs cache

# Set permissions
RUN chmod +x apify_main.py

# Default command
CMD ["python", "apify_main.py"]
EOF
    
    print_success "Apify actor structure created"
}

# Create Apify main file
create_apify_main() {
    print_status "Creating Apify main file..."
    
    cat > apify-actor/apify_main.py << 'EOF'
"""Apify main file for SPIDER framework."""

import asyncio
import json
import os
from typing import Dict, Any, List

from apify import Actor
from spider.main import Spider
from spider.core.config import Config
from spider.core.logger import setup_logging


async def main():
    """Main function for Apify actor."""
    # Initialize Apify Actor
    async with Actor() as actor:
        # Get input from Apify
        input_data = await actor.get_input()
        
        # Setup logging
        setup_logging(
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )
        
        # Parse input
        urls = input_data.get('urls', [])
        engine = input_data.get('engine', 'httpx')
        extract_data = input_data.get('extractData', True)
        max_concurrent = input_data.get('maxConcurrent', 16)
        request_delay = input_data.get('requestDelay', 1.0)
        use_proxy = input_data.get('useProxy', False)
        solve_captcha = input_data.get('solveCaptcha', False)
        
        if not urls:
            await actor.fail("No URLs provided in input")
            return
        
        # Create configuration
        config = Config(
            environment="production",
            debug=False,
            max_concurrent_requests=max_concurrent,
            request_delay=request_delay,
            proxy__enabled=use_proxy,
            captcha__enabled=solve_captcha,
            monitoring__enabled=False
        )
        
        # Create SPIDER instance
        spider = Spider(config)
        
        try:
            # Initialize SPIDER
            await spider.initialize()
            
            # Log start
            await actor.log.info(f"Starting to scrape {len(urls)} URLs with {engine} engine")
            
            # Scrape URLs
            results = await spider.scrape_urls(
                urls=urls,
                engine_type=engine,
                extract_data=extract_data
            )
            
            # Process results
            successful_results = [r for r in results if r.get('success', False)]
            failed_results = [r for r in results if not r.get('success', False)]
            
            # Log statistics
            await actor.log.info(f"Scraping completed: {len(successful_results)} successful, {len(failed_results)} failed")
            
            # Save results to Apify dataset
            for result in results:
                await actor.push_data(result)
            
            # Set output
            output = {
                'message': 'Scraping completed successfully',
                'statistics': {
                    'total_urls': len(urls),
                    'successful': len(successful_results),
                    'failed': len(failed_results),
                    'success_rate': len(successful_results) / len(urls) if urls else 0
                },
                'results': results
            }
            
            await actor.set_value('OUTPUT', output)
            
        except Exception as e:
            await actor.log.error(f"Scraping failed: {e}")
            await actor.fail(f"Scraping failed: {e}")
        
        finally:
            # Cleanup
            await spider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    print_success "Apify main file created"
}

# Copy application files
copy_application_files() {
    print_status "Copying application files..."
    
    # Copy spider package
    cp -r spider apify-actor/
    
    # Copy config
    cp -r config apify-actor/
    
    # Copy main.py
    cp main.py apify-actor/
    
    # Copy requirements.txt
    cp requirements.txt apify-actor/
    
    # Create .dockerignore
    cat > apify-actor/.dockerignore << EOF
# Git
.git
.gitignore

# Documentation
docs/
*.md

# Tests
tests/
pytest.ini

# Development files
.env
env.example
.pre-commit-config.yaml

# CI/CD
.github/

# Scripts
scripts/

# Docker
docker-compose.yml
Dockerfile

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Data
data/
logs/
cache/
*.db
*.sqlite
*.sqlite3
EOF
    
    print_success "Application files copied"
}

# Deploy to Apify
deploy_to_apify() {
    print_status "Deploying to Apify platform..."
    
    # Login to Apify
    apify login --token "$APIFY_API_TOKEN"
    
    # Navigate to actor directory
    cd apify-actor
    
    # Create actor
    apify create "$ACTOR_NAME" --template empty
    
    # Push actor
    apify push
    
    # Get actor ID
    ACTOR_ID=$(apify info | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$ACTOR_ID" ]; then
        print_success "Actor deployed successfully!"
        print_success "Actor ID: $ACTOR_ID"
        print_success "Actor URL: https://console.apify.com/actors/$ACTOR_ID"
    else
        print_error "Failed to get actor ID"
        exit 1
    fi
    
    cd ..
}

# Test deployed actor
test_actor() {
    print_status "Testing deployed actor..."
    
    # Create test input
    cat > test_input.json << EOF
{
  "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
  "engine": "httpx",
  "extractData": true,
  "maxConcurrent": 2,
  "requestDelay": 0.5,
  "useProxy": false,
  "solveCaptcha": false
}
EOF
    
    # Run actor
    apify call "$ACTOR_ID" --input test_input.json
    
    # Cleanup
    rm -f test_input.json
    
    print_success "Actor test completed"
}

# Create actor documentation
create_documentation() {
    print_status "Creating actor documentation..."
    
    cat > apify-actor/README.md << EOF
# SPIDER Scraper - Apify Actor

A comprehensive web scraping framework deployed as an Apify actor for scalable data extraction.

## Features

- **Multiple Engines**: Scrapy, Playwright, and HTTPX support
- **Data Extraction**: Automatic HTML, JSON, and XML data extraction
- **Proxy Support**: Optional proxy rotation for anti-detection
- **CAPTCHA Solving**: Automatic CAPTCHA resolution
- **Concurrent Processing**: Configurable concurrent request handling
- **Error Handling**: Comprehensive error handling and retry mechanisms

## Input Parameters

- \`urls\`: List of URLs to scrape (required)
- \`engine\`: Scraping engine to use (scrapy, playwright, httpx)
- \`extractData\`: Whether to extract and process data
- \`maxConcurrent\`: Maximum number of concurrent requests
- \`requestDelay\`: Delay between requests in seconds
- \`useProxy\`: Whether to use proxy rotation
- \`solveCaptcha\`: Whether to solve CAPTCHAs automatically

## Output

The actor outputs scraped data to the Apify dataset, including:

- URL and response status
- Scraped content
- Extracted data (if enabled)
- Error information (if any)
- Processing statistics

## Usage

1. Go to the [Apify Console](https://console.apify.com)
2. Find the SPIDER Scraper actor
3. Configure input parameters
4. Run the actor
5. Download results from the dataset

## Examples

### Basic Scraping
\`\`\`json
{
  "urls": ["https://example.com"],
  "engine": "httpx",
  "extractData": true
}
\`\`\`

### Advanced Scraping with Proxy
\`\`\`json
{
  "urls": ["https://example.com", "https://test.com"],
  "engine": "playwright",
  "extractData": true,
  "maxConcurrent": 4,
  "requestDelay": 1.0,
  "useProxy": true,
  "solveCaptcha": true
}
\`\`\`

## Support

For issues and questions, please visit the [SPIDER GitHub repository](https://github.com/spider-dev/spider).
EOF
    
    print_success "Documentation created"
}

# Cleanup
cleanup() {
    print_status "Cleaning up temporary files..."
    
    rm -rf apify-actor
    rm -f test_input.json
    
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    echo "Starting SPIDER Apify deployment..."
    echo
    
    check_prerequisites
    create_actor_structure
    create_apify_main
    copy_application_files
    create_documentation
    deploy_to_apify
    test_actor
    cleanup
    
    echo
    print_success "SPIDER Apify deployment completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Visit the Apify Console to manage your actor"
    echo "2. Configure input parameters for your scraping tasks"
    echo "3. Run the actor to start scraping"
    echo "4. Download results from the dataset"
    echo
    echo "Actor URL: https://console.apify.com/actors/$ACTOR_ID"
    echo
}

# Run main function with all arguments
main "$@"
