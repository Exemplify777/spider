"""Metrics collection for SPIDER framework."""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
from prometheus_client.core import CollectorRegistry

from ..core.logger import get_logger


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


@dataclass
class MetricData:
    """Metric data container."""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: float
    metric_type: MetricType


class BaseMetricsCollector(ABC):
    """Base class for metrics collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics collector.
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Metric name
            value: Increment value
            labels: Metric labels
        """
        pass
    
    @abstractmethod
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Metric labels
        """
        pass
    
    @abstractmethod
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        pass
    
    @abstractmethod
    def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a summary metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        pass


class PrometheusMetrics(BaseMetricsCollector):
    """Prometheus-based metrics collector."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Prometheus metrics collector.
        
        Args:
            config: Metrics configuration
        """
        super().__init__(config)
        
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.port = config.get('port', 8000)
        self.enabled = config.get('enabled', True)
        
        if self.enabled:
            self._setup_metrics()
            self._start_server()
    
    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics."""
        # Scraping metrics
        self.metrics['scraping_requests_total'] = Counter(
            'spider_scraping_requests_total',
            'Total number of scraping requests',
            ['engine', 'status', 'url_domain'],
            registry=self.registry
        )
        
        self.metrics['scraping_request_duration_seconds'] = Histogram(
            'spider_scraping_request_duration_seconds',
            'Time spent on scraping requests',
            ['engine', 'url_domain'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.metrics['scraping_content_size_bytes'] = Histogram(
            'spider_scraping_content_size_bytes',
            'Size of scraped content in bytes',
            ['engine', 'content_type'],
            buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
            registry=self.registry
        )
        
        # Proxy metrics
        self.metrics['proxy_requests_total'] = Counter(
            'spider_proxy_requests_total',
            'Total number of proxy requests',
            ['proxy_provider', 'status'],
            registry=self.registry
        )
        
        self.metrics['proxy_response_time_seconds'] = Histogram(
            'spider_proxy_response_time_seconds',
            'Proxy response time in seconds',
            ['proxy_provider'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        self.metrics['proxy_health_score'] = Gauge(
            'spider_proxy_health_score',
            'Proxy health score (0-1)',
            ['proxy_provider', 'proxy_host'],
            registry=self.registry
        )
        
        # CAPTCHA metrics
        self.metrics['captcha_attempts_total'] = Counter(
            'spider_captcha_attempts_total',
            'Total number of CAPTCHA solving attempts',
            ['captcha_provider', 'captcha_type', 'status'],
            registry=self.registry
        )
        
        self.metrics['captcha_solving_duration_seconds'] = Histogram(
            'spider_captcha_solving_duration_seconds',
            'Time spent solving CAPTCHAs',
            ['captcha_provider', 'captcha_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=self.registry
        )
        
        # Data processing metrics
        self.metrics['data_extraction_operations_total'] = Counter(
            'spider_data_extraction_operations_total',
            'Total number of data extraction operations',
            ['extractor_type', 'status'],
            registry=self.registry
        )
        
        self.metrics['data_transformation_operations_total'] = Counter(
            'spider_data_transformation_operations_total',
            'Total number of data transformation operations',
            ['transformer_type', 'status'],
            registry=self.registry
        )
        
        self.metrics['data_validation_operations_total'] = Counter(
            'spider_data_validation_operations_total',
            'Total number of data validation operations',
            ['validator_type', 'status'],
            registry=self.registry
        )
        
        # Storage metrics
        self.metrics['storage_operations_total'] = Counter(
            'spider_storage_operations_total',
            'Total number of storage operations',
            ['storage_type', 'operation', 'status'],
            registry=self.registry
        )
        
        self.metrics['storage_operation_duration_seconds'] = Histogram(
            'spider_storage_operation_duration_seconds',
            'Time spent on storage operations',
            ['storage_type', 'operation'],
            buckets=[0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # System metrics
        self.metrics['active_connections'] = Gauge(
            'spider_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        self.metrics['memory_usage_bytes'] = Gauge(
            'spider_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.metrics['cpu_usage_percent'] = Gauge(
            'spider_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Error metrics
        self.metrics['errors_total'] = Counter(
            'spider_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        self.logger.info("Prometheus metrics initialized")
    
    def _start_server(self) -> None:
        """Start Prometheus metrics server."""
        try:
            start_http_server(self.port, registry=self.registry)
            self.logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus metrics server: {e}")
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        if not self.enabled or name not in self.metrics:
            return
        
        labels = labels or {}
        self.metrics[name].labels(**labels).inc(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        if not self.enabled or name not in self.metrics:
            return
        
        labels = labels or {}
        self.metrics[name].labels(**labels).set(value)
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a histogram metric."""
        if not self.enabled or name not in self.metrics:
            return
        
        labels = labels or {}
        self.metrics[name].labels(**labels).observe(value)
    
    def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a summary metric."""
        if not self.enabled or name not in self.metrics:
            return
        
        labels = labels or {}
        self.metrics[name].labels(**labels).observe(value)
    
    def record_scraping_request(self, engine: str, status: str, url_domain: str, duration: float, content_size: int) -> None:
        """Record scraping request metrics."""
        labels = {
            'engine': engine,
            'status': status,
            'url_domain': url_domain
        }
        
        self.increment_counter('scraping_requests_total', labels=labels)
        self.observe_histogram('scraping_request_duration_seconds', duration, labels={'engine': engine, 'url_domain': url_domain})
        self.observe_histogram('scraping_content_size_bytes', content_size, labels={'engine': engine, 'content_type': 'unknown'})
    
    def record_proxy_request(self, provider: str, status: str, response_time: float, health_score: float, proxy_host: str) -> None:
        """Record proxy request metrics."""
        self.increment_counter('proxy_requests_total', labels={'proxy_provider': provider, 'status': status})
        self.observe_histogram('proxy_response_time_seconds', response_time, labels={'proxy_provider': provider})
        self.set_gauge('proxy_health_score', health_score, labels={'proxy_provider': provider, 'proxy_host': proxy_host})
    
    def record_captcha_attempt(self, provider: str, captcha_type: str, status: str, duration: float) -> None:
        """Record CAPTCHA solving attempt metrics."""
        self.increment_counter('captcha_attempts_total', labels={
            'captcha_provider': provider,
            'captcha_type': captcha_type,
            'status': status
        })
        self.observe_histogram('captcha_solving_duration_seconds', duration, labels={
            'captcha_provider': provider,
            'captcha_type': captcha_type
        })
    
    def record_data_operation(self, operation_type: str, component_type: str, status: str) -> None:
        """Record data processing operation metrics."""
        if operation_type == 'extraction':
            self.increment_counter('data_extraction_operations_total', labels={
                'extractor_type': component_type,
                'status': status
            })
        elif operation_type == 'transformation':
            self.increment_counter('data_transformation_operations_total', labels={
                'transformer_type': component_type,
                'status': status
            })
        elif operation_type == 'validation':
            self.increment_counter('data_validation_operations_total', labels={
                'validator_type': component_type,
                'status': status
            })
    
    def record_storage_operation(self, storage_type: str, operation: str, status: str, duration: float) -> None:
        """Record storage operation metrics."""
        self.increment_counter('storage_operations_total', labels={
            'storage_type': storage_type,
            'operation': operation,
            'status': status
        })
        self.observe_histogram('storage_operation_duration_seconds', duration, labels={
            'storage_type': storage_type,
            'operation': operation
        })
    
    def record_error(self, error_type: str, component: str) -> None:
        """Record error metrics."""
        self.increment_counter('errors_total', labels={
            'error_type': error_type,
            'component': component
        })
    
    def update_system_metrics(self) -> None:
        """Update system metrics."""
        import psutil
        
        # Memory usage
        memory_info = psutil.virtual_memory()
        self.set_gauge('memory_usage_bytes', memory_info.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.set_gauge('cpu_usage_percent', cpu_percent)
        
        # Active connections (simplified)
        try:
            connections = len(psutil.net_connections())
            self.set_gauge('active_connections', connections)
        except Exception:
            pass


class MetricsCollector:
    """Main metrics collector class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics collector.
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.collectors: List[BaseMetricsCollector] = []
        
        # Initialize Prometheus collector
        if config.get('prometheus', {}).get('enabled', True):
            prometheus_config = config.get('prometheus', {})
            prometheus_collector = PrometheusMetrics(prometheus_config)
            self.collectors.append(prometheus_collector)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric across all collectors."""
        for collector in self.collectors:
            collector.increment_counter(name, value, labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric across all collectors."""
        for collector in self.collectors:
            collector.set_gauge(name, value, labels)
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a histogram metric across all collectors."""
        for collector in self.collectors:
            collector.observe_histogram(name, value, labels)
    
    def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a summary metric across all collectors."""
        for collector in self.collectors:
            collector.observe_summary(name, value, labels)
    
    def record_scraping_request(self, engine: str, status: str, url_domain: str, duration: float, content_size: int) -> None:
        """Record scraping request metrics."""
        for collector in self.collectors:
            if hasattr(collector, 'record_scraping_request'):
                collector.record_scraping_request(engine, status, url_domain, duration, content_size)
    
    def record_proxy_request(self, provider: str, status: str, response_time: float, health_score: float, proxy_host: str) -> None:
        """Record proxy request metrics."""
        for collector in self.collectors:
            if hasattr(collector, 'record_proxy_request'):
                collector.record_proxy_request(provider, status, response_time, health_score, proxy_host)
    
    def record_captcha_attempt(self, provider: str, captcha_type: str, status: str, duration: float) -> None:
        """Record CAPTCHA solving attempt metrics."""
        for collector in self.collectors:
            if hasattr(collector, 'record_captcha_attempt'):
                collector.record_captcha_attempt(provider, captcha_type, status, duration)
    
    def record_data_operation(self, operation_type: str, component_type: str, status: str) -> None:
        """Record data processing operation metrics."""
        for collector in self.collectors:
            if hasattr(collector, 'record_data_operation'):
                collector.record_data_operation(operation_type, component_type, status)
    
    def record_storage_operation(self, storage_type: str, operation: str, status: str, duration: float) -> None:
        """Record storage operation metrics."""
        for collector in self.collectors:
            if hasattr(collector, 'record_storage_operation'):
                collector.record_storage_operation(storage_type, operation, status, duration)
    
    def record_error(self, error_type: str, component: str) -> None:
        """Record error metrics."""
        for collector in self.collectors:
            collector.record_error(error_type, component)
    
    def update_system_metrics(self) -> None:
        """Update system metrics across all collectors."""
        for collector in self.collectors:
            if hasattr(collector, 'update_system_metrics'):
                collector.update_system_metrics()
