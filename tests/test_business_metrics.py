"""
Tests for advanced business metrics and analytics.

This module tests the business metrics functionality.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.business_metrics import (
    MetricsCollector, BusinessAnalytics, MetricsDashboard,
    MetricValue, MetricDefinition, MetricDataPoint, MetricAggregation,
    BusinessKPI, PerformanceBenchmark,
    MetricType, MetricCategory, MetricGranularity
)


class TestMetricValue:
    """Test MetricValue data structure."""
    
    def test_metric_value_creation(self):
        """Test creating a metric value."""
        value = MetricValue(
            value=75.5,
            timestamp=time.time(),
            labels={"instance": "scraper-1", "region": "us-east"},
            metadata={"source": "system"}
        )
        
        assert value.value == 75.5
        assert value.labels["instance"] == "scraper-1"
        assert value.metadata["source"] == "system"


class TestMetricDefinition:
    """Test MetricDefinition data structure."""
    
    def test_metric_definition_creation(self):
        """Test creating a metric definition."""
        definition = MetricDefinition(
            name="requests_per_second",
            description="Number of requests per second",
            metric_type=MetricType.RATE,
            category=MetricCategory.PERFORMANCE,
            unit="requests/sec",
            granularity=MetricGranularity.SECOND,
            labels=["instance", "region"],
            aggregation_functions=["sum", "avg"],
            retention_days=30,
            alert_thresholds={"warning": 1000, "critical": 2000}
        )
        
        assert definition.name == "requests_per_second"
        assert definition.metric_type == MetricType.RATE
        assert definition.category == MetricCategory.PERFORMANCE
        assert definition.unit == "requests/sec"
        assert definition.granularity == MetricGranularity.SECOND
        assert len(definition.labels) == 2
        assert len(definition.aggregation_functions) == 2
        assert definition.retention_days == 30
        assert definition.alert_thresholds["warning"] == 1000


class TestMetricDataPoint:
    """Test MetricDataPoint data structure."""
    
    def test_metric_data_point_creation(self):
        """Test creating a metric data point."""
        data_point = MetricDataPoint(
            metric_name="response_time",
            value=1.25,
            timestamp=time.time(),
            labels={"url": "https://example.com"},
            metadata={"method": "GET"}
        )
        
        assert data_point.metric_name == "response_time"
        assert data_point.value == 1.25
        assert data_point.labels["url"] == "https://example.com"
        assert data_point.metadata["method"] == "GET"


class TestBusinessKPI:
    """Test BusinessKPI data structure."""
    
    def test_business_kpi_creation(self):
        """Test creating a business KPI."""
        kpi = BusinessKPI(
            name="Data Collection Efficiency",
            description="Data points collected per hour",
            value=1500.0,
            target_value=1000.0,
            unit="points/hour",
            category="Productivity",
            trend="up",
            confidence=0.85,
            last_updated=time.time(),
            metadata={"baseline": 1000}
        )
        
        assert kpi.name == "Data Collection Efficiency"
        assert kpi.value == 1500.0
        assert kpi.target_value == 1000.0
        assert kpi.trend == "up"
        assert kpi.confidence == 0.85


class TestPerformanceBenchmark:
    """Test PerformanceBenchmark data structure."""
    
    def test_performance_benchmark_creation(self):
        """Test creating a performance benchmark."""
        benchmark = PerformanceBenchmark(
            name="response_time_benchmark",
            metric_name="response_time",
            baseline_value=2.0,
            current_value=1.5,
            improvement_percentage=25.0,
            status="excellent",
            recommendations=["Consider scaling up", "Document practices"]
        )
        
        assert benchmark.name == "response_time_benchmark"
        assert benchmark.baseline_value == 2.0
        assert benchmark.current_value == 1.5
        assert benchmark.improvement_percentage == 25.0
        assert benchmark.status == "excellent"
        assert len(benchmark.recommendations) == 2


class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    def test_collector_initialization(self):
        """Test collector initialization."""
        collector = MetricsCollector(max_data_points=1000)
        
        assert collector.max_data_points == 1000
        assert len(collector.metrics) == 0
        assert len(collector.metric_definitions) > 0  # Should have default metrics
        assert len(collector.collectors) == 0
        assert collector.is_collecting is False
        assert collector.collection_task is None
    
    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()
        
        collector.record_metric(
            "requests_per_second",
            value=150.0,
            labels={"instance": "scraper-1"},
            metadata={"source": "test"}
        )
        
        assert "requests_per_second" in collector.metrics
        assert len(collector.metrics["requests_per_second"]) == 1
        
        data_point = collector.metrics["requests_per_second"][0]
        assert data_point.value == 150.0
        assert data_point.labels["instance"] == "scraper-1"
        assert data_point.metadata["source"] == "test"
    
    def test_record_unknown_metric(self):
        """Test recording an unknown metric."""
        collector = MetricsCollector()
        
        # Should not raise error, but should log warning
        collector.record_metric("unknown_metric", value=100.0)
        
        # Should not be recorded
        assert "unknown_metric" not in collector.metrics
    
    def test_get_metric_data(self):
        """Test getting metric data."""
        collector = MetricsCollector()
        
        # Record some data
        now = time.time()
        collector.record_metric("requests_per_second", 100.0)
        time.sleep(0.01)
        collector.record_metric("requests_per_second", 200.0)
        time.sleep(0.01)
        collector.record_metric("requests_per_second", 300.0)
        
        # Get all data
        all_data = collector.get_metric_data("requests_per_second")
        assert len(all_data) == 3
        
        # Get data with time filter
        recent_data = collector.get_metric_data(
            "requests_per_second",
            start_time=now + 0.005
        )
        assert len(recent_data) == 2
        
        # Get data with end time filter
        old_data = collector.get_metric_data(
            "requests_per_second",
            end_time=now + 0.005
        )
        assert len(old_data) == 1
    
    def test_get_metric_aggregation(self):
        """Test getting metric aggregation."""
        collector = MetricsCollector()
        
        # Record some data points
        base_time = time.time()
        for i in range(10):
            collector.record_metric("response_time", value=1.0 + i * 0.1)
            time.sleep(0.01)
        
        # Get aggregation
        aggregations = collector.get_metric_aggregation(
            "response_time",
            "avg",
            MetricGranularity.MINUTE,
            start_time=base_time
        )
        
        assert len(aggregations) > 0
        assert aggregations[0].metric_name == "response_time"
        assert aggregations[0].aggregation_function == "avg"
        assert aggregations[0].granularity == MetricGranularity.MINUTE
        assert aggregations[0].count == 10
    
    def test_get_metric_definitions(self):
        """Test getting metric definitions."""
        collector = MetricsCollector()
        
        definitions = collector.get_metric_definitions()
        
        assert len(definitions) > 0
        assert "requests_per_second" in definitions
        assert "response_time" in definitions
        assert "success_rate" in definitions
        
        # Check a specific definition
        rps_def = definitions["requests_per_second"]
        assert rps_def.metric_type == MetricType.RATE
        assert rps_def.category == MetricCategory.PERFORMANCE
        assert rps_def.unit == "requests/sec"
    
    def test_add_collector(self):
        """Test adding a metric collector."""
        collector = MetricsCollector()
        
        def test_collector():
            collector.record_metric("test_metric", 100.0)
        
        collector.add_collector("test", test_collector)
        
        assert "test" in collector.collectors
        assert collector.collectors["test"] == test_collector
    
    @pytest.mark.asyncio
    async def test_start_stop_collection(self):
        """Test starting and stopping collection."""
        collector = MetricsCollector()
        collector.collection_interval = 0.1
        
        # Add a test collector
        collector.add_collector("test", lambda: collector.record_metric("test_metric", 100.0))
        
        # Start collection
        await collector.start_collection()
        assert collector.is_collecting is True
        assert collector.collection_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop collection
        await collector.stop_collection()
        assert collector.is_collecting is False
        # Task should be cancelled or finished
        assert collector.collection_task is None or collector.collection_task.cancelled() or collector.collection_task.done()
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        collector = MetricsCollector()
        
        # Record some old data
        old_time = time.time() - 86400  # 24 hours ago
        with patch('time.time', return_value=old_time):
            collector.record_metric("requests_per_second", 100.0)
        
        # Record some recent data
        collector.record_metric("requests_per_second", 200.0)
        
        # Cleanup data older than 1 hour
        collector.cleanup_old_data(max_age_days=0.04)  # ~1 hour
        
        # Should only have recent data
        data = collector.get_metric_data("requests_per_second")
        assert len(data) == 1
        assert data[0].value == 200.0


class TestBusinessAnalytics:
    """Test business analytics functionality."""
    
    def test_analytics_initialization(self):
        """Test analytics initialization."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        assert analytics.metrics_collector == collector
        assert len(analytics.kpis) > 0
        assert len(analytics.benchmarks) == 0
        
        # Check default KPIs
        assert "data_collection_efficiency" in analytics.kpis
        assert "cost_per_data_point" in analytics.kpis
        assert "data_quality_score" in analytics.kpis
        assert "success_rate" in analytics.kpis
    
    def test_get_kpis(self):
        """Test getting KPIs."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        kpis = analytics.get_kpis()
        
        assert len(kpis) > 0
        assert all(isinstance(kpi, BusinessKPI) for kpi in kpis.values())
        
        # Check specific KPI
        efficiency_kpi = kpis["data_collection_efficiency"]
        assert efficiency_kpi.name == "Data Collection Efficiency"
        assert efficiency_kpi.unit == "points/hour"
    
    def test_get_kpi_summary(self):
        """Test getting KPI summary."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        summary = analytics.get_kpi_summary()
        
        assert "total_kpis" in summary
        assert "on_target" in summary
        assert "off_target" in summary
        assert "average_confidence" in summary
        assert "kpis" in summary
        
        assert summary["total_kpis"] > 0
        assert summary["average_confidence"] >= 0.0
        assert len(summary["kpis"]) == summary["total_kpis"]
    
    @pytest.mark.asyncio
    async def test_update_kpis(self):
        """Test updating KPIs."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Record some test data
        collector.record_metric("data_points_collected", 100.0)
        collector.record_metric("data_quality_score", 95.0)
        collector.record_metric("success_rate", 98.0)
        
        # Update KPIs
        await analytics.update_kpis()
        
        # Check that KPIs were updated
        kpis = analytics.get_kpis()
        assert kpis["data_collection_efficiency"].value > 0
        assert kpis["data_quality_score"].value == 95.0
        assert kpis["success_rate"].value == 98.0
    
    def test_create_performance_benchmark(self):
        """Test creating performance benchmark."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Record some baseline data
        base_time = time.time() - 3600  # 1 hour ago
        with patch('time.time', side_effect=[base_time + i for i in range(10)]):
            for i in range(10):
                collector.record_metric("response_time", 2.0 + i * 0.1)
        
        # Record some current data
        current_time = time.time()
        with patch('time.time', side_effect=[current_time + i for i in range(5)]):
            for i in range(5):
                collector.record_metric("response_time", 1.5 + i * 0.1)
        
        # Create benchmark
        benchmark = analytics.create_performance_benchmark("response_time", baseline_period_hours=1)
        
        assert benchmark.metric_name == "response_time"
        assert benchmark.baseline_value > 0
        assert benchmark.current_value > 0
        assert benchmark.improvement_percentage != 0
        assert benchmark.status in ["excellent", "good", "average", "poor", "critical"]
        assert len(benchmark.recommendations) > 0
    
    def test_calculate_trend(self):
        """Test trend calculation."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Test upward trend (needs to be more than 10% above target)
        trend = analytics._calculate_trend(120.0, 100.0)
        assert trend == "up"
        
        # Test downward trend (needs to be more than 10% below target)
        trend = analytics._calculate_trend(80.0, 100.0)
        assert trend == "down"
        
        # Test stable trend
        trend = analytics._calculate_trend(105.0, 100.0)
        assert trend == "stable"
        
        # Test reverse trend (higher is worse) - needs to be more than 10% above target
        trend = analytics._calculate_trend(120.0, 100.0, reverse=True)
        assert trend == "down"
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Create a KPI with recent timestamp
        kpi = BusinessKPI(
            name="test",
            description="test",
            value=100.0,
            target_value=100.0,
            unit="test",
            category="test",
            trend="stable",
            confidence=0.0,
            last_updated=time.time()
        )
        
        confidence = analytics._calculate_confidence(kpi)
        assert confidence > 0.8  # Should be high for recent data
        
        # Test with old data
        kpi.last_updated = time.time() - 86400  # 24 hours ago
        confidence = analytics._calculate_confidence(kpi)
        assert confidence < 0.5  # Should be lower for old data


class TestMetricsDashboard:
    """Test metrics dashboard functionality."""
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        assert dashboard.metrics_collector == collector
        assert dashboard.business_analytics == analytics
        assert "refresh_interval" in dashboard.dashboard_config
        assert "default_time_range" in dashboard.dashboard_config
    
    def test_get_dashboard_data(self):
        """Test getting dashboard data."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Record some test data
        collector.record_metric("requests_per_second", 150.0)
        collector.record_metric("response_time", 1.5)
        
        data = dashboard.get_dashboard_data("1h")
        
        assert "timestamp" in data
        assert "time_range" in data
        assert "kpis" in data
        assert "metrics" in data
        assert "alerts" in data
        assert "trends" in data
        
        assert data["time_range"] == "1h"
        assert len(data["metrics"]) > 0
        assert isinstance(data["alerts"], list)
        assert isinstance(data["trends"], dict)
    
    def test_parse_time_range(self):
        """Test time range parsing."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Test different time ranges
        now = time.time()
        
        start_time = dashboard._parse_time_range("30m")
        assert abs((now - start_time) - (30 * 60)) < 1  # Allow 1 second tolerance
        
        start_time = dashboard._parse_time_range("2h")
        assert abs((now - start_time) - (2 * 3600)) < 1
        
        start_time = dashboard._parse_time_range("1d")
        assert abs((now - start_time) - 86400) < 1
        
        start_time = dashboard._parse_time_range("invalid")
        assert abs((now - start_time) - 3600) < 1  # Default to 1 hour
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Record some test data
        collector.record_metric("requests_per_second", 150.0)
        collector.record_metric("response_time", 1.5)
        collector.record_metric("response_time", 2.0)
        
        summary = dashboard._get_metrics_summary(time.time() - 3600)
        
        assert "requests_per_second" in summary
        assert "response_time" in summary
        
        # Check specific metric summary
        rps_summary = summary["requests_per_second"]
        assert "current_value" in rps_summary
        assert "average" in rps_summary
        assert "min" in rps_summary
        assert "max" in rps_summary
        assert "count" in rps_summary
        assert "unit" in rps_summary
        assert "category" in rps_summary
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Create a KPI with downward trend
        kpi = analytics.kpis["data_collection_efficiency"]
        kpi.trend = "down"
        kpi.confidence = 0.8
        
        alerts = dashboard._get_active_alerts()
        
        assert isinstance(alerts, list)
        # Should have at least one alert for the downward trending KPI
        assert len(alerts) > 0
        assert any(alert["type"] == "kpi" for alert in alerts)
    
    def test_get_trend_analysis(self):
        """Test getting trend analysis."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Record some data with a trend
        base_time = time.time() - 3600
        for i in range(10):
            collector.record_metric("response_time", 1.0 + i * 0.1)
        
        trends = dashboard._get_trend_analysis(base_time)
        
        assert "response_time" in trends
        trend_data = trends["response_time"]
        assert "slope" in trend_data
        assert "direction" in trend_data
        assert "strength" in trend_data
        assert "correlation" in trend_data
        
        assert trend_data["direction"] in ["up", "down", "stable"]
        assert 0 <= trend_data["correlation"] <= 1
    
    def test_calculate_correlation(self):
        """Test correlation calculation."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Test perfect positive correlation
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        correlation = dashboard._calculate_correlation(x, y)
        assert abs(correlation - 1.0) < 0.001
        
        # Test perfect negative correlation
        y = [10, 8, 6, 4, 2]
        correlation = dashboard._calculate_correlation(x, y)
        assert abs(correlation - (-1.0)) < 0.001
        
        # Test no correlation
        y = [1, 1, 1, 1, 1]
        correlation = dashboard._calculate_correlation(x, y)
        assert abs(correlation) < 0.001
    
    def test_export_metrics_json(self):
        """Test exporting metrics as JSON."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Record some test data
        collector.record_metric("requests_per_second", 150.0)
        collector.record_metric("response_time", 1.5)
        
        json_data = dashboard.export_metrics("json", "1h")
        
        assert isinstance(json_data, str)
        data = json.loads(json_data)
        
        assert "export_timestamp" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "metrics" in data
        assert "requests_per_second" in data["metrics"]
        assert "response_time" in data["metrics"]
    
    def test_export_metrics_csv(self):
        """Test exporting metrics as CSV."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Record some test data
        collector.record_metric("requests_per_second", 150.0)
        collector.record_metric("response_time", 1.5)
        
        csv_data = dashboard.export_metrics("csv", "1h")
        
        assert isinstance(csv_data, str)
        lines = csv_data.split("\n")
        
        # Should have header and data lines
        assert len(lines) > 1
        assert "metric_name,timestamp,value,labels,metadata" in lines[0]
        
        # Should have data for both metrics
        data_lines = [line for line in lines[1:] if line.strip()]
        assert len(data_lines) >= 2
    
    def test_export_metrics_unsupported_format(self):
        """Test exporting with unsupported format."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            dashboard.export_metrics("xml", "1h")


