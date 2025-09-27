"""Intelligent load balancing for SPIDER framework."""

import asyncio
import time
import random
import statistics
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque, defaultdict
import math

from ..core.exceptions import SpiderError, EngineError
from ..core.logger import get_logger


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    RANDOM = "random"
    HASH = "hash"
    ADAPTIVE = "adaptive"


class HealthStatus(Enum):
    """Health status for load balancer."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class Server:
    """Server instance for load balancing."""
    id: str
    name: str
    address: str
    port: int
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0
    success_count: int = 0
    last_health_check: float = 0.0
    health_status: HealthStatus = HealthStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def average_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100
    
    @property
    def connection_utilization(self) -> float:
        """Get connection utilization percentage."""
        if self.max_connections == 0:
            return 0.0
        return (self.current_connections / self.max_connections) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Check if server is healthy."""
        return self.health_status == HealthStatus.HEALTHY
    
    @property
    def is_available(self) -> bool:
        """Check if server is available for new connections."""
        return (
            self.is_healthy and 
            self.current_connections < self.max_connections
        )


@dataclass
class LoadBalancerConfig:
    """Load balancer configuration."""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_interval: float = 30.0
    health_check_timeout: float = 5.0
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    enable_sticky_sessions: bool = False
    session_timeout: float = 3600.0


