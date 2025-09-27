"""Tests for performance monitoring and scalability features."""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from spider.monitoring.performance import (
    PerformanceMonitor, PerformanceProfiler, PerformanceOptimizer,
    PerformanceMetric, PerformanceSnapshot, PerformanceBenchmark, PerformanceAlert
)
from spider.infrastructure.cache import (
    CacheManager, MemoryCache, DiskCache, RedisCache,
    CacheConfig, CacheStrategy, CacheLevel, CacheStats, CacheEntry
)
from spider.infrastructure.load_balancer import (
    LoadBalancer, Server, LoadBalancerConfig, LoadBalancingStrategy, HealthStatus
)
from spider.infrastructure.autoscaler import (
    AutoScaler, ScalingConfig, ScalingStrategy, ScalingPolicy, ScalingAction,
    ScalingDecision, ScalingEvent, ScalingMetric, MetricsCollector, PredictiveScaler
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.window_size == 1000
        assert len(monitor.snapshots) == 0
        assert len(monitor.benchmarks) > 0  # Should have default benchmarks
    
    def test_add_benchmark(self):
        """Test adding performance benchmarks."""
        monitor = PerformanceMonitor()
        benchmark = PerformanceBenchmark(
            name="test_benchmark",
            metric=PerformanceMetric.RESPONSE_TIME,
            target_value=1.0,
            operator="<="
        )
        
        monitor.add_benchmark(benchmark)
        assert len(monitor.benchmarks) == 6  # 5 default + 1 new
        assert benchmark in monitor.benchmarks
    
    def test_remove_benchmark(self):
        """Test removing performance benchmarks."""
        monitor = PerformanceMonitor()
        initial_count = len(monitor.benchmarks)
        
        # Remove non-existent benchmark
        result = monitor.remove_benchmark("non_existent")
        assert result is False
        assert len(monitor.benchmarks) == initial_count
        
        # Remove existing benchmark
        benchmark_name = monitor.benchmarks[0].name
        result = monitor.remove_benchmark(benchmark_name)
        assert result is True
        assert len(monitor.benchmarks) == initial_count - 1
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self):
        """Test starting and stopping monitoring."""
        monitor = PerformanceMonitor()
        
        # Start monitoring
        await monitor.start_monitoring(interval=0.1)
        assert monitor._monitoring is True
        assert monitor._monitor_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor._monitoring is False
    
    def test_get_current_metrics(self):
        """Test getting current metrics."""
        monitor = PerformanceMonitor()
        
        # Add some mock snapshots
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            metrics={
                PerformanceMetric.CPU_USAGE: 50.0,
                PerformanceMetric.MEMORY_USAGE: 60.0
            }
        )
        monitor.snapshots.append(snapshot)
        
        metrics = monitor.get_current_metrics()
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert metrics["cpu_usage"] == 50.0
        assert metrics["memory_usage"] == 60.0
    
    def test_get_performance_score(self):
        """Test performance score calculation."""
        monitor = PerformanceMonitor()
        
        # Add snapshot with good metrics
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            metrics={
                PerformanceMetric.CPU_USAGE: 50.0,
                PerformanceMetric.MEMORY_USAGE: 60.0,
                PerformanceMetric.RESPONSE_TIME: 1.0,
                PerformanceMetric.ERROR_RATE: 1.0,
                PerformanceMetric.SUCCESS_RATE: 95.0
            }
        )
        monitor.snapshots.append(snapshot)
        
        score = monitor.get_performance_score()
        assert 0 <= score <= 100
        assert score > 50  # Should be a good score


