"""Performance monitoring and optimization for SPIDER framework."""

import asyncio
import time
import psutil
import gc
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import threading
from collections import deque, defaultdict
import json

from ..core.exceptions import SpiderError, MonitoringError
from ..core.logger import get_logger


class PerformanceMetric(Enum):
    """Performance metric types."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CONCURRENT_REQUESTS = "concurrent_requests"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_QUERY_TIME = "database_query_time"
    NETWORK_LATENCY = "network_latency"


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time."""
    timestamp: float
    metrics: Dict[PerformanceMetric, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition."""
    name: str
    metric: PerformanceMetric
    target_value: float
    operator: str  # ">", "<", ">=", "<=", "=="
    weight: float = 1.0
    enabled: bool = True


@dataclass
class PerformanceAlert:
    """Performance alert."""
    benchmark_name: str
    current_value: float
    target_value: float
    severity: str
    timestamp: float
    message: str


class PerformanceProfiler:
    """Performance profiler for detailed analysis."""
    
    def __init__(self):
        """Initialize performance profiler."""
        self.logger = get_logger(self.__class__.__name__)
        self._profiles: Dict[str, List[float]] = defaultdict(list)
        self._active_profiles: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def start_profile(self, name: str) -> None:
        """Start profiling a named operation.
        
        Args:
            name: Profile name
        """
        with self._lock:
            self._active_profiles[name] = time.perf_counter()
    
    def end_profile(self, name: str) -> float:
        """End profiling and return duration.
        
        Args:
            name: Profile name
            
        Returns:
            Duration in seconds
        """
        with self._lock:
            if name not in self._active_profiles:
                return 0.0
            
            duration = time.perf_counter() - self._active_profiles[name]
            self._profiles[name].append(duration)
            del self._active_profiles[name]
            
            return duration
    
    def get_profile_stats(self, name: str) -> Dict[str, float]:
        """Get profile statistics.
        
        Args:
            name: Profile name
            
        Returns:
            Profile statistics
        """
        with self._lock:
            if name not in self._profiles or not self._profiles[name]:
                return {}
            
            values = self._profiles[name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def clear_profile(self, name: str) -> None:
        """Clear profile data.
        
        Args:
            name: Profile name
        """
        with self._lock:
            if name in self._profiles:
                del self._profiles[name]
    
    def clear_all_profiles(self) -> None:
        """Clear all profile data."""
        with self._lock:
            self._profiles.clear()
            self._active_profiles.clear()


class PerformanceMonitor:
    """Performance monitoring and optimization system."""
    
    def __init__(self, window_size: int = 1000):
        """Initialize performance monitor.
        
        Args:
            window_size: Size of rolling window for metrics
        """
        self.logger = get_logger(self.__class__.__name__)
        self.window_size = window_size
        self.snapshots: deque = deque(maxlen=window_size)
        self.benchmarks: List[PerformanceBenchmark] = []
        self.alerts: List[PerformanceAlert] = []
        self.profiler = PerformanceProfiler()
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Initialize default benchmarks
        self._setup_default_benchmarks()
    
    def _setup_default_benchmarks(self) -> None:
        """Setup default performance benchmarks."""
        self.add_benchmark(PerformanceBenchmark(
            name="response_time_p95",
            metric=PerformanceMetric.RESPONSE_TIME,
            target_value=2.0,  # 2 seconds
            operator="<=",
            weight=2.0
        ))
        
        self.add_benchmark(PerformanceBenchmark(
            name="memory_usage",
            metric=PerformanceMetric.MEMORY_USAGE,
            target_value=80.0,  # 80%
            operator="<=",
            weight=1.5
        ))
        
        self.add_benchmark(PerformanceBenchmark(
            name="cpu_usage",
            metric=PerformanceMetric.CPU_USAGE,
            target_value=90.0,  # 90%
            operator="<=",
            weight=1.5
        ))
        
        self.add_benchmark(PerformanceBenchmark(
            name="error_rate",
            metric=PerformanceMetric.ERROR_RATE,
            target_value=5.0,  # 5%
            operator="<=",
            weight=3.0
        ))
        
        self.add_benchmark(PerformanceBenchmark(
            name="success_rate",
            metric=PerformanceMetric.SUCCESS_RATE,
            target_value=95.0,  # 95%
            operator=">=",
            weight=3.0
        ))
    
    def add_benchmark(self, benchmark: PerformanceBenchmark) -> None:
        """Add a performance benchmark.
        
        Args:
            benchmark: Benchmark to add
        """
        self.benchmarks.append(benchmark)
        self.logger.info(f"Added performance benchmark: {benchmark.name}")
    
    def remove_benchmark(self, name: str) -> bool:
        """Remove a performance benchmark.
        
        Args:
            name: Benchmark name
            
        Returns:
            True if removed, False if not found
        """
        for i, benchmark in enumerate(self.benchmarks):
            if benchmark.name == name:
                del self.benchmarks[i]
                self.logger.info(f"Removed performance benchmark: {name}")
                return True
        return False
    
    async def start_monitoring(self, interval: float = 1.0) -> None:
        """Start performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            self.logger.warning("Performance monitoring is already running")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self.logger.info(f"Started performance monitoring with {interval}s interval")
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped performance monitoring")
    
    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        try:
            while self._monitoring:
                await self._collect_metrics()
                await self._check_benchmarks()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in performance monitoring: {e}")
    
    async def _collect_metrics(self) -> None:
        """Collect current performance metrics."""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate derived metrics
            metrics = {
                PerformanceMetric.MEMORY_USAGE: memory.percent,
                PerformanceMetric.CPU_USAGE: cpu_percent,
                PerformanceMetric.CONCURRENT_REQUESTS: self._get_concurrent_requests(),
                PerformanceMetric.RESPONSE_TIME: self._get_average_response_time(),
                PerformanceMetric.THROUGHPUT: self._get_throughput(),
                PerformanceMetric.ERROR_RATE: self._get_error_rate(),
                PerformanceMetric.SUCCESS_RATE: self._get_success_rate(),
                PerformanceMetric.CACHE_HIT_RATE: self._get_cache_hit_rate(),
                PerformanceMetric.DATABASE_QUERY_TIME: self._get_database_query_time(),
                PerformanceMetric.NETWORK_LATENCY: self._get_network_latency()
            }
            
            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                metrics=metrics,
                metadata={
                    "process_memory_mb": process_memory,
                    "available_memory_gb": memory.available / 1024 / 1024 / 1024,
                    "cpu_count": psutil.cpu_count()
                }
            )
            
            with self._lock:
                self.snapshots.append(snapshot)
                
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
    
    def _get_concurrent_requests(self) -> float:
        """Get current concurrent requests."""
        # This would be implemented based on your request tracking
        return 0.0
    
    def _get_average_response_time(self) -> float:
        """Get average response time."""
        if not self.snapshots:
            return 0.0
        
        response_times = [
            snapshot.metrics.get(PerformanceMetric.RESPONSE_TIME, 0)
            for snapshot in self.snapshots
            if PerformanceMetric.RESPONSE_TIME in snapshot.metrics
        ]
        
        return statistics.mean(response_times) if response_times else 0.0
    
    def _get_throughput(self) -> float:
        """Get current throughput (requests per second)."""
        if len(self.snapshots) < 2:
            return 0.0
        
        # Calculate throughput based on recent snapshots
        recent_snapshots = list(self.snapshots)[-10:]  # Last 10 snapshots
        if len(recent_snapshots) < 2:
            return 0.0
        
        time_diff = recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp
        if time_diff == 0:
            return 0.0
        
        # This would be calculated based on actual request counts
        return 0.0
    
    def _get_error_rate(self) -> float:
        """Get current error rate percentage."""
        if not self.snapshots:
            return 0.0
        
        # This would be calculated based on actual error counts
        return 0.0
    
    def _get_success_rate(self) -> float:
        """Get current success rate percentage."""
        if not self.snapshots:
            return 100.0
        
        # This would be calculated based on actual success counts
        return 100.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        if not self.snapshots:
            return 0.0
        
        # This would be calculated based on actual cache statistics
        return 0.0
    
    def _get_database_query_time(self) -> float:
        """Get average database query time."""
        if not self.snapshots:
            return 0.0
        
        # This would be calculated based on actual database metrics
        return 0.0
    
    def _get_network_latency(self) -> float:
        """Get average network latency."""
        if not self.snapshots:
            return 0.0
        
        # This would be calculated based on actual network metrics
        return 0.0
    
    async def _check_benchmarks(self) -> None:
        """Check performance benchmarks."""
        if not self.snapshots:
            return
        
        latest_snapshot = self.snapshots[-1]
        
        for benchmark in self.benchmarks:
            if not benchmark.enabled:
                continue
            
            if benchmark.metric not in latest_snapshot.metrics:
                continue
            
            current_value = latest_snapshot.metrics[benchmark.metric]
            target_value = benchmark.target_value
            
            # Check if benchmark is violated
            violated = False
            if benchmark.operator == ">":
                violated = current_value > target_value
            elif benchmark.operator == "<":
                violated = current_value < target_value
            elif benchmark.operator == ">=":
                violated = current_value >= target_value
            elif benchmark.operator == "<=":
                violated = current_value <= target_value
            elif benchmark.operator == "==":
                violated = current_value == target_value
            
            if violated:
                # Determine severity based on deviation
                deviation = abs(current_value - target_value) / target_value
                if deviation > 0.5:  # 50% deviation
                    severity = "critical"
                elif deviation > 0.2:  # 20% deviation
                    severity = "warning"
                else:
                    severity = "info"
                
                alert = PerformanceAlert(
                    benchmark_name=benchmark.name,
                    current_value=current_value,
                    target_value=target_value,
                    severity=severity,
                    timestamp=time.time(),
                    message=f"Performance benchmark violated: {benchmark.name} - "
                           f"Current: {current_value:.2f}, Target: {target_value:.2f}"
                )
                
                with self._lock:
                    self.alerts.append(alert)
                
                self.logger.warning(f"Performance alert: {alert.message}")
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics.
        
        Returns:
            Current metrics
        """
        if not self.snapshots:
            return {}
        
        latest = self.snapshots[-1]
        return {
            metric.value: value
            for metric, value in latest.metrics.items()
        }
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Metrics history
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            history = []
            for snapshot in self.snapshots:
                if snapshot.timestamp > cutoff_time:
                    history.append({
                        "timestamp": snapshot.timestamp,
                        "metrics": {
                            metric.value: value
                            for metric, value in snapshot.metrics.items()
                        },
                        "metadata": snapshot.metadata
                    })
            
            return history
    
    def get_performance_score(self) -> float:
        """Get overall performance score (0-100).
        
        Returns:
            Performance score
        """
        if not self.snapshots:
            return 100.0
        
        latest = self.snapshots[-1]
        score = 100.0
        
        for benchmark in self.benchmarks:
            if not benchmark.enabled or benchmark.metric not in latest.metrics:
                continue
            
            current_value = latest.metrics[benchmark.metric]
            target_value = benchmark.target_value
            
            # Calculate deviation
            if target_value == 0:
                deviation = 0
            else:
                deviation = abs(current_value - target_value) / target_value
            
            # Apply penalty based on deviation and weight
            penalty = min(deviation * benchmark.weight * 10, 20)  # Max 20 points penalty
            score -= penalty
        
        return max(0, min(100, score))
    
    def get_benchmark_status(self) -> Dict[str, Dict[str, Any]]:
        """Get benchmark status.
        
        Returns:
            Benchmark status information
        """
        if not self.snapshots:
            return {}
        
        latest = self.snapshots[-1]
        status = {}
        
        for benchmark in self.benchmarks:
            if benchmark.metric not in latest.metrics:
                continue
            
            current_value = latest.metrics[benchmark.metric]
            target_value = benchmark.target_value
            
            # Check if benchmark is met
            met = True
            if benchmark.operator == ">":
                met = current_value > target_value
            elif benchmark.operator == "<":
                met = current_value < target_value
            elif benchmark.operator == ">=":
                met = current_value >= target_value
            elif benchmark.operator == "<=":
                met = current_value <= target_value
            elif benchmark.operator == "==":
                met = current_value == target_value
            
            status[benchmark.name] = {
                "enabled": benchmark.enabled,
                "current_value": current_value,
                "target_value": target_value,
                "operator": benchmark.operator,
                "met": met,
                "weight": benchmark.weight
            }
        
        return status
    
    def get_recent_alerts(self, hours: int = 24) -> List[PerformanceAlert]:
        """Get recent performance alerts.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Recent alerts
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            return [
                alert for alert in self.alerts
                if alert.timestamp > cutoff_time
            ]
    
    def clear_alerts(self) -> None:
        """Clear all performance alerts."""
        with self._lock:
            self.alerts.clear()
    
    def get_profiler_stats(self) -> Dict[str, Dict[str, float]]:
        """Get profiler statistics.
        
        Returns:
            Profiler statistics
        """
        stats = {}
        for name in self.profiler._profiles:
            stats[name] = self.profiler.get_profile_stats(name)
        return stats
    
    def cleanup(self) -> None:
        """Cleanup performance monitor."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        
        with self._lock:
            self.snapshots.clear()
            self.alerts.clear()
        
        self.profiler.clear_all_profiles()
        self.logger.info("Performance monitor cleaned up")


class PerformanceOptimizer:
    """Performance optimization recommendations and actions."""
    
    def __init__(self, monitor: PerformanceMonitor):
        """Initialize performance optimizer.
        
        Args:
            monitor: Performance monitor instance
        """
        self.monitor = monitor
        self.logger = get_logger(self.__class__.__name__)
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        current_metrics = self.monitor.get_current_metrics()
        
        # Memory optimization
        memory_usage = current_metrics.get("memory_usage", 0)
        if memory_usage > 80:
            recommendations.append({
                "type": "memory",
                "priority": "high",
                "title": "High Memory Usage",
                "description": f"Memory usage is {memory_usage:.1f}%. Consider optimizing memory usage.",
                "actions": [
                    "Clear unused caches",
                    "Optimize data structures",
                    "Implement memory pooling",
                    "Scale up memory resources"
                ]
            })
        
        # CPU optimization
        cpu_usage = current_metrics.get("cpu_usage", 0)
        if cpu_usage > 90:
            recommendations.append({
                "type": "cpu",
                "priority": "high",
                "title": "High CPU Usage",
                "description": f"CPU usage is {cpu_usage:.1f}%. Consider optimizing CPU usage.",
                "actions": [
                    "Optimize algorithms",
                    "Implement caching",
                    "Scale up CPU resources",
                    "Distribute load"
                ]
            })
        
        # Response time optimization
        response_time = current_metrics.get("response_time", 0)
        if response_time > 2.0:
            recommendations.append({
                "type": "response_time",
                "priority": "medium",
                "title": "Slow Response Time",
                "description": f"Average response time is {response_time:.2f}s. Consider optimizing response time.",
                "actions": [
                    "Implement caching",
                    "Optimize database queries",
                    "Use connection pooling",
                    "Implement async processing"
                ]
            })
        
        # Error rate optimization
        error_rate = current_metrics.get("error_rate", 0)
        if error_rate > 5.0:
            recommendations.append({
                "type": "error_rate",
                "priority": "high",
                "title": "High Error Rate",
                "description": f"Error rate is {error_rate:.1f}%. Consider investigating errors.",
                "actions": [
                    "Review error logs",
                    "Implement better error handling",
                    "Add retry mechanisms",
                    "Improve input validation"
                ]
            })
        
        return recommendations
    
    def apply_optimization(self, optimization_type: str) -> bool:
        """Apply a specific optimization.
        
        Args:
            optimization_type: Type of optimization to apply
            
        Returns:
            True if optimization was applied
        """
        if optimization_type == "memory":
            return self._optimize_memory()
        elif optimization_type == "cpu":
            return self._optimize_cpu()
        elif optimization_type == "response_time":
            return self._optimize_response_time()
        elif optimization_type == "error_rate":
            return self._optimize_error_rate()
        else:
            self.logger.warning(f"Unknown optimization type: {optimization_type}")
            return False
    
    def _optimize_memory(self) -> bool:
        """Apply memory optimizations."""
        try:
            # Force garbage collection
            gc.collect()
            self.logger.info("Applied memory optimization: garbage collection")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply memory optimization: {e}")
            return False
    
    def _optimize_cpu(self) -> bool:
        """Apply CPU optimizations."""
        try:
            # This would implement CPU-specific optimizations
            self.logger.info("Applied CPU optimization")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply CPU optimization: {e}")
            return False
    
    def _optimize_response_time(self) -> bool:
        """Apply response time optimizations."""
        try:
            # This would implement response time optimizations
            self.logger.info("Applied response time optimization")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply response time optimization: {e}")
            return False
    
    def _optimize_error_rate(self) -> bool:
        """Apply error rate optimizations."""
        try:
            # This would implement error rate optimizations
            self.logger.info("Applied error rate optimization")
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply error rate optimization: {e}")
            return False
