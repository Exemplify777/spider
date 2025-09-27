"""
Advanced Performance Analytics and Reporting

This module provides comprehensive performance analytics and reporting capabilities
for the SPIDER Framework in production environments.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path
import statistics
import numpy as np
import pandas as pd
from collections import defaultdict, deque

import aiohttp
import aiofiles
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeRange(Enum):
    """Time range for analytics"""
    LAST_HOUR = "1h"
    LAST_DAY = "24h"
    LAST_WEEK = "7d"
    LAST_MONTH = "30d"
    CUSTOM = "custom"


@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class PerformanceReport:
    """Performance report structure"""
    report_id: str
    title: str
    generated_at: datetime
    time_range: TimeRange
    summary: Dict[str, Any]
    metrics: Dict[str, List[MetricData]]
    insights: List[str]
    recommendations: List[str]
    charts: List[Dict[str, Any]]


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    prometheus_url: str = "http://prometheus:9090"
    data_retention_days: int = 30
    aggregation_interval: int = 300  # seconds
    report_generation_interval: int = 3600  # seconds
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage": 80.0,
        "memory_usage": 85.0,
        "disk_usage": 90.0,
        "response_time": 2000.0,
        "error_rate": 5.0
    })
    enabled_metrics: List[str] = field(default_factory=lambda: [
        "cpu_usage", "memory_usage", "disk_usage", "network_io",
        "response_time", "error_rate", "throughput", "queue_length"
    ])


class PerformanceAnalytics:
    """
    Advanced performance analytics and reporting system
    """
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.metrics_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.reports: Dict[str, PerformanceReport] = {}
        self.running = False
        self.analytics_tasks: List[asyncio.Task] = []
        
        # Initialize metrics storage
        self._initialize_metrics_storage()
    
    def _initialize_metrics_storage(self):
        """Initialize metrics storage"""
        # Create metrics storage directory
        self.metrics_dir = Path("/app/data/analytics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metric collections
        for metric in self.config.enabled_metrics:
            self.metrics_data[metric] = deque(maxlen=10000)
    
    async def start_analytics(self):
        """Start the performance analytics system"""
        if self.running:
            logger.warning("Analytics is already running")
            return
        
        self.running = True
        logger.info("Starting performance analytics system")
        
        # Start analytics tasks
        self.analytics_tasks = [
            asyncio.create_task(self._collect_metrics()),
            asyncio.create_task(self._aggregate_metrics()),
            asyncio.create_task(self._generate_reports()),
            asyncio.create_task(self._cleanup_old_data()),
        ]
        
        try:
            await asyncio.gather(*self.analytics_tasks)
        except Exception as e:
            logger.error(f"Error in analytics tasks: {e}")
        finally:
            self.running = False
    
    async def stop_analytics(self):
        """Stop the performance analytics system"""
        if not self.running:
            return
        
        logger.info("Stopping performance analytics system")
        self.running = False
        
        # Cancel all analytics tasks
        for task in self.analytics_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.analytics_tasks, return_exceptions=True)
    
    async def _collect_metrics(self):
        """Collect performance metrics"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Collect system metrics
                await self._collect_system_metrics(current_time)
                
                # Collect application metrics
                await self._collect_application_metrics(current_time)
                
                # Collect database metrics
                await self._collect_database_metrics(current_time)
                
                # Collect cache metrics
                await self._collect_cache_metrics(current_time)
                
                # Collect network metrics
                await self._collect_network_metrics(current_time)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            await asyncio.sleep(self.config.aggregation_interval)
    
    async def _collect_system_metrics(self, timestamp: datetime):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric("cpu_usage", cpu_percent, timestamp)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self._add_metric("memory_usage", memory.percent, timestamp)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric("disk_usage", disk_percent, timestamp)
            
            # Load average
            load_avg = psutil.getloadavg()[0]
            self._add_metric("load_average", load_avg, timestamp)
            
            # Process count
            process_count = len(psutil.pids())
            self._add_metric("process_count", process_count, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_application_metrics(self, timestamp: datetime):
        """Collect application performance metrics"""
        try:
            # Get metrics from Prometheus
            async with aiohttp.ClientSession() as session:
                # Response time
                response_time_query = "histogram_quantile(0.95, rate(spider_http_request_duration_seconds_bucket[5m]))"
                response_time = await self._query_prometheus(session, response_time_query)
                if response_time is not None:
                    self._add_metric("response_time", response_time * 1000, timestamp)  # Convert to ms
                
                # Error rate
                error_rate_query = "rate(spider_http_requests_total{status=~'5..'}[5m]) / rate(spider_http_requests_total[5m]) * 100"
                error_rate = await self._query_prometheus(session, error_rate_query)
                if error_rate is not None:
                    self._add_metric("error_rate", error_rate, timestamp)
                
                # Throughput
                throughput_query = "rate(spider_http_requests_total[5m])"
                throughput = await self._query_prometheus(session, throughput_query)
                if throughput is not None:
                    self._add_metric("throughput", throughput, timestamp)
                
                # Queue length
                queue_length_query = "spider_task_queue_length"
                queue_length = await self._query_prometheus(session, queue_length_query)
                if queue_length is not None:
                    self._add_metric("queue_length", queue_length, timestamp)
                
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    async def _collect_database_metrics(self, timestamp: datetime):
        """Collect database performance metrics"""
        try:
            # Database connection count
            # Implementation for database metrics collection
            pass
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
    
    async def _collect_cache_metrics(self, timestamp: datetime):
        """Collect cache performance metrics"""
        try:
            # Cache hit rate
            # Implementation for cache metrics collection
            pass
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
    
    async def _collect_network_metrics(self, timestamp: datetime):
        """Collect network performance metrics"""
        try:
            # Network I/O
            net_io = psutil.net_io_counters()
            self._add_metric("network_bytes_sent", net_io.bytes_sent, timestamp)
            self._add_metric("network_bytes_recv", net_io.bytes_recv, timestamp)
            
            # Network connections
            connections = len(psutil.net_connections())
            self._add_metric("network_connections", connections, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
    
    async def _query_prometheus(self, session: aiohttp.ClientSession, query: str) -> Optional[float]:
        """Query Prometheus for metric value"""
        try:
            async with session.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "success" and data["data"]["result"]:
                        return float(data["data"]["result"][0]["value"][1])
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
        
        return None
    
    def _add_metric(self, name: str, value: float, timestamp: datetime, labels: Dict[str, str] = None):
        """Add a metric data point"""
        metric_data = MetricData(
            name=name,
            value=value,
            timestamp=timestamp,
            labels=labels or {}
        )
        
        self.metrics_data[name].append(metric_data)
    
    async def _aggregate_metrics(self):
        """Aggregate metrics data"""
        while self.running:
            try:
                # Calculate aggregated metrics
                await self._calculate_aggregated_metrics()
                
                # Detect anomalies
                await self._detect_anomalies()
                
                # Update trend analysis
                await self._update_trend_analysis()
                
            except Exception as e:
                logger.error(f"Error aggregating metrics: {e}")
            
            await asyncio.sleep(self.config.aggregation_interval)
    
    async def _calculate_aggregated_metrics(self):
        """Calculate aggregated metrics"""
        for metric_name, data in self.metrics_data.items():
            if not data:
                continue
            
            # Calculate statistics
            values = [d.value for d in data]
            
            if values:
                # Calculate basic statistics
                mean_val = statistics.mean(values)
                median_val = statistics.median(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                min_val = min(values)
                max_val = max(values)
                
                # Store aggregated metrics
                current_time = datetime.now()
                self._add_metric(f"{metric_name}_mean", mean_val, current_time)
                self._add_metric(f"{metric_name}_median", median_val, current_time)
                self._add_metric(f"{metric_name}_std", std_val, current_time)
                self._add_metric(f"{metric_name}_min", min_val, current_time)
                self._add_metric(f"{metric_name}_max", max_val, current_time)
    
    async def _detect_anomalies(self):
        """Detect performance anomalies"""
        for metric_name, data in self.metrics_data.items():
            if len(data) < 10:  # Need enough data points
                continue
            
            values = [d.value for d in data]
            
            # Simple anomaly detection using z-score
            if len(values) > 1:
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values)
                
                if std_val > 0:
                    z_scores = [(v - mean_val) / std_val for v in values]
                    
                    # Flag values with z-score > 2 as anomalies
                    for i, z_score in enumerate(z_scores):
                        if abs(z_score) > 2:
                            logger.warning(f"Anomaly detected in {metric_name}: value={values[i]}, z-score={z_score:.2f}")
    
    async def _update_trend_analysis(self):
        """Update trend analysis"""
        for metric_name, data in self.metrics_data.items():
            if len(data) < 20:  # Need enough data points
                continue
            
            values = [d.value for d in data]
            timestamps = [d.timestamp for d in data]
            
            # Simple trend analysis
            if len(values) > 1:
                # Calculate trend using linear regression
                x = np.arange(len(values))
                y = np.array(values)
                
                # Simple linear regression
                slope = np.polyfit(x, y, 1)[0]
                
                # Store trend metric
                current_time = datetime.now()
                self._add_metric(f"{metric_name}_trend", slope, current_time)
    
    async def _generate_reports(self):
        """Generate performance reports"""
        while self.running:
            try:
                # Generate hourly reports
                await self._generate_hourly_report()
                
                # Generate daily reports
                if datetime.now().hour == 0:  # At midnight
                    await self._generate_daily_report()
                
                # Generate weekly reports
                if datetime.now().weekday() == 0 and datetime.now().hour == 0:  # Monday at midnight
                    await self._generate_weekly_report()
                
            except Exception as e:
                logger.error(f"Error generating reports: {e}")
            
            await asyncio.sleep(self.config.report_generation_interval)
    
    async def _generate_hourly_report(self):
        """Generate hourly performance report"""
        report_id = f"hourly_{datetime.now().strftime('%Y%m%d_%H')}"
        
        # Get metrics for the last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        metrics = await self._get_metrics_for_time_range(start_time, end_time)
        
        # Generate insights
        insights = await self._generate_insights(metrics)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(metrics)
        
        # Create report
        report = PerformanceReport(
            report_id=report_id,
            title="Hourly Performance Report",
            generated_at=datetime.now(),
            time_range=TimeRange.LAST_HOUR,
            summary=await self._generate_summary(metrics),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            charts=await self._generate_charts(metrics)
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated hourly report: {report_id}")
    
    async def _generate_daily_report(self):
        """Generate daily performance report"""
        report_id = f"daily_{datetime.now().strftime('%Y%m%d')}"
        
        # Get metrics for the last day
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        metrics = await self._get_metrics_for_time_range(start_time, end_time)
        
        # Generate insights
        insights = await self._generate_insights(metrics)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(metrics)
        
        # Create report
        report = PerformanceReport(
            report_id=report_id,
            title="Daily Performance Report",
            generated_at=datetime.now(),
            time_range=TimeRange.LAST_DAY,
            summary=await self._generate_summary(metrics),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            charts=await self._generate_charts(metrics)
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated daily report: {report_id}")
    
    async def _generate_weekly_report(self):
        """Generate weekly performance report"""
        report_id = f"weekly_{datetime.now().strftime('%Y%m%d')}"
        
        # Get metrics for the last week
        end_time = datetime.now()
        start_time = end_time - timedelta(weeks=1)
        
        metrics = await self._get_metrics_for_time_range(start_time, end_time)
        
        # Generate insights
        insights = await self._generate_insights(metrics)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(metrics)
        
        # Create report
        report = PerformanceReport(
            report_id=report_id,
            title="Weekly Performance Report",
            generated_at=datetime.now(),
            time_range=TimeRange.LAST_WEEK,
            summary=await self._generate_summary(metrics),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            charts=await self._generate_charts(metrics)
        )
        
        self.reports[report_id] = report
        logger.info(f"Generated weekly report: {report_id}")
    
    async def _get_metrics_for_time_range(self, start_time: datetime, end_time: datetime) -> Dict[str, List[MetricData]]:
        """Get metrics for a specific time range"""
        filtered_metrics = {}
        
        for metric_name, data in self.metrics_data.items():
            filtered_data = [
                d for d in data
                if start_time <= d.timestamp <= end_time
            ]
            if filtered_data:
                filtered_metrics[metric_name] = filtered_data
        
        return filtered_metrics
    
    async def _generate_summary(self, metrics: Dict[str, List[MetricData]]) -> Dict[str, Any]:
        """Generate metrics summary"""
        summary = {}
        
        for metric_name, data in metrics.items():
            if not data:
                continue
            
            values = [d.value for d in data]
            
            summary[metric_name] = {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        return summary
    
    async def _generate_insights(self, metrics: Dict[str, List[MetricData]]) -> List[str]:
        """Generate performance insights"""
        insights = []
        
        # Check for high CPU usage
        if "cpu_usage" in metrics:
            cpu_data = metrics["cpu_usage"]
            if cpu_data:
                avg_cpu = statistics.mean([d.value for d in cpu_data])
                if avg_cpu > 80:
                    insights.append(f"High CPU usage detected: {avg_cpu:.1f}% average")
        
        # Check for high memory usage
        if "memory_usage" in metrics:
            memory_data = metrics["memory_usage"]
            if memory_data:
                avg_memory = statistics.mean([d.value for d in memory_data])
                if avg_memory > 85:
                    insights.append(f"High memory usage detected: {avg_memory:.1f}% average")
        
        # Check for high response time
        if "response_time" in metrics:
            response_data = metrics["response_time"]
            if response_data:
                avg_response = statistics.mean([d.value for d in response_data])
                if avg_response > 2000:
                    insights.append(f"High response time detected: {avg_response:.1f}ms average")
        
        # Check for high error rate
        if "error_rate" in metrics:
            error_data = metrics["error_rate"]
            if error_data:
                avg_error = statistics.mean([d.value for d in error_data])
                if avg_error > 5:
                    insights.append(f"High error rate detected: {avg_error:.1f}% average")
        
        return insights
    
    async def _generate_recommendations(self, metrics: Dict[str, List[MetricData]]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # CPU recommendations
        if "cpu_usage" in metrics:
            cpu_data = metrics["cpu_usage"]
            if cpu_data:
                avg_cpu = statistics.mean([d.value for d in cpu_data])
                if avg_cpu > 80:
                    recommendations.append("Consider scaling up CPU resources or optimizing CPU-intensive operations")
        
        # Memory recommendations
        if "memory_usage" in metrics:
            memory_data = metrics["memory_usage"]
            if memory_data:
                avg_memory = statistics.mean([d.value for d in memory_data])
                if avg_memory > 85:
                    recommendations.append("Consider scaling up memory resources or optimizing memory usage")
        
        # Response time recommendations
        if "response_time" in metrics:
            response_data = metrics["response_time"]
            if response_data:
                avg_response = statistics.mean([d.value for d in response_data])
                if avg_response > 2000:
                    recommendations.append("Consider optimizing database queries, adding caching, or scaling resources")
        
        # Error rate recommendations
        if "error_rate" in metrics:
            error_data = metrics["error_rate"]
            if error_data:
                avg_error = statistics.mean([d.value for d in error_data])
                if avg_error > 5:
                    recommendations.append("Investigate and fix the root cause of errors")
        
        return recommendations
    
    async def _generate_charts(self, metrics: Dict[str, List[MetricData]]) -> List[Dict[str, Any]]:
        """Generate chart data for reports"""
        charts = []
        
        for metric_name, data in metrics.items():
            if not data:
                continue
            
            # Create time series chart
            chart_data = {
                "type": "line",
                "title": f"{metric_name.title()} Over Time",
                "x_axis": "Time",
                "y_axis": metric_name,
                "data": [
                    {
                        "x": d.timestamp.isoformat(),
                        "y": d.value
                    }
                    for d in data
                ]
            }
            
            charts.append(chart_data)
        
        return charts
    
    async def _cleanup_old_data(self):
        """Clean up old metrics data"""
        while self.running:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.config.data_retention_days)
                
                # Clean up old metrics data
                for metric_name, data in self.metrics_data.items():
                    # Remove old data points
                    while data and data[0].timestamp < cutoff_date:
                        data.popleft()
                
                # Clean up old reports
                reports_to_remove = [
                    report_id for report_id, report in self.reports.items()
                    if report.generated_at < cutoff_date
                ]
                
                for report_id in reports_to_remove:
                    del self.reports[report_id]
                
                if reports_to_remove:
                    logger.info(f"Cleaned up {len(reports_to_remove)} old reports")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
            
            await asyncio.sleep(3600)  # Clean up every hour
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_metrics": len(self.metrics_data),
            "total_data_points": sum(len(data) for data in self.metrics_data.values()),
            "total_reports": len(self.reports),
            "analytics_running": self.running,
            "last_collection": datetime.now().isoformat()
        }
    
    async def get_performance_report(self, report_id: str) -> Optional[PerformanceReport]:
        """Get a specific performance report"""
        return self.reports.get(report_id)
    
    async def get_metrics_for_metric(self, metric_name: str, time_range: TimeRange = TimeRange.LAST_HOUR) -> List[MetricData]:
        """Get metrics for a specific metric name"""
        if metric_name not in self.metrics_data:
            return []
        
        data = self.metrics_data[metric_name]
        
        if time_range == TimeRange.LAST_HOUR:
            cutoff = datetime.now() - timedelta(hours=1)
        elif time_range == TimeRange.LAST_DAY:
            cutoff = datetime.now() - timedelta(days=1)
        elif time_range == TimeRange.LAST_WEEK:
            cutoff = datetime.now() - timedelta(weeks=1)
        elif time_range == TimeRange.LAST_MONTH:
            cutoff = datetime.now() - timedelta(days=30)
        else:
            return list(data)
        
        return [d for d in data if d.timestamp >= cutoff]
    
    async def get_available_reports(self) -> List[str]:
        """Get list of available reports"""
        return list(self.reports.keys())
    
    async def export_report(self, report_id: str, format: str = "json") -> str:
        """Export a report in specified format"""
        if report_id not in self.reports:
            raise ValueError(f"Report {report_id} not found")
        
        report = self.reports[report_id]
        
        if format == "json":
            return json.dumps(report, default=str, indent=2)
        elif format == "yaml":
            return yaml.dump(report, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
