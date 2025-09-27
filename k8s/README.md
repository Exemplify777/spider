# SPIDER Framework - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the SPIDER framework in a production environment.

## Overview

The SPIDER framework is designed to be cloud-native and can be deployed on Kubernetes clusters. This directory provides all necessary manifests for a complete deployment including:

- Core application components
- Database and caching layers
- Monitoring and observability
- Security and compliance
- Backup and disaster recovery
- Auto-scaling and performance optimization

## Prerequisites

Before deploying SPIDER on Kubernetes, ensure you have:

1. **Kubernetes cluster** (v1.20+) running
2. **kubectl** configured to access your cluster
3. **Helm** (optional, for advanced deployments)
4. **Persistent storage** provisioner available
5. **Load balancer** or **Ingress controller** configured
6. **Monitoring stack** (Prometheus, Grafana) if using monitoring features

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Secrets

```bash
kubectl apply -f secrets.yaml
```

### 3. Create ConfigMap

```bash
kubectl apply -f configmap.yaml
```

### 4. Deploy Database

```bash
kubectl apply -f postgres.yaml
```

### 5. Deploy Redis

```bash
kubectl apply -f redis.yaml
```

### 6. Deploy Memcached

```bash
kubectl apply -f memcached.yaml
```

### 7. Deploy SPIDER Application

```bash
kubectl apply -f spider-app.yaml
```

### 8. Deploy Services

```bash
kubectl apply -f service.yaml
```

### 9. Deploy Ingress

```bash
kubectl apply -f ingress.yaml
```

### 10. Deploy Monitoring (Optional)

```bash
kubectl apply -f monitoring.yaml
```

## File Descriptions

### Core Application

- **`spider-app.yaml`** - Main SPIDER application deployment
- **`service.yaml`** - Kubernetes services for the application
- **`ingress.yaml`** - Ingress configuration for external access

### Database and Storage

- **`postgres.yaml`** - PostgreSQL database deployment
- **`redis.yaml`** - Redis cache deployment
- **`memcached.yaml`** - Memcached cache deployment
- **`pvc.yaml`** - Persistent Volume Claims for data storage

### Configuration

- **`namespace.yaml`** - Kubernetes namespace for SPIDER
- **`configmap.yaml`** - Application configuration
- **`secrets.yaml`** - Sensitive configuration data

### Monitoring and Observability

- **`monitoring.yaml`** - Prometheus and Grafana deployment
- **`performance.yaml`** - Performance monitoring configuration

### Security

- **`security.yaml`** - Security policies and configurations

### Scaling and Performance

- **`autoscaling.yaml`** - Horizontal Pod Autoscaler configuration
- **`hpa.yaml`** - Additional HPA configurations
- **`performance.yaml`** - Performance optimization settings

### Backup and Recovery

- **`backup.yaml`** - Backup and disaster recovery configuration

## Configuration

### Environment Variables

Key environment variables can be configured in `configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spider-config
data:
  DATABASE_URL: "postgresql://spider:password@postgres:5432/spider"
  REDIS_URL: "redis://redis:6379"
  MEMCACHED_URL: "memcached://memcached:11211"
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  MAX_CONNECTIONS: "100"
```

### Secrets

Sensitive data should be stored in `secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spider-secrets
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  JWT_SECRET: <base64-encoded-jwt-secret>
  ENCRYPTION_KEY: <base64-encoded-encryption-key>
```

## Scaling

### Horizontal Pod Autoscaling

The application supports horizontal pod autoscaling based on CPU and memory usage:

```bash
kubectl apply -f autoscaling.yaml
```

### Manual Scaling

Scale the application manually:

```bash
kubectl scale deployment spider-app --replicas=5
```

## Monitoring

### Prometheus Metrics

The application exposes Prometheus metrics on `/metrics` endpoint.

### Grafana Dashboards

Grafana dashboards are available for monitoring:
- Application metrics
- System resources
- Database performance
- Cache performance
- Error rates and response times

## Security

### Network Policies

Network policies restrict traffic between pods:

```bash
kubectl apply -f security.yaml
```

### RBAC

Role-Based Access Control is configured for:
- Service accounts
- Cluster roles
- Role bindings

### Pod Security

Pod security policies enforce:
- Non-root containers
- Read-only root filesystems
- Resource limits
- Security contexts

## Backup and Recovery

### Automated Backups

Backups are configured to run automatically:

```bash
kubectl apply -f backup.yaml
```

### Manual Backup

Create a manual backup:

```bash
kubectl exec -it spider-app-0 -- python -m spider.cli backup create
```

### Restore from Backup

Restore from a backup:

```bash
kubectl exec -it spider-app-0 -- python -m spider.cli backup restore <backup-id>
```

## Troubleshooting

### Common Issues

1. **Pod not starting**: Check logs and resource limits
2. **Database connection issues**: Verify database service and credentials
3. **Memory issues**: Adjust resource limits and HPA settings
4. **Storage issues**: Check PVC status and storage class

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n spider

# Check pod logs
kubectl logs -f deployment/spider-app -n spider

# Check service status
kubectl get services -n spider

# Check ingress status
kubectl get ingress -n spider

# Check persistent volumes
kubectl get pvc -n spider

# Check secrets
kubectl get secrets -n spider

# Check configmaps
kubectl get configmaps -n spider
```

### Logs

View application logs:

```bash
kubectl logs -f deployment/spider-app -n spider
```

View database logs:

```bash
kubectl logs -f deployment/postgres -n spider
```

View Redis logs:

```bash
kubectl logs -f deployment/redis -n spider
```

## Production Considerations

### Resource Requirements

Minimum resource requirements:
- **CPU**: 2 cores per pod
- **Memory**: 4GB per pod
- **Storage**: 100GB for database, 50GB for application

### High Availability

For high availability:
- Deploy multiple replicas
- Use anti-affinity rules
- Configure pod disruption budgets
- Set up health checks

### Performance Optimization

- Use resource requests and limits
- Configure horizontal pod autoscaling
- Optimize database connections
- Use caching effectively
- Monitor performance metrics

### Security Hardening

- Use non-root containers
- Implement network policies
- Enable RBAC
- Use secrets for sensitive data
- Regular security updates

## Customization

### Custom Configuration

Modify `configmap.yaml` for custom configuration:

```yaml
data:
  CUSTOM_SETTING: "value"
  ANOTHER_SETTING: "another_value"
```

### Custom Resources

Adjust resource limits in `spider-app.yaml`:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Custom Ingress

Modify `ingress.yaml` for custom routing:

```yaml
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: spider-service
            port:
              number: 8000
```

## Support

For issues with Kubernetes deployment:

1. Check the troubleshooting section
2. Review Kubernetes logs
3. Check resource usage
4. Verify configuration
5. Create a GitHub issue

## License

These Kubernetes manifests are part of the SPIDER framework and are subject to the same license terms.
