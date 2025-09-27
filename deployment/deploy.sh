#!/bin/bash

# SPIDER Framework Production Deployment Script
# Version: 2.0.0
# Description: Complete production deployment for SPIDER Framework

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="spider"
APP_NAME="spider"
VERSION="2.0.0"
ENVIRONMENT="production"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check if helm is installed (optional)
    if ! command -v helm &> /dev/null; then
        log_warning "Helm is not installed. Some features may not be available."
    fi
    
    log_success "Prerequisites check completed"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f deployment/kubernetes/namespace.yaml
        log_success "Namespace $NAMESPACE created"
    fi
}

deploy_database() {
    log_info "Deploying PostgreSQL database..."
    kubectl apply -f deployment/kubernetes/postgres.yaml
    kubectl wait --for=condition=ready pod -l app=spider,component=database -n "$NAMESPACE" --timeout=300s
    log_success "PostgreSQL database deployed"
}

deploy_cache() {
    log_info "Deploying Redis cache..."
    kubectl apply -f deployment/kubernetes/redis.yaml
    kubectl wait --for=condition=ready pod -l app=spider,component=cache -n "$NAMESPACE" --timeout=300s
    log_success "Redis cache deployed"
    
    log_info "Deploying Memcached cache..."
    kubectl apply -f deployment/kubernetes/memcached.yaml
    kubectl wait --for=condition=ready pod -l app=spider,component=memcached -n "$NAMESPACE" --timeout=300s
    log_success "Memcached cache deployed"
}

deploy_application() {
    log_info "Deploying SPIDER application..."
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/secrets.yaml
    kubectl apply -f deployment/kubernetes/spider-app.yaml
    kubectl wait --for=condition=ready pod -l app=spider,component=application -n "$NAMESPACE" --timeout=600s
    log_success "SPIDER application deployed"
}

deploy_ingress() {
    log_info "Deploying ingress configuration..."
    kubectl apply -f deployment/kubernetes/ingress.yaml
    log_success "Ingress configuration deployed"
}

deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    kubectl apply -f deployment/kubernetes/monitoring.yaml
    log_success "Monitoring stack deployed"
}

run_database_migration() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    kubectl wait --for=condition=ready pod -l app=spider,component=database -n "$NAMESPACE" --timeout=300s
    
    # Run migrations
    kubectl run spider-migration --image=spider:2.0.0 --rm -i --restart=Never -n "$NAMESPACE" -- \
        python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if all pods are running
    local pods_ready
    pods_ready=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
    local total_pods
    total_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
    
    if [ "$pods_ready" -eq "$total_pods" ]; then
        log_success "All pods are running and ready"
    else
        log_error "Some pods are not ready. Please check the status."
        kubectl get pods -n "$NAMESPACE"
        exit 1
    fi
    
    # Check if services are available
    if kubectl get service spider-service -n "$NAMESPACE" &> /dev/null; then
        log_success "SPIDER service is available"
    else
        log_error "SPIDER service is not available"
        exit 1
    fi
    
    # Check if ingress is configured
    if kubectl get ingress spider-ingress -n "$NAMESPACE" &> /dev/null; then
        log_success "Ingress is configured"
    else
        log_warning "Ingress is not configured"
    fi
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "  Namespace: $NAMESPACE"
    echo "  Application: $APP_NAME"
    echo "  Version: $VERSION"
    echo "  Environment: $ENVIRONMENT"
    echo ""
    
    log_info "Services:"
    kubectl get services -n "$NAMESPACE"
    echo ""
    
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE"
    echo ""
    
    log_info "Ingress:"
    kubectl get ingress -n "$NAMESPACE"
    echo ""
    
    log_info "To access the application:"
    echo "  kubectl port-forward -n $NAMESPACE service/spider-service 8000:8000"
    echo "  Then open http://localhost:8000 in your browser"
    echo ""
    
    log_info "To view logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=spider,component=application -f"
    echo ""
    
    log_info "To scale the application:"
    echo "  kubectl scale deployment spider-app -n $NAMESPACE --replicas=5"
}

cleanup_deployment() {
    log_info "Cleaning up deployment..."
    
    kubectl delete -f deployment/kubernetes/ingress.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/monitoring.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/spider-app.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/memcached.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/redis.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/postgres.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/secrets.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/configmap.yaml --ignore-not-found=true
    kubectl delete -f deployment/kubernetes/namespace.yaml --ignore-not-found=true
    
    log_success "Deployment cleaned up"
}

# Main deployment function
deploy() {
    log_info "Starting SPIDER Framework deployment..."
    log_info "Version: $VERSION"
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    echo ""
    
    check_prerequisites
    create_namespace
    deploy_database
    deploy_cache
    deploy_application
    run_database_migration
    deploy_ingress
    deploy_monitoring
    verify_deployment
    show_deployment_info
    
    log_success "SPIDER Framework deployment completed successfully!"
}

# Main script
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    cleanup)
        cleanup_deployment
        ;;
    verify)
        verify_deployment
        ;;
    info)
        show_deployment_info
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|verify|info}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy SPIDER Framework to Kubernetes"
        echo "  cleanup  - Remove SPIDER Framework from Kubernetes"
        echo "  verify   - Verify deployment status"
        echo "  info     - Show deployment information"
        exit 1
        ;;
esac
