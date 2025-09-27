# SPIDER Framework - Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Cloud Platform Deployment](#cloud-platform-deployment)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Configuration](#security-configuration)
10. [Scaling & Performance](#scaling--performance)
11. [Backup & Recovery](#backup--recovery)
12. [Troubleshooting](#troubleshooting)

## Deployment Overview

SPIDER Framework supports multiple deployment options from local development to enterprise production environments.

### Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX/HAProxy]
    end
    
    subgraph "Application Tier"
        API[FastAPI Application]
        WEB[React Dashboard]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        CACHE[(Memcached)]
    end
    
    subgraph "Storage Tier"
        FS[File System]
        S3[Cloud Storage]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end
    
    LB --> API
    LB --> WEB
    API --> DB
    API --> REDIS
    API --> CACHE
    API --> FS
    API --> S3
    API --> PROM
    PROM --> GRAF
    API --> ELK
```

## Prerequisites

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

### Software Dependencies

#### Required
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher (for web interface)
- **PostgreSQL**: 13 or higher
- **Redis**: 6 or higher

#### Optional
- **Docker**: 20.10 or higher
- **Kubernetes**: 1.21 or higher
- **NGINX**: 1.18 or higher

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/Exemplify777/spider.git
cd spider

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd web/dashboard
npm install
cd ../..

# Run database migrations
python -m spider.cli db migrate

# Start development server
python -m spider.main --config config/local.yaml
```

### Development Configuration

```yaml
# config/local.yaml
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

### Development Services

```bash
# Start PostgreSQL
docker run -d --name postgres-dev \
  -e POSTGRES_DB=spider \
  -e POSTGRES_USER=spider \
  -e POSTGRES_PASSWORD=spider \
  -p 5432:5432 \
  postgres:15

# Start Redis
docker run -d --name redis-dev \
  -p 6379:6379 \
  redis:7-alpine

# Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

## Docker Deployment

### Single Container Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  spider-api:
    image: spider:latest
    ports:
      - "8000:8000"
    environment:
      - SPIDER_DATABASE_URL=postgresql://spider:password@postgres:5432/spider
      - SPIDER_REDIS_URL=redis://redis:6379
      - SPIDER_SECRET_KEY=your-secret-key
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  spider-web:
    image: spider-web:latest
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - spider-api

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: spider
      POSTGRES_USER: spider
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

### Multi-Container Deployment

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
      - SPIDER_DATABASE_URL=${DATABASE_URL}
      - SPIDER_REDIS_URL=${REDIS_URL}
      - SPIDER_SECRET_KEY=${SECRET_KEY}
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

### Docker Build

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 spider && chown -R spider:spider /app
USER spider

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "spider.main", "--config", "config/production.yaml"]
```

## Kubernetes Deployment

### Namespace and ConfigMap

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

### Database Deployment

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

### Application Deployment

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

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: spider-ingress
  namespace: spider
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - example.com
    secretName: spider-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: spider-api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: spider-web
            port:
              number: 80
```

## Cloud Platform Deployment

### AWS Deployment

#### ECS Deployment

```yaml
# aws/ecs-task-definition.json
{
  "family": "spider-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "spider-api",
      "image": "account.dkr.ecr.region.amazonaws.com/spider:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/spider"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/spider",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Lambda Deployment

```yaml
# aws/lambda.yml
service: spider-lambda

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  memorySize: 1024
  timeout: 300
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    REDIS_URL: ${env:REDIS_URL}

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
```

### Azure Deployment

#### Container Instances

```yaml
# azure/container-instance.yml
apiVersion: 2021-07-01
location: eastus
name: spider-api
properties:
  containers:
  - name: spider-api
    properties:
      image: spider.azurecr.io/spider:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: DATABASE_URL
        value: "postgresql://user:pass@postgres-server.postgres.database.azure.com:5432/spider"
      - name: REDIS_URL
        value: "redis://redis-server.redis.cache.windows.net:6380"
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
    dnsNameLabel: spider-api
```

### Google Cloud Deployment

#### Cloud Run

```yaml
# gcp/cloud-run.yml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: spider-api
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/project-id/spider:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@/spider?host=/cloudsql/project-id:region:instance"
        - name: REDIS_URL
          value: "redis://redis-ip:6379"
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

## Production Deployment

### Production Checklist

- [ ] **Infrastructure**
  - [ ] Load balancer configured
  - [ ] SSL certificates installed
  - [ ] Database cluster setup
  - [ ] Redis cluster setup
  - [ ] Monitoring stack deployed

- [ ] **Security**
  - [ ] Firewall rules configured
  - [ ] SSL/TLS enabled
  - [ ] Authentication configured
  - [ ] Authorization rules set
  - [ ] Secrets management setup

- [ ] **Performance**
  - [ ] Caching enabled
  - [ ] CDN configured
  - [ ] Database optimized
  - [ ] Resource limits set
  - [ ] Auto-scaling configured

- [ ] **Monitoring**
  - [ ] Logging configured
  - [ ] Metrics collection enabled
  - [ ] Alerting rules set
  - [ ] Dashboards created
  - [ ] Health checks configured

### Production Configuration

```yaml
# config/production.yaml
database:
  url: "${SPIDER_DATABASE_URL}"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  echo: false
  connect_args:
    sslmode: "require"
    connect_timeout: 10

redis:
  url: "${SPIDER_REDIS_URL}"
  cluster_mode: true
  connection_pool:
    max_connections: 100
    retry_on_timeout: true

security:
  secret_key: "${SPIDER_SECRET_KEY}"
  jwt_secret: "${SPIDER_JWT_SECRET}"
  encryption_key: "${SPIDER_ENCRYPTION_KEY}"
  session_timeout: 3600
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 200

monitoring:
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"
  grafana:
    enabled: true
    url: "${SPIDER_GRAFANA_URL}"
  logging:
    level: "INFO"
    format: "json"
    file: "/var/log/spider/spider.log"
    max_size: "100MB"
    max_files: 10
    compress: true

performance:
  worker_processes: 4
  worker_threads: 8
  max_memory_usage: "2GB"
  cache_size: "512MB"
  connection_pool_size: 100
```

## Monitoring & Observability

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

### Grafana Dashboards

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
      }
    ]
  }
}
```

## Security Configuration

### SSL/TLS Setup

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/ssl/certs/spider.crt;
    ssl_certificate_key /etc/ssl/private/spider.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://spider-api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Rules

```bash
# iptables rules
# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow PostgreSQL (restrict to internal network)
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT

