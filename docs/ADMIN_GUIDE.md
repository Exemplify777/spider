# SPIDER Framework - Administrator Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Installation & Deployment](#installation--deployment)
4. [Configuration Management](#configuration-management)
5. [User Management](#user-management)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Performance Tuning](#performance-tuning)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

## Introduction

This guide is designed for system administrators responsible for deploying, configuring, and maintaining SPIDER Framework in production environments. It covers advanced configuration, security, monitoring, and operational procedures.

### Prerequisites

- Linux/Unix system administration experience
- Docker and Kubernetes knowledge
- Database administration (PostgreSQL, Redis)
- Network security concepts
- Monitoring and logging systems

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX/HAProxy]
    end
    
    subgraph "Web Tier"
        API[FastAPI Application]
        WEB[React Dashboard]
    end
    
    subgraph "Application Tier"
        SCRAPER[Scraping Engine]
        AI[AI/ML Services]
        PROCESSOR[Data Processor]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        CACHE[(Memcached)]
    end
    
    subgraph "Storage Tier"
        FS[File System]
        S3[AWS S3]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end
    
    LB --> API
    LB --> WEB
    API --> SCRAPER
    API --> AI
    API --> PROCESSOR
    SCRAPER --> DB
    AI --> DB
    PROCESSOR --> DB
    API --> REDIS
    API --> CACHE
    SCRAPER --> FS
    PROCESSOR --> S3
    API --> PROM
    PROM --> GRAF
    API --> ELK
```

### Component Overview

#### Core Services
- **API Gateway**: FastAPI-based REST API with authentication and rate limiting
- **Web Dashboard**: React-based user interface for management and monitoring
- **Scraping Engine**: Multi-engine scraping system (Scrapy, Playwright, HTTPX)
- **AI/ML Services**: Machine learning models for data processing and analysis
- **Data Processor**: ETL pipeline for data transformation and validation

#### Data Layer
- **PostgreSQL**: Primary database for metadata, user data, and job management
- **Redis**: Caching layer and session storage
- **Memcached**: Additional caching for performance optimization
- **File Storage**: Local filesystem or cloud storage for scraped data

#### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **ELK Stack**: Centralized logging (Elasticsearch, Logstash, Kibana)

## Installation & Deployment

### System Requirements

#### Minimum Requirements
- **CPU**: 4 cores, 2.4 GHz
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 1 Gbps

#### Recommended Requirements
- **CPU**: 8+ cores, 3.0+ GHz
- **RAM**: 32+ GB
- **Storage**: 500+ GB NVMe SSD
- **Network**: 10 Gbps

### Docker Deployment

#### Single Node Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: spider
      POSTGRES_USER: spider
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  spider-api:
    image: spider:latest
    environment:
      DATABASE_URL: postgresql://spider:${POSTGRES_PASSWORD}@postgres:5432/spider
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  spider-web:
    image: spider-web:latest
    ports:
      - "3000:3000"
    depends_on:
      - spider-api

volumes:
  postgres_data:
  redis_data:
```

#### Multi-Node Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - spider-api

  spider-api:
    image: spider:latest
    deploy:
      replicas: 3
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: spider
      POSTGRES_USER: spider
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
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

### Kubernetes Deployment

#### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: spider
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: spider-config
  namespace: spider
data:
  DATABASE_URL: "postgresql://spider:password@postgres:5432/spider"
  REDIS_URL: "redis://redis:6379"
  LOG_LEVEL: "INFO"
```

#### Database Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: spider
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: spider
        - name: POSTGRES_USER
          value: spider
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: spider
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### Application Deployment

```yaml
# k8s/spider-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spider-api
  namespace: spider
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spider-api
  template:
    metadata:
      labels:
        app: spider-api
    spec:
      containers:
      - name: spider-api
        image: spider:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: spider-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: spider-config
              key: REDIS_URL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: spider-api
  namespace: spider
spec:
  selector:
    app: spider-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Environment Setup

#### Production Environment Variables

```bash
# Database Configuration
export SPIDER_DATABASE_URL="postgresql://user:pass@host:5432/spider"
export SPIDER_DATABASE_POOL_SIZE=20
export SPIDER_DATABASE_MAX_OVERFLOW=30

# Redis Configuration
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

## Configuration Management

### Configuration Hierarchy

```mermaid
graph TD
    A[Environment Variables] --> B[Configuration Files]
    B --> C[Database Settings]
    C --> D[Runtime Configuration]
    
    A --> E[High Priority]
    B --> F[Medium Priority]
    C --> G[Low Priority]
    D --> H[Default Values]
```

### Configuration Files

#### Main Configuration (`config/production.yaml`)

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

# Redis Configuration
redis:
  url: "${SPIDER_REDIS_URL}"
  cluster_mode: true
  connection_pool:
    max_connections: 100
    retry_on_timeout: true
    socket_keepalive: true
    socket_keepalive_options: {}

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
    playwright:
      enabled: true
      headless: true
      timeout: 30000
      viewport: { width: 1920, height: 1080 }
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
    entities:
      name: "en_core_web_sm"
      path: "/models/entities"
    classification:
      name: "bert-base-uncased"
      path: "/models/classification"
  gpu:
    enabled: true
    device_id: 0
  batch_size: 32
  max_sequence_length: 512

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

# Performance Configuration
performance:
  worker_processes: 4
  worker_threads: 8
  max_memory_usage: "2GB"
  cache_size: "512MB"
  connection_pool_size: 100
```

### Configuration Validation

```python
# config/validation.py
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
    encryption_key: str
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('secret_key must be at least 32 characters')
        return v
```

## User Management

### User Roles and Permissions

```mermaid
graph TD
    A[Super Admin] --> B[Admin]
    B --> C[Manager]
    C --> D[Developer]
    D --> E[Viewer]
    
    A --> F[All Permissions]
    B --> G[User Management]
    C --> H[Project Management]
    D --> I[Scraper Management]
    E --> J[Read Only]
```

#### Role Definitions

```yaml
# roles.yaml
roles:
  super_admin:
    permissions:
      - user.create
      - user.read
      - user.update
      - user.delete
      - scraper.create
      - scraper.read
      - scraper.update
      - scraper.delete
      - system.configure
      - system.monitor
      - system.backup
    description: "Full system access"
  
  admin:
    permissions:
      - user.create
      - user.read
      - user.update
      - scraper.create
      - scraper.read
      - scraper.update
      - scraper.delete
      - system.monitor
    description: "Administrative access"
  
  manager:
    permissions:
      - user.read
      - scraper.create
      - scraper.read
      - scraper.update
      - scraper.delete
      - data.read
      - data.export
    description: "Project management access"
  
  developer:
    permissions:
      - scraper.create
      - scraper.read
      - scraper.update
      - scraper.delete
      - data.read
    description: "Development access"
  
  viewer:
    permissions:
      - scraper.read
      - data.read
    description: "Read-only access"
```

### User Management Commands

#### Create User

```bash
# Using CLI
python -m spider.cli user create \
  --username john.doe \
  --email john.doe@example.com \
  --role developer \
  --password "SecurePassword123!"

# Using API
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@example.com",
    "role": "developer",
    "password": "SecurePassword123!"
  }'
```

#### Update User Role

```bash
# Using CLI
python -m spider.cli user update-role \
  --username john.doe \
  --role manager

# Using API
curl -X PATCH http://localhost:8000/api/v1/users/john.doe/role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "manager"}'
```

#### List Users

```bash
# Using CLI
python -m spider.cli user list --role developer

# Using API
curl -X GET "http://localhost:8000/api/v1/users?role=developer" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Multi-Tenant Configuration

```yaml
# multi_tenant.yaml
multi_tenant:
  enabled: true
  isolation_level: "database"  # database, schema, table
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

## Security Configuration

### Authentication & Authorization

#### JWT Configuration

```yaml
# security/jwt.yaml
jwt:
  algorithm: "HS256"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  issuer: "spider"
  audience: "spider-users"
  secret_key: "${SPIDER_JWT_SECRET}"
  refresh_secret_key: "${SPIDER_JWT_REFRESH_SECRET}"
```

#### OAuth2 Configuration

```yaml
# security/oauth2.yaml
oauth2:
  providers:
    google:
      client_id: "${GOOGLE_CLIENT_ID}"
      client_secret: "${GOOGLE_CLIENT_SECRET}"
      redirect_uri: "https://example.com/auth/google/callback"
    microsoft:
      client_id: "${MICROSOFT_CLIENT_ID}"
      client_secret: "${MICROSOFT_CLIENT_SECRET}"
      redirect_uri: "https://example.com/auth/microsoft/callback"
    github:
      client_id: "${GITHUB_CLIENT_ID}"
      client_secret: "${GITHUB_CLIENT_SECRET}"
      redirect_uri: "https://example.com/auth/github/callback"
```

### Network Security

#### Firewall Rules

```bash
# iptables rules for SPIDER
# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow PostgreSQL (restrict to internal network)
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT

# Allow Redis (restrict to internal network)
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/8 -j ACCEPT

# Allow Prometheus (restrict to monitoring network)
iptables -A INPUT -p tcp --dport 9090 -s 10.0.1.0/24 -j ACCEPT

# Drop all other traffic
iptables -A INPUT -j DROP
```

#### SSL/TLS Configuration

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/ssl/certs/spider.crt;
    ssl_certificate_key /etc/ssl/private/spider.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    location / {
        proxy_pass http://spider-api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Data Encryption

#### Database Encryption

```yaml
# security/encryption.yaml
encryption:
  database:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation_interval: 90  # days
  files:
    enabled: true
    algorithm: "AES-256-CBC"
    key_derivation: "PBKDF2"
  api:
    enabled: true
    algorithm: "AES-256-GCM"
    key_exchange: "ECDH"
```

#### Key Management

```bash
# Generate encryption keys
python -m spider.cli security generate-keys

# Rotate encryption keys
python -m spider.cli security rotate-keys

# Backup encryption keys
python -m spider.cli security backup-keys --output /secure/backup/keys/
```

## Monitoring & Alerting

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'spider-api'
    static_configs:
      - targets: ['spider-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'spider-scrapers'
    static_configs:
      - targets: ['spider-scraper-1:8001', 'spider-scraper-2:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
  - name: spider.rules
    rules:
      - alert: HighErrorRate
        expr: rate(spider_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighMemoryUsage
        expr: spider_memory_usage_bytes / spider_memory_limit_bytes > 0.8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      - alert: DatabaseConnectionFailure
        expr: spider_database_connections_failed_total > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Database connection failed {{ $value }} times"

      - alert: ScraperFailure
        expr: spider_scraper_failures_total > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Scraper failures detected"
          description: "{{ $value }} scraper failures in the last 5 minutes"
```

### Grafana Dashboards

#### System Overview Dashboard

```json
{
  "dashboard": {
    "title": "SPIDER System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(spider_requests_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(spider_errors_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "spider_memory_usage_bytes",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Active Scrapers",
        "type": "singlestat",
        "targets": [
          {
            "expr": "spider_active_scrapers",
            "legendFormat": "Active Scrapers"
          }
        ]
      }
    ]
  }
}
```

### Log Management

#### ELK Stack Configuration

```yaml
# logging/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "spider" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} %{GREEDYDATA:message}" }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    mutate {
      add_field => { "service" => "spider" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "spider-logs-%{+YYYY.MM.dd}"
  }
}
```

## Performance Tuning

### Database Optimization

#### PostgreSQL Configuration

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Connection settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

-- Logging
log_statement = 'all'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

#### Index Optimization

```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_scrapers_tenant_id ON scrapers(tenant_id);
CREATE INDEX CONCURRENTLY idx_scrapers_status ON scrapers(status);
CREATE INDEX CONCURRENTLY idx_scrapers_created_at ON scrapers(created_at);
CREATE INDEX CONCURRENTLY idx_scraper_results_scraper_id ON scraper_results(scraper_id);
CREATE INDEX CONCURRENTLY idx_scraper_results_created_at ON scraper_results(created_at);

-- Composite indexes
CREATE INDEX CONCURRENTLY idx_scrapers_tenant_status ON scrapers(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_results_scraper_created ON scraper_results(scraper_id, created_at);
```

### Redis Optimization

```yaml
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
tcp-backlog 511
databases 16
save 900 1
save 300 10
save 60 10000
```

### Application Performance

#### Worker Configuration

```yaml
# performance/workers.yaml
workers:
  api:
    processes: 4
    threads_per_process: 2
    max_requests: 1000
    max_requests_jitter: 100
    timeout: 30
    keepalive: 2
  
  scrapers:
    processes: 8
    threads_per_process: 4
    max_requests: 500
    max_requests_jitter: 50
    timeout: 300
    keepalive: 5
  
  processors:
    processes: 4
    threads_per_process: 8
    max_requests: 2000
    max_requests_jitter: 200
    timeout: 60
    keepalive: 2
```

#### Caching Strategy

```yaml
# performance/caching.yaml
caching:
  redis:
    enabled: true
    ttl: 3600  # 1 hour
    max_connections: 100
    connection_pool:
      max_connections: 100
      retry_on_timeout: true
  
  memcached:
    enabled: true
    servers: ["memcached-1:11211", "memcached-2:11211"]
    ttl: 1800  # 30 minutes
  
  application:
    enabled: true
    size: "512MB"
    ttl: 300  # 5 minutes
    eviction_policy: "lru"
```

## Backup & Recovery

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup/backup_database.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="spider"
DB_USER="spider"
DB_HOST="postgres"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_DIR/spider_full_$DATE.backup"

# Incremental backup (WAL files)
pg_basebackup -h $DB_HOST -U $DB_USER -D "$BACKUP_DIR/wal_$DATE" \
  --format=tar \
  --gzip \
  --progress

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -name "wal_*" -mtime +30 -exec rm -rf {} \;
```

#### Backup Configuration

```yaml
# backup/backup_config.yaml
backup:
  database:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention_days: 30
    compression: true
    encryption: true
  
  files:
    enabled: true
    schedule: "0 3 * * *"  # Daily at 3 AM
    retention_days: 7
    include_patterns:
      - "/var/log/spider/*"
      - "/var/lib/spider/uploads/*"
    exclude_patterns:
      - "*.tmp"
      - "*.log"
  
  configuration:
    enabled: true
    schedule: "0 1 * * *"  # Daily at 1 AM
    retention_days: 90
    include_files:
      - "/etc/spider/*"
      - "/opt/spider/config/*"
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# recovery/restore_database.sh

BACKUP_FILE="$1"
DB_NAME="spider"
DB_USER="spider"
DB_HOST="postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
systemctl stop spider-api

# Drop and recreate database
psql -h $DB_HOST -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h $DB_HOST -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --clean \
  --if-exists \
  --verbose \
  $BACKUP_FILE

# Start application
systemctl start spider-api

echo "Database restored successfully"
```

#### Disaster Recovery Plan

```yaml
# disaster_recovery/plan.yaml
disaster_recovery:
  rto: "4 hours"  # Recovery Time Objective
  rpo: "1 hour"   # Recovery Point Objective
  
  procedures:
    database_failure:
      - stop_application
      - restore_database
      - verify_data_integrity
      - start_application
      - notify_team
    
    application_failure:
      - check_logs
      - restart_services
      - verify_health
      - notify_team
    
    complete_system_failure:
      - activate_backup_site
      - restore_database
      - restore_configuration
      - start_services
      - verify_functionality
      - notify_stakeholders
  
  contacts:
    primary: "admin@example.com"
    secondary: "+1-555-0123"
    escalation: "cto@example.com"
```

## Troubleshooting

### Common Issues

#### High Memory Usage

**Symptoms:**
- Memory usage > 80%
- Application slowdown
- Out of memory errors

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check application memory
curl -s http://localhost:8000/metrics | grep memory
```

**Solutions:**
1. Increase memory limits
2. Optimize data processing
3. Enable memory cleanup
4. Reduce batch sizes

#### Database Connection Issues

**Symptoms:**
- Connection timeout errors
- High connection count
- Slow queries

**Diagnosis:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check connection limits
SHOW max_connections;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Solutions:**
1. Increase connection pool size
2. Optimize queries
3. Add database indexes
4. Scale database horizontally

#### Scraping Failures

**Symptoms:**
- High error rates
- Empty results
- Timeout errors

**Diagnosis:**
```bash
# Check scraper logs
tail -f /var/log/spider/scrapers.log | grep ERROR

# Check scraper metrics
curl -s http://localhost:8000/metrics | grep scraper
```

**Solutions:**
1. Update selectors
2. Adjust rate limits
3. Use different scraping engine
4. Check target website changes

### Log Analysis

#### Log Aggregation

```bash
# Using ELK Stack
curl -X GET "elasticsearch:9200/spider-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"term": {"level": "ERROR"}},
          {"range": {"@timestamp": {"gte": "now-1h"}}}
        ]
      }
    }
  }'
