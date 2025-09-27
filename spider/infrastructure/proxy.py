"""Proxy management for SPIDER framework."""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx

try:
    from crawlee import ProxyConfiguration
except ImportError:
    ProxyConfiguration = None

from ..core.exceptions import ProxyError
from ..core.logger import get_logger


class ProxyStatus(Enum):
    """Proxy status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProxyInfo:
    """Proxy information container."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    country: Optional[str] = None
    status: ProxyStatus = ProxyStatus.UNKNOWN
    last_used: Optional[float] = None
    success_rate: float = 0.0
    response_time: float = 0.0
    error_count: int = 0
    
    @property
    def url(self) -> str:
        """Get proxy URL."""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if proxy is healthy."""
        return self.status == ProxyStatus.HEALTHY and self.success_rate > 0.5


class ProxyProvider(ABC):
    """Base class for proxy providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize proxy provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def get_proxies(self) -> List[ProxyInfo]:
        """Get list of available proxies.
        
        Returns:
            List of proxy information
        """
        pass
    
    @abstractmethod
    async def validate_proxy(self, proxy: ProxyInfo) -> bool:
        """Validate a proxy.
        
        Args:
            proxy: Proxy to validate
            
        Returns:
            True if proxy is valid
        """
        pass


class BrightDataProvider(ProxyProvider):
    """Bright Data proxy provider."""
    
    async def get_proxies(self) -> List[ProxyInfo]:
        """Get proxies from Bright Data."""
        try:
            # This is a simplified implementation
            # In practice, you'd integrate with Bright Data API
            proxies = []
            
            # Example configuration
            proxy_configs = self.config.get('proxies', [])
            for proxy_config in proxy_configs:
                proxy = ProxyInfo(
                    host=proxy_config['host'],
                    port=proxy_config['port'],
                    username=proxy_config.get('username'),
                    password=proxy_config.get('password'),
                    protocol=proxy_config.get('protocol', 'http'),
                    country=proxy_config.get('country')
                )
                proxies.append(proxy)
            
            return proxies
            
        except Exception as e:
            self.logger.error(f"Failed to get proxies from Bright Data: {e}")
            raise ProxyError(f"Bright Data proxy retrieval failed: {e}")
    
    async def validate_proxy(self, proxy: ProxyInfo) -> bool:
        """Validate Bright Data proxy."""
        try:
            async with httpx.AsyncClient(proxies=proxy.url) as client:
                response = await client.get(
                    "http://httpbin.org/ip",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False


class OxylabsProvider(ProxyProvider):
    """Oxylabs proxy provider."""
    
    async def get_proxies(self) -> List[ProxyInfo]:
        """Get proxies from Oxylabs."""
        try:
            # This is a simplified implementation
            # In practice, you'd integrate with Oxylabs API
            proxies = []
            
            proxy_configs = self.config.get('proxies', [])
            for proxy_config in proxy_configs:
                proxy = ProxyInfo(
                    host=proxy_config['host'],
                    port=proxy_config['port'],
                    username=proxy_config.get('username'),
                    password=proxy_config.get('password'),
                    protocol=proxy_config.get('protocol', 'http'),
                    country=proxy_config.get('country')
                )
                proxies.append(proxy)
            
            return proxies
            
        except Exception as e:
            self.logger.error(f"Failed to get proxies from Oxylabs: {e}")
            raise ProxyError(f"Oxylabs proxy retrieval failed: {e}")
    
    async def validate_proxy(self, proxy: ProxyInfo) -> bool:
        """Validate Oxylabs proxy."""
        try:
            async with httpx.AsyncClient(proxies=proxy.url) as client:
                response = await client.get(
                    "http://httpbin.org/ip",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False


class ProxyPool:
    """Proxy pool management."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize proxy pool.
        
        Args:
            config: Pool configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.rotation_interval = config.get('rotation_interval', 300)  # 5 minutes
        self.last_rotation = 0
        self.health_check_interval = config.get('health_check_interval', 60)  # 1 minute
        self.last_health_check = 0
    
    async def add_proxy(self, proxy: ProxyInfo) -> None:
        """Add proxy to pool.
        
        Args:
            proxy: Proxy to add
        """
        self.proxies.append(proxy)
        self.logger.info(f"Added proxy: {proxy.host}:{proxy.port}")
    
    async def add_proxies(self, proxies: List[ProxyInfo]) -> None:
        """Add multiple proxies to pool.
        
        Args:
            proxies: Proxies to add
        """
        for proxy in proxies:
            await self.add_proxy(proxy)
    
    async def get_proxy(self, strategy: str = "round_robin") -> Optional[ProxyInfo]:
        """Get a proxy from the pool.
        
        Args:
            strategy: Selection strategy (round_robin, random, healthiest)
            
        Returns:
            Selected proxy or None
        """
        if not self.proxies:
            return None
        
        # Check if rotation is needed
        current_time = time.time()
        if current_time - self.last_rotation > self.rotation_interval:
            await self._rotate_proxies()
            self.last_rotation = current_time
        
        # Check if health check is needed
        if current_time - self.last_health_check > self.health_check_interval:
            await self._health_check_proxies()
            self.last_health_check = current_time
        
        # Filter healthy proxies
        healthy_proxies = [p for p in self.proxies if p.is_healthy]
        if not healthy_proxies:
            self.logger.warning("No healthy proxies available")
            return None
        
        # Select proxy based on strategy
        if strategy == "round_robin":
            proxy = healthy_proxies[self.current_index % len(healthy_proxies)]
            self.current_index += 1
        elif strategy == "random":
            proxy = random.choice(healthy_proxies)
        elif strategy == "healthiest":
            proxy = max(healthy_proxies, key=lambda p: p.success_rate)
        else:
            proxy = healthy_proxies[0]
        
        proxy.last_used = current_time
        return proxy
    
    async def _rotate_proxies(self) -> None:
        """Rotate proxy order."""
        random.shuffle(self.proxies)
        self.logger.info("Rotated proxy order")
    
    async def _health_check_proxies(self) -> None:
        """Perform health check on all proxies."""
        self.logger.info("Performing proxy health check")
        
        tasks = []
        for proxy in self.proxies:
            task = self._check_proxy_health(proxy)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.proxies[i].status = ProxyStatus.UNHEALTHY
                self.proxies[i].error_count += 1
            else:
                self.proxies[i].status = ProxyStatus.HEALTHY if result else ProxyStatus.UNHEALTHY
    
    async def _check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """Check health of a single proxy.
        
        Args:
            proxy: Proxy to check
            
        Returns:
            True if proxy is healthy
        """
        try:
            start_time = time.time()
            async with httpx.AsyncClient(proxies=proxy.url) as client:
                response = await client.get(
                    "http://httpbin.org/ip",
                    timeout=5.0
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    proxy.response_time = response_time
                    proxy.success_rate = min(1.0, proxy.success_rate + 0.1)
                    return True
                else:
                    proxy.error_count += 1
                    proxy.success_rate = max(0.0, proxy.success_rate - 0.1)
                    return False
        except Exception as e:
            self.logger.debug(f"Proxy health check failed for {proxy.host}:{proxy.port}: {e}")
            proxy.error_count += 1
            proxy.success_rate = max(0.0, proxy.success_rate - 0.1)
            return False
    
    def update_proxy_stats(self, proxy: ProxyInfo, success: bool, response_time: float) -> None:
        """Update proxy statistics.
        
        Args:
            proxy: Proxy to update
            success: Whether request was successful
            response_time: Response time in seconds
        """
        if success:
            proxy.success_rate = min(1.0, proxy.success_rate + 0.05)
        else:
            proxy.success_rate = max(0.0, proxy.success_rate - 0.05)
            proxy.error_count += 1
        
        proxy.response_time = response_time
        proxy.last_used = time.time()


class ProxyManager:
    """Main proxy management class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize proxy manager.
        
        Args:
            config: Proxy configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.pool = ProxyPool(config.get('pool', {}))
        self.providers: List[ProxyProvider] = []
        self.crawlee_config: Optional[ProxyConfiguration] = None
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize proxy providers."""
        provider_configs = self.config.get('providers', [])
        
        for provider_config in provider_configs:
            provider_type = provider_config.get('type')
            provider_settings = provider_config.get('settings', {})
            
            if provider_type == 'bright_data':
                provider = BrightDataProvider(provider_settings)
            elif provider_type == 'oxylabs':
                provider = OxylabsProvider(provider_settings)
            else:
                self.logger.warning(f"Unknown proxy provider type: {provider_type}")
                continue
            
            self.providers.append(provider)
    
    async def initialize(self) -> None:
        """Initialize proxy manager."""
        self.logger.info("Initializing proxy manager")
        
        # Load proxies from all providers
        for provider in self.providers:
            try:
                proxies = await provider.get_proxies()
                await self.pool.add_proxies(proxies)
            except Exception as e:
                self.logger.error(f"Failed to load proxies from provider: {e}")
        
        # Initialize Crawlee proxy configuration
        if self.config.get('crawlee_integration', True):
            self.crawlee_config = ProxyConfiguration({
                'proxyUrls': [proxy.url for proxy in self.pool.proxies]
            })
        
        self.logger.info(f"Proxy manager initialized with {len(self.pool.proxies)} proxies")
    
    async def get_proxy(self, strategy: str = "round_robin") -> Optional[ProxyInfo]:
        """Get a proxy from the pool.
        
        Args:
            strategy: Selection strategy
            
        Returns:
            Selected proxy or None
        """
        return await self.pool.get_proxy(strategy)
    
    async def report_proxy_result(
        self, 
        proxy: ProxyInfo, 
        success: bool, 
        response_time: float
    ) -> None:
        """Report proxy usage result.
        
        Args:
            proxy: Proxy that was used
            success: Whether request was successful
            response_time: Response time in seconds
        """
        self.pool.update_proxy_stats(proxy, success, response_time)
    
    async def refresh_proxies(self) -> None:
        """Refresh proxy pool from providers."""
        self.logger.info("Refreshing proxy pool")
        
        # Clear existing proxies
        self.pool.proxies.clear()
        
        # Reload from providers
        for provider in self.providers:
            try:
                proxies = await provider.get_proxies()
                await self.pool.add_proxies(proxies)
            except Exception as e:
                self.logger.error(f"Failed to refresh proxies from provider: {e}")
        
        self.logger.info(f"Proxy pool refreshed with {len(self.pool.proxies)} proxies")
    
    def get_crawlee_config(self) -> Optional[ProxyConfiguration]:
        """Get Crawlee proxy configuration.
        
        Returns:
            Crawlee proxy configuration or None
        """
        return self.crawlee_config
