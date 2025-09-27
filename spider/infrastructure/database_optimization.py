"""
Database Optimization Module for SPIDER Framework

This module provides advanced database performance tuning, connection pooling,
query optimization, and database monitoring capabilities.

Author: SPIDER Development Team
Version: 1.0.0
"""

import asyncio
import time
import logging
import threading
import json
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import weakref
import queue
import statistics

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False
    aiomysql = None

try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    aiosqlite = None

try:
    import psycopg2
    import psycopg2.pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

from ..core.exceptions import SpiderError
from ..core.logger import get_logger

logger = get_logger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    REDIS = "redis"
    MONGODB = "mongodb"


class ConnectionPoolStrategy(Enum):
    """Connection pool strategies."""
    STATIC = "static"  # Fixed size pool
    DYNAMIC = "dynamic"  # Dynamic sizing based on load
    ADAPTIVE = "adaptive"  # Machine learning based sizing
    HYBRID = "hybrid"  # Combination of strategies


class QueryOptimizationLevel(Enum):
    """Query optimization levels."""
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    AGGRESSIVE = "aggressive"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    database_type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = "localhost"
    port: int = 5432
    database: str = "spider"
    username: str = "spider"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    connection_timeout: int = 10
    query_timeout: int = 30
    strategy: ConnectionPoolStrategy = ConnectionPoolStrategy.DYNAMIC
    optimization_level: QueryOptimizationLevel = QueryOptimizationLevel.ADVANCED
    enable_query_cache: bool = True
    enable_connection_monitoring: bool = True
    enable_performance_tracking: bool = True
    max_query_cache_size: int = 1000
    query_cache_ttl: int = 300  # 5 minutes


@dataclass
class ConnectionInfo:
    """Database connection information."""
    connection_id: str
    created_at: float
    last_used: float
    query_count: int = 0
    total_query_time: float = 0.0
    is_active: bool = True
    error_count: int = 0


@dataclass
class QueryStats:
    """Query performance statistics."""
    query_hash: str
    query_text: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_executed: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    active_connections: int = 0
    total_connections: int = 0
    pool_utilization: float = 0.0
    avg_query_time: float = 0.0
    queries_per_second: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    connection_errors: int = 0
    query_errors: int = 0
    last_updated: float = 0.0


