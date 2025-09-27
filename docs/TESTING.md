# SPIDER Framework - Testing Guide

## Testing Overview

SPIDER implements comprehensive testing strategies to ensure reliability, performance, and security.

### Test Coverage Goals
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **E2E Tests**: Critical user journeys
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_engines/       # Scraping engine tests
│   ├── test_ai/            # AI/ML component tests
│   ├── test_api/           # API endpoint tests
│   └── test_models/        # Data model tests
├── integration/             # Integration tests
│   ├── test_database/      # Database integration
│   ├── test_redis/         # Redis integration
│   └── test_external/      # External service integration
├── e2e/                    # End-to-end tests
│   ├── test_scraping/      # Complete scraping workflows
│   └── test_ui/            # Web interface tests
├── performance/             # Performance tests
│   ├── test_load/          # Load testing
│   └── test_stress/        # Stress testing
├── security/               # Security tests
│   ├── test_auth/          # Authentication tests
│   └── test_authorization/ # Authorization tests
└── fixtures/               # Test fixtures and data
```

## Unit Testing

### Engine Testing

```python
# tests/unit/test_engines/test_scrapy_engine.py
import pytest
from spider.engines.scrapy_engine import ScrapyEngine

class TestScrapyEngine:
    def setup_method(self):
        self.engine = ScrapyEngine()
    
    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful scraping."""
        result = await self.engine.scrape({
            "url": "https://example.com",
            "selectors": {"title": "h1::text"}
        })
        
        assert result["status"] == "success"
        assert len(result["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_scrape_failure(self):
        """Test scraping failure handling."""
        result = await self.engine.scrape({
            "url": "invalid-url",
            "selectors": {"title": "h1::text"}
        })
        
        assert result["status"] == "error"
        assert "error" in result
```

### AI/ML Testing

```python
# tests/unit/test_ai/test_sentiment_analyzer.py
import pytest
from spider.ai.nlp import SentimentAnalyzer

class TestSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        """Test positive sentiment analysis."""
        result = await self.analyzer.analyze("This product is amazing!")
        
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        """Test negative sentiment analysis."""
        result = await self.analyzer.analyze("This product is terrible!")
        
        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.8
```

### API Testing

```python
# tests/unit/test_api/test_scrapers.py
import pytest
from spider.api.scrapers import ScraperAPI

class TestScraperAPI:
    def setup_method(self):
        self.api = ScraperAPI()
    
    def test_create_scraper_validation(self):
        """Test scraper creation validation."""
        valid_data = {
            "name": "Test Scraper",
            "url": "https://example.com",
            "engine": "scrapy",
            "selectors": {"title": "h1::text"}
        }
        
        assert self.api.validate_scraper_data(valid_data) == True
        
        invalid_data = {
            "name": "",  # Empty name
            "url": "invalid-url",  # Invalid URL
            "engine": "invalid-engine"  # Invalid engine
        }
        
        assert self.api.validate_scraper_data(invalid_data) == False
```

## Integration Testing

### Database Integration

```python
# tests/integration/test_database/test_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from spider.database import Base, Scraper

class TestDatabaseIntegration:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def test_scraper_creation(self):
        """Test scraper creation in database."""
        scraper = Scraper(
            name="Test Scraper",
            url="https://example.com",
            engine="scrapy",
            selectors={"title": "h1::text"}
        )
        
        self.session.add(scraper)
        self.session.commit()
        
        assert scraper.id is not None
        assert scraper.created_at is not None
```

### Redis Integration

```python
# tests/integration/test_redis/test_caching.py
import pytest
import redis
from spider.redis import RedisClient

class TestRedisIntegration:
    def setup_method(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=15)
        self.redis_client.flushdb()
    
    def test_cache_set_get(self):
        """Test cache set and get operations."""
        client = RedisClient(self.redis_client)
        
        # Set cache
        client.set("test_key", "test_value", ttl=60)
        
        # Get cache
        value = client.get("test_key")
        assert value == "test_value"
```

## End-to-End Testing

### Scraping Workflow Testing

```python
# tests/e2e/test_scraping/test_complete_workflow.py
import pytest
from spider import Spider

class TestCompleteScrapingWorkflow:
    def setup_method(self):
        self.spider = Spider()
    
    @pytest.mark.asyncio
    async def test_e2e_scraping_workflow(self):
        """Test complete scraping workflow from creation to results."""
        # Create scraper
        scraper = await self.spider.create_scraper({
            "name": "E2E Test Scraper",
            "url": "https://httpbin.org/html",
            "engine": "scrapy",
            "selectors": {
                "title": "h1::text",
                "content": "p::text"
            }
        })
        
        assert scraper["status"] == "created"
        scraper_id = scraper["id"]
        
        # Run scraper
        job = await self.spider.run_scraper(scraper_id)
        assert job["status"] == "queued"
        
        # Wait for completion and get results
        # ... implementation details ...
        
        # Cleanup
        await self.spider.delete_scraper(scraper_id)
```

## Performance Testing

### Load Testing

```python
# tests/performance/test_load/test_api_load.py
import pytest
import asyncio
import aiohttp

class TestAPILoad:
    def setup_method(self):
        self.base_url = "http://localhost:8000"
        self.api_key = "test-api-key"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent API requests."""
        async def make_request(session, request_id):
            async with session.get(f"{self.base_url}/api/v1/scrapers") as response:
                return await response.json()
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Make 100 concurrent requests
            tasks = [make_request(session, i) for i in range(100)]
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            assert len(results) == 100
            for result in results:
                assert "scrapers" in result
