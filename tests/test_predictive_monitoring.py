"""
Tests for Predictive Monitoring Module

This module tests the predictive monitoring functionality including:
- Predictive analytics engine
- Anomaly detection
- Capacity planning
- Performance forecasting

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from spider.monitoring.predictive import (
    PredictiveAnalyticsEngine, PredictiveMonitor,
    PredictionType, SeverityLevel, PredictionResult,
    PerformanceForecast
)
from spider.monitoring.anomaly_detection import (
    AnomalyDetectionManager, StatisticalAnomalyDetector,
    MLAnomalyDetector, TimeSeriesAnomalyDetector,
    AnomalyType, DetectionMethod, AnomalyDetectionResult
)
from spider.monitoring.capacity_planning import (
    CapacityPlanningManager, ResourceMonitor, PredictiveScaler,
    CapacityForecaster, CostOptimizer, ResourceType, ScalingAction,
    ScalingRecommendation, CapacityForecast, CostOptimization, ResourceMetrics
)


class TestPredictiveAnalyticsEngine:
    """Test PredictiveAnalyticsEngine functionality"""
    
    @pytest.fixture
    def engine(self):
        return PredictiveAnalyticsEngine()
    
    @pytest.mark.asyncio
    async def test_predict_anomaly(self, engine):
        """Test anomaly prediction"""
        # Test normal data
        data = np.array([[0.5, 0.6, 0.4]])
        features = ['cpu', 'memory', 'disk']
        
        result = await engine.predict_anomaly(data, features)
        
        # The result should be from the anomaly_detection module, not predictive module
        from spider.monitoring.anomaly_detection import AnomalyDetectionResult as ADResult
        assert isinstance(result, ADResult)
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_predict_failure(self, engine):
        """Test failure prediction"""
        metrics = {
            'cpu_usage': 0.9,
            'memory_usage': 0.8,
            'disk_usage': 0.7,
            'error_rate': 0.05,
            'response_time': 2.0
        }
        
        result = await engine.predict_failure(metrics)
        
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == PredictionType.FAILURE
        assert result.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_forecast_performance(self, engine):
        """Test performance forecasting"""
        # Generate historical data
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        values = [0.5 + 0.1 * np.sin(i * 0.1) + np.random.normal(0, 0.05) for i in range(24)]
        historical_data = list(zip(timestamps, values))
        
        forecast = await engine.forecast_performance('cpu_usage', historical_data, 12)
        
        assert isinstance(forecast, PerformanceForecast)
        assert forecast.metric_name == 'cpu_usage'
        assert len(forecast.predicted_values) == 12
        assert len(forecast.timestamps) == 12
        assert len(forecast.confidence_intervals) == 12
        assert forecast.trend in ['increasing', 'decreasing', 'stable']
        assert 0.0 <= forecast.r_squared <= 1.0
    
    @pytest.mark.asyncio
    async def test_predict_capacity_exhaustion(self, engine):
        """Test capacity exhaustion prediction"""
        resource_usage = {
            'cpu': 0.8,
            'memory': 0.7,
            'disk': 0.6
        }
        growth_rates = {
            'cpu': 0.1,  # 10% per hour
            'memory': 0.05,
            'disk': 0.02
        }
        
        result = await engine.predict_capacity_exhaustion(resource_usage, growth_rates)
        
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == PredictionType.CAPACITY_EXHAUSTION
        assert result.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_train_models(self, engine):
        """Test model training"""
        training_data = {
            'cpu_usage': [(datetime.now() - timedelta(hours=i), 0.5 + 0.1 * np.sin(i * 0.1)) for i in range(100)],
            'memory_usage': [(datetime.now() - timedelta(hours=i), 0.6 + 0.1 * np.cos(i * 0.1)) for i in range(100)]
        }
        
        await engine.train_models(training_data)
        
        # Check that models were trained
        performance = engine.get_model_performance()
        assert isinstance(performance, dict)
    
    def test_get_prediction_history(self, engine):
        """Test prediction history retrieval"""
        history = engine.get_prediction_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestPredictiveMonitor:
    """Test PredictiveMonitor functionality"""
    
    @pytest.fixture
    def monitor(self):
        return PredictiveMonitor()
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring"""
        assert not monitor.monitoring_active
        
        await monitor.start_monitoring(interval=0.1)
        assert monitor.monitoring_active
        
        await asyncio.sleep(0.2)  # Let it run briefly
        
        await monitor.stop_monitoring()
        assert not monitor.monitoring_active
    
    @pytest.mark.asyncio
    async def test_record_metric(self, monitor):
        """Test metric recording"""
        monitor.record_metric('cpu_usage', 0.8)
        monitor.record_metric('memory_usage', 0.6)
        
        # Check that metrics were recorded
        status = monitor.get_monitoring_status()
        assert 'cpu_usage' in status['metrics_tracked']
        assert 'memory_usage' in status['metrics_tracked']
    
    @pytest.mark.asyncio
    async def test_get_forecast(self, monitor):
        """Test forecast retrieval"""
        # Record some historical data
        for i in range(20):
            monitor.record_metric('cpu_usage', 0.5 + 0.1 * np.sin(i * 0.1))
            await asyncio.sleep(0.01)
        
        forecast = await monitor.get_forecast('cpu_usage', hours=12)
        
        if forecast:  # May be None if insufficient data
            assert isinstance(forecast, PerformanceForecast)
            assert forecast.metric_name == 'cpu_usage'
            assert len(forecast.predicted_values) == 12
    
    def test_add_alert_callback(self, monitor):
        """Test adding alert callbacks"""
        callback = Mock()
        monitor.add_alert_callback(callback)
        
        assert callback in monitor.alert_callbacks
    
    def test_get_monitoring_status(self, monitor):
        """Test monitoring status retrieval"""
        status = monitor.get_monitoring_status()
        
        assert 'monitoring_active' in status
        assert 'metrics_tracked' in status
        assert 'buffer_sizes' in status
        assert 'model_performance' in status
        assert 'recent_predictions' in status


