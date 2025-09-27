"""
GPU Acceleration Module for SPIDER Framework

This module provides GPU acceleration capabilities for ML workloads,
data processing, and performance-critical operations.

Author: SPIDER Development Team
Version: 1.0.0
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import cupy as cp
    import cupyx.scipy.sparse as cpx_sparse
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None
    cpx_sparse = None

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from ..core.exceptions import SpiderError
from ..core.logger import get_logger

logger = get_logger(__name__)


class GPUDeviceType(Enum):
    """Types of GPU devices."""
    CUDA = "cuda"
    ROCM = "rocm"
    CPU = "cpu"


@dataclass
class GPUInfo:
    """Information about a GPU device."""
    device_id: int
    name: str
    memory_total: int
    memory_used: int
    memory_free: int
    utilization: float
    temperature: float
    power_usage: float
    device_type: GPUDeviceType


@dataclass
class GPUPerformanceMetrics:
    """GPU performance metrics."""
    device_id: int
    operations_per_second: float
    memory_bandwidth: float
    compute_utilization: float
    memory_utilization: float
    power_efficiency: float
    temperature: float
    timestamp: float


class GPUManager:
    """Manages GPU resources and operations."""
    
    def __init__(self, enable_gpu: bool = True, device_preference: str = "auto"):
        """Initialize GPU manager.
        
        Args:
            enable_gpu: Whether to enable GPU acceleration
            device_preference: Preferred device type ("auto", "cuda", "cpu")
        """
        self.enable_gpu = enable_gpu and CUPY_AVAILABLE
        self.device_preference = device_preference
        self.available_devices: List[GPUInfo] = []
        self.active_devices: Dict[int, bool] = {}
        self.performance_metrics: List[GPUPerformanceMetrics] = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        
        if self.enable_gpu:
            self._initialize_gpu()
        else:
            logger.warning("GPU acceleration not available. Falling back to CPU.")
    
    def _initialize_gpu(self):
        """Initialize GPU devices."""
        try:
            if CUPY_AVAILABLE:
                # Get available CUDA devices
                device_count = cp.cuda.runtime.getDeviceCount()
                for i in range(device_count):
                    with cp.cuda.Device(i):
                        device_info = self._get_device_info(i)
                        self.available_devices.append(device_info)
                        self.active_devices[i] = True
                
                logger.info(f"Initialized {len(self.available_devices)} GPU devices")
            else:
                logger.warning("CuPy not available. GPU acceleration disabled.")
                self.enable_gpu = False
                
        except Exception as e:
            logger.error(f"Failed to initialize GPU: {e}")
            self.enable_gpu = False
    
    def _get_device_info(self, device_id: int) -> GPUInfo:
        """Get information about a specific GPU device."""
        try:
            with cp.cuda.Device(device_id):
                # Get device properties
                props = cp.cuda.runtime.getDeviceProperties(device_id)
                
                # Get memory info
                mempool = cp.get_default_memory_pool()
                memory_total = props.totalGlobalMem
                memory_used = mempool.used_bytes()
                memory_free = memory_total - memory_used
                
                # Get utilization (simplified)
                utilization = 0.0  # Would need nvidia-ml-py for real utilization
                temperature = 0.0  # Would need nvidia-ml-py for real temperature
                power_usage = 0.0  # Would need nvidia-ml-py for real power usage
                
                return GPUInfo(
                    device_id=device_id,
                    name=props.name.decode('utf-8'),
                    memory_total=memory_total,
                    memory_used=memory_used,
                    memory_free=memory_free,
                    utilization=utilization,
                    temperature=temperature,
                    power_usage=power_usage,
                    device_type=GPUDeviceType.CUDA
                )
        except Exception as e:
            logger.error(f"Failed to get device info for device {device_id}: {e}")
            return GPUInfo(
                device_id=device_id,
                name="Unknown",
                memory_total=0,
                memory_used=0,
                memory_free=0,
                utilization=0.0,
                temperature=0.0,
                power_usage=0.0,
                device_type=GPUDeviceType.CPU
            )
    
    def get_available_devices(self) -> List[GPUInfo]:
        """Get list of available GPU devices."""
        return self.available_devices.copy()
    
    def get_device_info(self, device_id: int) -> Optional[GPUInfo]:
        """Get information about a specific device."""
        for device in self.available_devices:
            if device.device_id == device_id:
                return device
        return None
    
    def select_best_device(self) -> Optional[int]:
        """Select the best available GPU device."""
        if not self.available_devices:
            return None
        
        # Select device with most free memory
        best_device = max(self.available_devices, key=lambda d: d.memory_free)
        return best_device.device_id
    
    def allocate_memory(self, device_id: int, size_bytes: int) -> bool:
        """Allocate memory on a specific device."""
        try:
            if not self.enable_gpu:
                return False
            
            with cp.cuda.Device(device_id):
                # Check if enough memory is available
                device_info = self.get_device_info(device_id)
                if device_info and device_info.memory_free < size_bytes:
                    logger.warning(f"Insufficient memory on device {device_id}")
                    return False
                
                # Allocate memory (this is a simplified check)
                return True
                
        except Exception as e:
            logger.error(f"Failed to allocate memory on device {device_id}: {e}")
            return False
    
    def free_memory(self, device_id: int):
        """Free memory on a specific device."""
        try:
            if not self.enable_gpu:
                return
            
            with cp.cuda.Device(device_id):
                # Clear memory pool
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                
        except Exception as e:
            logger.error(f"Failed to free memory on device {device_id}: {e}")
    
    def get_memory_usage(self, device_id: int) -> Dict[str, int]:
        """Get memory usage for a specific device."""
        try:
            if not self.enable_gpu:
                return {"used": 0, "free": 0, "total": 0}
            
            with cp.cuda.Device(device_id):
                mempool = cp.get_default_memory_pool()
                used = mempool.used_bytes()
                total = cp.cuda.runtime.getDeviceProperties(device_id).totalGlobalMem
                free = total - used
                
                return {
                    "used": used,
                    "free": free,
                    "total": total
                }
        except Exception as e:
            logger.error(f"Failed to get memory usage for device {device_id}: {e}")
            return {"used": 0, "free": 0, "total": 0}
    
    async def run_gpu_task(self, task_func, device_id: int, *args, **kwargs):
        """Run a task on a specific GPU device."""
        if not self.enable_gpu:
            # Fallback to CPU
            return await asyncio.get_event_loop().run_in_executor(
                self._executor, task_func, *args, **kwargs
            )
        
        def gpu_task():
            with cp.cuda.Device(device_id):
                return task_func(*args, **kwargs)
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, gpu_task
        )
    
    def benchmark_device(self, device_id: int) -> GPUPerformanceMetrics:
        """Benchmark a specific GPU device."""
        try:
            if not self.enable_gpu:
                return GPUPerformanceMetrics(
                    device_id=device_id,
                    operations_per_second=0.0,
                    memory_bandwidth=0.0,
                    compute_utilization=0.0,
                    memory_utilization=0.0,
                    power_efficiency=0.0,
                    temperature=0.0,
                    timestamp=time.time()
                )
            
            with cp.cuda.Device(device_id):
                # Simple matrix multiplication benchmark
                size = 1000
                a = cp.random.random((size, size), dtype=cp.float32)
                b = cp.random.random((size, size), dtype=cp.float32)
                
                # Warm up
                for _ in range(10):
                    cp.dot(a, b)
                cp.cuda.Stream.null.synchronize()
                
                # Benchmark
                start_time = time.time()
                iterations = 100
                for _ in range(iterations):
                    cp.dot(a, b)
                cp.cuda.Stream.null.synchronize()
                end_time = time.time()
                
                # Calculate metrics
                operations_per_second = iterations / (end_time - start_time)
                memory_bandwidth = (size * size * 4 * 3) / (end_time - start_time)  # Simplified
                
                device_info = self.get_device_info(device_id)
                temperature = device_info.temperature if device_info else 0.0
                
                metrics = GPUPerformanceMetrics(
                    device_id=device_id,
                    operations_per_second=operations_per_second,
                    memory_bandwidth=memory_bandwidth,
                    compute_utilization=min(100.0, operations_per_second / 1000 * 100),
                    memory_utilization=min(100.0, memory_bandwidth / (1024**3) * 100),
                    power_efficiency=operations_per_second / max(1.0, device_info.power_usage) if device_info else 0.0,
                    temperature=temperature,
                    timestamp=time.time()
                )
                
                with self._lock:
                    self.performance_metrics.append(metrics)
                    # Keep only last 100 metrics
                    if len(self.performance_metrics) > 100:
                        self.performance_metrics = self.performance_metrics[-100:]
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to benchmark device {device_id}: {e}")
            return GPUPerformanceMetrics(
                device_id=device_id,
                operations_per_second=0.0,
                memory_bandwidth=0.0,
                compute_utilization=0.0,
                memory_utilization=0.0,
                power_efficiency=0.0,
                temperature=0.0,
                timestamp=time.time()
            )
    
    def get_performance_metrics(self, device_id: Optional[int] = None) -> List[GPUPerformanceMetrics]:
        """Get performance metrics for devices."""
        with self._lock:
            if device_id is not None:
                return [m for m in self.performance_metrics if m.device_id == device_id]
            return self.performance_metrics.copy()
    
    def cleanup(self):
        """Cleanup GPU resources."""
        try:
            if self.enable_gpu and CUPY_AVAILABLE:
                for device_id in self.active_devices:
                    self.free_memory(device_id)
            
            self._executor.shutdown(wait=True)
            logger.info("GPU manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during GPU cleanup: {e}")


class GPUAcceleratedProcessor:
    """GPU-accelerated data processor."""
    
    def __init__(self, gpu_manager: GPUManager):
        """Initialize GPU-accelerated processor.
        
        Args:
            gpu_manager: GPU manager instance
        """
        self.gpu_manager = gpu_manager
        self.device_id = gpu_manager.select_best_device()
    
    async def process_data(self, data: Union[List, np.ndarray], operation: str) -> Any:
        """Process data using GPU acceleration.
        
        Args:
            data: Input data to process
            operation: Operation to perform
        """
        if not self.gpu_manager.enable_gpu or self.device_id is None:
            # Fallback to CPU processing
            return self._cpu_process_data(data, operation)
        
        try:
            return await self.gpu_manager.run_gpu_task(
                self._gpu_process_data, self.device_id, data, operation
            )
        except Exception as e:
            logger.error(f"GPU processing failed, falling back to CPU: {e}")
            return self._cpu_process_data(data, operation)
    
    def _gpu_process_data(self, data: Union[List, np.ndarray], operation: str) -> Any:
        """Process data on GPU."""
        if not CUPY_AVAILABLE:
            return self._cpu_process_data(data, operation)
        
        # Convert to CuPy array
        if isinstance(data, list):
            data = np.array(data)
        
        gpu_data = cp.asarray(data)
        
        if operation == "matrix_multiply":
            # Simple matrix multiplication
            if len(gpu_data.shape) == 2:
                result = cp.dot(gpu_data, gpu_data.T)
            else:
                result = gpu_data * gpu_data
        elif operation == "normalize":
            # Normalize data
            mean = cp.mean(gpu_data)
            std = cp.std(gpu_data)
            result = (gpu_data - mean) / (std + 1e-8)
        elif operation == "sort":
            # Sort data
            result = cp.sort(gpu_data)
        else:
            # Default: return as-is
            result = gpu_data
        
        # Convert back to numpy array
        return cp.asnumpy(result)
    
    def _cpu_process_data(self, data: Union[List, np.ndarray], operation: str) -> Any:
        """Process data on CPU (fallback)."""
        if not NUMPY_AVAILABLE:
            return data
        
        if isinstance(data, list):
            data = np.array(data)
        
        if operation == "matrix_multiply":
            if len(data.shape) == 2:
                return np.dot(data, data.T)
            else:
                return data * data
        elif operation == "normalize":
            mean = np.mean(data)
            std = np.std(data)
            return (data - mean) / (std + 1e-8)
        elif operation == "sort":
            return np.sort(data)
        else:
            return data


# Global GPU manager instance
_gpu_manager: Optional[GPUManager] = None


def get_gpu_manager() -> GPUManager:
    """Get the global GPU manager instance."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager


def cleanup_gpu_resources():
    """Cleanup global GPU resources."""
    global _gpu_manager
    if _gpu_manager is not None:
        _gpu_manager.cleanup()
        _gpu_manager = None