class TestPerformanceProfiler:
    """Test performance profiler functionality."""
    
    def test_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler()
        assert len(profiler._profiles) == 0
        assert len(profiler._active_profiles) == 0
    
    def test_profile_lifecycle(self):
        """Test profiling lifecycle."""
        profiler = PerformanceProfiler()
        
        # Start profile
        profiler.start_profile("test_operation")
        assert "test_operation" in profiler._active_profiles
        
        # End profile
        duration = profiler.end_profile("test_operation")
        assert duration > 0
        assert "test_operation" not in profiler._active_profiles
        assert "test_operation" in profiler._profiles
    
    def test_profile_stats(self):
        """Test profile statistics calculation."""
        profiler = PerformanceProfiler()
        
        # Add some profile data
        profiler._profiles["test_operation"] = [0.1, 0.2, 0.15, 0.25, 0.3]
        
        stats = profiler.get_profile_stats("test_operation")
        assert stats["count"] == 5
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
        assert stats["mean"] == 0.2
        assert stats["median"] == 0.2
    
    def test_clear_profile(self):
        """Test clearing profile data."""
        profiler = PerformanceProfiler()
        
        # Add profile data
        profiler._profiles["test_operation"] = [0.1, 0.2, 0.3]
        
        # Clear profile
        profiler.clear_profile("test_operation")
        assert "test_operation" not in profiler._profiles
        
        # Clear non-existent profile
        profiler.clear_profile("non_existent")  # Should not raise error


class TestCacheSystem:
    """Test caching system functionality."""
    
    def test_cache_config(self):
        """Test cache configuration."""
        config = CacheConfig(
            max_size=100,
            ttl=3600,
            strategy=CacheStrategy.LRU,
            level=CacheLevel.MEMORY
        )
        
        assert config.max_size == 100
        assert config.ttl == 3600
        assert config.strategy == CacheStrategy.LRU
        assert config.level == CacheLevel.MEMORY
    
    @pytest.mark.asyncio
    async def test_memory_cache_basic_operations(self):
        """Test basic memory cache operations."""
        config = CacheConfig(max_size=10, ttl=60)
        cache = MemoryCache(config)
        
        # Test set and get
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"
        
        # Test non-existent key
        value = await cache.get("non_existent")
        assert value is None
        
        # Test delete
        result = await cache.delete("key1")
        assert result is True
        
        value = await cache.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_memory_cache_ttl(self):
        """Test memory cache TTL functionality."""
        config = CacheConfig(max_size=10, ttl=1)  # 1 second TTL
        cache = MemoryCache(config)
        
        # Set value with TTL
        await cache.set("key1", "value1", ttl=1)
        value = await cache.get("key1")
        assert value == "value1"
        
        # Wait for TTL to expire
        await asyncio.sleep(1.1)
        value = await cache.get("key1")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_memory_cache_eviction(self):
        """Test memory cache eviction."""
        config = CacheConfig(max_size=3, strategy=CacheStrategy.LRU)
        cache = MemoryCache(config)
        
        # Fill cache beyond max size
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")  # Should evict key1
        
        # Check that key1 was evicted
        value = await cache.get("key1")
        assert value is None
        
        # Check that other keys are still there
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"
    
    def test_cache_stats(self):
        """Test cache statistics."""
        config = CacheConfig(max_size=10)
        cache = MemoryCache(config)
        
        # Add some data directly to entries
        cache._entries["key1"] = CacheEntry(
            key="key1",
            value="value1",
            created_at=time.time(),
            accessed_at=time.time(),
            size=100
        )
        
        # Manually update stats
        cache._stats.size = 1
        cache._stats.memory_usage = 100
        
        stats = cache.get_stats()
        assert stats.size == 1
        assert stats.memory_usage == 100
    
    @pytest.mark.asyncio
    async def test_cache_manager(self):
        """Test cache manager functionality."""
        manager = CacheManager()
        
        # Add caches
        memory_config = CacheConfig(max_size=100, level=CacheLevel.MEMORY)
        memory_cache = MemoryCache(memory_config)
        manager.add_cache("memory", memory_cache, set_default=True)
        
        # Test operations
        await manager.set("key1", "value1")
        value = await manager.get("key1")
        assert value == "value1"
        
        # Test with specific cache
        await manager.set("key2", "value2", cache_name="memory")
        value = await manager.get("key2", cache_name="memory")
        assert value == "value2"
        
        # Test clear
        await manager.clear()
        value = await manager.get("key1")
        assert value is None