class TestStatisticalAnomalyDetector:
    """Test StatisticalAnomalyDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        return StatisticalAnomalyDetector()
    
    @pytest.mark.asyncio
    async def test_detect_z_score_anomaly(self, detector):
        """Test Z-score anomaly detection"""
        # Normal data
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3])
        features = ['cpu', 'memory', 'disk', 'network', 'storage']
        
        result = await detector.detect_z_score_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.Z_SCORE
        assert result.anomaly_type == AnomalyType.STATISTICAL
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_iqr_anomaly(self, detector):
        """Test IQR anomaly detection"""
        # Normal data
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3])
        features = ['cpu', 'memory', 'disk', 'network', 'storage']
        
        result = await detector.detect_iqr_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.IQR
        assert result.anomaly_type == AnomalyType.STATISTICAL
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_z_score_anomaly_with_outlier(self, detector):
        """Test Z-score detection with clear outlier"""
        # Data with clear outlier
        data = np.array([0.5, 0.6, 0.4, 0.7, 5.0])  # 5.0 is clearly an outlier
        features = ['cpu', 'memory', 'disk', 'network', 'storage']
        
        result = await detector.detect_z_score_anomaly(data, features, threshold=1.5)  # Lower threshold
        
        assert isinstance(result, AnomalyDetectionResult)
        # Should detect the outlier
        assert result.is_anomaly
        assert result.anomaly_score > 0.5


class TestMLAnomalyDetector:
    """Test MLAnomalyDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        return MLAnomalyDetector()
    
    @pytest.mark.asyncio
    async def test_detect_isolation_forest_anomaly(self, detector):
        """Test Isolation Forest anomaly detection"""
        data = np.array([[0.5, 0.6, 0.4]])
        features = ['cpu', 'memory', 'disk']
        
        result = await detector.detect_isolation_forest_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.ISOLATION_FOREST
        assert result.anomaly_type == AnomalyType.ISOLATION
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_one_class_svm_anomaly(self, detector):
        """Test One-Class SVM anomaly detection"""
        data = np.array([[0.5, 0.6, 0.4]])
        features = ['cpu', 'memory', 'disk']
        
        result = await detector.detect_one_class_svm_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.ONE_CLASS_SVM
        assert result.anomaly_type == AnomalyType.ISOLATION
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_local_outlier_factor_anomaly(self, detector):
        """Test Local Outlier Factor anomaly detection"""
        data = np.array([[0.5, 0.6, 0.4]])
        features = ['cpu', 'memory', 'disk']
        
        result = await detector.detect_local_outlier_factor_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.LOCAL_OUTLIER_FACTOR
        assert result.anomaly_type == AnomalyType.DENSITY
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    def test_add_training_data(self, detector):
        """Test adding training data"""
        features = ['cpu', 'memory', 'disk']
        data = np.array([[0.5, 0.6, 0.4], [0.7, 0.8, 0.3]])
        
        detector.add_training_data(features, data)
        
        # Check that data was added
        assert tuple(features) in detector.training_data
        assert len(detector.training_data[tuple(features)]) == 2


