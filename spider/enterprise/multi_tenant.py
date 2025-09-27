"""Multi-tenant support for SPIDER framework."""

import asyncio
import time
import json
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import weakref
from datetime import datetime, timedelta

from ..core.exceptions import SpiderError, ValidationError
from ..core.logger import get_logger


class TenantStatus(Enum):
    """Tenant status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"


class TenantTier(Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class ResourceType(Enum):
    """Resource types for tenant isolation."""
    SCRAPING_JOBS = "scraping_jobs"
    DATA_STORAGE = "data_storage"
    API_REQUESTS = "api_requests"
    CONCURRENT_WORKERS = "concurrent_workers"
    CUSTOM_SCRAPERS = "custom_scrapers"
    SCHEDULED_JOBS = "scheduled_jobs"


@dataclass
class TenantLimits:
    """Tenant resource limits."""
    max_scraping_jobs: int = 10
    max_data_storage_mb: int = 1000
    max_api_requests_per_hour: int = 1000
    max_concurrent_workers: int = 5
    max_custom_scrapers: int = 3
    max_scheduled_jobs: int = 10
    max_retention_days: int = 30
    max_export_size_mb: int = 100


@dataclass
class TenantUsage:
    """Current tenant resource usage."""
    scraping_jobs: int = 0
    data_storage_mb: float = 0.0
    api_requests_hour: int = 0
    concurrent_workers: int = 0
    custom_scrapers: int = 0
    scheduled_jobs: int = 0
    last_reset: float = field(default_factory=time.time)


@dataclass
class Tenant:
    """Tenant information."""
    tenant_id: str
    name: str
    domain: str
    tier: TenantTier
    status: TenantStatus
    limits: TenantLimits
    usage: TenantUsage
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantContext:
    """Context for tenant-specific operations."""
    tenant_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """Manages multi-tenant operations."""
    
    def __init__(self):
        """Initialize tenant manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_contexts: Dict[str, TenantContext] = {}
        self.usage_tracking: Dict[str, Dict[ResourceType, int]] = defaultdict(lambda: defaultdict(int))
        self.rate_limiting: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.lock = threading.RLock()
        
        # Setup default tiers
        self._setup_default_tiers()
    
    def _setup_default_tiers(self) -> None:
        """Setup default tenant tiers."""
        self.tier_limits = {
            TenantTier.FREE: TenantLimits(
                max_scraping_jobs=5,
                max_data_storage_mb=100,
                max_api_requests_per_hour=100,
                max_concurrent_workers=2,
                max_custom_scrapers=1,
                max_scheduled_jobs=3,
                max_retention_days=7,
                max_export_size_mb=10
            ),
            TenantTier.BASIC: TenantLimits(
                max_scraping_jobs=25,
                max_data_storage_mb=1000,
                max_api_requests_per_hour=1000,
                max_concurrent_workers=5,
                max_custom_scrapers=5,
                max_scheduled_jobs=10,
                max_retention_days=30,
                max_export_size_mb=100
            ),
            TenantTier.PROFESSIONAL: TenantLimits(
                max_scraping_jobs=100,
                max_data_storage_mb=10000,
                max_api_requests_per_hour=10000,
                max_concurrent_workers=20,
                max_custom_scrapers=20,
                max_scheduled_jobs=50,
                max_retention_days=90,
                max_export_size_mb=1000
            ),
            TenantTier.ENTERPRISE: TenantLimits(
                max_scraping_jobs=1000,
                max_data_storage_mb=100000,
                max_api_requests_per_hour=100000,
                max_concurrent_workers=100,
                max_custom_scrapers=100,
                max_scheduled_jobs=500,
                max_retention_days=365,
                max_export_size_mb=10000
            )
        }
    
    def create_tenant(
        self,
        name: str,
        domain: str,
        tier: TenantTier = TenantTier.FREE,
        custom_limits: Optional[TenantLimits] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a new tenant.
        
        Args:
            name: Tenant name
            domain: Tenant domain
            tier: Tenant tier
            custom_limits: Optional custom limits
            metadata: Optional metadata
            
        Returns:
            Created tenant
        """
        with self.lock:
            tenant_id = str(uuid.uuid4())
            
            # Use tier limits or custom limits
            limits = custom_limits or self.tier_limits.get(tier, TenantLimits())
            
            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                domain=domain,
                tier=tier,
                status=TenantStatus.PENDING,
                limits=limits,
                usage=TenantUsage(),
                created_at=time.time(),
                updated_at=time.time(),
                metadata=metadata or {}
            )
            
            self.tenants[tenant_id] = tenant
            self.logger.info(f"Created tenant: {name} ({tenant_id})")
            
            return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant or None if not found
        """
        with self.lock:
            return self.tenants.get(tenant_id)
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain.
        
        Args:
            domain: Tenant domain
            
        Returns:
            Tenant or None if not found
        """
        with self.lock:
            for tenant in self.tenants.values():
                if tenant.domain == domain:
                    return tenant
            return None
    
    def update_tenant(self, tenant_id: str, **kwargs) -> bool:
        """Update tenant information.
        
        Args:
            tenant_id: Tenant ID
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        with self.lock:
            if tenant_id not in self.tenants:
                return False
            
            tenant = self.tenants[tenant_id]
            
            # Update allowed fields
            allowed_fields = ['name', 'domain', 'tier', 'status', 'metadata', 'settings']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(tenant, field, value)
            
            tenant.updated_at = time.time()
            self.logger.info(f"Updated tenant: {tenant_id}")
            
            return True
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if tenant_id not in self.tenants:
                return False
            
            del self.tenants[tenant_id]
            
            # Clean up related data
            if tenant_id in self.usage_tracking:
                del self.usage_tracking[tenant_id]
            
            if tenant_id in self.rate_limiting:
                del self.rate_limiting[tenant_id]
            
            self.logger.info(f"Deleted tenant: {tenant_id}")
            return True
    
    def set_tenant_context(self, context: TenantContext) -> None:
        """Set current tenant context.
        
        Args:
            context: Tenant context
        """
        with self.lock:
            self.tenant_contexts[context.tenant_id] = context
    
    def get_tenant_context(self, tenant_id: str) -> Optional[TenantContext]:
        """Get tenant context.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant context or None
        """
        with self.lock:
            return self.tenant_contexts.get(tenant_id)
    
    def check_resource_limit(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        requested_amount: int = 1
    ) -> Tuple[bool, str]:
        """Check if tenant can use requested amount of resource.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Resource type
            requested_amount: Amount requested
            
        Returns:
            Tuple of (can_use, error_message)
        """
        with self.lock:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            if tenant.status != TenantStatus.ACTIVE:
                return False, f"Tenant status is {tenant.status.value}"
            
            # Check if tenant has expired
            if tenant.expires_at and time.time() > tenant.expires_at:
                return False, "Tenant has expired"
            
            # Get current usage
            current_usage = self.usage_tracking[tenant_id][resource_type]
            
            # Get limit based on resource type
            if resource_type == ResourceType.SCRAPING_JOBS:
                limit = tenant.limits.max_scraping_jobs
            elif resource_type == ResourceType.DATA_STORAGE:
                limit = tenant.limits.max_data_storage_mb
            elif resource_type == ResourceType.API_REQUESTS:
                limit = tenant.limits.max_api_requests_per_hour
            elif resource_type == ResourceType.CONCURRENT_WORKERS:
                limit = tenant.limits.max_concurrent_workers
            elif resource_type == ResourceType.CUSTOM_SCRAPERS:
                limit = tenant.limits.max_custom_scrapers
            elif resource_type == ResourceType.SCHEDULED_JOBS:
                limit = tenant.limits.max_scheduled_jobs
            else:
                return True, ""  # Unknown resource type, allow
            
            if current_usage + requested_amount > limit:
                return False, f"Resource limit exceeded for {resource_type.value}: {current_usage + requested_amount}/{limit}"
            
            return True, ""
    
    def use_resource(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        amount: int = 1
    ) -> bool:
        """Use tenant resource.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Resource type
            amount: Amount to use
            
        Returns:
            True if successful, False if limit exceeded
        """
        can_use, error = self.check_resource_limit(tenant_id, resource_type, amount)
        
        if not can_use:
            self.logger.warning(f"Resource usage denied for {tenant_id}: {error}")
            return False
        
        with self.lock:
            self.usage_tracking[tenant_id][resource_type] += amount
            
            # Update tenant usage
            tenant = self.get_tenant(tenant_id)
            if tenant:
                if resource_type == ResourceType.SCRAPING_JOBS:
                    tenant.usage.scraping_jobs += amount
                elif resource_type == ResourceType.DATA_STORAGE:
                    tenant.usage.data_storage_mb += amount
                elif resource_type == ResourceType.API_REQUESTS:
                    tenant.usage.api_requests_hour += amount
                elif resource_type == ResourceType.CONCURRENT_WORKERS:
                    tenant.usage.concurrent_workers += amount
                elif resource_type == ResourceType.CUSTOM_SCRAPERS:
                    tenant.usage.custom_scrapers += amount
                elif resource_type == ResourceType.SCHEDULED_JOBS:
                    tenant.usage.scheduled_jobs += amount
        
        return True
    
    def release_resource(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        amount: int = 1
    ) -> None:
        """Release tenant resource.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Resource type
            amount: Amount to release
        """
        with self.lock:
            current_usage = self.usage_tracking[tenant_id][resource_type]
            self.usage_tracking[tenant_id][resource_type] = max(0, current_usage - amount)
            
            # Update tenant usage
            tenant = self.get_tenant(tenant_id)
            if tenant:
                if resource_type == ResourceType.SCRAPING_JOBS:
                    tenant.usage.scraping_jobs = max(0, tenant.usage.scraping_jobs - amount)
                elif resource_type == ResourceType.DATA_STORAGE:
                    tenant.usage.data_storage_mb = max(0, tenant.usage.data_storage_mb - amount)
                elif resource_type == ResourceType.API_REQUESTS:
                    tenant.usage.api_requests_hour = max(0, tenant.usage.api_requests_hour - amount)
                elif resource_type == ResourceType.CONCURRENT_WORKERS:
                    tenant.usage.concurrent_workers = max(0, tenant.usage.concurrent_workers - amount)
                elif resource_type == ResourceType.CUSTOM_SCRAPERS:
                    tenant.usage.custom_scrapers = max(0, tenant.usage.custom_scrapers - amount)
                elif resource_type == ResourceType.SCHEDULED_JOBS:
                    tenant.usage.scheduled_jobs = max(0, tenant.usage.scheduled_jobs - amount)
    
    def reset_usage(self, tenant_id: str) -> None:
        """Reset tenant usage counters.
        
        Args:
            tenant_id: Tenant ID
        """
        with self.lock:
            if tenant_id in self.usage_tracking:
                for resource_type in ResourceType:
                    self.usage_tracking[tenant_id][resource_type] = 0
            
            tenant = self.get_tenant(tenant_id)
            if tenant:
                tenant.usage = TenantUsage()
                tenant.usage.last_reset = time.time()
    
    def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage statistics.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Usage statistics
        """
        with self.lock:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return {}
            
            usage_stats = {
                "tenant_id": tenant_id,
                "tier": tenant.tier.value,
                "limits": {
                    "max_scraping_jobs": tenant.limits.max_scraping_jobs,
                    "max_data_storage_mb": tenant.limits.max_data_storage_mb,
                    "max_api_requests_per_hour": tenant.limits.max_api_requests_per_hour,
                    "max_concurrent_workers": tenant.limits.max_concurrent_workers,
                    "max_custom_scrapers": tenant.limits.max_custom_scrapers,
                    "max_scheduled_jobs": tenant.limits.max_scheduled_jobs
                },
                "current_usage": {
                    "scraping_jobs": self.usage_tracking[tenant_id][ResourceType.SCRAPING_JOBS],
                    "data_storage_mb": self.usage_tracking[tenant_id][ResourceType.DATA_STORAGE],
                    "api_requests_hour": self.usage_tracking[tenant_id][ResourceType.API_REQUESTS],
                    "concurrent_workers": self.usage_tracking[tenant_id][ResourceType.CONCURRENT_WORKERS],
                    "custom_scrapers": self.usage_tracking[tenant_id][ResourceType.CUSTOM_SCRAPERS],
                    "scheduled_jobs": self.usage_tracking[tenant_id][ResourceType.SCHEDULED_JOBS]
                },
                "utilization_percentage": {}
            }
            
            # Calculate utilization percentages
            for resource_type in ResourceType:
                current = self.usage_tracking[tenant_id][resource_type]
                if resource_type == ResourceType.SCRAPING_JOBS:
                    limit = tenant.limits.max_scraping_jobs
                elif resource_type == ResourceType.DATA_STORAGE:
                    limit = tenant.limits.max_data_storage_mb
                elif resource_type == ResourceType.API_REQUESTS:
                    limit = tenant.limits.max_api_requests_per_hour
                elif resource_type == ResourceType.CONCURRENT_WORKERS:
                    limit = tenant.limits.max_concurrent_workers
                elif resource_type == ResourceType.CUSTOM_SCRAPERS:
                    limit = tenant.limits.max_custom_scrapers
                elif resource_type == ResourceType.SCHEDULED_JOBS:
                    limit = tenant.limits.max_scheduled_jobs
                else:
                    continue
                
                if limit > 0:
                    usage_stats["utilization_percentage"][resource_type.value] = (current / limit) * 100
                else:
                    usage_stats["utilization_percentage"][resource_type.value] = 0
            
            return usage_stats
    
    def list_tenants(self, status: Optional[TenantStatus] = None) -> List[Tenant]:
        """List tenants.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of tenants
        """
        with self.lock:
            tenants = list(self.tenants.values())
            
            if status:
                tenants = [t for t in tenants if t.status == status]
            
            return sorted(tenants, key=lambda t: t.created_at, reverse=True)
    
    def cleanup_expired_tenants(self) -> int:
        """Clean up expired tenants.
        
        Returns:
            Number of tenants cleaned up
        """
        with self.lock:
            current_time = time.time()
            expired_tenants = []
            
            for tenant_id, tenant in self.tenants.items():
                if tenant.expires_at and current_time > tenant.expires_at:
                    expired_tenants.append(tenant_id)
            
            for tenant_id in expired_tenants:
                self.delete_tenant(tenant_id)
            
            self.logger.info(f"Cleaned up {len(expired_tenants)} expired tenants")
            return len(expired_tenants)
    
    def get_tenant_statistics(self) -> Dict[str, Any]:
        """Get overall tenant statistics.
        
        Returns:
            Tenant statistics
        """
        with self.lock:
            total_tenants = len(self.tenants)
            active_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE])
            
            tier_distribution = defaultdict(int)
            for tenant in self.tenants.values():
                tier_distribution[tenant.tier.value] += 1
            
            return {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "inactive_tenants": total_tenants - active_tenants,
                "tier_distribution": dict(tier_distribution),
                "total_usage": {
                    "scraping_jobs": sum(self.usage_tracking[t][ResourceType.SCRAPING_JOBS] for t in self.usage_tracking),
                    "data_storage_mb": sum(self.usage_tracking[t][ResourceType.DATA_STORAGE] for t in self.usage_tracking),
                    "api_requests_hour": sum(self.usage_tracking[t][ResourceType.API_REQUESTS] for t in self.usage_tracking)
                }
            }


class TenantMiddleware:
    """Middleware for tenant-aware operations."""
    
    def __init__(self, tenant_manager: TenantManager):
        """Initialize tenant middleware.
        
        Args:
            tenant_manager: Tenant manager instance
        """
        self.tenant_manager = tenant_manager
        self.logger = get_logger(self.__class__.__name__)
    
    def get_current_tenant(self, request_headers: Dict[str, str]) -> Optional[Tenant]:
        """Get current tenant from request headers.
        
        Args:
            request_headers: Request headers
            
        Returns:
            Current tenant or None
        """
        # Check for tenant ID in headers
        tenant_id = request_headers.get('X-Tenant-ID')
        if tenant_id:
            return self.tenant_manager.get_tenant(tenant_id)
        
        # Check for domain-based tenant resolution
        host = request_headers.get('Host', '')
        if host:
            return self.tenant_manager.get_tenant_by_domain(host)
        
        return None
    
    def validate_tenant_access(self, tenant: Tenant, resource: str) -> bool:
        """Validate tenant access to resource.
        
        Args:
            tenant: Tenant instance
            resource: Resource identifier
            
        Returns:
            True if access allowed
        """
        # Check tenant status
        if tenant.status != TenantStatus.ACTIVE:
            return False
        
        # Check if tenant has expired
        if tenant.expires_at and time.time() > tenant.expires_at:
            return False
        
        # Add custom access control logic here
        return True
    
    def enforce_tenant_limits(self, tenant_id: str, operation: str, **kwargs) -> bool:
        """Enforce tenant limits for operation.
        
        Args:
            tenant_id: Tenant ID
            operation: Operation type
            **kwargs: Operation parameters
            
        Returns:
            True if operation allowed
        """
        # Map operations to resource types
        operation_mapping = {
            'scrape': ResourceType.SCRAPING_JOBS,
            'store_data': ResourceType.DATA_STORAGE,
            'api_request': ResourceType.API_REQUESTS,
            'start_worker': ResourceType.CONCURRENT_WORKERS,
            'create_scraper': ResourceType.CUSTOM_SCRAPERS,
            'schedule_job': ResourceType.SCHEDULED_JOBS
        }
        
        resource_type = operation_mapping.get(operation)
        if not resource_type:
            return True  # Unknown operation, allow
        
        amount = kwargs.get('amount', 1)
        can_use, error = self.tenant_manager.check_resource_limit(tenant_id, resource_type, amount)
        
        if not can_use:
            self.logger.warning(f"Tenant limit exceeded: {error}")
            return False
        
        return True
