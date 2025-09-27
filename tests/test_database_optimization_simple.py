"""Simplified tests for database optimization module."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.database_optimization import (
    DatabaseType, ConnectionPoolStrategy, QueryOptimizationLevel,
    DatabaseConfig, ConnectionInfo, QueryStats, DatabaseMetrics,
    ConnectionPool, DatabaseOptimizer, get_database_manager, cleanup_database_resources
)


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = DatabaseConfig()
        assert config.database_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.pool_size == 10
        assert config.strategy == ConnectionPoolStrategy.DYNAMIC
        assert config.optimization_level == QueryOptimizationLevel.ADVANCED
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = DatabaseConfig(
            database_type=DatabaseType.MYSQL,
            host="test-host",
            port=3306,
            pool_size=20,
            strategy=ConnectionPoolStrategy.STATIC,
            optimization_level=QueryOptimizationLevel.AGGRESSIVE
        )
        assert config.database_type == DatabaseType.MYSQL
        assert config.host == "test-host"
        assert config.port == 3306
        assert config.pool_size == 20
        assert config.strategy == ConnectionPoolStrategy.STATIC
        assert config.optimization_level == QueryOptimizationLevel.AGGRESSIVE


class TestConnectionInfo:
    """Test connection information."""
    
    def test_connection_info_creation(self):
        """Test connection info creation."""
        conn_info = ConnectionInfo(
            connection_id="test-conn-1",
            created_at=time.time(),
            last_used=time.time()
        )
        assert conn_info.connection_id == "test-conn-1"
        assert conn_info.query_count == 0
        assert conn_info.is_active is True
        assert conn_info.error_count == 0


class TestQueryStats:
    """Test query statistics."""
    
    def test_query_stats_creation(self):
        """Test query stats creation."""
        stats = QueryStats(
            query_hash="abc123",
            query_text="SELECT * FROM users"
        )
        assert stats.query_hash == "abc123"
        assert stats.query_text == "SELECT * FROM users"
        assert stats.execution_count == 0
        assert stats.total_time == 0.0
        assert stats.min_time == float('inf')
        assert stats.max_time == 0.0
        assert stats.avg_time == 0.0
        assert stats.error_count == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0


class TestDatabaseMetrics:
    """Test database metrics."""
    
    def test_database_metrics_creation(self):
        """Test database metrics creation."""
        metrics = DatabaseMetrics()
        assert metrics.active_connections == 0
        assert metrics.total_connections == 0
        assert metrics.pool_utilization == 0.0
        assert metrics.avg_query_time == 0.0
        assert metrics.queries_per_second == 0.0
        assert metrics.error_rate == 0.0
        assert metrics.cache_hit_rate == 0.0
        assert metrics.connection_errors == 0
        assert metrics.query_errors == 0


class TestConnectionPool:
    """Test connection pool."""
    
    def test_initialization_without_drivers(self):
        """Test initialization without database drivers."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', False):
            with patch('spider.infrastructure.database_optimization.PSYCOPG2_AVAILABLE', False):
                with pytest.raises(Exception):
                    ConnectionPool(config)
    
    def test_optimize_query(self):
        """Test query optimization."""
        config = DatabaseConfig(
            optimization_level=QueryOptimizationLevel.ADVANCED
        )
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            
            # Test query optimization
            original_query = "SELECT * FROM users WHERE id = 1"
            optimized_query = pool.optimize_query(original_query)
            
            # Should be different (optimized)
            assert optimized_query != original_query
            assert "SELECT specific_columns" in optimized_query
    
    def test_get_metrics(self):
        """Test getting database metrics."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            
            metrics = pool.get_metrics()
            assert isinstance(metrics, DatabaseMetrics)
            assert metrics.total_connections == config.pool_size
    
    def test_get_query_stats(self):
        """Test getting query statistics."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            
            stats = pool.get_query_stats()
            assert isinstance(stats, dict)
            assert len(stats) == 0  # Initially empty
    
    def test_get_slow_queries(self):
        """Test getting slow queries."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            
            # Add some mock query stats
            pool.query_stats = {
                "query1": QueryStats(
                    query_hash="query1",
                    query_text="SELECT * FROM users",
                    avg_time=0.5
                ),
                "query2": QueryStats(
                    query_hash="query2",
                    query_text="SELECT * FROM products",
                    avg_time=1.5
                )
            }
            
            slow_queries = pool.get_slow_queries(1.0)  # Threshold 1 second
            assert len(slow_queries) == 1
            assert slow_queries[0].avg_time >= 1.0


class TestDatabaseOptimizer:
    """Test database optimizer."""
    
    def test_initialization(self):
        """Test optimizer initialization."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            optimizer = DatabaseOptimizer(pool)
            
            assert optimizer.connection_pool == pool
            assert len(optimizer.optimization_rules) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_query_performance(self):
        """Test query performance analysis."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            optimizer = DatabaseOptimizer(pool)
            
            # Add some mock query stats
            pool.query_stats = {
                "query1": QueryStats(
                    query_hash="query1",
                    query_text="SELECT * FROM users",
                    avg_time=0.5,
                    execution_count=10
                ),
                "query2": QueryStats(
                    query_hash="query2",
                    query_text="SELECT * FROM products",
                    avg_time=2.0,
                    execution_count=5
                )
            }
            
            # Analyze performance
            analysis = await optimizer.analyze_query_performance()
            
            assert "total_queries" in analysis
            assert "slow_queries" in analysis
            assert "avg_query_time" in analysis
            assert "recommendations" in analysis
            assert isinstance(analysis["recommendations"], list)
            assert analysis["total_queries"] == 2
            assert analysis["slow_queries"] == 1  # query2 is slow
    
    @pytest.mark.asyncio
    async def test_optimize_database(self):
        """Test database optimization."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        # Mock the pool initialization to avoid async issues
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            optimizer = DatabaseOptimizer(pool)
            
            # Optimize database
            results = await optimizer.optimize_database()
            
            assert "indexes_created" in results
            assert "queries_optimized" in results
            assert "cache_cleared" in results
            assert "connections_optimized" in results
            assert results["cache_cleared"] == 1


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_get_database_manager_without_async(self):
        """Test getting database manager without async context."""
        # This should work without async context
        with patch.object(ConnectionPool, '_initialize_pool'):
            manager = get_database_manager()
            assert isinstance(manager, ConnectionPool)
    
    def test_cleanup_database_resources(self):
        """Test cleanup database resources."""
        # Should not raise exception
        cleanup_database_resources()


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test different database types
        postgres_config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        mysql_config = DatabaseConfig(database_type=DatabaseType.MYSQL)
        sqlite_config = DatabaseConfig(database_type=DatabaseType.SQLITE)
        
        assert postgres_config.database_type == DatabaseType.POSTGRESQL
        assert mysql_config.database_type == DatabaseType.MYSQL
        assert sqlite_config.database_type == DatabaseType.SQLITE
    
    def test_connection_pool_strategies(self):
        """Test different connection pool strategies."""
        static_config = DatabaseConfig(strategy=ConnectionPoolStrategy.STATIC)
        dynamic_config = DatabaseConfig(strategy=ConnectionPoolStrategy.DYNAMIC)
        adaptive_config = DatabaseConfig(strategy=ConnectionPoolStrategy.ADAPTIVE)
        hybrid_config = DatabaseConfig(strategy=ConnectionPoolStrategy.HYBRID)
        
        assert static_config.strategy == ConnectionPoolStrategy.STATIC
        assert dynamic_config.strategy == ConnectionPoolStrategy.DYNAMIC
        assert adaptive_config.strategy == ConnectionPoolStrategy.ADAPTIVE
        assert hybrid_config.strategy == ConnectionPoolStrategy.HYBRID
    
    def test_query_optimization_levels(self):
        """Test different query optimization levels."""
        none_config = DatabaseConfig(optimization_level=QueryOptimizationLevel.NONE)
        basic_config = DatabaseConfig(optimization_level=QueryOptimizationLevel.BASIC)
        advanced_config = DatabaseConfig(optimization_level=QueryOptimizationLevel.ADVANCED)
        aggressive_config = DatabaseConfig(optimization_level=QueryOptimizationLevel.AGGRESSIVE)
        
        assert none_config.optimization_level == QueryOptimizationLevel.NONE
        assert basic_config.optimization_level == QueryOptimizationLevel.BASIC
        assert advanced_config.optimization_level == QueryOptimizationLevel.ADVANCED
        assert aggressive_config.optimization_level == QueryOptimizationLevel.AGGRESSIVE
    
    def test_query_optimization_different_levels(self):
        """Test query optimization with different levels."""
        query = "SELECT * FROM users WHERE id = 1"
        
        # Test different optimization levels
        with patch.object(ConnectionPool, '_initialize_pool'):
            # None level
            config_none = DatabaseConfig(optimization_level=QueryOptimizationLevel.NONE)
            pool_none = ConnectionPool(config_none)
            optimized_none = pool_none.optimize_query(query)
            assert optimized_none == query  # Should be unchanged
            
            # Basic level
            config_basic = DatabaseConfig(optimization_level=QueryOptimizationLevel.BASIC)
            pool_basic = ConnectionPool(config_basic)
            optimized_basic = pool_basic.optimize_query(query)
            assert optimized_basic != query  # Should be optimized
            
            # Advanced level
            config_advanced = DatabaseConfig(optimization_level=QueryOptimizationLevel.ADVANCED)
            pool_advanced = ConnectionPool(config_advanced)
            optimized_advanced = pool_advanced.optimize_query(query)
            assert optimized_advanced != query  # Should be optimized
            
            # Aggressive level
            config_aggressive = DatabaseConfig(optimization_level=QueryOptimizationLevel.AGGRESSIVE)
            pool_aggressive = ConnectionPool(config_aggressive)
            optimized_aggressive = pool_aggressive.optimize_query(query)
            assert optimized_aggressive != query  # Should be optimized
    
    def test_metrics_calculation(self):
        """Test metrics calculation."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch.object(ConnectionPool, '_initialize_pool'):
            pool = ConnectionPool(config)
            
            # Add some mock data
            pool.query_stats = {
                "query1": QueryStats(
                    query_hash="query1",
                    query_text="SELECT * FROM users",
                    execution_count=10,
                    total_time=5.0,
                    error_count=1,
                    cache_hits=8,
                    cache_misses=2
                )
            }
            
            # Manually trigger metrics calculation
            pool._update_query_stats("query1", "SELECT * FROM users", 0.5, False, False)
            
            # Get metrics
            metrics = pool.get_metrics()
            
            # Check that metrics are calculated
            assert metrics.total_connections == config.pool_size
            assert metrics.avg_query_time >= 0
            assert metrics.queries_per_second >= 0
            assert metrics.error_rate >= 0
            assert metrics.cache_hit_rate >= 0
