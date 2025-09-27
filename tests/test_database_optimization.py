"""Tests for database optimization module."""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, MagicMock, AsyncMock

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
    
    @pytest.mark.asyncio
    async def test_asyncpg_pool_creation(self):
        """Test asyncpg pool creation."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                mock_asyncpg.create_pool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_aiomysql_pool_creation(self):
        """Test aiomysql pool creation."""
        config = DatabaseConfig(database_type=DatabaseType.MYSQL)
        
        with patch('spider.infrastructure.database_optimization.AIOMYSQL_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.aiomysql') as mock_aiomysql:
                mock_pool = AsyncMock()
                mock_aiomysql.create_pool = AsyncMock(return_value=mock_pool)
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                mock_aiomysql.create_pool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_aiosqlite_pool_creation(self):
        """Test aiosqlite pool creation."""
        config = DatabaseConfig(database_type=DatabaseType.SQLITE)
        
        with patch('spider.infrastructure.database_optimization.AIOSQLITE_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.aiosqlite') as mock_aiosqlite:
                mock_conn = AsyncMock()
                mock_aiosqlite.connect = AsyncMock(return_value=mock_conn)
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                mock_aiosqlite.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_connection_asyncpg(self):
        """Test getting connection with asyncpg."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_pool.acquire = AsyncMock(return_value=mock_connection)
                mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                connection = await pool.get_connection()
                assert connection == mock_connection
                mock_pool.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_release_connection_asyncpg(self):
        """Test releasing connection with asyncpg."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                await pool.release_connection(mock_connection)
                mock_pool.release.assert_called_once_with(mock_connection)
    
    @pytest.mark.asyncio
    async def test_execute_query_asyncpg(self):
        """Test executing query with asyncpg."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                result = await pool.execute_query("SELECT * FROM users")
                assert result == mock_result
                mock_connection.fetch.assert_called_once_with("SELECT * FROM users")
                mock_pool.release.assert_called_once_with(mock_connection)
    
    @pytest.mark.asyncio
    async def test_query_caching(self):
        """Test query result caching."""
        config = DatabaseConfig(
            database_type=DatabaseType.POSTGRESQL,
            enable_query_cache=True,
            query_cache_ttl=60
        )
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # First execution
                result1 = await pool.execute_query("SELECT * FROM users")
                assert result1 == mock_result
                
                # Second execution (should use cache)
                result2 = await pool.execute_query("SELECT * FROM users")
                assert result2 == mock_result
                
                # Should only call fetch once due to caching
                assert mock_connection.fetch.call_count == 1
    
    @pytest.mark.asyncio
    async def test_query_stats_update(self):
        """Test query statistics update."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Execute query
                await pool.execute_query("SELECT * FROM users")
                
                # Check stats
                stats = pool.get_query_stats()
                assert len(stats) == 1
                
                query_hash = list(stats.keys())[0]
                query_stats = stats[query_hash]
                assert query_stats.execution_count == 1
                assert query_stats.query_text == "SELECT * FROM users"
                assert query_stats.avg_time > 0
    
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting database metrics."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                metrics = pool.get_metrics()
                assert isinstance(metrics, DatabaseMetrics)
                assert metrics.total_connections == config.pool_size
    
    @pytest.mark.asyncio
    async def test_get_slow_queries(self):
        """Test getting slow queries."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Execute a slow query (simulated)
                with patch('time.time', side_effect=[0, 2]):  # 2 second execution
                    await pool.execute_query("SELECT * FROM users")
                
                # Get slow queries
                slow_queries = pool.get_slow_queries(1.0)  # Threshold 1 second
                assert len(slow_queries) == 1
                assert slow_queries[0].avg_time >= 1.0
    
    def test_optimize_query(self):
        """Test query optimization."""
        config = DatabaseConfig(
            optimization_level=QueryOptimizationLevel.ADVANCED
        )
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                
                # Test query optimization
                original_query = "SELECT * FROM users WHERE id = 1"
                optimized_query = pool.optimize_query(original_query)
                
                # Should be different (optimized)
                assert optimized_query != original_query
                assert "SELECT specific_columns" in optimized_query
    
    @pytest.mark.asyncio
    async def test_close_pool(self):
        """Test closing connection pool."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Close pool
                await pool.close()
                
                # Should not raise exception
                assert True


class TestDatabaseOptimizer:
    """Test database optimizer."""
    
    @pytest.mark.asyncio
    async def test_analyze_query_performance(self):
        """Test query performance analysis."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                optimizer = DatabaseOptimizer(pool)
                
                # Analyze performance
                analysis = await optimizer.analyze_query_performance()
                
                assert "total_queries" in analysis
                assert "slow_queries" in analysis
                assert "avg_query_time" in analysis
                assert "recommendations" in analysis
                assert isinstance(analysis["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_optimize_database(self):
        """Test database optimization."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
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
    
    def test_get_database_manager(self):
        """Test getting database manager."""
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                manager = get_database_manager()
                assert isinstance(manager, ConnectionPool)
    
    def test_cleanup_database_resources(self):
        """Test cleanup database resources."""
        # Should not raise exception
        cleanup_database_resources()


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full database workflow."""
        config = DatabaseConfig(
            database_type=DatabaseType.POSTGRESQL,
            enable_query_cache=True,
            enable_connection_monitoring=True
        )
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Execute multiple queries
                await pool.execute_query("SELECT * FROM users")
                await pool.execute_query("SELECT * FROM products")
                
                # Check metrics
                metrics = pool.get_metrics()
                assert metrics.total_connections == config.pool_size
                
                # Check query stats
                stats = pool.get_query_stats()
                assert len(stats) == 2
                
                # Test optimizer
                optimizer = DatabaseOptimizer(pool)
                analysis = await optimizer.analyze_query_performance()
                assert analysis["total_queries"] == 2
                
                # Cleanup
                await pool.close()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in database operations."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                
                # Simulate query error
                mock_connection.fetch.side_effect = Exception("Query failed")
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Execute query that will fail
                with pytest.raises(Exception):
                    await pool.execute_query("SELECT * FROM users")
                
                # Check error metrics
                metrics = pool.get_metrics()
                assert metrics.query_errors > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent database operations."""
        config = DatabaseConfig(database_type=DatabaseType.POSTGRESQL)
        
        with patch('spider.infrastructure.database_optimization.ASYNCPG_AVAILABLE', True):
            with patch('spider.infrastructure.database_optimization.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_result = [{"id": 1, "name": "test"}]
                
                mock_connection.fetch.return_value = mock_result
                mock_pool.acquire.return_value = mock_connection
                mock_asyncpg.create_pool.return_value = mock_pool
                
                pool = ConnectionPool(config)
                await asyncio.sleep(0.1)  # Allow initialization to complete
                
                # Execute concurrent queries
                async def execute_query(i):
                    return await pool.execute_query(f"SELECT * FROM table{i}")
                
                tasks = [execute_query(i) for i in range(5)]
                results = await asyncio.gather(*tasks)
                
                # All queries should succeed
                assert len(results) == 5
                for result in results:
                    assert result == mock_result
                
                # Check that all queries were executed
                stats = pool.get_query_stats()
                assert len(stats) == 5