@dataclass
class LoadBalancerStats:
    """Load balancer statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    current_connections: int = 0
    server_count: int = 0
    healthy_servers: int = 0
    unhealthy_servers: int = 0


class HealthChecker:
    """Health checker for servers."""
    
    def __init__(self, timeout: float = 5.0):
        """Initialize health checker.
        
        Args:
            timeout: Health check timeout
        """
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)
    
    async def check_health(self, server: Server) -> HealthStatus:
        """Check server health.
        
        Args:
            server: Server to check
            
        Returns:
            Health status
        """
        try:
            # This would implement actual health checking
            # For now, we'll simulate based on server metrics
            
            # Check if server has too many errors
            if server.error_count > 10 and server.success_rate < 50:
                return HealthStatus.UNHEALTHY
            
            # Check if server is overloaded
            if server.connection_utilization > 90:
                return HealthStatus.DEGRADED
            
            # Check if server has recent activity
            if time.time() - server.last_health_check > 300:  # 5 minutes
                return HealthStatus.UNKNOWN
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            self.logger.error(f"Health check failed for {server.id}: {e}")
            return HealthStatus.UNHEALTHY


class LoadBalancer:
    """Intelligent load balancer for SPIDER framework."""
    
    def __init__(self, config: LoadBalancerConfig):
        """Initialize load balancer.
        
        Args:
            config: Load balancer configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.servers: Dict[str, Server] = {}
        self.stats = LoadBalancerStats()
        self.health_checker = HealthChecker(config.health_check_timeout)
        self._lock = threading.RLock()
        self._round_robin_index = 0
        self._session_servers: Dict[str, str] = {}  # session_id -> server_id
        self._circuit_breakers: Dict[str, float] = {}  # server_id -> open_until
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def add_server(self, server: Server) -> None:
        """Add server to load balancer.
        
        Args:
            server: Server instance
        """
        with self._lock:
            self.servers[server.id] = server
            self.stats.server_count = len(self.servers)
            self.logger.info(f"Added server: {server.name} ({server.address}:{server.port})")
    
    def remove_server(self, server_id: str) -> bool:
        """Remove server from load balancer.
        
        Args:
            server_id: Server ID
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if server_id in self.servers:
                del self.servers[server_id]
                self.stats.server_count = len(self.servers)
                self.logger.info(f"Removed server: {server_id}")
                return True
            return False
    
    def get_server(self, server_id: str) -> Optional[Server]:
        """Get server by ID.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server instance or None
        """
        return self.servers.get(server_id)
    
    async def select_server(
        self, 
        session_id: Optional[str] = None,
        request_hash: Optional[str] = None
    ) -> Optional[Server]:
        """Select server using configured strategy.
        
        Args:
            session_id: Optional session ID for sticky sessions
            request_hash: Optional request hash for hash-based routing
            
        Returns:
            Selected server or None
        """
        with self._lock:
            # Check for sticky sessions
            if self.config.enable_sticky_sessions and session_id:
                if session_id in self._session_servers:
                    server_id = self._session_servers[session_id]
                    if server_id in self.servers:
                        server = self.servers[server_id]
                        if server.is_available:
                            return server
            
            # Filter available servers
            available_servers = [
                server for server in self.servers.values()
                if server.is_available and not self._is_circuit_open(server.id)
            ]
            
            if not available_servers:
                self.logger.warning("No available servers")
                return None
            
            # Select server based on strategy
            if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected = self._select_round_robin(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected = self._select_least_connections(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                selected = self._select_least_response_time(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                selected = self._select_weighted_round_robin(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_LEAST_CONNECTIONS:
                selected = self._select_weighted_least_connections(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.RANDOM:
                selected = self._select_random(available_servers)
            elif self.config.strategy == LoadBalancingStrategy.HASH:
                selected = self._select_hash(available_servers, request_hash)
            elif self.config.strategy == LoadBalancingStrategy.ADAPTIVE:
                selected = self._select_adaptive(available_servers)
            else:
                selected = available_servers[0]
            
            # Update session mapping for sticky sessions
            if self.config.enable_sticky_sessions and session_id:
                self._session_servers[session_id] = selected.id
            
            return selected
    
    def _select_round_robin(self, servers: List[Server]) -> Server:
        """Select server using round-robin strategy."""
        if not servers:
            return None
        
        selected = servers[self._round_robin_index % len(servers)]
        self._round_robin_index += 1
        return selected
    
    def _select_least_connections(self, servers: List[Server]) -> Server:
        """Select server with least connections."""
        return min(servers, key=lambda s: s.current_connections)
    
    def _select_least_response_time(self, servers: List[Server]) -> Server:
        """Select server with least response time."""
        return min(servers, key=lambda s: s.average_response_time)
    
    def _select_weighted_round_robin(self, servers: List[Server]) -> Server:
        """Select server using weighted round-robin strategy."""
        if not servers:
            return None
        
        # Calculate total weight
        total_weight = sum(server.weight for server in servers)
        if total_weight == 0:
            return servers[0]
        
        # Use round-robin with weights
        current_weight = 0
        for server in servers:
            current_weight += server.weight
            if self._round_robin_index % total_weight < current_weight:
                self._round_robin_index += 1
                return server
        
        return servers[0]
    
    def _select_weighted_least_connections(self, servers: List[Server]) -> Server:
        """Select server using weighted least connections."""
        if not servers:
            return None
        
        # Calculate weighted connection ratio
        best_server = None
        best_ratio = float('inf')
        
        for server in servers:
            if server.weight == 0:
                continue
            
            ratio = server.current_connections / server.weight
            if ratio < best_ratio:
                best_ratio = ratio
                best_server = server
        
        return best_server or servers[0]
    
    def _select_random(self, servers: List[Server]) -> Server:
        """Select server randomly."""
        return random.choice(servers)
    
    def _select_hash(self, servers: List[Server], request_hash: Optional[str]) -> Server:
        """Select server using hash-based routing."""
        if not servers or not request_hash:
            return servers[0] if servers else None
        
        # Use hash to select server
        hash_value = hash(request_hash)
        index = hash_value % len(servers)
        return servers[index]
    
    def _select_adaptive(self, servers: List[Server]) -> Server:
        """Select server using adaptive strategy."""
        if not servers:
            return None
        
        # Calculate score for each server based on multiple factors
        best_server = None
        best_score = float('-inf')
        
        for server in servers:
            # Calculate composite score
            score = 0
            
            # Weight by server weight
            score += server.weight * 10
            
            # Penalize by connection utilization
            score -= server.connection_utilization * 0.1
            
            # Penalize by response time
            score -= server.average_response_time * 0.01
            
            # Reward by success rate
            score += server.success_rate * 0.1
            
            # Penalize by error count
            score -= server.error_count * 0.5
            
            if score > best_score:
                best_score = score
                best_server = server
        
        return best_server or servers[0]
    
    def _is_circuit_open(self, server_id: str) -> bool:
        """Check if circuit breaker is open for server.
        
        Args:
            server_id: Server ID
            
        Returns:
            True if circuit is open
        """
        if server_id not in self._circuit_breakers:
            return False
        
        open_until = self._circuit_breakers[server_id]
        if time.time() < open_until:
            return True
        
        # Circuit breaker timeout expired
        del self._circuit_breakers[server_id]
        return False
    
    async def record_request(
        self, 
        server: Server, 
        success: bool, 
        response_time: float
    ) -> None:
        """Record request result.
        
        Args:
            server: Server that handled the request
            success: Whether request was successful
            response_time: Response time in seconds
        """
        with self._lock:
            # Update server stats
            server.response_times.append(response_time)
            if success:
                server.success_count += 1
            else:
                server.error_count += 1
                
                # Check circuit breaker
                if server.error_count >= self.config.circuit_breaker_threshold:
                    self._circuit_breakers[server.id] = (
                        time.time() + self.config.circuit_breaker_timeout
                    )
                    self.logger.warning(f"Circuit breaker opened for server {server.id}")
            
            # Update load balancer stats
            self.stats.total_requests += 1
            if success:
                self.stats.successful_requests += 1
            else:
                self.stats.failed_requests += 1
            
            # Update average response time
            all_response_times = []
            for s in self.servers.values():
                all_response_times.extend(s.response_times)
            
            if all_response_times:
                self.stats.average_response_time = statistics.mean(all_response_times)
    
    async def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self._monitoring:
            self.logger.warning("Health monitoring is already running")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Started health monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped health monitoring")
    
    async def _monitor_loop(self) -> None:
        """Health monitoring loop."""
        try:
            while self._monitoring:
                await self._check_all_servers()
                await asyncio.sleep(self.config.health_check_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in health monitoring: {e}")
    
    async def _check_all_servers(self) -> None:
        """Check health of all servers."""
        tasks = []
        for server in self.servers.values():
            tasks.append(self._check_server_health(server))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_server_health(self, server: Server) -> None:
        """Check health of a single server.
        
        Args:
            server: Server to check
        """
        try:
            health_status = await self.health_checker.check_health(server)
            server.health_status = health_status
            server.last_health_check = time.time()
            
            # Update stats
            with self._lock:
                healthy_count = sum(1 for s in self.servers.values() if s.is_healthy)
                self.stats.healthy_servers = healthy_count
                self.stats.unhealthy_servers = len(self.servers) - healthy_count
                
        except Exception as e:
            self.logger.error(f"Health check failed for {server.id}: {e}")
            server.health_status = HealthStatus.UNHEALTHY
    
    def get_stats(self) -> LoadBalancerStats:
        """Get load balancer statistics.
        
        Returns:
            Load balancer statistics
        """
        with self._lock:
            # Update current connections
            self.stats.current_connections = sum(
                server.current_connections for server in self.servers.values()
            )
            
            return LoadBalancerStats(
                total_requests=self.stats.total_requests,
                successful_requests=self.stats.successful_requests,
                failed_requests=self.stats.failed_requests,
                average_response_time=self.stats.average_response_time,
                current_connections=self.stats.current_connections,
                server_count=self.stats.server_count,
                healthy_servers=self.stats.healthy_servers,
                unhealthy_servers=self.stats.unhealthy_servers
            )
    
    def get_server_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all servers.
        
        Returns:
            Server statistics
        """
        with self._lock:
            return {
                server_id: {
                    "name": server.name,
                    "address": f"{server.address}:{server.port}",
                    "weight": server.weight,
                    "current_connections": server.current_connections,
                    "max_connections": server.max_connections,
                    "connection_utilization": server.connection_utilization,
                    "average_response_time": server.average_response_time,
                    "success_rate": server.success_rate,
                    "health_status": server.health_status.value,
                    "is_available": server.is_available
                }
                for server_id, server in self.servers.items()
            }
    
    def cleanup(self) -> None:
        """Cleanup load balancer."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        
        with self._lock:
            self.servers.clear()
            self._session_servers.clear()
            self._circuit_breakers.clear()
        
        self.logger.info("Load balancer cleaned up")
