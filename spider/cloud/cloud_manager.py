"""
Cloud Manager

Unified cloud management system for AWS, Azure, and GCP services.
Provides abstraction layer for multi-cloud deployments and management.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

from .aws_integration import AWSIntegration, AWSConfig
from .azure_integration import AzureIntegration, AzureConfig
from .gcp_integration import GCPIntegration, GCPConfig

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Cloud provider enumeration."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ServiceType(str, Enum):
    """Service type enumeration."""
    STORAGE = "storage"
    COMPUTE = "compute"
    FUNCTIONS = "functions"
    ML = "ml"
    DATABASE = "database"
    MONITORING = "monitoring"


@dataclass
class CloudConfig:
    """Unified cloud configuration."""
    provider: CloudProvider
    region: str
    credentials: Dict[str, str]
    project_id: Optional[str] = None
    resource_group: Optional[str] = None
    enabled_services: List[ServiceType] = None
    
    def __post_init__(self):
        if self.enabled_services is None:
            self.enabled_services = [ServiceType.STORAGE, ServiceType.COMPUTE]


@dataclass
class CloudResource:
    """Cloud resource representation."""
    resource_id: str
    provider: CloudProvider
    service_type: ServiceType
    name: str
    region: str
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = None


@dataclass
class CloudCost:
    """Cloud cost information."""
    provider: CloudProvider
    service: str
    cost: float
    currency: str
    period: str
    details: Dict[str, Any] = None


class CloudManager:
    """
    Unified cloud management system.
    
    Features:
    - Multi-cloud provider support (AWS, Azure, GCP)
    - Unified resource management
    - Cost monitoring and optimization
    - Service health monitoring
    - Automated scaling and deployment
    """
    
    def __init__(self):
        """Initialize cloud manager."""
        self.providers: Dict[CloudProvider, Any] = {}
        self.resources: Dict[str, CloudResource] = {}
        self.costs: List[CloudCost] = []
        self.health_status: Dict[CloudProvider, Dict[str, Any]] = {}
    
    def add_provider(self, config: CloudConfig) -> bool:
        """
        Add cloud provider.
        
        Args:
            config: Cloud configuration
            
        Returns:
            True if successful
        """
        try:
            if config.provider == CloudProvider.AWS:
                aws_config = AWSConfig(
                    access_key_id=config.credentials.get('access_key_id'),
                    secret_access_key=config.credentials.get('secret_access_key'),
                    region=config.credentials.get('region', 'us-east-1'),
                    session_token=config.credentials.get('session_token')
                )
                self.providers[CloudProvider.AWS] = AWSIntegration(aws_config)
                
            elif config.provider == CloudProvider.AZURE:
                azure_config = AzureConfig(
                    subscription_id=config.credentials.get('subscription_id'),
                    tenant_id=config.credentials.get('tenant_id'),
                    client_id=config.credentials.get('client_id'),
                    client_secret=config.credentials.get('client_secret'),
                    region=config.credentials.get('region', 'eastus'),
                    resource_group=config.resource_group or 'spider-rg'
                )
                self.providers[CloudProvider.AZURE] = AzureIntegration(azure_config)
                
            elif config.provider == CloudProvider.GCP:
                gcp_config = GCPConfig(
                    project_id=config.project_id or config.credentials.get('project_id'),
                    service_account_path=config.credentials.get('service_account_path'),
                    region=config.credentials.get('region', 'us-central1'),
                    zone=config.credentials.get('zone', 'us-central1-a')
                )
                self.providers[CloudProvider.GCP] = GCPIntegration(gcp_config)
            
            logger.info(f"Added cloud provider: {config.provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add cloud provider {config.provider.value}: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[CloudProvider, bool]:
        """
        Test connections to all providers.
        
        Returns:
            Dictionary of provider connection status
        """
        results = {}
        
        for provider, integration in self.providers.items():
            try:
                status = await integration.test_connection()
                results[provider] = status
                logger.info(f"Connection test for {provider.value}: {'PASS' if status else 'FAIL'}")
            except Exception as e:
                logger.error(f"Connection test failed for {provider.value}: {e}")
                results[provider] = False
        
        return results
    
    async def get_provider_services(self, provider: CloudProvider) -> List[str]:
        """
        Get available services for a provider.
        
        Args:
            provider: Cloud provider
            
        Returns:
            List of available services
        """
        if provider not in self.providers:
            return []
        
        try:
            integration = self.providers[provider]
            return integration.get_available_services()
        except Exception as e:
            logger.error(f"Failed to get services for {provider.value}: {e}")
            return []
    
    async def get_service_status(self, provider: CloudProvider, service: str) -> Dict[str, Any]:
        """
        Get service status for a provider.
        
        Args:
            provider: Cloud provider
            service: Service name
            
        Returns:
            Service status information
        """
        if provider not in self.providers:
            return {"error": "Provider not configured"}
        
        try:
            integration = self.providers[provider]
            return integration.get_service_status(service)
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {"error": str(e)}
    
    async def create_storage_resource(self, provider: CloudProvider, name: str,
                                    region: str = None) -> Optional[CloudResource]:
        """
        Create storage resource.
        
        Args:
            provider: Cloud provider
            name: Resource name
            region: Region (optional)
            
        Returns:
            Cloud resource or None
        """
        if provider not in self.providers:
            return None
        
        try:
            integration = self.providers[provider]
            
            if provider == CloudProvider.AWS:
                success = await integration.s3.create_bucket(name, region)
            elif provider == CloudProvider.AZURE:
                success = await integration.blob_storage.create_container(name)
            elif provider == CloudProvider.GCP:
                success = await integration.cloud_storage.create_bucket(name, region)
            else:
                return None
            
            if success:
                resource = CloudResource(
                    resource_id=f"{provider.value}-{name}",
                    provider=provider,
                    service_type=ServiceType.STORAGE,
                    name=name,
                    region=region or "default",
                    status="created",
                    created_at=datetime.utcnow()
                )
                self.resources[resource.resource_id] = resource
                return resource
            
        except Exception as e:
            logger.error(f"Failed to create storage resource: {e}")
        
        return None
    
    async def create_compute_resource(self, provider: CloudProvider, name: str,
                                    instance_type: str, region: str = None) -> Optional[CloudResource]:
        """
        Create compute resource.
        
        Args:
            provider: Cloud provider
            name: Resource name
            instance_type: Instance type
            region: Region (optional)
            
        Returns:
            Cloud resource or None
        """
        if provider not in self.providers:
            return None
        
        try:
            integration = self.providers[provider]
            
            if provider == CloudProvider.AWS:
                instance_id = await integration.ec2.create_instance(
                    "ami-0c02fb55956c7d316", instance_type, "spider-key", ["sg-12345678"]
                )
            elif provider == CloudProvider.AZURE:
                instance_id = await integration.vm_compute.create_vm(
                    name, region or "eastus", instance_type, "admin", "password123"
                )
            elif provider == CloudProvider.GCP:
                instance_id = await integration.compute_engine.create_instance(
                    name, instance_type
                )
            else:
                return None
            
            if instance_id:
                resource = CloudResource(
                    resource_id=instance_id,
                    provider=provider,
                    service_type=ServiceType.COMPUTE,
                    name=name,
                    region=region or "default",
                    status="created",
                    created_at=datetime.utcnow(),
                    metadata={"instance_type": instance_type}
                )
                self.resources[resource.resource_id] = resource
                return resource
            
        except Exception as e:
            logger.error(f"Failed to create compute resource: {e}")
        
        return None
    
    async def upload_file(self, provider: CloudProvider, file_path: str,
                         container: str, blob_name: str) -> bool:
        """
        Upload file to cloud storage.
        
        Args:
            provider: Cloud provider
            file_path: Local file path
            container: Container/bucket name
            blob_name: Blob/object name
            
        Returns:
            True if successful
        """
        if provider not in self.providers:
            return False
        
        try:
            integration = self.providers[provider]
            
            if provider == CloudProvider.AWS:
                return await integration.s3.upload_file(file_path, container, blob_name)
            elif provider == CloudProvider.AZURE:
                return await integration.blob_storage.upload_blob(file_path, container, blob_name)
            elif provider == CloudProvider.GCP:
                return await integration.cloud_storage.upload_blob(file_path, container, blob_name)
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
        
        return False
    
    async def download_file(self, provider: CloudProvider, container: str,
                           blob_name: str, file_path: str) -> bool:
        """
        Download file from cloud storage.
        
        Args:
            provider: Cloud provider
            container: Container/bucket name
            blob_name: Blob/object name
            file_path: Local file path
            
        Returns:
            True if successful
        """
        if provider not in self.providers:
            return False
        
        try:
            integration = self.providers[provider]
            
            if provider == CloudProvider.AWS:
                return await integration.s3.download_file(container, blob_name, file_path)
            elif provider == CloudProvider.AZURE:
                return await integration.blob_storage.download_blob(container, blob_name, file_path)
            elif provider == CloudProvider.GCP:
                return await integration.cloud_storage.download_blob(container, blob_name, file_path)
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
        
        return False
    
    async def list_resources(self, provider: CloudProvider = None,
                           service_type: ServiceType = None) -> List[CloudResource]:
        """
        List cloud resources.
        
        Args:
            provider: Filter by provider (optional)
            service_type: Filter by service type (optional)
            
        Returns:
            List of cloud resources
        """
        resources = list(self.resources.values())
        
        if provider:
            resources = [r for r in resources if r.provider == provider]
        
        if service_type:
            resources = [r for r in resources if r.service_type == service_type]
        
        return resources
    
    async def get_resource_status(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resource status.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Resource status or None
        """
        if resource_id not in self.resources:
            return None
        
        resource = self.resources[resource_id]
        integration = self.providers.get(resource.provider)
        
        if not integration:
            return None
        
        try:
            if resource.service_type == ServiceType.COMPUTE:
                if resource.provider == CloudProvider.AWS:
                    return await integration.ec2.get_instance_status(resource.name)
                elif resource.provider == CloudProvider.AZURE:
                    return await integration.vm_compute.get_vm_status(resource.name)
                elif resource.provider == CloudProvider.GCP:
                    return await integration.compute_engine.get_instance_status(resource.name)
            
            return {
                "resource_id": resource_id,
                "status": resource.status,
                "provider": resource.provider.value,
                "service_type": resource.service_type.value
            }
            
        except Exception as e:
            logger.error(f"Failed to get resource status: {e}")
            return None
    
    async def delete_resource(self, resource_id: str) -> bool:
        """
        Delete cloud resource.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            True if successful
        """
        if resource_id not in self.resources:
            return False
        
        resource = self.resources[resource_id]
        integration = self.providers.get(resource.provider)
        
        if not integration:
            return False
        
        try:
            success = False
            
            if resource.service_type == ServiceType.COMPUTE:
                if resource.provider == CloudProvider.AWS:
                    success = await integration.ec2.terminate_instance(resource.name)
                elif resource.provider == CloudProvider.AZURE:
                    success = await integration.vm_compute.delete_vm(resource.name)
                elif resource.provider == CloudProvider.GCP:
                    success = await integration.compute_engine.delete_instance(resource.name)
            
            if success:
                del self.resources[resource_id]
                logger.info(f"Deleted resource: {resource_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete resource: {e}")
            return False
    
    async def get_health_status(self) -> Dict[CloudProvider, Dict[str, Any]]:
        """
        Get health status of all providers.
        
        Returns:
            Health status for each provider
        """
        health_status = {}
        
        for provider, integration in self.providers.items():
            try:
                services = await self.get_provider_services(provider)
                service_status = {}
                
                for service in services:
                    status = await self.get_service_status(provider, service)
                    service_status[service] = status
                
                health_status[provider] = {
                    "overall_status": "healthy",
                    "services": service_status,
                    "last_checked": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                health_status[provider] = {
                    "overall_status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.utcnow().isoformat()
                }
        
        self.health_status = health_status
        return health_status
    
    async def estimate_cost(self, provider: CloudProvider, 
                          resource_type: str, specifications: Dict[str, Any]) -> Optional[CloudCost]:
        """
        Estimate cost for cloud resources.
        
        Args:
            provider: Cloud provider
            resource_type: Type of resource
            specifications: Resource specifications
            
        Returns:
            Cost estimate or None
        """
        try:
            # This is a simplified cost estimation
            # In practice, you'd integrate with cloud provider cost APIs
            
            base_costs = {
                CloudProvider.AWS: {"storage": 0.023, "compute": 0.10},
                CloudProvider.AZURE: {"storage": 0.018, "compute": 0.12},
                CloudProvider.GCP: {"storage": 0.020, "compute": 0.11}
            }
            
            base_cost = base_costs.get(provider, {}).get(resource_type, 0.0)
            
            # Simple calculation based on specifications
            if resource_type == "storage":
                size_gb = specifications.get("size_gb", 1)
                estimated_cost = base_cost * size_gb
            elif resource_type == "compute":
                hours = specifications.get("hours", 1)
                estimated_cost = base_cost * hours
            else:
                estimated_cost = base_cost
            
            return CloudCost(
                provider=provider,
                service=resource_type,
                cost=estimated_cost,
                currency="USD",
                period="monthly",
                details=specifications
            )
            
        except Exception as e:
            logger.error(f"Failed to estimate cost: {e}")
            return None
    
    def get_cloud_summary(self) -> Dict[str, Any]:
        """Get cloud infrastructure summary."""
        return {
            "total_providers": len(self.providers),
            "total_resources": len(self.resources),
            "providers": list(self.providers.keys()),
            "resource_types": list(set(r.service_type.value for r in self.resources.values())),
            "health_status": self.health_status,
            "last_updated": datetime.utcnow().isoformat()
        }
