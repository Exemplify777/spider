"""
Cost Optimization and Resource Management

This module provides comprehensive cost optimization and resource management capabilities
for the SPIDER Framework in production environments.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path
import statistics

import aiohttp
import aiofiles
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import boto3
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from google.cloud import billing_v1
from google.cloud import compute_v1

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Resource types"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    COMPUTE = "compute"


class OptimizationAction(Enum):
    """Optimization actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    TERMINATE = "terminate"
    RESIZE = "resize"
    MIGRATE = "migrate"
    SCHEDULE = "schedule"


@dataclass
class ResourceUsage:
    """Resource usage data"""
    resource_type: ResourceType
    current_usage: float
    capacity: float
    utilization_percent: float
    cost_per_hour: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation"""
    id: str
    title: str
    description: str
    resource_type: ResourceType
    action: OptimizationAction
    current_cost: float
    potential_savings: float
    confidence: float
    implementation_effort: str  # low, medium, high
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CostOptimizationConfig:
    """Cost optimization configuration"""
    aws_region: str = "us-west-2"
    azure_subscription_id: str = ""
    gcp_project_id: str = ""
    cost_threshold_percent: float = 80.0
    utilization_threshold_percent: float = 70.0
    optimization_interval: int = 3600  # seconds
    cost_analysis_window: int = 24  # hours
    enabled_optimizations: List[str] = field(default_factory=lambda: [
        "right_sizing", "scheduling", "reserved_instances", "spot_instances"
    ])
    notification_webhook: Optional[str] = None


class CostOptimizer:
    """
    Cost optimization and resource management system
    """
    
    def __init__(self, config: CostOptimizationConfig):
        self.config = config
        self.resource_usage: Dict[str, ResourceUsage] = {}
        self.recommendations: Dict[str, CostOptimizationRecommendation] = {}
        self.cost_history: List[Dict[str, Any]] = []
        self.running = False
        self.optimization_tasks: List[asyncio.Task] = []
        
        # Initialize cloud clients
        self._initialize_cloud_clients()
    
    def _initialize_cloud_clients(self):
        """Initialize cloud provider clients"""
        # AWS clients
        try:
            self.aws_ec2 = boto3.client('ec2', region_name=self.config.aws_region)
            self.aws_cloudwatch = boto3.client('cloudwatch', region_name=self.config.aws_region)
            self.aws_ce = boto3.client('ce', region_name=self.config.aws_region)
        except Exception as e:
            logger.warning(f"AWS clients not available: {e}")
            self.aws_ec2 = None
            self.aws_cloudwatch = None
            self.aws_ce = None
        
        # Azure clients
        try:
            if self.config.azure_subscription_id:
                self.azure_resource_client = ResourceManagementClient(
                    credential=None,  # Use default credential
                    subscription_id=self.config.azure_subscription_id
                )
                self.azure_compute_client = ComputeManagementClient(
                    credential=None,  # Use default credential
                    subscription_id=self.config.azure_subscription_id
                )
            else:
                self.azure_resource_client = None
                self.azure_compute_client = None
        except Exception as e:
            logger.warning(f"Azure clients not available: {e}")
            self.azure_resource_client = None
            self.azure_compute_client = None
        
        # GCP clients
        try:
            if self.config.gcp_project_id:
                self.gcp_billing_client = billing_v1.CloudBillingClient()
                self.gcp_compute_client = compute_v1.InstancesClient()
            else:
                self.gcp_billing_client = None
                self.gcp_compute_client = None
        except Exception as e:
            logger.warning(f"GCP clients not available: {e}")
            self.gcp_billing_client = None
            self.gcp_compute_client = None
    
    async def start_cost_optimization(self):
        """Start the cost optimization system"""
        if self.running:
            logger.warning("Cost optimization is already running")
            return
        
        self.running = True
        logger.info("Starting cost optimization system")
        
        # Start optimization tasks
        self.optimization_tasks = [
            asyncio.create_task(self._collect_resource_usage()),
            asyncio.create_task(self._analyze_costs()),
            asyncio.create_task(self._generate_recommendations()),
            asyncio.create_task(self._apply_optimizations()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.optimization_tasks)
        except Exception as e:
            logger.error(f"Error in optimization tasks: {e}")
        finally:
            self.running = False
    
    async def stop_cost_optimization(self):
        """Stop the cost optimization system"""
        if not self.running:
            return
        
        logger.info("Stopping cost optimization system")
        self.running = False
        
        # Cancel all optimization tasks
        for task in self.optimization_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.optimization_tasks, return_exceptions=True)
    
    async def _collect_resource_usage(self):
        """Collect resource usage data"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Collect Kubernetes resource usage
                await self._collect_kubernetes_usage(current_time)
                
                # Collect AWS resource usage
                await self._collect_aws_usage(current_time)
                
                # Collect Azure resource usage
                await self._collect_azure_usage(current_time)
                
                # Collect GCP resource usage
                await self._collect_gcp_usage(current_time)
                
            except Exception as e:
                logger.error(f"Error collecting resource usage: {e}")
            
            await asyncio.sleep(self.config.optimization_interval)
    
    async def _collect_kubernetes_usage(self, timestamp: datetime):
        """Collect Kubernetes resource usage"""
        try:
            # Load Kubernetes client
            config.load_incluster_config()
            k8s_client = client.CoreV1Api()
            k8s_metrics_client = client.CustomObjectsApi()
            
            # Get pod resource usage
            pods = k8s_client.list_namespaced_pod(namespace="spider")
            
            for pod in pods.items:
                if pod.status.phase == "Running":
                    # Get CPU usage
                    cpu_usage = await self._get_pod_cpu_usage(k8s_metrics_client, pod.metadata.name)
                    if cpu_usage is not None:
                        self._add_resource_usage(
                            f"pod_{pod.metadata.name}_cpu",
                            ResourceType.CPU,
                            cpu_usage,
                            timestamp
                        )
                    
                    # Get memory usage
                    memory_usage = await self._get_pod_memory_usage(k8s_metrics_client, pod.metadata.name)
                    if memory_usage is not None:
                        self._add_resource_usage(
                            f"pod_{pod.metadata.name}_memory",
                            ResourceType.MEMORY,
                            memory_usage,
                            timestamp
                        )
            
        except Exception as e:
            logger.error(f"Error collecting Kubernetes usage: {e}")
    
    async def _get_pod_cpu_usage(self, metrics_client, pod_name: str) -> Optional[float]:
        """Get pod CPU usage"""
        try:
            # Query metrics server for CPU usage
            response = metrics_client.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace="spider",
                plural="pods"
            )
            
            for pod in response.get("items", []):
                if pod["metadata"]["name"] == pod_name:
                    containers = pod.get("containers", [])
                    if containers:
                        cpu_usage = containers[0].get("usage", {}).get("cpu", "0")
                        # Convert from millicores to cores
                        return float(cpu_usage.replace("m", "")) / 1000 if cpu_usage.endswith("m") else float(cpu_usage)
        except Exception as e:
            logger.error(f"Error getting pod CPU usage: {e}")
        
        return None
    
    async def _get_pod_memory_usage(self, metrics_client, pod_name: str) -> Optional[float]:
        """Get pod memory usage"""
        try:
            # Query metrics server for memory usage
            response = metrics_client.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace="spider",
                plural="pods"
            )
            
            for pod in response.get("items", []):
                if pod["metadata"]["name"] == pod_name:
                    containers = pod.get("containers", [])
                    if containers:
                        memory_usage = containers[0].get("usage", {}).get("memory", "0")
                        # Convert from bytes to MB
                        return float(memory_usage.replace("Ki", "")) / 1024 if memory_usage.endswith("Ki") else float(memory_usage) / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting pod memory usage: {e}")
        
        return None
    
    async def _collect_aws_usage(self, timestamp: datetime):
        """Collect AWS resource usage"""
        if not self.aws_cloudwatch:
            return
        
        try:
            # Get EC2 instance metrics
            response = self.aws_cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': 'i-1234567890abcdef0'  # Replace with actual instance ID
                    }
                ],
                StartTime=timestamp - timedelta(hours=1),
                EndTime=timestamp,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                cpu_usage = response['Datapoints'][0]['Average']
                self._add_resource_usage(
                    "aws_ec2_cpu",
                    ResourceType.CPU,
                    cpu_usage,
                    timestamp
                )
        
        except Exception as e:
            logger.error(f"Error collecting AWS usage: {e}")
    
    async def _collect_azure_usage(self, timestamp: datetime):
        """Collect Azure resource usage"""
        if not self.azure_compute_client:
            return
        
        try:
            # Get Azure VM metrics
            # Implementation for Azure resource usage collection
            pass
        except Exception as e:
            logger.error(f"Error collecting Azure usage: {e}")
    
    async def _collect_gcp_usage(self, timestamp: datetime):
        """Collect GCP resource usage"""
        if not self.gcp_compute_client:
            return
        
        try:
            # Get GCP VM metrics
            # Implementation for GCP resource usage collection
            pass
        except Exception as e:
            logger.error(f"Error collecting GCP usage: {e}")
    
    def _add_resource_usage(self, resource_id: str, resource_type: ResourceType, 
                           usage: float, timestamp: datetime, capacity: float = 100.0):
        """Add resource usage data"""
        utilization_percent = (usage / capacity) * 100 if capacity > 0 else 0
        
        # Estimate cost (simplified)
        cost_per_hour = self._estimate_cost(resource_type, usage)
        
        resource_usage = ResourceUsage(
            resource_type=resource_type,
            current_usage=usage,
            capacity=capacity,
            utilization_percent=utilization_percent,
            cost_per_hour=cost_per_hour,
            timestamp=timestamp
        )
        
        self.resource_usage[resource_id] = resource_usage
    
    def _estimate_cost(self, resource_type: ResourceType, usage: float) -> float:
        """Estimate cost for resource usage"""
        # Simplified cost estimation
        cost_per_unit = {
            ResourceType.CPU: 0.05,  # $0.05 per CPU hour
            ResourceType.MEMORY: 0.01,  # $0.01 per GB hour
            ResourceType.STORAGE: 0.10,  # $0.10 per GB hour
            ResourceType.NETWORK: 0.01,  # $0.01 per GB
            ResourceType.DATABASE: 0.20,  # $0.20 per hour
            ResourceType.CACHE: 0.15,  # $0.15 per hour
            ResourceType.COMPUTE: 0.10,  # $0.10 per hour
        }
        
        return cost_per_unit.get(resource_type, 0.05) * usage
    
    async def _analyze_costs(self):
        """Analyze costs and identify optimization opportunities"""
        while self.running:
            try:
                # Calculate total costs
                total_cost = sum(usage.cost_per_hour for usage in self.resource_usage.values())
                
                # Store cost history
                self.cost_history.append({
                    "timestamp": datetime.now(),
                    "total_cost": total_cost,
                    "resource_count": len(self.resource_usage)
                })
                
                # Identify high-cost resources
                high_cost_resources = [
                    (resource_id, usage) for resource_id, usage in self.resource_usage.items()
                    if usage.cost_per_hour > total_cost * 0.1  # More than 10% of total cost
                ]
                
                # Identify underutilized resources
                underutilized_resources = [
                    (resource_id, usage) for resource_id, usage in self.resource_usage.items()
                    if usage.utilization_percent < self.config.utilization_threshold_percent
                ]
                
                logger.info(f"Cost analysis: Total cost=${total_cost:.2f}/hour, "
                          f"High-cost resources={len(high_cost_resources)}, "
                          f"Underutilized resources={len(underutilized_resources)}")
                
            except Exception as e:
                logger.error(f"Error analyzing costs: {e}")
            
            await asyncio.sleep(self.config.optimization_interval)
    
    async def _generate_recommendations(self):
        """Generate cost optimization recommendations"""
        while self.running:
            try:
                # Clear existing recommendations
                self.recommendations.clear()
                
                # Generate right-sizing recommendations
                await self._generate_right_sizing_recommendations()
                
                # Generate scheduling recommendations
                await self._generate_scheduling_recommendations()
                
                # Generate reserved instance recommendations
                await self._generate_reserved_instance_recommendations()
                
                # Generate spot instance recommendations
                await self._generate_spot_instance_recommendations()
                
                logger.info(f"Generated {len(self.recommendations)} cost optimization recommendations")
                
            except Exception as e:
                logger.error(f"Error generating recommendations: {e}")
            
            await asyncio.sleep(self.config.optimization_interval)
    
    async def _generate_right_sizing_recommendations(self):
        """Generate right-sizing recommendations"""
        for resource_id, usage in self.resource_usage.items():
            if usage.utilization_percent < 30:  # Underutilized
                recommendation = CostOptimizationRecommendation(
                    id=f"right_size_{resource_id}",
                    title=f"Right-size {resource_id}",
                    description=f"Resource {resource_id} is only {usage.utilization_percent:.1f}% utilized. Consider downsizing.",
                    resource_type=usage.resource_type,
                    action=OptimizationAction.RESIZE,
                    current_cost=usage.cost_per_hour,
                    potential_savings=usage.cost_per_hour * 0.5,  # 50% savings
                    confidence=0.8,
                    implementation_effort="low",
                    risks=["May impact performance during peak usage"],
                    prerequisites=["Monitor resource usage patterns"]
                )
                
                self.recommendations[recommendation.id] = recommendation
            
            elif usage.utilization_percent > 90:  # Overutilized
                recommendation = CostOptimizationRecommendation(
                    id=f"scale_up_{resource_id}",
                    title=f"Scale up {resource_id}",
                    description=f"Resource {resource_id} is {usage.utilization_percent:.1f}% utilized. Consider scaling up to avoid performance issues.",
                    resource_type=usage.resource_type,
                    action=OptimizationAction.SCALE_UP,
                    current_cost=usage.cost_per_hour,
                    potential_savings=0,  # No immediate savings
                    confidence=0.9,
                    implementation_effort="medium",
                    risks=["Increased costs"],
                    prerequisites=["Monitor performance metrics"]
                )
                
                self.recommendations[recommendation.id] = recommendation
    
    async def _generate_scheduling_recommendations(self):
        """Generate scheduling recommendations"""
        # Analyze usage patterns to identify resources that can be scheduled
        for resource_id, usage in self.resource_usage.items():
            if usage.resource_type in [ResourceType.COMPUTE, ResourceType.DATABASE]:
                # Check if resource has predictable usage patterns
                if self._has_predictable_pattern(resource_id):
                    recommendation = CostOptimizationRecommendation(
                        id=f"schedule_{resource_id}",
                        title=f"Schedule {resource_id}",
                        description=f"Resource {resource_id} has predictable usage patterns. Consider scheduling it during off-hours.",
                        resource_type=usage.resource_type,
                        action=OptimizationAction.SCHEDULE,
                        current_cost=usage.cost_per_hour,
                        potential_savings=usage.cost_per_hour * 0.6,  # 60% savings
                        confidence=0.7,
                        implementation_effort="medium",
                        risks=["May impact availability during off-hours"],
                        prerequisites=["Implement proper scheduling automation"]
                    )
                    
                    self.recommendations[recommendation.id] = recommendation
    
    async def _generate_reserved_instance_recommendations(self):
        """Generate reserved instance recommendations"""
        # Analyze usage patterns for reserved instance opportunities
        for resource_id, usage in self.resource_usage.items():
            if usage.resource_type == ResourceType.COMPUTE and usage.utilization_percent > 70:
                recommendation = CostOptimizationRecommendation(
                    id=f"reserved_{resource_id}",
                    title=f"Use Reserved Instance for {resource_id}",
                    description=f"Resource {resource_id} has consistent usage. Consider using reserved instances for cost savings.",
                    resource_type=usage.resource_type,
                    action=OptimizationAction.MIGRATE,
                    current_cost=usage.cost_per_hour,
                    potential_savings=usage.cost_per_hour * 0.3,  # 30% savings
                    confidence=0.8,
                    implementation_effort="high",
                    risks=["Commitment to long-term usage"],
                    prerequisites=["Analyze usage patterns over longer period"]
                )
                
                self.recommendations[recommendation.id] = recommendation
    
    async def _generate_spot_instance_recommendations(self):
        """Generate spot instance recommendations"""
        # Analyze workload characteristics for spot instance opportunities
        for resource_id, usage in self.resource_usage.items():
            if usage.resource_type == ResourceType.COMPUTE and self._is_spot_suitable(resource_id):
                recommendation = CostOptimizationRecommendation(
                    id=f"spot_{resource_id}",
                    title=f"Use Spot Instance for {resource_id}",
                    description=f"Resource {resource_id} is suitable for spot instances. Consider using spot instances for significant cost savings.",
                    resource_type=usage.resource_type,
                    action=OptimizationAction.MIGRATE,
                    current_cost=usage.cost_per_hour,
                    potential_savings=usage.cost_per_hour * 0.7,  # 70% savings
                    confidence=0.6,
                    implementation_effort="high",
                    risks=["Instance may be terminated with short notice"],
                    prerequisites=["Implement fault tolerance and auto-recovery"]
                )
                
                self.recommendations[recommendation.id] = recommendation
    
    def _has_predictable_pattern(self, resource_id: str) -> bool:
        """Check if resource has predictable usage patterns"""
        # Simplified pattern detection
        # In production, implement more sophisticated pattern analysis
        return True
    
    def _is_spot_suitable(self, resource_id: str) -> bool:
        """Check if resource is suitable for spot instances"""
        # Simplified suitability check
        # In production, analyze workload characteristics
        return True
    
    async def _apply_optimizations(self):
        """Apply cost optimizations"""
        while self.running:
            try:
                # Apply high-confidence, low-effort recommendations
                for recommendation in self.recommendations.values():
                    if (recommendation.confidence > 0.8 and 
                        recommendation.implementation_effort == "low" and
                        recommendation.potential_savings > 0):
                        
                        await self._apply_recommendation(recommendation)
                
            except Exception as e:
                logger.error(f"Error applying optimizations: {e}")
            
            await asyncio.sleep(self.config.optimization_interval)
    
    async def _apply_recommendation(self, recommendation: CostOptimizationRecommendation):
        """Apply a specific recommendation"""
        try:
            if recommendation.action == OptimizationAction.RESIZE:
                await self._resize_resource(recommendation)
            elif recommendation.action == OptimizationAction.SCHEDULE:
                await self._schedule_resource(recommendation)
            elif recommendation.action == OptimizationAction.MIGRATE:
                await self._migrate_resource(recommendation)
            
            logger.info(f"Applied recommendation: {recommendation.title}")
            
        except Exception as e:
            logger.error(f"Error applying recommendation {recommendation.id}: {e}")
    
    async def _resize_resource(self, recommendation: CostOptimizationRecommendation):
        """Resize a resource"""
        # Implementation for resource resizing
        pass
    
    async def _schedule_resource(self, recommendation: CostOptimizationRecommendation):
        """Schedule a resource"""
        # Implementation for resource scheduling
        pass
    
    async def _migrate_resource(self, recommendation: CostOptimizationRecommendation):
        """Migrate a resource"""
        # Implementation for resource migration
        pass
    
    async def _cleanup_old_data(self):
        """Clean up old data"""
        while self.running:
            try:
                # Clean up old cost history
                cutoff_date = datetime.now() - timedelta(days=30)
                self.cost_history = [
                    entry for entry in self.cost_history
                    if entry["timestamp"] > cutoff_date
                ]
                
                # Clean up old resource usage data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.resource_usage = {
                    resource_id: usage for resource_id, usage in self.resource_usage.items()
                    if usage.timestamp > cutoff_time
                }
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(3600)  # Clean up every hour
    
    async def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        total_cost = sum(usage.cost_per_hour for usage in self.resource_usage.values())
        
        return {
            "total_cost_per_hour": total_cost,
            "total_cost_per_day": total_cost * 24,
            "total_cost_per_month": total_cost * 24 * 30,
            "resource_count": len(self.resource_usage),
            "recommendation_count": len(self.recommendations),
            "potential_savings": sum(rec.potential_savings for rec in self.recommendations.values()),
            "optimization_running": self.running,
            "last_analysis": datetime.now().isoformat()
        }
    
    async def get_recommendations(self, resource_type: Optional[ResourceType] = None) -> List[CostOptimizationRecommendation]:
        """Get cost optimization recommendations"""
        recommendations = list(self.recommendations.values())
        
        if resource_type:
            recommendations = [
                rec for rec in recommendations
                if rec.resource_type == resource_type
            ]
        
        return sorted(recommendations, key=lambda x: x.potential_savings, reverse=True)
    
    async def get_resource_usage(self, resource_type: Optional[ResourceType] = None) -> List[ResourceUsage]:
        """Get resource usage data"""
        usage_data = list(self.resource_usage.values())
        
        if resource_type:
            usage_data = [
                usage for usage in usage_data
                if usage.resource_type == resource_type
            ]
        
        return sorted(usage_data, key=lambda x: x.timestamp, reverse=True)
    
    async def get_cost_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get cost history"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            entry for entry in self.cost_history
            if entry["timestamp"] > cutoff_date
        ]
