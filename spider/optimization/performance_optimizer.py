"""
Performance Optimizer

Advanced performance optimization for the SPIDER framework.
Includes algorithm optimization, memory management, and performance tuning.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import numpy as np
import pandas as pd
import psutil
import gc
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
import threading
import multiprocessing

logger = logging.getLogger(__name__)


class OptimizationType(str, Enum):
    """Optimization type enumeration."""
    MEMORY = "memory"
    CPU = "cpu"
    I_O = "i_o"
    NETWORK = "network"
    ALGORITHM = "algorithm"
    CACHING = "caching"
    PARALLELIZATION = "parallelization"


class OptimizationLevel(str, Enum):
    """Optimization level enumeration."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    AGGRESSIVE = "aggressive"


@dataclass
class OptimizationConfig:
    """Performance optimization configuration."""
    optimization_types: List[OptimizationType] = field(default_factory=lambda: [OptimizationType.MEMORY, OptimizationType.CPU])
    optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE
    max_memory_usage: float = 0.8  # 80% of available memory
    max_cpu_usage: float = 0.8  # 80% of available CPU
    enable_parallelization: bool = True
    max_workers: int = None  # Auto-detect if None
    enable_caching: bool = True
    cache_size_mb: int = 100
    enable_profiling: bool = True
    profiling_interval: int = 60  # seconds
    enable_gc_optimization: bool = True
    gc_threshold: int = 1000  # objects
    enable_memory_mapping: bool = True
    chunk_size: int = 10000
    enable_compression: bool = True
    compression_level: int = 6