class TestTimeSeriesAnomalyDetector:
    """Test TimeSeriesAnomalyDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        return TimeSeriesAnomalyDetector()
    
    @pytest.mark.asyncio
    async def test_detect_moving_average_anomaly(self, detector):
        """Test moving average anomaly detection"""
        # Generate time series data with enough points for moving average
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3, 0.8, 0.2, 0.9, 0.1, 0.6] * 10)  # 50 points
        features = ['cpu_usage']
        
        result = await detector.detect_moving_average_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.MOVING_AVERAGE
        assert result.anomaly_type == AnomalyType.TEMPORAL
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_exponential_smoothing_anomaly(self, detector):
        """Test exponential smoothing anomaly detection"""
        # Generate time series data
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3, 0.8, 0.2, 0.9, 0.1, 0.6])
        features = ['cpu_usage']
        
        result = await detector.detect_exponential_smoothing_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.detection_method == DetectionMethod.EXPONENTIAL_SMOOTHING
        assert result.anomaly_type == AnomalyType.TEMPORAL
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0


class TestAnomalyDetectionManager:
    """Test AnomalyDetectionManager functionality"""
    
    @pytest.fixture
    def manager(self):
        return AnomalyDetectionManager()
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, manager):
        """Test anomaly detection with multiple methods"""
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3])
        features = ['cpu', 'memory', 'disk', 'network', 'storage']
        
        results = await manager.detect_anomalies(data, features)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert isinstance(result, AnomalyDetectionResult)
            assert result.features == features
    
    @pytest.mark.asyncio
    async def test_get_consensus_anomaly(self, manager):
        """Test consensus anomaly detection"""
        data = np.array([0.5, 0.6, 0.4, 0.7, 0.3])
        features = ['cpu', 'memory', 'disk', 'network', 'storage']
        
        result = await manager.get_consensus_anomaly(data, features)
        
        assert isinstance(result, AnomalyDetectionResult)
        assert result.features == features
        assert isinstance(result.is_anomaly, bool)
        assert 0.0 <= result.anomaly_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
    
    def test_get_detection_history(self, manager):
        """Test detection history retrieval"""
        history = manager.get_detection_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size
    
    def test_get_detection_statistics(self, manager):
        """Test detection statistics"""
        stats = manager.get_detection_statistics()
        
        assert 'total_detections' in stats
        assert 'anomaly_rate' in stats
        assert 'method_usage' in stats
        assert 'feature_frequency' in stats
        
        assert isinstance(stats['total_detections'], int)
        assert 0.0 <= stats['anomaly_rate'] <= 1.0


class TestResourceMonitor:
    """Test ResourceMonitor functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ResourceMonitor()
    
    def test_record_metrics(self, monitor):
        """Test recording resource metrics"""
        from spider.monitoring.capacity_planning import ResourceMetrics, ResourceType
        
        metrics = ResourceMetrics(
            resource_type=ResourceType.CPU,
            current_usage=0.8,
            peak_usage=0.9,
            average_usage=0.7,
            capacity=100.0,
            timestamp=datetime.now()
        )
        
        monitor.record_metrics(metrics)
        
        # Check that metrics were recorded
        current = monitor.get_current_metrics(ResourceType.CPU)
        assert current is not None
        assert current.current_usage == 0.8
    
    def test_get_usage_trend(self, monitor):
        """Test getting usage trend"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Record some metrics
        for i in range(10):
            metrics = ResourceMetrics(
                resource_type=ResourceType.CPU,
                current_usage=0.5 + i * 0.01,
                peak_usage=0.9,
                average_usage=0.7,
                capacity=100.0,
                timestamp=datetime.now() - timedelta(hours=i)
            )
            monitor.record_metrics(metrics)
        
        trend = monitor.get_usage_trend(ResourceType.CPU, hours=24)
        assert isinstance(trend, list)
        assert len(trend) > 0
    
    def test_get_peak_usage(self, monitor):
        """Test getting peak usage"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Record metrics with different usage levels
        for usage in [0.5, 0.8, 0.6, 0.9, 0.7]:
            metrics = ResourceMetrics(
                resource_type=ResourceType.CPU,
                current_usage=usage,
                peak_usage=usage,
                average_usage=usage,
                capacity=100.0,
                timestamp=datetime.now()
            )
            monitor.record_metrics(metrics)
        
        peak = monitor.get_peak_usage(ResourceType.CPU)
        assert peak == 0.9  # Should be the highest usage recorded