# Allow Redis (restrict to internal network)
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/8 -j ACCEPT

# Drop all other traffic
iptables -A INPUT -j DROP
```

## Scaling & Performance

### Horizontal Scaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: spider-api-hpa
  namespace: spider
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: spider-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

```yaml
# k8s/vertical-pod-autoscaler.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: spider-api-vpa
  namespace: spider
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: spider-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: spider-api
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
```

## Backup & Recovery

### Database Backup

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

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
```

### Application Backup

```bash
#!/bin/bash
# backup/backup_application.sh

BACKUP_DIR="/backups/spider"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration
cp -r /etc/spider $BACKUP_DIR/config_$DATE

# Backup data
cp -r /var/lib/spider $BACKUP_DIR/data_$DATE

# Backup logs
cp -r /var/log/spider $BACKUP_DIR/logs_$DATE

# Compress backup
tar -czf $BACKUP_DIR/spider_backup_$DATE.tar.gz -C $BACKUP_DIR config_$DATE data_$DATE logs_$DATE

# Cleanup
rm -rf $BACKUP_DIR/config_$DATE $BACKUP_DIR/data_$DATE $BACKUP_DIR/logs_$DATE
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check application memory
curl -s http://localhost:8000/metrics | grep memory
```

#### Database Connection Issues
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

#### Scraping Failures
```bash
# Check scraper logs
tail -f /var/log/spider/scrapers.log | grep ERROR

# Check scraper metrics
curl -s http://localhost:8000/metrics | grep scraper
```

### Debug Mode

```bash
# Enable debug mode
export SPIDER_DEBUG=true

# Or use command line flag
python -m spider.main --debug
```

### Log Analysis

```bash
# View recent logs
tail -f logs/spider.log

# Search for errors
grep "ERROR" logs/spider.log

# Analyze performance
grep "PERFORMANCE" logs/spider.log | jq
```

---

## Support

For deployment support:
- **Documentation**: [github.com/Exemplify777/spider/docs](https://github.com/Exemplify777/spider/docs)
- **Deployment Examples**: `/deployment/examples/`