@dataclass
class OptimizationResult:
    """Performance optimization result."""
    optimization_id: str
    optimization_type: OptimizationType
    performance_metrics: Dict[str, float]
    optimization_suggestions: List[str]
    memory_usage: Dict[str, float]
    cpu_usage: Dict[str, float]
    execution_time: float
    before_metrics: Dict[str, float] = field(default_factory=dict)
    after_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceOptimizer:
    """
    Advanced performance optimization system.
    
    Features:
    - Memory optimization and garbage collection
    - CPU optimization and parallelization
    - I/O optimization and caching
    - Algorithm optimization
    - Real-time performance monitoring
    - Automatic optimization suggestions
    """
    
    def __init__(self, config: OptimizationConfig = None):
        """Initialize performance optimizer."""
        self.config = config or OptimizationConfig()
        self.optimization_history = []
        self.performance_metrics = {}
        self.optimization_cache = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Initialize system monitoring
        self._initialize_system_monitoring()
    
    def _initialize_system_monitoring(self):
        """Initialize system monitoring."""
        self.system_info = {
            "cpu_count": multiprocessing.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        # Set max_workers if not specified
        if self.config.max_workers is None:
            self.config.max_workers = min(self.system_info["cpu_count"], 8)
    
    async def optimize_performance(self, func: callable, *args, **kwargs) -> OptimizationResult:
        """
        Optimize performance of a function.
        
        Args:
            func: Function to optimize
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Optimization result
        """
        optimization_id = f"opt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Start monitoring
            await self._start_monitoring()
            
            # Get baseline metrics
            before_metrics = self._get_current_metrics()
            
            # Apply optimizations
            optimized_func = await self._apply_optimizations(func)
            
            # Execute optimized function
            start_time = time.time()
            result = await self._execute_optimized_function(optimized_func, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Get after metrics
            after_metrics = self._get_current_metrics()
            
            # Calculate performance improvements
            performance_metrics = self._calculate_performance_metrics(before_metrics, after_metrics, execution_time)
            
            # Generate optimization suggestions
            suggestions = await self._generate_optimization_suggestions(performance_metrics)
            
            # Create result
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                optimization_type=OptimizationType.ALGORITHM,
                performance_metrics=performance_metrics,
                optimization_suggestions=suggestions,
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage(),
                execution_time=execution_time,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                metadata={
                    "function_name": func.__name__,
                    "optimization_level": self.config.optimization_level.value,
                    "optimization_types": [t.value for t in self.config.optimization_types]
                }
            )
            
            # Store in history
            self.optimization_history.append({
                "optimization_id": optimization_id,
                "function_name": func.__name__,
                "execution_time": execution_time,
                "performance_improvement": performance_metrics.get("performance_improvement", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Performance optimization completed: {optimization_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            raise
        finally:
            await self._stop_monitoring()
    
    async def _apply_optimizations(self, func: callable) -> callable:
        """Apply various optimizations to a function."""
        optimized_func = func
        
        # Memory optimization
        if OptimizationType.MEMORY in self.config.optimization_types:
            optimized_func = self._apply_memory_optimization(optimized_func)
        
        # CPU optimization
        if OptimizationType.CPU in self.config.optimization_types:
            optimized_func = self._apply_cpu_optimization(optimized_func)
        
        # Caching optimization
        if OptimizationType.CACHING in self.config.optimization_types and self.config.enable_caching:
            optimized_func = self._apply_caching_optimization(optimized_func)
        
        # Parallelization optimization
        if OptimizationType.PARALLELIZATION in self.config.optimization_types and self.config.enable_parallelization:
            optimized_func = self._apply_parallelization_optimization(optimized_func)
        
        return optimized_func
    
    def _apply_memory_optimization(self, func: callable) -> callable:
        """Apply memory optimization to a function."""
        @wraps(func)
        async def memory_optimized_func(*args, **kwargs):
            # Enable garbage collection optimization
            if self.config.enable_gc_optimization:
                gc.set_threshold(self.config.gc_threshold)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Force garbage collection
            if self.config.enable_gc_optimization:
                gc.collect()
            
            return result
        
        return memory_optimized_func
    
    def _apply_cpu_optimization(self, func: callable) -> callable:
        """Apply CPU optimization to a function."""
        @wraps(func)
        async def cpu_optimized_func(*args, **kwargs):
            # Set CPU affinity if available
            try:
                import os
                os.sched_setaffinity(0, range(self.config.max_workers))
            except (ImportError, OSError):
                pass  # Not available on this system
            
            # Execute function
            result = await func(*args, **kwargs)
            
            return result
        
        return cpu_optimized_func
    
    def _apply_caching_optimization(self, func: callable) -> callable:
        """Apply caching optimization to a function."""
        @wraps(func)
        async def cached_func(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}_{hash(str(args))}_{hash(str(kwargs))}"
            
            # Check cache
            if cache_key in self.optimization_cache:
                return self.optimization_cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            self.optimization_cache[cache_key] = result
            
            # Limit cache size
            if len(self.optimization_cache) > 1000:  # Max 1000 cached results
                # Remove oldest entries
                oldest_key = next(iter(self.optimization_cache))
                del self.optimization_cache[oldest_key]
            
            return result
        
        return cached_func
    
    def _apply_parallelization_optimization(self, func: callable) -> callable:
        """Apply parallelization optimization to a function."""
        @wraps(func)
        async def parallelized_func(*args, **kwargs):
            # Check if function can be parallelized
            if self._can_parallelize(func, args, kwargs):
                # Use ThreadPoolExecutor for I/O bound tasks
                with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(executor, func, *args, **kwargs)
            else:
                # Execute normally
                result = await func(*args, **kwargs)
            
            return result
        
        return parallelized_func
    
    def _can_parallelize(self, func: callable, args: tuple, kwargs: dict) -> bool:
        """Check if a function can be parallelized."""
        # Simple heuristic: check if function is I/O bound
        # This is a simplified check - in practice, you'd have more sophisticated logic
        return len(args) > 0 and isinstance(args[0], (list, tuple, np.ndarray, pd.DataFrame))
    
    async def _execute_optimized_function(self, func: callable, *args, **kwargs) -> Any:
        """Execute the optimized function."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run in executor for non-async functions
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        return {
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent(),
            "memory_available": psutil.virtual_memory().available,
            "process_count": len(psutil.pids()),
            "timestamp": time.time()
        }
    
    def _calculate_performance_metrics(self, before: Dict[str, float], 
                                     after: Dict[str, float], 
                                     execution_time: float) -> Dict[str, float]:
        """Calculate performance metrics."""
        metrics = {
            "execution_time": execution_time,
            "memory_usage_before": before.get("memory_usage", 0),
            "memory_usage_after": after.get("memory_usage", 0),
            "cpu_usage_before": before.get("cpu_usage", 0),
            "cpu_usage_after": after.get("cpu_usage", 0),
            "memory_improvement": before.get("memory_usage", 0) - after.get("memory_usage", 0),
            "cpu_improvement": before.get("cpu_usage", 0) - after.get("cpu_usage", 0),
        }
        
        # Calculate performance improvement percentage
        if before.get("memory_usage", 0) > 0:
            metrics["memory_improvement_percent"] = (metrics["memory_improvement"] / before["memory_usage"]) * 100
        
        if before.get("cpu_usage", 0) > 0:
            metrics["cpu_improvement_percent"] = (metrics["cpu_improvement"] / before["cpu_usage"]) * 100
        
        # Overall performance improvement
        metrics["performance_improvement"] = (metrics["memory_improvement_percent"] + metrics["cpu_improvement_percent"]) / 2
        
        return metrics
    
    async def _generate_optimization_suggestions(self, metrics: Dict[str, float]) -> List[str]:
        """Generate optimization suggestions based on metrics."""
        suggestions = []
        
        # Memory optimization suggestions
        if metrics.get("memory_usage_after", 0) > 80:
            suggestions.append("Consider reducing memory usage - current usage is above 80%")
        
        if metrics.get("memory_improvement", 0) < 0:
            suggestions.append("Memory usage increased - consider memory optimization")
        
        # CPU optimization suggestions
        if metrics.get("cpu_usage_after", 0) > 80:
            suggestions.append("Consider CPU optimization - current usage is above 80%")
        
        if metrics.get("cpu_improvement", 0) < 0:
            suggestions.append("CPU usage increased - consider parallelization")
        
        # Execution time suggestions
        if metrics.get("execution_time", 0) > 10:
            suggestions.append("Execution time is high - consider algorithm optimization")
        
        # General suggestions
        if metrics.get("performance_improvement", 0) < 5:
            suggestions.append("Performance improvement is minimal - consider more aggressive optimization")
        
        return suggestions
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "free": memory.free
        }
    
    def _get_cpu_usage(self) -> Dict[str, float]:
        """Get current CPU usage."""
        return {
            "percent": psutil.cpu_percent(),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
    
    async def _start_monitoring(self):
        """Start performance monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.start()
    
    async def _stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
    
    def _monitoring_loop(self):
        """Performance monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self._get_current_metrics()
                self.performance_metrics[datetime.utcnow().isoformat()] = metrics
                
                # Keep only last 1000 metrics
                if len(self.performance_metrics) > 1000:
                    oldest_key = min(self.performance_metrics.keys())
                    del self.performance_metrics[oldest_key]
                
                time.sleep(self.config.profiling_interval)
            except Exception as e:
                logger.warning(f"Monitoring loop error: {e}")
                break
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return self.optimization_history
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return self.system_info
    
    def clear_cache(self):
        """Clear optimization cache."""
        self.optimization_cache.clear()
        logger.info("Optimization cache cleared")
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        if not self.optimization_history:
            return {"total_optimizations": 0}
        
        total_optimizations = len(self.optimization_history)
        avg_execution_time = np.mean([h["execution_time"] for h in self.optimization_history])
        avg_improvement = np.mean([h["performance_improvement"] for h in self.optimization_history])
        
        return {
            "total_optimizations": total_optimizations,
            "average_execution_time": avg_execution_time,
            "average_performance_improvement": avg_improvement,
            "cache_size": len(self.optimization_cache),
            "last_optimization": self.optimization_history[-1]["timestamp"] if self.optimization_history else None
        }
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize a pandas DataFrame for memory usage."""
        if not isinstance(df, pd.DataFrame):
            return df
        
        # Convert object columns to category if they have low cardinality
        for col in df.columns:
            if df[col].dtype == 'object':
                if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                    df[col] = df[col].astype('category')
        
        # Downcast numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        return df
    
    def optimize_numpy_array(self, arr: np.ndarray) -> np.ndarray:
        """Optimize a numpy array for memory usage."""
        if not isinstance(arr, np.ndarray):
            return arr
        
        # Use appropriate dtype
        if arr.dtype == np.float64:
            if np.all(arr == arr.astype(np.float32)):
                arr = arr.astype(np.float32)
        elif arr.dtype == np.int64:
            if np.all(arr == arr.astype(np.int32)):
                arr = arr.astype(np.int32)
        
        return arr