class TestBusinessMetricsIntegration:
    """Integration tests for business metrics system."""
    
    @pytest.mark.asyncio
    async def test_complete_metrics_workflow(self):
        """Test complete metrics workflow."""
        collector = MetricsCollector()
        collector.collection_interval = 0.1
        analytics = BusinessAnalytics(collector)
        dashboard = MetricsDashboard(collector, analytics)
        
        # Add a test collector
        def test_collector():
            collector.record_metric("requests_per_second", 150.0)
            collector.record_metric("response_time", 1.5)
            collector.record_metric("data_points_collected", 100.0)
        
        collector.add_collector("test", test_collector)
        
        # Start collection
        await collector.start_collection()
        
        # Let it collect some data
        await asyncio.sleep(0.2)
        
        # Update KPIs
        await analytics.update_kpis()
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data("1h")
        
        # Stop collection
        await collector.stop_collection()
        
        # Verify data was collected
        assert len(collector.get_metric_data("requests_per_second")) > 0
        assert len(collector.get_metric_data("response_time")) > 0
        assert len(collector.get_metric_data("data_points_collected")) > 0
        
        # Verify KPIs were updated
        kpis = analytics.get_kpis()
        assert kpis["data_collection_efficiency"].value > 0
        
        # Verify dashboard data
        assert len(dashboard_data["metrics"]) > 0
        assert "requests_per_second" in dashboard_data["metrics"]
    
    def test_metric_aggregation_workflow(self):
        """Test metric aggregation workflow."""
        collector = MetricsCollector()
        
        # Record data over time
        base_time = time.time()
        for i in range(20):
            collector.record_metric("response_time", 1.0 + i * 0.1)
            time.sleep(0.01)
        
        # Get different aggregations
        avg_agg = collector.get_metric_aggregation(
            "response_time", "avg", MetricGranularity.MINUTE, start_time=base_time
        )
        sum_agg = collector.get_metric_aggregation(
            "response_time", "sum", MetricGranularity.MINUTE, start_time=base_time
        )
        max_agg = collector.get_metric_aggregation(
            "response_time", "max", MetricGranularity.MINUTE, start_time=base_time
        )
        
        assert len(avg_agg) > 0
        assert len(sum_agg) > 0
        assert len(max_agg) > 0
        
        # Check aggregation values
        assert avg_agg[0].aggregation_function == "avg"
        assert sum_agg[0].aggregation_function == "sum"
        assert max_agg[0].aggregation_function == "max"
        
        # Sum should be higher than average
        assert sum_agg[0].value > avg_agg[0].value
        # Max should be higher than average
        assert max_agg[0].value > avg_agg[0].value
    
    def test_kpi_trend_analysis(self):
        """Test KPI trend analysis."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Record data that shows improvement
        base_time = time.time() - 3600
        for i in range(10):
            collector.record_metric("data_quality_score", 80.0 + i * 2.0)
        
        # Update KPIs
        asyncio.run(analytics.update_kpis())
        
        # Check that trend was calculated
        kpis = analytics.get_kpis()
        quality_kpi = kpis["data_quality_score"]
        
        # Should have a trend (up, down, or stable)
        assert quality_kpi.trend in ["up", "down", "stable"]
        assert quality_kpi.confidence > 0.0
    
    def test_benchmark_creation_workflow(self):
        """Test benchmark creation workflow."""
        collector = MetricsCollector()
        analytics = BusinessAnalytics(collector)
        
        # Record some data points with different timestamps
        base_time = time.time() - 3600  # 1 hour ago
        for i in range(5):
            with patch('time.time', return_value=base_time + i * 60):
                collector.record_metric("response_time", 3.0 + i * 0.1)
        
        # Record current data
        current_time = time.time() - 300  # 5 minutes ago
        for i in range(3):
            with patch('time.time', return_value=current_time + i * 60):
                collector.record_metric("response_time", 1.0 + i * 0.1)
        
        # Create benchmark
        benchmark = analytics.create_performance_benchmark("response_time", baseline_period_hours=1)
        
        # Should have some data
        assert benchmark.baseline_value > 0 or benchmark.current_value > 0
        assert benchmark.status in ["excellent", "good", "average", "poor", "critical", "unknown"]
        assert len(benchmark.recommendations) > 0