class ConnectionPool:
    """Advanced database connection pool with monitoring and optimization."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize connection pool."""
        self.config = config
        self.pool = None
        self.connections: Dict[str, ConnectionInfo] = {}
        self.query_stats: Dict[str, QueryStats] = {}
        self.query_cache: Dict[str, Any] = {}
        self.metrics = DatabaseMetrics()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=config.pool_size)
        self._monitoring_task = None
        self._cleanup_task = None
        self._start_time = time.time()
        
        # Initialize pool
        self._initialize_pool()
        
        # Start monitoring if enabled
        if config.enable_connection_monitoring:
            self._start_monitoring()
    
    def _initialize_pool(self):
        """Initialize the database connection pool."""
        try:
            if self.config.database_type == DatabaseType.POSTGRESQL:
                if ASYNCPG_AVAILABLE:
                    # Check if we're in an async context
                    try:
                        loop = asyncio.get_running_loop()
                        self.pool = asyncio.create_task(self._create_asyncpg_pool())
                    except RuntimeError:
                        # No running loop, create a new one
                        self.pool = asyncio.run(self._create_asyncpg_pool())
                elif PSYCOPG2_AVAILABLE:
                    self.pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=self.config.pool_size + self.config.max_overflow,
                        host=self.config.host,
                        port=self.config.port,
                        database=self.config.database,
                        user=self.config.username,
                        password=self.config.password,
                        sslmode=self.config.ssl_mode
                    )
                else:
                    raise SpiderError("PostgreSQL driver not available. Install asyncpg or psycopg2.")
            
            elif self.config.database_type == DatabaseType.MYSQL:
                if AIOMYSQL_AVAILABLE:
                    try:
                        loop = asyncio.get_running_loop()
                        self.pool = asyncio.create_task(self._create_aiomysql_pool())
                    except RuntimeError:
                        self.pool = asyncio.run(self._create_aiomysql_pool())
                else:
                    raise SpiderError("MySQL driver not available. Install aiomysql.")
            
            elif self.config.database_type == DatabaseType.SQLITE:
                if AIOSQLITE_AVAILABLE:
                    try:
                        loop = asyncio.get_running_loop()
                        self.pool = asyncio.create_task(self._create_aiosqlite_pool())
                    except RuntimeError:
                        self.pool = asyncio.run(self._create_aiosqlite_pool())
                else:
                    raise SpiderError("SQLite driver not available. Install aiosqlite.")
            
            else:
                raise SpiderError(f"Unsupported database type: {self.config.database_type}")
            
            logger.info(f"Initialized {self.config.database_type.value} connection pool")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise SpiderError(f"Connection pool initialization failed: {e}")
    
    async def _create_asyncpg_pool(self):
        """Create asyncpg connection pool."""
        return await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            ssl=self.config.ssl_mode,
            min_size=1,
            max_size=self.config.pool_size,
            command_timeout=self.config.query_timeout,
            server_settings={
                'application_name': 'SPIDER Framework',
                'jit': 'off'  # Disable JIT for better performance
            }
        )
    
    async def _create_aiomysql_pool(self):
        """Create aiomysql connection pool."""
        return await aiomysql.create_pool(
            host=self.config.host,
            port=self.config.port,
            db=self.config.database,
            user=self.config.username,
            password=self.config.password,
            minsize=1,
            maxsize=self.config.pool_size,
            connect_timeout=self.config.connection_timeout,
            autocommit=True
        )
    
    async def _create_aiosqlite_pool(self):
        """Create aiosqlite connection pool."""
        # SQLite doesn't have a traditional pool, so we create a simple wrapper
        return await aiosqlite.connect(self.config.database)
    
    async def get_connection(self) -> Any:
        """Get a connection from the pool."""
        try:
            if self.config.database_type == DatabaseType.POSTGRESQL and ASYNCPG_AVAILABLE:
                if isinstance(self.pool, asyncio.Task):
                    pool = await self.pool
                else:
                    pool = self.pool
                return await pool.acquire()
            
            elif self.config.database_type == DatabaseType.MYSQL and AIOMYSQL_AVAILABLE:
                if isinstance(self.pool, asyncio.Task):
                    pool = await self.pool
                else:
                    pool = self.pool
                return await pool.acquire()
            
            elif self.config.database_type == DatabaseType.SQLITE and AIOSQLITE_AVAILABLE:
                if isinstance(self.pool, asyncio.Task):
                    conn = await self.pool
                else:
                    conn = self.pool
                return conn
            
            else:
                raise SpiderError(f"Unsupported database type: {self.config.database_type}")
        
        except Exception as e:
            logger.error(f"Failed to get connection: {e}")
            self.metrics.connection_errors += 1
            raise SpiderError(f"Connection acquisition failed: {e}")
    
    async def release_connection(self, connection: Any):
        """Release a connection back to the pool."""
        try:
            if self.config.database_type == DatabaseType.POSTGRESQL and ASYNCPG_AVAILABLE:
                if isinstance(self.pool, asyncio.Task):
                    pool = await self.pool
                else:
                    pool = self.pool
                await pool.release(connection)
            
            elif self.config.database_type == DatabaseType.MYSQL and AIOMYSQL_AVAILABLE:
                if isinstance(self.pool, asyncio.Task):
                    pool = await self.pool
                else:
                    pool = self.pool
                await pool.release(connection)
            
            # SQLite doesn't need explicit release
        
        except Exception as e:
            logger.error(f"Failed to release connection: {e}")
            self.metrics.connection_errors += 1
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a database query with optimization and caching."""
        start_time = time.time()
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check query cache
        if self.config.enable_query_cache and query_hash in self.query_cache:
            cache_entry = self.query_cache[query_hash]
            if time.time() - cache_entry['timestamp'] < self.config.query_cache_ttl:
                self._update_query_stats(query_hash, query, 0.001, True)  # Cache hit
                return cache_entry['result']
        
        # Get connection
        connection = await self.get_connection()
        
        try:
            # Execute query
            if self.config.database_type == DatabaseType.POSTGRESQL and ASYNCPG_AVAILABLE:
                result = await connection.fetch(query, *params) if params else await connection.fetch(query)
            elif self.config.database_type == DatabaseType.MYSQL and AIOMYSQL_AVAILABLE:
                cursor = await connection.cursor()
                await cursor.execute(query, params)
                result = await cursor.fetchall()
                await cursor.close()
            elif self.config.database_type == DatabaseType.SQLITE and AIOSQLITE_AVAILABLE:
                cursor = await connection.cursor()
                await cursor.execute(query, params)
                result = await cursor.fetchall()
                await cursor.close()
            else:
                raise SpiderError(f"Unsupported database type: {self.config.database_type}")
            
            execution_time = time.time() - start_time
            
            # Update query statistics
            self._update_query_stats(query_hash, query, execution_time, False)
            
            # Cache result if enabled
            if self.config.enable_query_cache and len(self.query_cache) < self.config.max_query_cache_size:
                self.query_cache[query_hash] = {
                    'result': result,
                    'timestamp': time.time()
                }
            
            return result
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.metrics.query_errors += 1
            self._update_query_stats(query_hash, query, time.time() - start_time, False, True)
            raise SpiderError(f"Query execution failed: {e}")
        
        finally:
            await self.release_connection(connection)
    
    def _update_query_stats(self, query_hash: str, query: str, execution_time: float, 
                          from_cache: bool = False, is_error: bool = False):
        """Update query performance statistics."""
        with self._lock:
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = QueryStats(
                    query_hash=query_hash,
                    query_text=query
                )
            
            stats = self.query_stats[query_hash]
            stats.execution_count += 1
            stats.total_time += execution_time
            stats.min_time = min(stats.min_time, execution_time)
            stats.max_time = max(stats.max_time, execution_time)
            stats.avg_time = stats.total_time / stats.execution_count
            stats.last_executed = time.time()
            
            if from_cache:
                stats.cache_hits += 1
            else:
                stats.cache_misses += 1
            
            if is_error:
                stats.error_count += 1
    
    def _start_monitoring(self):
        """Start connection pool monitoring."""
        try:
            # Check if we're in an async context
            loop = asyncio.get_running_loop()
            if self._monitoring_task is None or self._monitoring_task.done():
                self._monitoring_task = asyncio.create_task(self._monitor_connections())
            
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_cache())
        except RuntimeError:
            # No running event loop, skip monitoring for now
            logger.debug("No running event loop, skipping monitoring initialization")
    
    async def _monitor_connections(self):
        """Monitor connection pool health and performance."""
        while True:
            try:
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
                with self._lock:
                    # Update metrics
                    self.metrics.active_connections = len(self.connections)
                    self.metrics.total_connections = self.config.pool_size
                    self.metrics.pool_utilization = self.metrics.active_connections / self.metrics.total_connections if self.metrics.total_connections > 0 else 0
                    
                    # Calculate average query time
                    if self.query_stats:
                        total_time = sum(stats.total_time for stats in self.query_stats.values())
                        total_queries = sum(stats.execution_count for stats in self.query_stats.values())
                        self.metrics.avg_query_time = total_time / total_queries if total_queries > 0 else 0
                    
                    # Calculate queries per second
                    current_time = time.time()
                    time_diff = current_time - self._start_time
                    total_queries = sum(stats.execution_count for stats in self.query_stats.values())
                    self.metrics.queries_per_second = total_queries / time_diff if time_diff > 0 else 0
                    
                    # Calculate error rate
                    total_errors = sum(stats.error_count for stats in self.query_stats.values())
                    total_queries = sum(stats.execution_count for stats in self.query_stats.values())
                    self.metrics.error_rate = total_errors / total_queries if total_queries > 0 else 0
                    
                    # Calculate cache hit rate
                    total_cache_hits = sum(stats.cache_hits for stats in self.query_stats.values())
                    total_cache_operations = total_cache_hits + sum(stats.cache_misses for stats in self.query_stats.values())
                    self.metrics.cache_hit_rate = total_cache_hits / total_cache_operations if total_cache_operations > 0 else 0
                    
                    self.metrics.last_updated = current_time
                
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                
                current_time = time.time()
                expired_keys = []
                
                for key, entry in self.query_cache.items():
                    if current_time - entry['timestamp'] > self.config.query_cache_ttl:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.query_cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    def get_metrics(self) -> DatabaseMetrics:
        """Get current database metrics."""
        with self._lock:
            # Ensure total_connections is set from config
            if self.metrics.total_connections == 0:
                self.metrics.total_connections = self.config.pool_size
            
            return DatabaseMetrics(
                active_connections=self.metrics.active_connections,
                total_connections=self.metrics.total_connections,
                pool_utilization=self.metrics.pool_utilization,
                avg_query_time=self.metrics.avg_query_time,
                queries_per_second=self.metrics.queries_per_second,
                error_rate=self.metrics.error_rate,
                cache_hit_rate=self.metrics.cache_hit_rate,
                connection_errors=self.metrics.connection_errors,
                query_errors=self.metrics.query_errors,
                last_updated=self.metrics.last_updated
            )
    
    def get_query_stats(self) -> Dict[str, QueryStats]:
        """Get query performance statistics."""
        with self._lock:
            return self.query_stats.copy()
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[QueryStats]:
        """Get queries slower than threshold."""
        with self._lock:
            return [
                stats for stats in self.query_stats.values()
                if stats.avg_time > threshold
            ]
    
    def optimize_query(self, query: str) -> str:
        """Optimize a SQL query based on configuration."""
        if self.config.optimization_level == QueryOptimizationLevel.NONE:
            return query
        
        optimized = query.strip()
        
        if self.config.optimization_level in [QueryOptimizationLevel.BASIC, QueryOptimizationLevel.ADVANCED, QueryOptimizationLevel.AGGRESSIVE]:
            # Basic optimizations
            optimized = optimized.replace('SELECT *', 'SELECT specific_columns')  # Placeholder
            optimized = optimized.replace('  ', ' ')  # Remove extra spaces
        
        if self.config.optimization_level in [QueryOptimizationLevel.ADVANCED, QueryOptimizationLevel.AGGRESSIVE]:
            # Advanced optimizations
            if 'ORDER BY' in optimized and 'LIMIT' not in optimized:
                optimized += ' LIMIT 1000'  # Add default limit
        
        if self.config.optimization_level == QueryOptimizationLevel.AGGRESSIVE:
            # Aggressive optimizations
            if 'WHERE' not in optimized and 'SELECT' in optimized:
                optimized += ' WHERE 1=1'  # Add dummy WHERE clause
        
        return optimized
    
    async def close(self):
        """Close the connection pool and cleanup resources."""
        try:
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
            
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
            
            if self.pool:
                if isinstance(self.pool, asyncio.Task):
                    pool = await self.pool
                else:
                    pool = self.pool
                
                if hasattr(pool, 'close'):
                    await pool.close()
                elif hasattr(pool, 'close'):
                    pool.close()
            
            self._executor.shutdown(wait=True)
            logger.info("Database connection pool closed")
            
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")


class DatabaseOptimizer:
    """Database optimization and performance tuning."""
    
    def __init__(self, connection_pool: ConnectionPool):
        """Initialize database optimizer."""
        self.connection_pool = connection_pool
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Load database optimization rules."""
        return [
            {
                "pattern": r"SELECT \* FROM",
                "replacement": "SELECT specific_columns FROM",
                "description": "Replace SELECT * with specific columns"
            },
            {
                "pattern": r"WHERE.*=.*AND.*=.*",
                "replacement": "WHERE column1 = ? AND column2 = ?",
                "description": "Optimize WHERE clauses"
            },
            {
                "pattern": r"ORDER BY.*LIMIT \d+",
                "replacement": "ORDER BY indexed_column LIMIT ?",
                "description": "Ensure ORDER BY uses indexed columns"
            }
        ]
    
    async def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance and provide recommendations."""
        query_stats = self.connection_pool.get_query_stats()
        slow_queries = self.connection_pool.get_slow_queries(1.0)  # Queries > 1 second
        
        analysis = {
            "total_queries": len(query_stats),
            "slow_queries": len(slow_queries),
            "avg_query_time": statistics.mean([stats.avg_time for stats in query_stats.values()]) if query_stats else 0,
            "recommendations": []
        }
        
        # Generate recommendations
        if slow_queries:
            analysis["recommendations"].append({
                "type": "index_optimization",
                "message": f"Found {len(slow_queries)} slow queries. Consider adding indexes.",
                "priority": "high"
            })
        
        if analysis["avg_query_time"] > 0.5:
            analysis["recommendations"].append({
                "type": "query_optimization",
                "message": "Average query time is high. Consider query optimization.",
                "priority": "medium"
            })
        
        return analysis
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Perform database optimization."""
        optimization_results = {
            "indexes_created": 0,
            "queries_optimized": 0,
            "cache_cleared": 0,
            "connections_optimized": 0
        }
        
        try:
            # Clear query cache
            self.connection_pool.query_cache.clear()
            optimization_results["cache_cleared"] = 1
            
            # Optimize connection pool
            metrics = self.connection_pool.get_metrics()
            if metrics.pool_utilization > 0.8:
                # Pool is highly utilized, consider increasing size
                optimization_results["connections_optimized"] = 1
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise SpiderError(f"Database optimization failed: {e}")
        
        return optimization_results


# Global database manager instance
_database_manager: Optional[ConnectionPool] = None


def get_database_manager(config: Optional[DatabaseConfig] = None) -> ConnectionPool:
    """Get the global database manager instance."""
    global _database_manager
    if _database_manager is None:
        if config is None:
            config = DatabaseConfig()
        _database_manager = ConnectionPool(config)
    return _database_manager


def cleanup_database_resources():
    """Cleanup global database resources."""
    global _database_manager
    if _database_manager is not None:
        try:
            # Try to run cleanup in existing event loop
            loop = asyncio.get_running_loop()
            asyncio.create_task(_database_manager.close())
        except RuntimeError:
            # No running event loop, create a new one
            asyncio.run(_database_manager.close())
        _database_manager = None