class TestPredictiveScaler:
    """Test PredictiveScaler functionality"""
    
    @pytest.fixture
    def scaler(self):
        return PredictiveScaler()
    
    @pytest.mark.asyncio
    async def test_analyze_scaling_need_scale_up(self, scaler):
        """Test scaling analysis for scale up scenario"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # High usage scenario
        current_usage = 0.9
        usage_trend = [0.8, 0.85, 0.9, 0.88, 0.92]
        capacity = 100.0
        
        result = await scaler.analyze_scaling_need(
            ResourceType.CPU, current_usage, usage_trend, capacity
        )
        
        assert isinstance(result, ScalingRecommendation)
        assert result.resource_type == ResourceType.CPU
        assert result.action in [ScalingAction.SCALE_UP, ScalingAction.SCALE_OUT, ScalingAction.NO_ACTION]
        assert result.current_capacity == capacity
        assert result.scaling_factor > 0
        assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_scaling_need_scale_down(self, scaler):
        """Test scaling analysis for scale down scenario"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Low usage scenario
        current_usage = 0.2
        usage_trend = [0.3, 0.25, 0.2, 0.18, 0.22] * 3  # Need more data for scale down
        capacity = 100.0
        
        result = await scaler.analyze_scaling_need(
            ResourceType.CPU, current_usage, usage_trend, capacity
        )
        
        assert isinstance(result, ScalingRecommendation)
        assert result.resource_type == ResourceType.CPU
        assert result.action in [ScalingAction.SCALE_DOWN, ScalingAction.SCALE_IN, ScalingAction.NO_ACTION]
        assert result.current_capacity == capacity
        assert 0.0 <= result.confidence <= 1.0
    
    def test_record_scaling_action(self, scaler):
        """Test recording scaling actions"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Check that we're not in cooldown initially
        assert not scaler._is_in_cooldown(ResourceType.CPU)
        
        scaler.record_scaling_action(ResourceType.CPU)
        
        # Check that cooldown was set (should be True after recording)
        assert scaler._is_in_cooldown(ResourceType.CPU)
    
    def test_get_scaling_history(self, scaler):
        """Test getting scaling history"""
        history = scaler.get_scaling_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestCapacityForecaster:
    """Test CapacityForecaster functionality"""
    
    @pytest.fixture
    def forecaster(self):
        return CapacityForecaster()
    
    @pytest.mark.asyncio
    async def test_forecast_capacity_usage(self, forecaster):
        """Test capacity usage forecasting"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Generate historical data
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        values = [0.5 + 0.1 * np.sin(i * 0.1) + np.random.normal(0, 0.05) for i in range(24)]
        historical_data = list(zip(timestamps, values))
        
        forecast = await forecaster.forecast_capacity_usage(
            ResourceType.CPU, historical_data, 12
        )
        
        assert isinstance(forecast, CapacityForecast)
        assert forecast.resource_type == ResourceType.CPU
        assert len(forecast.forecasted_usage) == 12
        assert len(forecast.timestamps) == 12
        assert len(forecast.confidence_intervals) == 12
        assert 0.0 <= forecast.peak_usage_prediction <= 1.0
    
    @pytest.mark.asyncio
    async def test_forecast_capacity_usage_insufficient_data(self, forecaster):
        """Test forecasting with insufficient data"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Insufficient data
        historical_data = [(datetime.now(), 0.5)]
        
        forecast = await forecaster.forecast_capacity_usage(
            ResourceType.CPU, historical_data, 12
        )
        
        assert isinstance(forecast, CapacityForecast)
        assert forecast.resource_type == ResourceType.CPU
        assert len(forecast.forecasted_usage) == 12
        assert "Insufficient historical data" in forecast.recommendations[0]
    
    def test_get_forecast_history(self, forecaster):
        """Test getting forecast history"""
        history = forecaster.get_forecast_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestCostOptimizer:
    """Test CostOptimizer functionality"""
    
    @pytest.fixture
    def optimizer(self):
        return CostOptimizer()
    
    @pytest.mark.asyncio
    async def test_optimize_costs(self, optimizer):
        """Test cost optimization"""
        from spider.monitoring.capacity_planning import ResourceType
        
        current_resources = {
            ResourceType.CPU: 100.0,
            ResourceType.MEMORY: 200.0,
            ResourceType.STORAGE: 500.0
        }
        
        usage_patterns = {
            ResourceType.CPU: [0.8, 0.9, 0.7, 0.85, 0.9],
            ResourceType.MEMORY: [0.6, 0.7, 0.5, 0.65, 0.7],
            ResourceType.STORAGE: [0.4, 0.5, 0.3, 0.45, 0.5]
        }
        
        cost_per_unit = {
            ResourceType.CPU: 0.1,
            ResourceType.MEMORY: 0.05,
            ResourceType.STORAGE: 0.02
        }
        
        optimization = await optimizer.optimize_costs(
            current_resources, usage_patterns, cost_per_unit
        )
        
        assert isinstance(optimization, CostOptimization)
        assert optimization.current_cost > 0
        assert optimization.optimized_cost >= 0
        assert optimization.savings_percentage >= 0
        assert isinstance(optimization.recommendations, list)
        assert optimization.implementation_effort in ['low', 'medium', 'high']
    
    def test_get_optimization_history(self, optimizer):
        """Test getting optimization history"""
        history = optimizer.get_optimization_history()
        assert isinstance(history, list)
        assert len(history) <= 1000  # Max history size


class TestCapacityPlanningManager:
    """Test CapacityPlanningManager functionality"""
    
    @pytest.fixture
    def manager(self):
        return CapacityPlanningManager()
    
    @pytest.mark.asyncio
    async def test_start_stop_planning(self, manager):
        """Test starting and stopping capacity planning"""
        assert not manager.planning_active
        
        await manager.start_planning(interval=0.1)
        assert manager.planning_active
        
        await asyncio.sleep(0.2)  # Let it run briefly
        
        await manager.stop_planning()
        assert not manager.planning_active
    
    def test_record_resource_metrics(self, manager):
        """Test recording resource metrics"""
        from spider.monitoring.capacity_planning import ResourceType
        
        manager.record_resource_metrics(
            ResourceType.CPU, 0.8, 100.0
        )
        
        # Check that metrics were recorded
        current = manager.resource_monitor.get_current_metrics(ResourceType.CPU)
        assert current is not None
        assert current.current_usage == 0.8
        assert current.capacity == 100.0
    
    @pytest.mark.asyncio
    async def test_get_scaling_recommendations(self, manager):
        """Test getting scaling recommendations"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Record some metrics first
        manager.record_resource_metrics(ResourceType.CPU, 0.9, 100.0)
        
        # Record usage trend
        for i in range(20):
            manager.record_resource_metrics(
                ResourceType.CPU, 0.8 + i * 0.01, 100.0,
                timestamp=datetime.now() - timedelta(hours=i)
            )
        
        recommendation = await manager.get_scaling_recommendations(ResourceType.CPU)
        
        if recommendation:  # May be None if no scaling needed
            assert isinstance(recommendation, ScalingRecommendation)
            assert recommendation.resource_type == ResourceType.CPU
    
    @pytest.mark.asyncio
    async def test_get_capacity_forecast(self, manager):
        """Test getting capacity forecast"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Record historical data
        for i in range(30):
            manager.record_resource_metrics(
                ResourceType.CPU, 0.5 + 0.1 * np.sin(i * 0.1), 100.0,
                timestamp=datetime.now() - timedelta(hours=i)
            )
        
        forecast = await manager.get_capacity_forecast(ResourceType.CPU, hours=12)
        
        if forecast:  # May be None if insufficient data
            assert isinstance(forecast, CapacityForecast)
            assert forecast.resource_type == ResourceType.CPU
            assert len(forecast.forecasted_usage) == 12
    
    @pytest.mark.asyncio
    async def test_optimize_costs(self, manager):
        """Test cost optimization"""
        from spider.monitoring.capacity_planning import ResourceType
        
        # Record some metrics
        manager.record_resource_metrics(ResourceType.CPU, 0.8, 100.0)
        manager.record_resource_metrics(ResourceType.MEMORY, 0.6, 200.0)
        
        cost_per_unit = {
            ResourceType.CPU: 0.1,
            ResourceType.MEMORY: 0.05,
            ResourceType.STORAGE: 0.02
        }
        
        optimization = await manager.optimize_costs(cost_per_unit)
        
        assert isinstance(optimization, CostOptimization)
        assert optimization.current_cost > 0
        assert optimization.optimized_cost >= 0
    
    def test_add_alert_callback(self, manager):
        """Test adding alert callbacks"""
        callback = Mock()
        manager.add_alert_callback(callback)
        
        assert callback in manager.alert_callbacks
    
    def test_get_planning_status(self, manager):
        """Test getting planning status"""
        status = manager.get_planning_status()
        
        assert 'planning_active' in status
        assert 'monitored_resources' in status
        assert 'scaling_recommendations' in status
        assert 'capacity_forecasts' in status
        assert 'cost_optimizations' in status


@pytest.mark.asyncio
async def test_integration_predictive_monitoring():
    """Test integration of predictive monitoring components"""
    # Create components
    engine = PredictiveAnalyticsEngine()
    monitor = PredictiveMonitor()
    anomaly_manager = AnomalyDetectionManager()
    capacity_manager = CapacityPlanningManager()
    
    # Test anomaly detection
    data = np.array([0.5, 0.6, 0.4, 0.7, 0.3])
    features = ['cpu', 'memory', 'disk', 'network', 'storage']
    
    anomaly_results = await anomaly_manager.detect_anomalies(data, features)
    assert len(anomaly_results) > 0
    
    # Test failure prediction
    metrics = {'cpu_usage': 0.8, 'memory_usage': 0.7, 'error_rate': 0.05}
    failure_result = await engine.predict_failure(metrics)
    assert isinstance(failure_result, PredictionResult)
    
    # Test capacity planning
    capacity_manager.record_resource_metrics(ResourceType.CPU, 0.9, 100.0)
    scaling_rec = await capacity_manager.get_scaling_recommendations(ResourceType.CPU)
    if scaling_rec:
        assert isinstance(scaling_rec, ScalingRecommendation)
    
    # Test monitoring integration
    await monitor.start_monitoring(interval=0.1)
    await asyncio.sleep(0.2)
    await monitor.stop_monitoring()
    
    status = monitor.get_monitoring_status()
    assert 'monitoring_active' in status


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
