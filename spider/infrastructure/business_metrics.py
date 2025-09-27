"""
Advanced business metrics and analytics for web scraping.

This module provides comprehensive metrics collection, analysis, and reporting
for monitoring scraping performance, business value, and operational efficiency.
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta
import hashlib
import uuid


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    RATE = "rate"
    PERCENTILE = "percentile"


class MetricCategory(Enum):
    """Categories of metrics."""
    PERFORMANCE = "performance"
    BUSINESS = "business"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    QUALITY = "quality"
    COST = "cost"
    COMPLIANCE = "compliance"


class MetricGranularity(Enum):
    """Time granularity for metrics."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class MetricValue:
    """Represents a metric value."""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricDefinition:
    """Defines a metric."""
    name: str
    description: str
    metric_type: MetricType
    category: MetricCategory
    unit: str
    granularity: MetricGranularity
    labels: List[str] = field(default_factory=list)
    aggregation_functions: List[str] = field(default_factory=lambda: ["sum", "avg", "min", "max"])
    retention_days: int = 30
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class MetricDataPoint:
    """Represents a single data point for a metric."""
    metric_name: str
    value: float
    timestamp: float
    labels: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricAggregation:
    """Represents aggregated metric data."""
    metric_name: str
    aggregation_function: str
    value: float
    timestamp: float
    granularity: MetricGranularity
    labels: Dict[str, str]
    count: int
    min_value: float
    max_value: float
    std_dev: float