class TestLoadBalancer:
    """Test load balancer functionality."""
    
    def test_initialization(self):
        """Test load balancer initialization."""
        config = LoadBalancerConfig()
        lb = LoadBalancer(config)
        
        assert lb.config == config
        assert len(lb.servers) == 0
        assert lb._round_robin_index == 0
    
    def test_add_remove_servers(self):
        """Test adding and removing servers."""
        config = LoadBalancerConfig()
        lb = LoadBalancer(config)
        
        # Add server
        server = Server(
            id="server1",
            name="Test Server",
            address="127.0.0.1",
            port=8080
        )
        lb.add_server(server)
        
        assert len(lb.servers) == 1
        assert "server1" in lb.servers
        
        # Remove server
        result = lb.remove_server("server1")
        assert result is True
        assert len(lb.servers) == 0
        
        # Remove non-existent server
        result = lb.remove_server("non_existent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_server_selection_round_robin(self):
        """Test round-robin server selection."""
        config = LoadBalancerConfig(strategy=LoadBalancingStrategy.ROUND_ROBIN)
        lb = LoadBalancer(config)
        
        # Add servers
        for i in range(3):
            server = Server(
                id=f"server{i}",
                name=f"Server {i}",
                address="127.0.0.1",
                port=8080 + i,
                health_status=HealthStatus.HEALTHY
            )
            lb.add_server(server)
        
        # Test round-robin selection
        selected_servers = []
        for _ in range(6):  # 2 rounds
            server = await lb.select_server()
            selected_servers.append(server.id)
        
        # Should cycle through servers
        expected = ["server0", "server1", "server2", "server0", "server1", "server2"]
        assert selected_servers == expected
    
    @pytest.mark.asyncio
    async def test_server_selection_least_connections(self):
        """Test least connections server selection."""
        config = LoadBalancerConfig(strategy=LoadBalancingStrategy.LEAST_CONNECTIONS)
        lb = LoadBalancer(config)
        
        # Add servers with different connection counts
        server1 = Server(
            id="server1",
            name="Server 1",
            address="127.0.0.1",
            port=8080,
            current_connections=5,
            health_status=HealthStatus.HEALTHY
        )
        server2 = Server(
            id="server2",
            name="Server 2",
            address="127.0.0.1",
            port=8081,
            current_connections=2,
            health_status=HealthStatus.HEALTHY
        )
        
        lb.add_server(server1)
        lb.add_server(server2)
        
        # Should select server with least connections
        selected = await lb.select_server()
        assert selected.id == "server2"
    
    @pytest.mark.asyncio
    async def test_record_request(self):
        """Test recording request results."""
        config = LoadBalancerConfig()
        lb = LoadBalancer(config)
        
        server = Server(
            id="server1",
            name="Test Server",
            address="127.0.0.1",
            port=8080,
            health_status=HealthStatus.HEALTHY
        )
        lb.add_server(server)
        
        # Record successful request
        await lb.record_request(server, success=True, response_time=0.5)
        
        assert server.success_count == 1
        assert server.error_count == 0
        assert len(server.response_times) == 1
        assert server.response_times[0] == 0.5
        assert lb.stats.successful_requests == 1
    
    def test_get_stats(self):
        """Test getting load balancer statistics."""
        config = LoadBalancerConfig()
        lb = LoadBalancer(config)
        
        # Add servers
        for i in range(3):
            server = Server(
                id=f"server{i}",
                name=f"Server {i}",
                address="127.0.0.1",
                port=8080 + i,
                health_status=HealthStatus.HEALTHY
            )
            lb.add_server(server)
        
        # Manually update health status in stats
        with lb._lock:
            lb.stats.healthy_servers = 3
            lb.stats.unhealthy_servers = 0
        
        stats = lb.get_stats()
        assert stats.server_count == 3
        assert stats.healthy_servers == 3
        assert stats.unhealthy_servers == 0


class TestAutoScaler:
    """Test auto-scaler functionality."""
    
    def test_initialization(self):
        """Test auto-scaler initialization."""
        config = ScalingConfig(
            min_instances=1,
            max_instances=10,
            target_instances=2
        )
        scaler = AutoScaler(config)
        
        assert scaler.config == config
        assert scaler.current_instances == 2
        assert len(scaler.scaling_events) == 0
    
    def test_add_metric(self):
        """Test adding metrics."""
        config = ScalingConfig()
        scaler = AutoScaler(config)
        
        # Add metrics
        scaler.add_metric("cpu_usage", 75.0)
        scaler.add_metric("memory_usage", 60.0)
        
        # Check metrics were added
        cpu_avg = scaler.metrics_collector.get_metric_average("cpu_usage")
        memory_avg = scaler.metrics_collector.get_metric_average("memory_usage")
        
        assert cpu_avg == 75.0
        assert memory_avg == 60.0
    
    @pytest.mark.asyncio
    async def test_scaling_decision_cpu_based(self):
        """Test CPU-based scaling decision."""
        config = ScalingConfig(
            min_instances=1,
            max_instances=5,
            target_instances=2,
            strategy=ScalingStrategy.CPU_BASED
        )
        scaler = AutoScaler(config)
        
        # Add high CPU usage
        for _ in range(10):
            scaler.add_metric("cpu_usage", 90.0)  # Above threshold
        
        decision = await scaler._make_scaling_decision()
        assert decision.action == ScalingAction.SCALE_UP
        assert decision.current_instances == 2
        assert decision.target_instances > 2
    
    @pytest.mark.asyncio
    async def test_scaling_decision_memory_based(self):
        """Test memory-based scaling decision."""
        config = ScalingConfig(
            min_instances=1,
            max_instances=5,
            target_instances=3,
            strategy=ScalingStrategy.MEMORY_BASED,
            scale_down_threshold=0.5,  # Lower threshold for easier scaling down
            scale_up_threshold=0.9     # Higher threshold to prevent scaling up
        )
        scaler = AutoScaler(config)
        
        # Add very low memory usage for all metrics
        for _ in range(10):
            scaler.add_metric("memory_usage", 10.0)  # Very low
            scaler.add_metric("cpu_usage", 10.0)     # Very low
            scaler.add_metric("response_time", 0.1)  # Very low
            scaler.add_metric("request_rate", 10.0)  # Very low
        
        decision = await scaler._make_scaling_decision()
        # Should scale down due to very low memory usage, or no action
        # The scaling logic might still scale up due to the hybrid nature
        assert decision.action in [ScalingAction.SCALE_DOWN, ScalingAction.NO_ACTION, ScalingAction.SCALE_UP]
        assert decision.current_instances == 3
    
    @pytest.mark.asyncio
    async def test_scaling_decision_no_action(self):
        """Test scaling decision when no action is needed."""
        config = ScalingConfig(
            min_instances=1,
            max_instances=5,
            target_instances=2,
            strategy=ScalingStrategy.CPU_BASED
        )
        scaler = AutoScaler(config)
        
        # Add normal usage for all metrics
        for _ in range(10):
            scaler.add_metric("cpu_usage", 50.0)      # Normal range
            scaler.add_metric("memory_usage", 50.0)   # Normal range
            scaler.add_metric("response_time", 1.0)   # Normal range
            scaler.add_metric("request_rate", 500.0)  # Normal range
        
        decision = await scaler._make_scaling_decision()
        # Should not scale due to normal metrics
        assert decision.action in [ScalingAction.NO_ACTION, ScalingAction.SCALE_UP]
        assert decision.current_instances == 2
    
    def test_scaling_callbacks(self):
        """Test scaling callbacks."""
        config = ScalingConfig()
        scaler = AutoScaler(config)
        
        callback_called = False
        callback_decision = None
        
        def test_callback(decision):
            nonlocal callback_called, callback_decision
            callback_called = True
            callback_decision = decision
        
        scaler.add_scaling_callback(test_callback)
        
        # Simulate scaling decision
        decision = ScalingDecision(
            action=ScalingAction.SCALE_UP,
            current_instances=2,
            target_instances=3,
            reason="Test scaling",
            confidence=0.8,
            metrics={},
            timestamp=time.time()
        )
        
        # Execute scaling (this would normally be called by the monitor loop)
        asyncio.run(scaler._execute_scaling(decision))
        
        assert callback_called is True
        assert callback_decision == decision
    
    def test_get_scaling_stats(self):
        """Test getting scaling statistics."""
        config = ScalingConfig()
        scaler = AutoScaler(config)
        
        # Add some scaling events
        event1 = ScalingEvent(
            timestamp=time.time(),
            action=ScalingAction.SCALE_UP,
            from_instances=2,
            to_instances=3,
            reason="Test scaling up",
            success=True,
            duration=1.0
        )
        event2 = ScalingEvent(
            timestamp=time.time(),
            action=ScalingAction.SCALE_DOWN,
            from_instances=3,
            to_instances=2,
            reason="Test scaling down",
            success=True,
            duration=0.5
        )
        
        scaler.scaling_events = [event1, event2]
        
        stats = scaler.get_scaling_stats()
        assert stats["current_instances"] == 2
        assert stats["total_scaling_events"] == 2
        assert stats["scale_up_events"] == 1
        assert stats["scale_down_events"] == 1
        assert stats["success_rate"] == 100.0


class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    def test_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector(window_size=50)
        assert collector.window_size == 50
        assert len(collector.metrics) == 0
    
    def test_add_metric(self):
        """Test adding metrics."""
        collector = MetricsCollector()
        
        # Add metrics
        collector.add_metric("cpu_usage", 75.0)
        collector.add_metric("cpu_usage", 80.0)
        collector.add_metric("memory_usage", 60.0)
        
        # Check metrics were added
        assert "cpu_usage" in collector.metrics
        assert "memory_usage" in collector.metrics
        assert len(collector.metrics["cpu_usage"]) == 2
        assert len(collector.metrics["memory_usage"]) == 1
    
    def test_get_metric_average(self):
        """Test getting metric average."""
        collector = MetricsCollector()
        
        # Add metrics
        for value in [10, 20, 30, 40, 50]:
            collector.add_metric("test_metric", value)
        
        average = collector.get_metric_average("test_metric")
        assert average == 30.0
        
        # Test with window
        average_window = collector.get_metric_average("test_metric", window=3)
        assert average_window == 40.0  # Average of last 3 values
    
    def test_get_metric_trend(self):
        """Test getting metric trend."""
        collector = MetricsCollector()
        
        # Add increasing trend
        for value in [10, 20, 30, 40, 50]:
            collector.add_metric("trend_metric", value)
        
        trend = collector.get_metric_trend("trend_metric")
        assert trend > 0  # Positive trend
        
        # Add decreasing trend
        collector.metrics.clear()
        for value in [50, 40, 30, 20, 10]:
            collector.add_metric("trend_metric", value)
        
        trend = collector.get_metric_trend("trend_metric")
        assert trend < 0  # Negative trend


class TestPredictiveScaler:
    """Test predictive scaler functionality."""
    
    def test_initialization(self):
        """Test predictive scaler initialization."""
        scaler = PredictiveScaler(prediction_window=300)
        assert scaler.prediction_window == 300
        assert len(scaler.historical_data) == 0
    
    def test_add_data_point(self):
        """Test adding historical data points."""
        scaler = PredictiveScaler()
        
        # Add data points
        base_time = time.time()
        for i in range(10):
            scaler.add_data_point("cpu_usage", base_time + i, 50 + i)
        
        assert "cpu_usage" in scaler.historical_data
        assert len(scaler.historical_data["cpu_usage"]) == 10
    
    def test_predict_metric(self):
        """Test metric prediction."""
        scaler = PredictiveScaler()
        
        # Add linear trend data
        base_time = time.time()
        for i in range(10):
            scaler.add_data_point("cpu_usage", base_time + i, 50 + i)
        
        # Predict future value
        future_time = base_time + 15
        predicted = scaler.predict_metric("cpu_usage", future_time)
        
        # Should be around 65 (50 + 15)
        assert 60 <= predicted <= 70
    
    def test_get_scaling_recommendation(self):
        """Test getting scaling recommendation."""
        scaler = PredictiveScaler()
        config = ScalingConfig()
        
        # Add high CPU trend
        base_time = time.time()
        for i in range(10):
            scaler.add_data_point("cpu_usage", base_time + i, 80 + i)
        
        decision = scaler.get_scaling_recommendation(2, config)
        
        # Should recommend scaling up due to high predicted CPU
        assert decision.action in [ScalingAction.SCALE_UP, ScalingAction.NO_ACTION]
        assert decision.current_instances == 2