```

#### Performance Analysis

```bash
# Analyze slow queries
grep "slow query" /var/log/spider/spider.log | \
  awk '{print $NF}' | sort | uniq -c | sort -nr

# Analyze error patterns
grep "ERROR" /var/log/spider/spider.log | \
  awk '{print $5}' | sort | uniq -c | sort -nr
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks

```bash
#!/bin/bash
# maintenance/daily_tasks.sh

# Check system health
python -m spider.cli health check

# Clean up old logs
find /var/log/spider -name "*.log" -mtime +7 -delete

# Clean up temporary files
find /tmp -name "spider_*" -mtime +1 -delete

# Check disk space
df -h | awk '$5 > 80 {print $0}'

# Check memory usage
free -h
```

#### Weekly Tasks

```bash
#!/bin/bash
# maintenance/weekly_tasks.sh

# Update database statistics
psql -d spider -c "ANALYZE;"

# Vacuum database
psql -d spider -c "VACUUM ANALYZE;"

# Clean up old data
python -m spider.cli data cleanup --older-than 30d

# Update AI models
python -m spider.cli ai update-models

# Generate reports
python -m spider.cli reports generate --type weekly
```

#### Monthly Tasks

```bash
#!/bin/bash
# maintenance/monthly_tasks.sh

# Full database backup
./backup/backup_database.sh

# Update system packages
apt update && apt upgrade -y

# Rotate encryption keys
python -m spider.cli security rotate-keys

# Performance analysis
python -m spider.cli performance analyze

# Security audit
python -m spider.cli security audit
```