@dataclass
class BusinessKPI:
    """Represents a business key performance indicator."""
    name: str
    description: str
    value: float
    target_value: float
    unit: str
    category: str
    trend: str  # "up", "down", "stable"
    confidence: float
    last_updated: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    """Represents a performance benchmark."""
    name: str
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percentage: float
    status: str  # "excellent", "good", "average", "poor", "critical"
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    """Collects and stores metrics data."""
    
    def __init__(self, max_data_points: int = 100000):
        """Initialize the metrics collector.
        
        Args:
            max_data_points: Maximum number of data points to keep in memory
        """
        self.max_data_points = max_data_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_data_points))
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.collectors: Dict[str, Callable] = {}
        self.is_collecting = False
        self.collection_task: Optional[asyncio.Task] = None
        self.collection_interval = 30.0  # seconds
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default metric definitions."""
        # Performance metrics
        self._add_metric_definition(
            name="requests_per_second",
            description="Number of requests processed per second",
            metric_type=MetricType.RATE,
            category=MetricCategory.PERFORMANCE,
            unit="requests/sec",
            granularity=MetricGranularity.SECOND
        )
        
        self._add_metric_definition(
            name="response_time",
            description="Average response time for requests",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.PERFORMANCE,
            unit="seconds",
            granularity=MetricGranularity.SECOND
        )
        
        self._add_metric_definition(
            name="success_rate",
            description="Percentage of successful requests",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.PERFORMANCE,
            unit="percent",
            granularity=MetricGranularity.MINUTE
        )
        
        # Business metrics
        self._add_metric_definition(
            name="data_points_collected",
            description="Number of data points collected",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.BUSINESS,
            unit="points",
            granularity=MetricGranularity.MINUTE
        )
        
        self._add_metric_definition(
            name="unique_urls_scraped",
            description="Number of unique URLs scraped",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.BUSINESS,
            unit="urls",
            granularity=MetricGranularity.HOUR
        )
        
        self._add_metric_definition(
            name="data_quality_score",
            description="Overall data quality score",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.QUALITY,
            unit="score",
            granularity=MetricGranularity.MINUTE
        )
        
        # Operational metrics
        self._add_metric_definition(
            name="proxy_usage",
            description="Proxy usage percentage",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.OPERATIONAL,
            unit="percent",
            granularity=MetricGranularity.MINUTE
        )
        
        self._add_metric_definition(
            name="captcha_solve_rate",
            description="CAPTCHA solving success rate",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.OPERATIONAL,
            unit="percent",
            granularity=MetricGranularity.MINUTE
        )
        
        # Cost metrics
        self._add_metric_definition(
            name="proxy_cost_per_hour",
            description="Proxy costs per hour",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.COST,
            unit="USD",
            granularity=MetricGranularity.HOUR
        )
        
        self._add_metric_definition(
            name="captcha_cost_per_solve",
            description="CAPTCHA solving cost per solve",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.COST,
            unit="USD",
            granularity=MetricGranularity.MINUTE
        )
    
    def _add_metric_definition(self, name: str, description: str, metric_type: MetricType,
                             category: MetricCategory, unit: str, granularity: MetricGranularity,
                             labels: List[str] = None, retention_days: int = 30):
        """Add a metric definition.
        
        Args:
            name: Metric name
            description: Metric description
            metric_type: Type of metric
            category: Category of metric
            unit: Unit of measurement
            granularity: Time granularity
            labels: List of label names
            retention_days: Data retention period in days
        """
        self.metric_definitions[name] = MetricDefinition(
            name=name,
            description=description,
            metric_type=metric_type,
            category=category,
            unit=unit,
            granularity=granularity,
            labels=labels or [],
            retention_days=retention_days
        )
    
    def record_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None,
                     metadata: Dict[str, Any] = None):
        """Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            labels: Metric labels
            metadata: Additional metadata
        """
        if metric_name not in self.metric_definitions:
            logging.warning(f"Unknown metric: {metric_name}")
            return
        
        data_point = MetricDataPoint(
            metric_name=metric_name,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            metadata=metadata or {}
        )
        
        self.metrics[metric_name].append(data_point)
        logging.debug(f"Recorded metric {metric_name}: {value}")
    
    def get_metric_data(self, metric_name: str, start_time: float = None, 
                       end_time: float = None) -> List[MetricDataPoint]:
        """Get metric data for a specific time range.
        
        Args:
            metric_name: Name of the metric
            start_time: Start time (Unix timestamp)
            end_time: End time (Unix timestamp)
            
        Returns:
            List of metric data points
        """
        if metric_name not in self.metrics:
            return []
        
        data_points = list(self.metrics[metric_name])
        
        if start_time:
            data_points = [dp for dp in data_points if dp.timestamp >= start_time]
        
        if end_time:
            data_points = [dp for dp in data_points if dp.timestamp <= end_time]
        
        return data_points
    
    def get_metric_aggregation(self, metric_name: str, aggregation_function: str,
                             granularity: MetricGranularity, start_time: float = None,
                             end_time: float = None) -> List[MetricAggregation]:
        """Get aggregated metric data.
        
        Args:
            metric_name: Name of the metric
            aggregation_function: Function to use for aggregation
            granularity: Time granularity for aggregation
            start_time: Start time (Unix timestamp)
            end_time: End time (Unix timestamp)
            
        Returns:
            List of aggregated metric data
        """
        data_points = self.get_metric_data(metric_name, start_time, end_time)
        if not data_points:
            return []
        
        # Group data points by time buckets
        bucket_size = self._get_bucket_size(granularity)
        buckets = defaultdict(list)
        
        for dp in data_points:
            bucket_time = int(dp.timestamp // bucket_size) * bucket_size
            buckets[bucket_time].append(dp)
        
        # Aggregate each bucket
        aggregations = []
        for bucket_time, points in buckets.items():
            values = [dp.value for dp in points]
            
            if aggregation_function == "sum":
                value = sum(values)
            elif aggregation_function == "avg":
                value = statistics.mean(values)
            elif aggregation_function == "min":
                value = min(values)
            elif aggregation_function == "max":
                value = max(values)
            elif aggregation_function == "count":
                value = len(values)
            else:
                value = statistics.mean(values)  # Default to average
            
            aggregation = MetricAggregation(
                metric_name=metric_name,
                aggregation_function=aggregation_function,
                value=value,
                timestamp=bucket_time,
                granularity=granularity,
                labels={},  # Could be aggregated from individual points
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                std_dev=statistics.stdev(values) if len(values) > 1 else 0.0
            )
            
            aggregations.append(aggregation)
        
        return sorted(aggregations, key=lambda x: x.timestamp)
    
    def _get_bucket_size(self, granularity: MetricGranularity) -> int:
        """Get bucket size in seconds for a granularity.
        
        Args:
            granularity: Time granularity
            
        Returns:
            Bucket size in seconds
        """
        if granularity == MetricGranularity.SECOND:
            return 1
        elif granularity == MetricGranularity.MINUTE:
            return 60
        elif granularity == MetricGranularity.HOUR:
            return 3600
        elif granularity == MetricGranularity.DAY:
            return 86400
        elif granularity == MetricGranularity.WEEK:
            return 604800
        elif granularity == MetricGranularity.MONTH:
            return 2592000  # Approximate
        else:
            return 60  # Default to minute
    
    async def start_collection(self):
        """Start automatic metric collection."""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logging.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop automatic metric collection."""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logging.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Main collection loop."""
        while self.is_collecting:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self):
        """Collect metrics from registered collectors."""
        for collector_name, collector_func in self.collectors.items():
            try:
                if asyncio.iscoroutinefunction(collector_func):
                    await collector_func()
                else:
                    collector_func()
            except Exception as e:
                logging.error(f"Error in collector {collector_name}: {e}")
    
    def add_collector(self, name: str, collector_func: Callable):
        """Add a metric collector function.
        
        Args:
            name: Name of the collector
            collector_func: Function that collects metrics
        """
        self.collectors[name] = collector_func
        logging.info(f"Added metric collector: {name}")
    
    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Get all metric definitions."""
        return self.metric_definitions.copy()
    
    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old metric data.
        
        Args:
            max_age_days: Maximum age of data to keep
        """
        cutoff_time = time.time() - (max_age_days * 86400)
        
        for metric_name in self.metrics:
            # Remove old data points
            while (self.metrics[metric_name] and 
                   self.metrics[metric_name][0].timestamp < cutoff_time):
                self.metrics[metric_name].popleft()
        
        logging.info(f"Cleaned up metric data older than {max_age_days} days")


class BusinessAnalytics:
    """Provides business analytics and insights."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize business analytics.
        
        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics_collector = metrics_collector
        self.kpis: Dict[str, BusinessKPI] = {}
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        
        # Initialize default KPIs
        self._initialize_default_kpis()
    
    def _initialize_default_kpis(self):
        """Initialize default business KPIs."""
        # Data collection efficiency
        self.kpis["data_collection_efficiency"] = BusinessKPI(
            name="Data Collection Efficiency",
            description="Data points collected per hour",
            value=0.0,
            target_value=1000.0,
            unit="points/hour",
            category="Productivity",
            trend="stable",
            confidence=0.0,
            last_updated=time.time()
        )
        
        # Cost per data point
        self.kpis["cost_per_data_point"] = BusinessKPI(
            name="Cost per Data Point",
            description="Average cost to collect one data point",
            value=0.0,
            target_value=0.01,
            unit="USD",
            category="Cost",
            trend="stable",
            confidence=0.0,
            last_updated=time.time()
        )
        
        # Data quality score
        self.kpis["data_quality_score"] = BusinessKPI(
            name="Data Quality Score",
            description="Overall quality of collected data",
            value=0.0,
            target_value=95.0,
            unit="score",
            category="Quality",
            trend="stable",
            confidence=0.0,
            last_updated=time.time()
        )
        
        # Success rate
        self.kpis["success_rate"] = BusinessKPI(
            name="Success Rate",
            description="Percentage of successful scraping operations",
            value=0.0,
            target_value=98.0,
            unit="percent",
            category="Reliability",
            trend="stable",
            confidence=0.0,
            last_updated=time.time()
        )
    
    async def update_kpis(self):
        """Update all KPIs based on current metrics."""
        for kpi_name, kpi in self.kpis.items():
            try:
                await self._update_kpi(kpi_name, kpi)
            except Exception as e:
                logging.error(f"Error updating KPI {kpi_name}: {e}")
    
    async def _update_kpi(self, kpi_name: str, kpi: BusinessKPI):
        """Update a specific KPI.
        
        Args:
            kpi_name: Name of the KPI
            kpi: KPI object to update
        """
        if kpi_name == "data_collection_efficiency":
            # Calculate data points per hour
            data_points = self.metrics_collector.get_metric_data(
                "data_points_collected", 
                start_time=time.time() - 3600  # Last hour
            )
            kpi.value = len(data_points)
            kpi.trend = self._calculate_trend(kpi.value, kpi.target_value)
            
        elif kpi_name == "cost_per_data_point":
            # Calculate cost per data point
            proxy_costs = self.metrics_collector.get_metric_data(
                "proxy_cost_per_hour",
                start_time=time.time() - 3600
            )
            captcha_costs = self.metrics_collector.get_metric_data(
                "captcha_cost_per_solve",
                start_time=time.time() - 3600
            )
            
            total_cost = sum(dp.value for dp in proxy_costs) + sum(dp.value for dp in captcha_costs)
            data_points = len(self.metrics_collector.get_metric_data(
                "data_points_collected",
                start_time=time.time() - 3600
            ))
            
            kpi.value = total_cost / data_points if data_points > 0 else 0.0
            kpi.trend = self._calculate_trend(kpi.value, kpi.target_value, reverse=True)
            
        elif kpi_name == "data_quality_score":
            # Get latest data quality score
            quality_data = self.metrics_collector.get_metric_data(
                "data_quality_score",
                start_time=time.time() - 300  # Last 5 minutes
            )
            kpi.value = quality_data[-1].value if quality_data else 0.0
            kpi.trend = self._calculate_trend(kpi.value, kpi.target_value)
            
        elif kpi_name == "success_rate":
            # Calculate success rate
            success_data = self.metrics_collector.get_metric_data(
                "success_rate",
                start_time=time.time() - 300  # Last 5 minutes
            )
            kpi.value = success_data[-1].value if success_data else 0.0
            kpi.trend = self._calculate_trend(kpi.value, kpi.target_value)
        
        kpi.last_updated = time.time()
        kpi.confidence = self._calculate_confidence(kpi)
    
    def _calculate_trend(self, current_value: float, target_value: float, 
                        reverse: bool = False) -> str:
        """Calculate trend direction.
        
        Args:
            current_value: Current value
            target_value: Target value
            reverse: If True, higher is worse
            
        Returns:
            Trend direction
        """
        if reverse:
            if current_value > target_value * 1.1:
                return "down"
            elif current_value < target_value * 0.9:
                return "up"
            else:
                return "stable"
        else:
            if current_value > target_value * 1.1:
                return "up"
            elif current_value < target_value * 0.9:
                return "down"
            else:
                return "stable"
    
    def _calculate_confidence(self, kpi: BusinessKPI) -> float:
        """Calculate confidence level for a KPI.
        
        Args:
            kpi: KPI to calculate confidence for
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        # Simple confidence calculation based on data recency and consistency
        age_hours = (time.time() - kpi.last_updated) / 3600
        
        if age_hours < 1:
            return 0.9
        elif age_hours < 6:
            return 0.7
        elif age_hours < 24:
            return 0.5
        else:
            return 0.3
    
    def get_kpis(self) -> Dict[str, BusinessKPI]:
        """Get all KPIs."""
        return self.kpis.copy()
    
    def get_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary.
        
        Returns:
            Dictionary with KPI summary information
        """
        total_kpis = len(self.kpis)
        on_target = sum(1 for kpi in self.kpis.values() 
                       if abs(kpi.value - kpi.target_value) / kpi.target_value < 0.1)
        
        return {
            "total_kpis": total_kpis,
            "on_target": on_target,
            "off_target": total_kpis - on_target,
            "average_confidence": statistics.mean([kpi.confidence for kpi in self.kpis.values()]),
            "kpis": {name: {
                "value": kpi.value,
                "target": kpi.target_value,
                "trend": kpi.trend,
                "confidence": kpi.confidence
            } for name, kpi in self.kpis.items()}
        }
    
    def create_performance_benchmark(self, metric_name: str, baseline_period_hours: int = 24) -> PerformanceBenchmark:
        """Create a performance benchmark.
        
        Args:
            metric_name: Name of the metric to benchmark
            baseline_period_hours: Hours to look back for baseline
            
        Returns:
            Performance benchmark
        """
        # Get baseline data
        baseline_data = self.metrics_collector.get_metric_data(
            metric_name,
            start_time=time.time() - (baseline_period_hours * 3600),
            end_time=time.time() - (baseline_period_hours * 3600 // 2)
        )
        
        # Get current data
        current_data = self.metrics_collector.get_metric_data(
            metric_name,
            start_time=time.time() - 3600  # Last hour
        )
        
        if not baseline_data or not current_data:
            return PerformanceBenchmark(
                name=f"{metric_name}_benchmark",
                metric_name=metric_name,
                baseline_value=0.0,
                current_value=0.0,
                improvement_percentage=0.0,
                status="unknown",
                recommendations=["Insufficient data for benchmarking"]
            )
        
        baseline_value = statistics.mean([dp.value for dp in baseline_data])
        current_value = statistics.mean([dp.value for dp in current_data])
        
        improvement_percentage = ((current_value - baseline_value) / baseline_value) * 100 if baseline_value > 0 else 0.0
        
        # Determine status
        if improvement_percentage > 20:
            status = "excellent"
        elif improvement_percentage > 10:
            status = "good"
        elif improvement_percentage > -10:
            status = "average"
        elif improvement_percentage > -20:
            status = "poor"
        else:
            status = "critical"
        
        # Generate recommendations
        recommendations = []
        if status in ["poor", "critical"]:
            recommendations.append("Investigate performance degradation")
            recommendations.append("Check for resource constraints")
            recommendations.append("Review recent configuration changes")
        elif status == "excellent":
            recommendations.append("Consider scaling up operations")
            recommendations.append("Document successful practices")
        
        return PerformanceBenchmark(
            name=f"{metric_name}_benchmark",
            metric_name=metric_name,
            baseline_value=baseline_value,
            current_value=current_value,
            improvement_percentage=improvement_percentage,
            status=status,
            recommendations=recommendations
        )


class MetricsDashboard:
    """Provides metrics dashboard and reporting functionality."""
    
    def __init__(self, metrics_collector: MetricsCollector, business_analytics: BusinessAnalytics):
        """Initialize metrics dashboard.
        
        Args:
            metrics_collector: Metrics collector instance
            business_analytics: Business analytics instance
        """
        self.metrics_collector = metrics_collector
        self.business_analytics = business_analytics
        self.dashboard_config = {
            "refresh_interval": 30,  # seconds
            "default_time_range": "1h",
            "chart_types": ["line", "bar", "pie", "gauge"],
            "export_formats": ["json", "csv", "pdf"]
        }
    
    def get_dashboard_data(self, time_range: str = "1h") -> Dict[str, Any]:
        """Get dashboard data for a specific time range.
        
        Args:
            time_range: Time range (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary with dashboard data
        """
        start_time = self._parse_time_range(time_range)
        
        return {
            "timestamp": time.time(),
            "time_range": time_range,
            "kpis": self.business_analytics.get_kpi_summary(),
            "metrics": self._get_metrics_summary(start_time),
            "alerts": self._get_active_alerts(),
            "trends": self._get_trend_analysis(start_time)
        }
    
    def _parse_time_range(self, time_range: str) -> float:
        """Parse time range string to start time.
        
        Args:
            time_range: Time range string
            
        Returns:
            Start time as Unix timestamp
        """
        now = time.time()
        
        try:
            if time_range.endswith("m"):
                minutes = int(time_range[:-1])
                return now - (minutes * 60)
            elif time_range.endswith("h"):
                hours = int(time_range[:-1])
                return now - (hours * 3600)
            elif time_range.endswith("d"):
                days = int(time_range[:-1])
                return now - (days * 86400)
            else:
                return now - 3600  # Default to 1 hour
        except (ValueError, IndexError):
            return now - 3600  # Default to 1 hour on error
    
    def _get_metrics_summary(self, start_time: float) -> Dict[str, Any]:
        """Get metrics summary for dashboard.
        
        Args:
            start_time: Start time for data
            
        Returns:
            Dictionary with metrics summary
        """
        summary = {}
        
        for metric_name, definition in self.metrics_collector.get_metric_definitions().items():
            data = self.metrics_collector.get_metric_data(metric_name, start_time=start_time)
            
            if data:
                values = [dp.value for dp in data]
                summary[metric_name] = {
                    "current_value": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                    "unit": definition.unit,
                    "category": definition.category.value
                }
            else:
                summary[metric_name] = {
                    "current_value": 0,
                    "average": 0,
                    "min": 0,
                    "max": 0,
                    "count": 0,
                    "unit": definition.unit,
                    "category": definition.category.value
                }
        
        return summary
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts.
        
        Returns:
            List of active alerts
        """
        alerts = []
        
        # Check KPI alerts
        for kpi_name, kpi in self.business_analytics.get_kpis().items():
            if kpi.trend == "down" and kpi.confidence > 0.7:
                alerts.append({
                    "type": "kpi",
                    "severity": "warning",
                    "message": f"{kpi.name} is trending down",
                    "value": kpi.value,
                    "target": kpi.target_value
                })
        
        # Check metric alerts
        for metric_name, definition in self.metrics_collector.get_metric_definitions().items():
            if definition.alert_thresholds:
                data = self.metrics_collector.get_metric_data(metric_name, start_time=time.time() - 300)
                if data:
                    current_value = data[-1].value
                    for threshold_name, threshold_value in definition.alert_thresholds.items():
                        if current_value > threshold_value:
                            alerts.append({
                                "type": "metric",
                                "severity": "critical",
                                "message": f"{metric_name} exceeds {threshold_name} threshold",
                                "value": current_value,
                                "threshold": threshold_value
                            })
        
        return alerts
    
    def _get_trend_analysis(self, start_time: float) -> Dict[str, Any]:
        """Get trend analysis.
        
        Args:
            start_time: Start time for analysis
            
        Returns:
            Dictionary with trend analysis
        """
        trends = {}
        
        for metric_name in self.metrics_collector.get_metric_definitions().keys():
            data = self.metrics_collector.get_metric_data(metric_name, start_time=start_time)
            
            if len(data) > 1:
                values = [dp.value for dp in data]
                # Simple linear trend calculation
                n = len(values)
                x = list(range(n))
                y = values
                
                # Calculate slope
                x_mean = statistics.mean(x)
                y_mean = statistics.mean(y)
                
                numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
                
                slope = numerator / denominator if denominator != 0 else 0
                
                trends[metric_name] = {
                    "slope": slope,
                    "direction": "up" if slope > 0 else "down" if slope < 0 else "stable",
                    "strength": abs(slope),
                    "correlation": self._calculate_correlation(x, y)
                }
        
        return trends
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient.
        
        Args:
            x: X values
            y: Y values
            
        Returns:
            Correlation coefficient
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        x_var = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_var = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        denominator = (x_var * y_var) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def export_metrics(self, format: str = "json", time_range: str = "24h") -> str:
        """Export metrics data.
        
        Args:
            format: Export format
            time_range: Time range for export
            
        Returns:
            Exported data as string
        """
        start_time = self._parse_time_range(time_range)
        
        if format == "json":
            return self._export_json(start_time)
        elif format == "csv":
            return self._export_csv(start_time)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, start_time: float) -> str:
        """Export data as JSON.
        
        Args:
            start_time: Start time for data
            
        Returns:
            JSON string
        """
        data = {
            "export_timestamp": time.time(),
            "start_time": start_time,
            "end_time": time.time(),
            "metrics": {}
        }
        
        for metric_name in self.metrics_collector.get_metric_definitions().keys():
            metric_data = self.metrics_collector.get_metric_data(metric_name, start_time=start_time)
            data["metrics"][metric_name] = [
                {
                    "timestamp": dp.timestamp,
                    "value": dp.value,
                    "labels": dp.labels,
                    "metadata": dp.metadata
                }
                for dp in metric_data
            ]
        
        return json.dumps(data, indent=2)
    
    def _export_csv(self, start_time: float) -> str:
        """Export data as CSV.
        
        Args:
            start_time: Start time for data
            
        Returns:
            CSV string
        """
        lines = ["metric_name,timestamp,value,labels,metadata"]
        
        for metric_name in self.metrics_collector.get_metric_definitions().keys():
            metric_data = self.metrics_collector.get_metric_data(metric_name, start_time=start_time)
            for dp in metric_data:
                labels_str = json.dumps(dp.labels) if dp.labels else ""
                metadata_str = json.dumps(dp.metadata) if dp.metadata else ""
                lines.append(f"{metric_name},{dp.timestamp},{dp.value},{labels_str},{metadata_str}")
        
        return "\n".join(lines)