```

## Security Testing

### Authentication Testing

```python
# tests/security/test_auth/test_jwt.py
import pytest
import jwt
from spider.auth import JWTManager

class TestJWTSecurity:
    def setup_method(self):
        self.jwt_manager = JWTManager()
    
    def test_token_generation(self):
        """Test JWT token generation."""
        user_id = "user123"
        role = "developer"
        
        token = self.jwt_manager.generate_token(user_id, role)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode token
        payload = jwt.decode(token, self.jwt_manager.secret_key, algorithms=["HS256"])
        assert payload["user_id"] == user_id
        assert payload["role"] == role
```

## Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --verbose
    --cov=spider
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
```

### Test Environment Setup

```python
# tests/conftest.py
import pytest
import asyncio
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from spider.database import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
```

## Running Tests

### Command Line

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=spider --cov-report=html

# Run specific test
pytest tests/unit/test_engines/test_scrapy_engine.py::TestScrapyEngine::test_scrape_success

# Run with markers
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "performance"
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: spider_test
      
      redis:
        image: redis:7
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=spider --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Data Management

### Test Fixtures

```python
# tests/fixtures/scraper_data.py
import pytest

@pytest.fixture
def sample_scraper_data():
    """Sample scraper data for testing."""
    return {
        "name": "Test Scraper",
        "url": "https://httpbin.org/html",
        "engine": "scrapy",
        "selectors": {
            "title": "h1::text",
            "content": "p::text"
        }
    }

@pytest.fixture
def sample_scraping_results():
    """Sample scraping results for testing."""
    return [
        {
            "title": "Test Page",
            "content": "This is a test page content.",
            "url": "https://httpbin.org/html"
        }
    ]
```

## Best Practices

### Test Organization
1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use Descriptive Names**: Test names should describe what is being tested
3. **One Assertion Per Test**: Each test should verify one specific behavior
4. **Independent Tests**: Tests should not depend on each other
5. **Clean Setup/Teardown**: Properly clean up after each test

### Test Data Management
1. **Use Fixtures**: Reusable test data and setup
2. **Mock External Dependencies**: Don't rely on external services
3. **Use Test Databases**: Isolated database for testing
4. **Clean Test Data**: Remove test data after tests complete

### Performance Testing
1. **Set Realistic Loads**: Test with realistic user loads
2. **Monitor Resources**: Track CPU, memory, and disk usage
3. **Test Edge Cases**: Test under extreme conditions
4. **Measure Response Times**: Ensure acceptable performance

### Security Testing
1. **Test Authentication**: Verify login/logout functionality
2. **Test Authorization**: Check permission enforcement
3. **Test Input Validation**: Verify input sanitization
4. **Test Error Handling**: Ensure errors don't leak information

---

## Support

For testing support:
- **Documentation**: [github.com/Exemplify777/spider/docs](https://github.com/Exemplify777/spider/docs)
- **Test Examples**: `/tests/examples/`