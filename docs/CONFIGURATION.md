# SPIDER Framework - Configuration Guide

## Table of Contents
1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [Database Configuration](#database-configuration)
5. [Redis Configuration](#redis-configuration)
6. [Scraping Configuration](#scraping-configuration)
7. [AI/ML Configuration](#aiml-configuration)
8. [Security Configuration](#security-configuration)
9. [Monitoring Configuration](#monitoring-configuration)
10. [Performance Configuration](#performance-configuration)
11. [Multi-Tenant Configuration](#multi-tenant-configuration)
12. [Deployment Configurations](#deployment-configurations)

## Configuration Overview

SPIDER uses a hierarchical configuration system with the following priority order:

1. **Environment Variables** (Highest Priority)
2. **Configuration Files**
3. **Database Settings**
4. **Default Values** (Lowest Priority)

```mermaid
graph TD
    A[Environment Variables] --> B[Configuration Files]
    B --> C[Database Settings]
    C --> D[Default Values]
    
    A --> E[High Priority]
    B --> F[Medium Priority]
    C --> G[Low Priority]
    D --> H[Fallback]
```

## Environment Variables

### Core Environment Variables

```bash
# Database
export SPIDER_DATABASE_URL="postgresql://user:pass@host:5432/spider"
export SPIDER_DATABASE_POOL_SIZE=20
export SPIDER_DATABASE_MAX_OVERFLOW=30

# Redis
export SPIDER_REDIS_URL="redis://host:6379"
export SPIDER_REDIS_CLUSTER_MODE=true

# Security
export SPIDER_SECRET_KEY="your-secret-key-here"
export SPIDER_JWT_SECRET="your-jwt-secret-here"
export SPIDER_ENCRYPTION_KEY="your-encryption-key-here"

# Monitoring
export SPIDER_PROMETHEUS_ENABLED=true
export SPIDER_PROMETHEUS_PORT=9090
export SPIDER_GRAFANA_URL="http://grafana:3000"

# Logging
export SPIDER_LOG_LEVEL=INFO
export SPIDER_LOG_FORMAT=json
export SPIDER_LOG_FILE="/var/log/spider/spider.log"

# AI/ML
export SPIDER_AI_ENABLED=true
export SPIDER_AI_MODEL_PATH="/models"
export SPIDER_AI_GPU_ENABLED=true

# Scraping
export SPIDER_DEFAULT_ENGINE="scrapy"
export SPIDER_RATE_LIMIT_RPS=10
export SPIDER_RATE_LIMIT_BURST=50
```

### Optional Environment Variables

```bash
# Application
export SPIDER_DEBUG=false
export SPIDER_WORKERS=4
export SPIDER_HOST=0.0.0.0
export SPIDER_PORT=8000

# Caching
export SPIDER_CACHE_ENABLED=true
export SPIDER_CACHE_TTL=3600
export SPIDER_MEMCACHED_URL="memcached://host:11211"

# Proxy
export SPIDER_PROXY_ENABLED=false
export SPIDER_PROXY_URL="http://proxy:8080"

# File Storage
export SPIDER_STORAGE_TYPE="local"
export SPIDER_STORAGE_PATH="/var/lib/spider"
export SPIDER_S3_BUCKET="spider-data"
export SPIDER_S3_REGION="us-east-1"

# Email
export SPIDER_SMTP_HOST="smtp.example.com"
export SPIDER_SMTP_PORT=587
export SPIDER_SMTP_USER="noreply@example.com"
export SPIDER_SMTP_PASSWORD="password"
```

## Configuration Files

### Main Configuration (`config/production.yaml`)

```yaml
# Database Configuration
database:
  url: "${SPIDER_DATABASE_URL}"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  echo: false
  echo_pool: false
  connect_args:
    sslmode: "require"
    connect_timeout: 10

# Redis Configuration
redis:
  url: "${SPIDER_REDIS_URL}"
  cluster_mode: true
  connection_pool:
    max_connections: 100
    retry_on_timeout: true
    socket_keepalive: true
    socket_keepalive_options: {}
  decode_responses: true

# Security Configuration
security:
  secret_key: "${SPIDER_SECRET_KEY}"
  jwt_secret: "${SPIDER_JWT_SECRET}"
  encryption_key: "${SPIDER_ENCRYPTION_KEY}"
  session_timeout: 3600
  password_policy:
    min_length: 8
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_special: true
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 200

# Scraping Configuration
scraping:
  default_engine: "scrapy"
  engines:
    scrapy:
      enabled: true
      concurrent_requests: 16
      download_delay: 1
      randomize_delay: 0.5
      user_agent: "Mozilla/5.0 (compatible; SPIDER/2.0)"
      robots_txt_obey: true
    playwright:
      enabled: true
      headless: true
      timeout: 30000
      viewport: { width: 1920, height: 1080 }
      browser: "chromium"
    httpx:
      enabled: true
      timeout: 30
      limits:
        max_keepalive_connections: 20
        max_connections: 100
  rate_limit:
    requests_per_second: 10
    burst_size: 50
    backoff_strategy: "exponential"
  proxy:
    enabled: false
    rotation_strategy: "round_robin"
    health_check_interval: 300

# AI/ML Configuration
ai:
  enabled: true
  models:
    sentiment:
      name: "distilbert-base-uncased"
      path: "/models/sentiment"
      batch_size: 32
    entities:
      name: "en_core_web_sm"
      path: "/models/entities"
      batch_size: 16
    classification:
      name: "bert-base-uncased"
      path: "/models/classification"
      batch_size: 32
  gpu:
    enabled: true
    device_id: 0
  max_sequence_length: 512
  cache_models: true

# Monitoring Configuration
monitoring:
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"
  grafana:
    enabled: true
    url: "${SPIDER_GRAFANA_URL}"
    api_key: "${SPIDER_GRAFANA_API_KEY}"
  logging:
    level: "INFO"
    format: "json"
    file: "/var/log/spider/spider.log"
    max_size: "100MB"
    max_files: 10
    compress: true
  alerts:
    enabled: true
    channels:
      - type: "email"
        recipients: ["admin@example.com"]
      - type: "slack"
        webhook_url: "https://hooks.slack.com/..."

# Performance Configuration
performance:
  worker_processes: 4
  worker_threads: 8
  max_memory_usage: "2GB"
  cache_size: "512MB"
  connection_pool_size: 100
  enable_compression: true
  compression_level: 6
```

### Local Development (`config/local.yaml`)

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

monitoring:
  prometheus:
    enabled: false
  logging:
    level: "DEBUG"
    format: "text"
```

## Database Configuration

### PostgreSQL Settings

```yaml
database:
  url: "postgresql://user:password@host:5432/spider"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  echo: false
  connect_args:
    sslmode: "require"
    connect_timeout: 10
    application_name: "spider"
  engine_options:
    pool_pre_ping: true
    pool_recycle: 3600
```

### SQLite Settings

```yaml
database:
  url: "sqlite:///spider.db"
  echo: true
  connect_args:
    check_same_thread: false
```

### MySQL Settings

```yaml
database:
  url: "mysql+pymysql://user:password@host:3306/spider"
  pool_size: 20
  max_overflow: 30
  connect_args:
    charset: "utf8mb4"
    autocommit: true
```

## Redis Configuration

### Single Redis Instance

```yaml
redis:
  url: "redis://localhost:6379"
  decode_responses: true
  connection_pool:
    max_connections: 100
    retry_on_timeout: true
```

### Redis Cluster

```yaml
redis:
  cluster_mode: true
  nodes:
    - "redis://node1:6379"
    - "redis://node2:6379"
    - "redis://node3:6379"
  decode_responses: true
  skip_full_coverage_check: true
```

### Redis with Authentication

```yaml
redis:
  url: "redis://:password@host:6379"
  decode_responses: true
  connection_pool:
    max_connections: 100
    retry_on_timeout: true
```

## Scraping Configuration

### Engine-Specific Settings

```yaml
scraping:
  engines:
    scrapy:
      enabled: true
      settings:
        CONCURRENT_REQUESTS: 16
        DOWNLOAD_DELAY: 1
        RANDOMIZE_DOWNLOAD_DELAY: 0.5
        USER_AGENT: "Mozilla/5.0 (compatible; SPIDER/2.0)"
        ROBOTSTXT_OBEY: true
        DOWNLOAD_TIMEOUT: 180
        RETRY_TIMES: 2
        RETRY_HTTP_CODES: [500, 502, 503, 504, 408, 429]
    
    playwright:
      enabled: true
      settings:
        headless: true
        timeout: 30000
        viewport: { width: 1920, height: 1080 }
        browser: "chromium"
        args:
          - "--no-sandbox"
          - "--disable-dev-shm-usage"
        ignore_https_errors: true
    
    httpx:
      enabled: true
      settings:
        timeout: 30
        limits:
          max_keepalive_connections: 20
          max_connections: 100
        headers:
          User-Agent: "Mozilla/5.0 (compatible; SPIDER/2.0)"
        follow_redirects: true
        verify_ssl: true
```

### Rate Limiting

```yaml
scraping:
  rate_limit:
    enabled: true
    requests_per_second: 10
    burst_size: 50
    backoff_strategy: "exponential"
    respect_robots_txt: true
    custom_delays:
      "example.com": 2.0
      "slow-site.com": 5.0
```

### Proxy Configuration

```yaml
scraping:
  proxy:
    enabled: true
    rotation_strategy: "round_robin"
    health_check_interval: 300
    proxies:
      - "http://proxy1:8080"
      - "http://proxy2:8080"
      - "socks5://proxy3:1080"
    authentication:
      username: "proxy_user"
      password: "proxy_pass"
```

## AI/ML Configuration

### Model Configuration

```yaml
ai:
  enabled: true
  models:
    sentiment:
      name: "distilbert-base-uncased"
      path: "/models/sentiment"
      batch_size: 32
      max_length: 512
      device: "cuda"
    
    entities:
      name: "en_core_web_sm"
      path: "/models/entities"
      batch_size: 16
      device: "cpu"
    
    classification:
      name: "bert-base-uncased"
      path: "/models/classification"
      batch_size: 32
      max_length: 512
      device: "cuda"
    
    vision:
      name: "resnet50"
      path: "/models/vision"
      batch_size: 8
      device: "cuda"
  
  gpu:
    enabled: true
    device_id: 0
    memory_fraction: 0.8
  
  cache:
    enabled: true
    ttl: 3600
    max_size: "1GB"
```

### Model Training

```yaml
ai:
  training:
    enabled: true
    data_path: "/data/training"
    output_path: "/models/trained"
    batch_size: 32
    epochs: 10
    learning_rate: 0.001
    validation_split: 0.2
    early_stopping:
      enabled: true
      patience: 3
      min_delta: 0.001
```

## Security Configuration

### Authentication

```yaml
security:
  authentication:
    jwt:
      algorithm: "HS256"
      access_token_expire_minutes: 30
      refresh_token_expire_days: 7
      issuer: "spider"
      audience: "spider-users"
    
    oauth2:
      providers:
        google:
          client_id: "${GOOGLE_CLIENT_ID}"
          client_secret: "${GOOGLE_CLIENT_SECRET}"
        microsoft:
          client_id: "${MICROSOFT_CLIENT_ID}"
          client_secret: "${MICROSOFT_CLIENT_SECRET}"
    
    password_policy:
      min_length: 8
      require_uppercase: true
      require_lowercase: true
      require_numbers: true
      require_special: true
      max_age_days: 90
      history_count: 5
```

### Encryption

```yaml
security:
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_interval: 90
    database:
      enabled: true
    files:
      enabled: true
    api:
      enabled: true
```

### Rate Limiting

```yaml
security:
  rate_limiting:
    enabled: true
    global:
      requests_per_minute: 1000
      burst_size: 2000
    per_user:
      requests_per_minute: 100
      burst_size: 200
    per_ip:
      requests_per_minute: 500
      burst_size: 1000
```

## Monitoring Configuration

### Prometheus

```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"
    scrape_interval: 15s
    rules:
      - "alert_rules.yml"
```

### Grafana

```yaml
monitoring:
  grafana:
    enabled: true
    url: "http://grafana:3000"
    api_key: "${GRAFANA_API_KEY}"
    dashboards:
      - "system_overview"
      - "scraping_metrics"
      - "ai_metrics"
      - "business_metrics"
```

### Logging

```yaml
monitoring:
  logging:
    level: "INFO"
    format: "json"
    file: "/var/log/spider/spider.log"
    max_size: "100MB"
    max_files: 10
    compress: true
    structured: true
    fields:
      service: "spider"
      version: "2.0.0"
```

## Performance Configuration

### Worker Configuration

```yaml
performance:
  workers:
    api:
      processes: 4
      threads_per_process: 2
      max_requests: 1000
      timeout: 30
    
    scrapers:
      processes: 8
      threads_per_process: 4
      max_requests: 500
      timeout: 300
    
    processors:
      processes: 4
      threads_per_process: 8
      max_requests: 2000
      timeout: 60
```

### Caching

```yaml
performance:
  caching:
    redis:
      enabled: true
      ttl: 3600
      max_connections: 100
    
    memcached:
      enabled: true
      servers: ["memcached-1:11211", "memcached-2:11211"]
      ttl: 1800
    
    application:
      enabled: true
      size: "512MB"
      ttl: 300
      eviction_policy: "lru"
```

## Multi-Tenant Configuration

```yaml
multi_tenant:
  enabled: true
  isolation_level: "database"
  default_tenant: "default"
  tenant_creation:
    auto_create: true
    require_approval: false
  resource_limits:
    max_scrapers: 100
    max_data_size: "10GB"
    max_api_calls: 10000
  billing:
    enabled: true
    currency: "USD"
    plans:
      basic:
        price: 29.99
        limits:
          max_scrapers: 10
          max_data_size: "1GB"
      professional:
        price: 99.99
        limits:
          max_scrapers: 50
          max_data_size: "5GB"
      enterprise:
        price: 299.99
        limits:
          max_scrapers: 100
          max_data_size: "10GB"
```

## Deployment Configurations

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  spider-api:
    image: spider:latest
    environment:
      - SPIDER_DATABASE_URL=postgresql://spider:password@postgres:5432/spider
      - SPIDER_REDIS_URL=redis://redis:6379
      - SPIDER_SECRET_KEY=your-secret-key
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: spider
      POSTGRES_USER: spider
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spider-config
data:
  SPIDER_DATABASE_URL: "postgresql://spider:password@postgres:5432/spider"
  SPIDER_REDIS_URL: "redis://redis:6379"
  SPIDER_LOG_LEVEL: "INFO"
```

### Environment-Specific Configs

#### Development
```yaml
# config/development.yaml
database:
  url: "sqlite:///spider.db"
  echo: true

logging:
  level: "DEBUG"
  format: "text"

monitoring:
  prometheus:
    enabled: false
```

#### Staging
```yaml
# config/staging.yaml
database:
  url: "${SPIDER_DATABASE_URL}"
  pool_size: 10

logging:
  level: "INFO"
  format: "json"

monitoring:
  prometheus:
    enabled: true
```

#### Production
```yaml
# config/production.yaml
database:
  url: "${SPIDER_DATABASE_URL}"
  pool_size: 20
  max_overflow: 30

logging:
  level: "WARNING"
  format: "json"

monitoring:
  prometheus:
    enabled: true
  alerts:
    enabled: true
```

## Configuration Validation

### Schema Validation

```python
# config/schema.py
from pydantic import BaseModel, validator
from typing import Optional

class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    
    @validator('pool_size')
    def validate_pool_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('pool_size must be between 1 and 100')
        return v

class SecurityConfig(BaseModel):
    secret_key: str
    jwt_secret: str
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('secret_key must be at least 32 characters')
        return v
```

### Configuration Testing

```bash
# Validate configuration
python -m spider.cli config validate

# Test configuration
python -m spider.cli config test

# Show effective configuration
python -m spider.cli config show
```

## Best Practices

1. **Use Environment Variables**: For sensitive data and environment-specific settings
2. **Validate Configuration**: Always validate configuration on startup
3. **Document Settings**: Document all configuration options
4. **Use Hierarchical Configs**: Override defaults with environment-specific configs
5. **Secure Secrets**: Never commit secrets to version control
6. **Test Configurations**: Test configurations in different environments
7. **Monitor Changes**: Log configuration changes for audit purposes

---

## Support

For configuration support:
- **Documentation**: [github.com/Exemplify777/spider/docs](https://github.com/Exemplify777/spider/docs)
- **Configuration Examples**: `/config/examples/`