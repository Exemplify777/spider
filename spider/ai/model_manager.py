"""
Model Manager

Comprehensive model management system for deployment, monitoring,
and lifecycle management of ML models in the SPIDER framework.

Author: SPIDER Development Team
Version: 1.0.0
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from .model_registry import ModelRegistry, ModelType, ModelStatus, ModelMetadata

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    UPDATING = "updating"
    ROLLING_BACK = "rolling_back"
    STOPPED = "stopped"


class MonitoringMetric(str, Enum):
    """Monitoring metric enumeration."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    MSE = "mse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    PREDICTION_LATENCY = "prediction_latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


@dataclass
class DeploymentConfig:
    """Model deployment configuration."""
    model_id: str
    model_version: str
    deployment_name: str
    endpoint_url: str
    replicas: int = 1
    cpu_limit: str = "1000m"
    memory_limit: str = "1Gi"
    auto_scaling: bool = True
    min_replicas: int = 1
    max_replicas: int = 10
    health_check_interval: int = 30
    timeout: int = 30
    environment_variables: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentInfo:
    """Model deployment information."""
    deployment_id: str
    model_id: str
    model_version: str
    deployment_name: str
    endpoint_url: str
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
    replicas: int
    healthy_replicas: int
    config: DeploymentConfig
    metrics: Dict[str, float] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_id: str
    model_version: str
    timestamp: datetime
    metric_name: MonitoringMetric
    value: float
    threshold: Optional[float] = None
    is_alert: bool = False
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelAlert:
    """Model performance alert."""
    alert_id: str
    model_id: str
    model_version: str
    metric_name: MonitoringMetric
    current_value: float
    threshold_value: float
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ModelDeployment:
    """Model deployment manager."""
    
    def __init__(self, registry: ModelRegistry = None):
        """
        Initialize model deployment manager.
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry or ModelRegistry()
        self.deployments: Dict[str, DeploymentInfo] = {}
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self._load_deployments()
    
    def _load_deployments(self):
        """Load existing deployments from storage."""
        # In a real implementation, this would load from persistent storage
        pass
    
    def _save_deployments(self):
        """Save deployments to storage."""
        # In a real implementation, this would save to persistent storage
        pass
    
    def deploy_model(self, config: DeploymentConfig) -> str:
        """
        Deploy a model.
        
        Args:
            config: Deployment configuration
            
        Returns:
            Deployment ID
        """
        deployment_id = f"{config.model_id}_{config.model_version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create deployment info
        deployment_info = DeploymentInfo(
            deployment_id=deployment_id,
            model_id=config.model_id,
            model_version=config.model_version,
            deployment_name=config.deployment_name,
            endpoint_url=config.endpoint_url,
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            replicas=config.replicas,
            healthy_replicas=0,
            config=config
        )
        
        # Store deployment
        self.deployments[deployment_id] = deployment_info
        self.deployment_configs[deployment_id] = config
        
        # Start deployment process
        asyncio.create_task(self._deploy_model_async(deployment_id))
        
        logger.info(f"Started deployment of model {config.model_id} v{config.model_version}")
        return deployment_id
    
    async def _deploy_model_async(self, deployment_id: str):
        """Asynchronous model deployment."""
        deployment = self.deployments[deployment_id]
        deployment.status = DeploymentStatus.DEPLOYING
        deployment.updated_at = datetime.utcnow()
        
        try:
            # Simulate deployment process
            await asyncio.sleep(5)  # Simulate deployment time
            
            # Update status
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.healthy_replicas = deployment.replicas
            deployment.last_health_check = datetime.utcnow()
            deployment.updated_at = datetime.utcnow()
            
            logger.info(f"Successfully deployed model {deployment.model_id} v{deployment.model_version}")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.errors.append(str(e))
            deployment.updated_at = datetime.utcnow()
            logger.error(f"Failed to deploy model {deployment.model_id} v{deployment.model_version}: {e}")
        
        self._save_deployments()
    
    def update_deployment(self, deployment_id: str, new_config: DeploymentConfig) -> bool:
        """
        Update a model deployment.
        
        Args:
            deployment_id: Deployment ID
            new_config: New deployment configuration
            
        Returns:
            True if successful
        """
        if deployment_id not in self.deployments:
            return False
        
        deployment = self.deployments[deployment_id]
        deployment.status = DeploymentStatus.UPDATING
        deployment.updated_at = datetime.utcnow()
        
        # Update configuration
        deployment.config = new_config
        self.deployment_configs[deployment_id] = new_config
        
        # Start update process
        asyncio.create_task(self._update_deployment_async(deployment_id))
        
        return True
    
    async def _update_deployment_async(self, deployment_id: str):
        """Asynchronous deployment update."""
        deployment = self.deployments[deployment_id]
        
        try:
            # Simulate update process
            await asyncio.sleep(3)
            
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.updated_at = datetime.utcnow()
            
            logger.info(f"Successfully updated deployment {deployment_id}")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.errors.append(str(e))
            deployment.updated_at = datetime.utcnow()
            logger.error(f"Failed to update deployment {deployment_id}: {e}")
        
        self._save_deployments()
    
    def stop_deployment(self, deployment_id: str) -> bool:
        """
        Stop a model deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            True if successful
        """
        if deployment_id not in self.deployments:
            return False
        
        deployment = self.deployments[deployment_id]
        deployment.status = DeploymentStatus.STOPPED
        deployment.healthy_replicas = 0
        deployment.updated_at = datetime.utcnow()
        
        self._save_deployments()
        logger.info(f"Stopped deployment {deployment_id}")
        return True
    
    def get_deployment(self, deployment_id: str) -> Optional[DeploymentInfo]:
        """Get deployment information."""
        return self.deployments.get(deployment_id)
    
    def list_deployments(self, model_id: str = None) -> List[DeploymentInfo]:
        """List deployments."""
        deployments = list(self.deployments.values())
        
        if model_id:
            deployments = [d for d in deployments if d.model_id == model_id]
        
        return sorted(deployments, key=lambda d: d.created_at, reverse=True)
    
    def health_check(self, deployment_id: str) -> bool:
        """
        Perform health check on deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            True if healthy
        """
        if deployment_id not in self.deployments:
            return False
        
        deployment = self.deployments[deployment_id]
        
        # Simulate health check
        is_healthy = deployment.status == DeploymentStatus.DEPLOYED
        
        if is_healthy:
            deployment.healthy_replicas = deployment.replicas
        else:
            deployment.healthy_replicas = 0
        
        deployment.last_health_check = datetime.utcnow()
        self._save_deployments()
        
        return is_healthy


class ModelMonitoring:
    """Model performance monitoring."""
    
    def __init__(self, registry: ModelRegistry = None):
        """
        Initialize model monitoring.
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry or ModelRegistry()
        self.performance_history: List[ModelPerformance] = []
        self.alerts: List[ModelAlert] = []
        self.metric_thresholds: Dict[MonitoringMetric, float] = {
            MonitoringMetric.ACCURACY: 0.8,
            MonitoringMetric.PRECISION: 0.8,
            MonitoringMetric.RECALL: 0.8,
            MonitoringMetric.F1_SCORE: 0.8,
            MonitoringMetric.MSE: 1.0,
            MonitoringMetric.MAE: 1.0,
            MonitoringMetric.R2_SCORE: 0.7,
            MonitoringMetric.PREDICTION_LATENCY: 1000.0,  # milliseconds
            MonitoringMetric.THROUGHPUT: 100.0,  # requests per minute
            MonitoringMetric.ERROR_RATE: 0.05,
            MonitoringMetric.MEMORY_USAGE: 0.8,  # 80%
            MonitoringMetric.CPU_USAGE: 0.8,  # 80%
        }
    
    def record_metric(self, model_id: str, model_version: str, 
                     metric_name: MonitoringMetric, value: float,
                     context: Dict[str, Any] = None) -> None:
        """
        Record a performance metric.
        
        Args:
            model_id: Model ID
            model_version: Model version
            metric_name: Metric name
            value: Metric value
            context: Additional context
        """
        performance = ModelPerformance(
            model_id=model_id,
            model_version=model_version,
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            value=value,
            threshold=self.metric_thresholds.get(metric_name),
            is_alert=self._check_alert(metric_name, value),
            context=context or {}
        )
        
        self.performance_history.append(performance)
        
        # Check for alerts
        if performance.is_alert:
            self._create_alert(performance)
        
        # Keep only last 1000 records per model
        self._cleanup_history(model_id)
    
    def _check_alert(self, metric_name: MonitoringMetric, value: float) -> bool:
        """Check if metric value triggers an alert."""
        threshold = self.metric_thresholds.get(metric_name)
        if threshold is None:
            return False
        
        # For metrics where higher is better
        if metric_name in [MonitoringMetric.ACCURACY, MonitoringMetric.PRECISION, 
                          MonitoringMetric.RECALL, MonitoringMetric.F1_SCORE, 
                          MonitoringMetric.R2_SCORE, MonitoringMetric.THROUGHPUT]:
            return value < threshold
        
        # For metrics where lower is better
        else:
            return value > threshold
    
    def _create_alert(self, performance: ModelPerformance) -> None:
        """Create an alert for performance issue."""
        alert_id = f"{performance.model_id}_{performance.metric_name.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine severity
        threshold = performance.threshold or 0
        deviation = abs(performance.value - threshold) / threshold if threshold != 0 else 0
        
        if deviation > 0.5:
            severity = "critical"
        elif deviation > 0.3:
            severity = "high"
        elif deviation > 0.1:
            severity = "medium"
        else:
            severity = "low"
        
        alert = ModelAlert(
            alert_id=alert_id,
            model_id=performance.model_id,
            model_version=performance.model_version,
            metric_name=performance.metric_name,
            current_value=performance.value,
            threshold_value=threshold,
            severity=severity,
            message=f"{performance.metric_name.value} is {performance.value:.3f}, threshold is {threshold:.3f}",
            timestamp=datetime.utcnow()
        )
        
        self.alerts.append(alert)
        logger.warning(f"Created alert for model {performance.model_id}: {alert.message}")
    
    def _cleanup_history(self, model_id: str) -> None:
        """Clean up old performance history."""
        model_records = [p for p in self.performance_history if p.model_id == model_id]
        if len(model_records) > 1000:
            # Keep only the most recent 1000 records
            model_records.sort(key=lambda p: p.timestamp, reverse=True)
            records_to_keep = model_records[:1000]
            
            # Remove old records
            self.performance_history = [
                p for p in self.performance_history 
                if p.model_id != model_id or p in records_to_keep
            ]
    
    def get_performance_history(self, model_id: str, 
                               metric_name: MonitoringMetric = None,
                               hours: int = 24) -> List[ModelPerformance]:
        """
        Get performance history for a model.
        
        Args:
            model_id: Model ID
            metric_name: Specific metric (optional)
            hours: Number of hours to look back
            
        Returns:
            List of performance records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        records = [
            p for p in self.performance_history
            if p.model_id == model_id and p.timestamp >= cutoff_time
        ]
        
        if metric_name:
            records = [p for p in records if p.metric_name == metric_name]
        
        return sorted(records, key=lambda p: p.timestamp)
    
    def get_active_alerts(self, model_id: str = None) -> List[ModelAlert]:
        """Get active alerts."""
        alerts = [a for a in self.alerts if not a.resolved]
        
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Resolved alert {alert_id}")
                return True
        
        return False
    
    def set_metric_threshold(self, metric_name: MonitoringMetric, threshold: float) -> None:
        """Set threshold for a metric."""
        self.metric_thresholds[metric_name] = threshold
        logger.info(f"Set threshold for {metric_name.value} to {threshold}")
    
    def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """Get overall model health."""
        recent_records = self.get_performance_history(model_id, hours=1)
        active_alerts = self.get_active_alerts(model_id)
        
        health_score = 100.0
        
        # Deduct points for alerts
        for alert in active_alerts:
            if alert.severity == "critical":
                health_score -= 20
            elif alert.severity == "high":
                health_score -= 10
            elif alert.severity == "medium":
                health_score -= 5
            else:
                health_score -= 2
        
        # Ensure health score doesn't go below 0
        health_score = max(0, health_score)
        
        return {
            "model_id": model_id,
            "health_score": health_score,
            "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
            "active_alerts": len(active_alerts),
            "recent_metrics": len(recent_records),
            "last_updated": datetime.utcnow()
        }


class ModelManager:
    """Main model manager combining all capabilities."""
    
    def __init__(self, registry: ModelRegistry = None):
        """
        Initialize model manager.
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry or ModelRegistry()
        self.deployment = ModelDeployment(registry)
        self.monitoring = ModelMonitoring(registry)
    
    async def deploy_model(self, model_id: str, model_version: str = None,
                          deployment_name: str = None,
                          endpoint_url: str = None,
                          replicas: int = 1) -> str:
        """
        Deploy a model.
        
        Args:
            model_id: Model ID
            model_version: Model version (latest if None)
            deployment_name: Deployment name
            endpoint_url: Endpoint URL
            replicas: Number of replicas
            
        Returns:
            Deployment ID
        """
        # Get model metadata
        metadata = self.registry.get_model_metadata(model_id, model_version)
        if not metadata:
            raise ValueError(f"Model {model_id} not found")
        
        # Generate deployment name if not provided
        if not deployment_name:
            deployment_name = f"{metadata.name}-{metadata.version}"
        
        # Generate endpoint URL if not provided
        if not endpoint_url:
            endpoint_url = f"http://localhost:8000/models/{model_id}/{metadata.version}"
        
        # Create deployment configuration
        config = DeploymentConfig(
            model_id=model_id,
            model_version=metadata.version,
            deployment_name=deployment_name,
            endpoint_url=endpoint_url,
            replicas=replicas
        )
        
        # Deploy model
        deployment_id = self.deployment.deploy_model(config)
        
        # Update model status
        self.registry.update_model_status(model_id, metadata.version, ModelStatus.DEPLOYED)
        
        return deployment_id
    
    def stop_model(self, deployment_id: str) -> bool:
        """Stop a model deployment."""
        deployment = self.deployment.get_deployment(deployment_id)
        if not deployment:
            return False
        
        success = self.deployment.stop_deployment(deployment_id)
        
        if success:
            # Update model status
            self.registry.update_model_status(
                deployment.model_id, 
                deployment.model_version, 
                ModelStatus.TRAINED
            )
        
        return success
    
    def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive model status."""
        metadata = self.registry.get_model_metadata(model_id)
        if not metadata:
            return {"error": "Model not found"}
        
        deployments = self.deployment.list_deployments(model_id)
        health = self.monitoring.get_model_health(model_id)
        
        return {
            "model_info": {
                "model_id": model_id,
                "name": metadata.name,
                "version": metadata.version,
                "status": metadata.status.value,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat()
            },
            "deployments": [
                {
                    "deployment_id": d.deployment_id,
                    "status": d.status.value,
                    "endpoint_url": d.endpoint_url,
                    "replicas": d.replicas,
                    "healthy_replicas": d.healthy_replicas,
                    "created_at": d.created_at.isoformat()
                }
                for d in deployments
            ],
            "health": health,
            "performance_history": len(self.monitoring.get_performance_history(model_id)),
            "active_alerts": len(self.monitoring.get_active_alerts(model_id))
        }
    
    def list_models(self, status: ModelStatus = None) -> List[Dict[str, Any]]:
        """List all models with their status."""
        models = self.registry.list_models(status=status)
        
        result = []
        for model in models:
            health = self.monitoring.get_model_health(model.model_id)
            deployments = self.deployment.list_deployments(model.model_id)
            
            result.append({
                "model_id": model.model_id,
                "name": model.name,
                "version": model.version,
                "status": model.status.value,
                "model_type": model.model_type.value,
                "created_at": model.created_at.isoformat(),
                "health_score": health["health_score"],
                "deployments": len(deployments),
                "active_alerts": health["active_alerts"]
            })
        
        return result
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        registry_stats = self.registry.get_registry_stats()
        deployments = self.deployment.list_deployments()
        
        return {
            **registry_stats,
            "total_deployments": len(deployments),
            "active_deployments": len([d for d in deployments if d.status == DeploymentStatus.DEPLOYED]),
            "total_alerts": len(self.monitoring.alerts),
            "active_alerts": len(self.monitoring.get_active_alerts())
        }
