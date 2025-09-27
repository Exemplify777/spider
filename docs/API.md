# SPIDER Framework - API Reference

## Authentication

SPIDER uses JWT tokens for authentication:

```bash
Authorization: Bearer <your-jwt-token>
```

### Login
```bash
POST /auth/login
{
  "username": "your-username",
  "password": "your-password"
}
```

## Core Endpoints

### Health Check
```bash
GET /health
```

### System Info
```bash
GET /info
```

## Scraping API

### Create Scraper
```bash
POST /api/v1/scrapers
{
  "name": "Product Scraper",
  "url": "https://shop.example.com/products",
  "engine": "scrapy",
  "selectors": {
    "title": "h1::text",
    "price": ".price::text"
  }
}
```

### List Scrapers
```bash
GET /api/v1/scrapers?page=1&limit=20
```

### Run Scraper
```bash
POST /api/v1/scrapers/{scraper_id}/run
```

### Get Results
```bash
GET /api/v1/scrapers/{scraper_id}/results
```

## AI/ML API

### Sentiment Analysis
```bash
POST /api/v1/ai/sentiment
{
  "text": "This product is amazing!"
}
```

### Entity Recognition
```bash
POST /api/v1/ai/entities
{
  "text": "Apple Inc. was founded by Steve Jobs."
}
```

### Text Classification
```bash
POST /api/v1/ai/classify
{
  "text": "Breaking news: New technology announced",
  "categories": ["news", "technology", "business"]
}
```

## Data Processing

### Process Data
```bash
POST /api/v1/process
{
  "data": [...],
  "processors": ["clean", "validate", "enrich"]
}
```

## User Management

### Create User
```bash
POST /api/v1/users
{
  "username": "john.doe",
  "email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "role": "developer"
}
```

### List Users
```bash
GET /api/v1/users
```

## Monitoring

### System Metrics
```bash
GET /api/v1/metrics
```

### Scraper Statistics
```bash
GET /api/v1/scrapers/{scraper_id}/stats
```

## WebSocket API

```javascript
const ws = new WebSocket('wss://api.example.com/ws?token=your-jwt-token');
```

### Message Types
- `job_status`: Job progress updates
- `alert`: System alerts
- `metrics`: Real-time metrics

## SDK Examples

### Python
```python
from spider import SpiderClient

client = SpiderClient(api_key="your-api-key")
scraper = client.scrapers.create({...})
job = client.scrapers.run(scraper.id)
results = client.scrapers.get_results(scraper.id)
```

### JavaScript
```javascript
import { SpiderClient } from '@spider/sdk';

const client = new SpiderClient({ apiKey: 'your-api-key' });
const scraper = await client.scrapers.create({...});
const job = await client.scrapers.run(scraper.id);
const results = await client.scrapers.getResults(scraper.id);
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "url",
      "reason": "URL is required"
    }
  }
}
```

### HTTP Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 429: Rate Limited
- 500: Internal Server Error

## Rate Limiting

- Default: 100 requests per minute
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## Support

- **API Docs**: https://api.example.com/docs
- **GitHub**: https://github.com/Exemplify777/spider