### System Updates

#### Application Updates

```bash
# Update application
git pull origin main
pip install -r requirements.txt
npm install --prefix web/dashboard

# Run database migrations
python -m spider.cli db migrate

# Restart services
systemctl restart spider-api
systemctl restart spider-web
```

#### Configuration Updates

```bash
# Validate configuration
python -m spider.cli config validate

# Apply configuration changes
python -m spider.cli config apply

# Restart services
systemctl reload spider-api
```

### Capacity Planning

#### Resource Monitoring

```bash
# Monitor resource usage
python -m spider.cli monitor resources --duration 24h

# Generate capacity report
python -m spider.cli reports capacity --output capacity_report.pdf
```

#### Scaling Decisions

```yaml
# scaling/thresholds.yaml
scaling:
  cpu:
    scale_up_threshold: 70
    scale_down_threshold: 30
    min_replicas: 2
    max_replicas: 10
  
  memory:
    scale_up_threshold: 80
    scale_down_threshold: 40
    min_replicas: 2
    max_replicas: 10
  
  requests:
    scale_up_threshold: 1000
    scale_down_threshold: 100
    min_replicas: 2
    max_replicas: 20
```

---

## Support

### Emergency Procedures

1. **System Down**: Check logs, restart services, contact team
2. **Data Loss**: Restore from backup, verify integrity
3. **Security Incident**: Isolate system, investigate, patch
4. **Performance Issues**: Scale resources, optimize queries

### Contact Information

- **Primary Admin**: admin@example.com
- **Secondary Admin**: +1-555-0123
- **Emergency**: +1-555-9111
- **Documentation**: https://github.com/Exemplify777/spider/docs

### Resources

- **System Documentation**: `/docs/`
- **Configuration Examples**: `/config/examples/`
- **Monitoring Dashboards**: http://grafana.example.com
- **Log Aggregation**: http://kibana.example.com
