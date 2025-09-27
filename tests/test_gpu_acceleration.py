"""Tests for GPU acceleration module."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock

from spider.infrastructure.gpu_acceleration import (
    GPUManager, GPUAcceleratedProcessor, GPUDeviceType, GPUInfo,
    GPUPerformanceMetrics, get_gpu_manager, cleanup_gpu_resources
)


class TestGPUManager:
    """Test GPU manager functionality."""
    
    def test_initialization_without_gpu(self):
        """Test GPU manager initialization without GPU support."""
        with patch('spider.infrastructure.gpu_acceleration.CUPY_AVAILABLE', False):
            manager = GPUManager(enable_gpu=False)
            assert not manager.enable_gpu
            assert len(manager.available_devices) == 0
    
    def test_initialization_with_gpu(self):
        """Test GPU manager initialization with GPU support."""
        with patch('spider.infrastructure.gpu_acceleration.CUPY_AVAILABLE', True):
            with patch('spider.infrastructure.gpu_acceleration.cp') as mock_cp:
                mock_cp.cuda.runtime.getDeviceCount.return_value = 1
                mock_cp.cuda.runtime.getDeviceProperties.return_value = Mock(
                    name=b'Test GPU',
                    totalGlobalMem=1024**3
                )
                mock_cp.get_default_memory_pool.return_value = Mock(used_bytes=lambda: 0)
                
                manager = GPUManager(enable_gpu=True)
                assert manager.enable_gpu
                assert len(manager.available_devices) == 1
    
    def test_get_available_devices(self):
        """Test getting available devices."""
        manager = GPUManager(enable_gpu=False)
        devices = manager.get_available_devices()
        assert isinstance(devices, list)
    
    def test_get_device_info(self):
        """Test getting device information."""
        manager = GPUManager(enable_gpu=False)
        device_info = manager.get_device_info(0)
        assert device_info is None or isinstance(device_info, GPUInfo)
    
    def test_select_best_device(self):
        """Test selecting best device."""
        manager = GPUManager(enable_gpu=False)
        best_device = manager.select_best_device()
        assert best_device is None or isinstance(best_device, int)
    
    def test_allocate_memory(self):
        """Test memory allocation."""
        manager = GPUManager(enable_gpu=False)
        result = manager.allocate_memory(0, 1024)
        assert isinstance(result, bool)
    
    def test_free_memory(self):
        """Test memory freeing."""
        manager = GPUManager(enable_gpu=False)
        # Should not raise exception
        manager.free_memory(0)
    
    def test_get_memory_usage(self):
        """Test getting memory usage."""
        manager = GPUManager(enable_gpu=False)
        usage = manager.get_memory_usage(0)
        assert isinstance(usage, dict)
        assert "used" in usage
        assert "free" in usage
        assert "total" in usage
    
    @pytest.mark.asyncio
    async def test_run_gpu_task(self):
        """Test running GPU task."""
        manager = GPUManager(enable_gpu=False)
        
        def test_task(x, y):
            return x + y
        
        result = await manager.run_gpu_task(test_task, 0, 1, 2)
        assert result == 3
    
    def test_benchmark_device(self):
        """Test device benchmarking."""
        manager = GPUManager(enable_gpu=False)
        metrics = manager.benchmark_device(0)
        assert isinstance(metrics, GPUPerformanceMetrics)
        assert metrics.device_id == 0
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        manager = GPUManager(enable_gpu=False)
        metrics = manager.get_performance_metrics()
        assert isinstance(metrics, list)
    
    def test_cleanup(self):
        """Test cleanup."""
        manager = GPUManager(enable_gpu=False)
        # Should not raise exception
        manager.cleanup()


class TestGPUAcceleratedProcessor:
    """Test GPU-accelerated processor."""
    
    def test_initialization(self):
        """Test processor initialization."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        assert processor.gpu_manager == manager
    
    @pytest.mark.asyncio
    async def test_process_data_matrix_multiply(self):
        """Test matrix multiplication processing."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        
        data = [[1, 2], [3, 4]]
        result = await processor.process_data(data, "matrix_multiply")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_data_normalize(self):
        """Test data normalization."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        
        data = [1, 2, 3, 4, 5]
        result = await processor.process_data(data, "normalize")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_data_sort(self):
        """Test data sorting."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        
        data = [3, 1, 4, 1, 5]
        result = await processor.process_data(data, "sort")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_process_data_unknown_operation(self):
        """Test unknown operation fallback."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        
        data = [1, 2, 3]
        result = await processor.process_data(data, "unknown")
        # Convert to list for comparison if it's a numpy array
        if hasattr(result, 'tolist'):
            result = result.tolist()
        assert result == data


class TestGPUInfo:
    """Test GPU info dataclass."""
    
    def test_gpu_info_creation(self):
        """Test GPU info creation."""
        info = GPUInfo(
            device_id=0,
            name="Test GPU",
            memory_total=1024**3,
            memory_used=512**3,
            memory_free=512**3,
            utilization=50.0,
            temperature=60.0,
            power_usage=100.0,
            device_type=GPUDeviceType.CUDA
        )
        assert info.device_id == 0
        assert info.name == "Test GPU"
        assert info.memory_total == 1024**3
        assert info.device_type == GPUDeviceType.CUDA


class TestGPUPerformanceMetrics:
    """Test GPU performance metrics."""
    
    def test_metrics_creation(self):
        """Test metrics creation."""
        metrics = GPUPerformanceMetrics(
            device_id=0,
            operations_per_second=1000.0,
            memory_bandwidth=1024.0,
            compute_utilization=80.0,
            memory_utilization=60.0,
            power_efficiency=10.0,
            temperature=65.0,
            timestamp=time.time()
        )
        assert metrics.device_id == 0
        assert metrics.operations_per_second == 1000.0
        assert metrics.temperature == 65.0


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_get_gpu_manager(self):
        """Test getting GPU manager."""
        manager = get_gpu_manager()
        assert isinstance(manager, GPUManager)
    
    def test_cleanup_gpu_resources(self):
        """Test cleanup GPU resources."""
        # Should not raise exception
        cleanup_gpu_resources()


class TestGPUIntegration:
    """Test GPU integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_gpu_fallback_to_cpu(self):
        """Test GPU fallback to CPU when GPU is not available."""
        manager = GPUManager(enable_gpu=False)
        processor = GPUAcceleratedProcessor(manager)
        
        data = [1, 2, 3, 4, 5]
        result = await processor.process_data(data, "normalize")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_gpu_tasks(self):
        """Test concurrent GPU task execution."""
        manager = GPUManager(enable_gpu=False)
        
        async def task(x):
            return await manager.run_gpu_task(lambda y: y * 2, 0, x)
        
        tasks = [task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(isinstance(r, int) for r in results)
    
    def test_memory_management(self):
        """Test memory management."""
        manager = GPUManager(enable_gpu=False)
        
        # Test memory allocation
        allocated = manager.allocate_memory(0, 1024)
        assert isinstance(allocated, bool)
        
        # Test memory usage
        usage = manager.get_memory_usage(0)
        assert isinstance(usage, dict)
        
        # Test memory freeing
        manager.free_memory(0)
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        manager = GPUManager(enable_gpu=False)
        
        # Run benchmark
        metrics = manager.benchmark_device(0)
        assert isinstance(metrics, GPUPerformanceMetrics)
        
        # Get performance metrics
        all_metrics = manager.get_performance_metrics()
        assert isinstance(all_metrics, list)
        
        # Get metrics for specific device
        device_metrics = manager.get_performance_metrics(0)
        assert isinstance(device_metrics, list)
