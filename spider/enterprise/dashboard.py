"""Enterprise monitoring dashboards for SPIDER framework."""

import asyncio
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import statistics

from ..core.exceptions import SpiderError, MonitoringError
from ..core.logger import get_logger


class DashboardType(Enum):
    """Dashboard types."""
    OVERVIEW = "overview"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TENANT = "tenant"
    CUSTOM = "custom"


class WidgetType(Enum):
    """Widget types."""
    METRIC = "metric"
    CHART = "chart"
    TABLE = "table"
    ALERT = "alert"
    LOG = "log"
    MAP = "map"


class ChartType(Enum):
    """Chart types."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    HEATMAP = "heatmap"


@dataclass
class WidgetConfig:
    """Widget configuration."""
    widget_id: str
    widget_type: WidgetType
    title: str
    position: Tuple[int, int]  # (x, y)
    size: Tuple[int, int]  # (width, height)
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 30  # seconds
    enabled: bool = True


@dataclass
class Dashboard:
    """Dashboard definition."""
    dashboard_id: str
    name: str
    dashboard_type: DashboardType
    description: str = ""
    widgets: List[WidgetConfig] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    is_public: bool = False
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class MetricData:
    """Metric data point."""
    timestamp: float
    value: Union[int, float, str]
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartData:
    """Chart data."""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Alert rule definition."""
    rule_id: str
    name: str
    metric: str
    condition: str  # e.g., "value > 100"
    threshold: Union[int, float]
    severity: str = "warning"
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)


class MetricCollector:
    """Collects and stores metrics."""
    
    def __init__(self):
        """Initialize metric collector."""
        self.logger = get_logger(self.__class__.__name__)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.lock = threading.RLock()
    
    def record_metric(
        self,
        metric_name: str,
        value: Union[int, float, str],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric.
        
        Args:
            metric_name: Metric name
            value: Metric value
            labels: Optional labels
            metadata: Optional metadata
        """
        with self.lock:
            metric_data = MetricData(
                timestamp=time.time(),
                value=value,
                labels=labels or {},
                metadata=metadata or {}
            )
            
            self.metrics[metric_name].append(metric_data)
    
    def get_metric_data(
        self,
        metric_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[MetricData]:
        """Get metric data.
        
        Args:
            metric_name: Metric name
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Optional limit on number of points
            
        Returns:
            List of metric data points
        """
        with self.lock:
            if metric_name not in self.metrics:
                return []
            
            data = list(self.metrics[metric_name])
            
            # Apply time filters
            if start_time:
                data = [d for d in data if d.timestamp >= start_time]
            
            if end_time:
                data = [d for d in data if d.timestamp <= end_time]
            
            # Apply limit
            if limit:
                data = data[-limit:]
            
            return data
    
    def get_metric_summary(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get metric summary statistics.
        
        Args:
            metric_name: Metric name
            hours: Number of hours to analyze
            
        Returns:
            Metric summary
        """
        with self.lock:
            if metric_name not in self.metrics:
                return {}
            
            cutoff_time = time.time() - (hours * 3600)
            data = [
                d for d in self.metrics[metric_name]
                if d.timestamp >= cutoff_time
            ]
            
            if not data:
                return {}
            
            # Extract numeric values
            numeric_values = [d.value for d in data if isinstance(d.value, (int, float))]
            
            if not numeric_values:
                return {
                    "count": len(data),
                    "latest_value": data[-1].value if data else None,
                    "latest_timestamp": data[-1].timestamp if data else None
                }
            
            return {
                "count": len(data),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": statistics.mean(numeric_values),
                "median": statistics.median(numeric_values),
                "latest_value": data[-1].value,
                "latest_timestamp": data[-1].timestamp,
                "trend": self._calculate_trend(numeric_values)
            }
    
    def _calculate_trend(self, values: List[Union[int, float]]) -> str:
        """Calculate trend direction.
        
        Args:
            values: List of numeric values
            
        Returns:
            Trend direction (up, down, stable)
        """
        if len(values) < 2:
            return "stable"
        
        # Compare first half with second half
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])
        
        if second_half_avg > first_half_avg * 1.05:
            return "up"
        elif second_half_avg < first_half_avg * 0.95:
            return "down"
        else:
            return "stable"


class ChartGenerator:
    """Generates chart data."""
    
    def __init__(self, metric_collector: MetricCollector):
        """Initialize chart generator.
        
        Args:
            metric_collector: Metric collector instance
        """
        self.metric_collector = metric_collector
        self.logger = get_logger(self.__class__.__name__)
    
    def generate_line_chart(
        self,
        metric_name: str,
        hours: int = 24,
        group_by: str = "hour"
    ) -> ChartData:
        """Generate line chart data.
        
        Args:
            metric_name: Metric name
            hours: Number of hours to analyze
            group_by: Grouping interval (hour, minute, day)
            
        Returns:
            Chart data
        """
        cutoff_time = time.time() - (hours * 3600)
        data = self.metric_collector.get_metric_data(metric_name, start_time=cutoff_time)
        
        if not data:
            return ChartData(labels=[], datasets=[])
        
        # Group data by time interval
        grouped_data = self._group_data_by_interval(data, group_by)
        
        labels = list(grouped_data.keys())
        values = list(grouped_data.values())
        
        return ChartData(
            labels=labels,
            datasets=[{
                "label": metric_name,
                "data": values,
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "fill": True
            }]
        )
    
    def generate_bar_chart(
        self,
        metric_name: str,
        hours: int = 24,
        group_by: str = "hour"
    ) -> ChartData:
        """Generate bar chart data.
        
        Args:
            metric_name: Metric name
            hours: Number of hours to analyze
            group_by: Grouping interval
            
        Returns:
            Chart data
        """
        cutoff_time = time.time() - (hours * 3600)
        data = self.metric_collector.get_metric_data(metric_name, start_time=cutoff_time)
        
        if not data:
            return ChartData(labels=[], datasets=[])
        
        grouped_data = self._group_data_by_interval(data, group_by)
        
        labels = list(grouped_data.keys())
        values = list(grouped_data.values())
        
        return ChartData(
            labels=labels,
            datasets=[{
                "label": metric_name,
                "data": values,
                "backgroundColor": "#10b981",
                "borderColor": "#059669",
                "borderWidth": 1
            }]
        )
    
    def generate_pie_chart(
        self,
        metric_name: str,
        label_field: str = "labels",
        hours: int = 24
    ) -> ChartData:
        """Generate pie chart data.
        
        Args:
            metric_name: Metric name
            label_field: Field to use for labels
            hours: Number of hours to analyze
            
        Returns:
            Chart data
        """
        cutoff_time = time.time() - (hours * 3600)
        data = self.metric_collector.get_metric_data(metric_name, start_time=cutoff_time)
        
        if not data:
            return ChartData(labels=[], datasets=[])
        
        # Group by label field
        grouped_data = defaultdict(float)
        for point in data:
            if label_field in point.labels:
                label = point.labels[label_field]
                if isinstance(point.value, (int, float)):
                    grouped_data[label] += point.value
                else:
                    grouped_data[label] += 1
        
        labels = list(grouped_data.keys())
        values = list(grouped_data.values())
        
        # Generate colors
        colors = self._generate_colors(len(labels))
        
        return ChartData(
            labels=labels,
            datasets=[{
                "data": values,
                "backgroundColor": colors,
                "borderWidth": 1
            }]
        )
    
    def generate_gauge_chart(
        self,
        metric_name: str,
        max_value: Optional[float] = None,
        hours: int = 1
    ) -> ChartData:
        """Generate gauge chart data.
        
        Args:
            metric_name: Metric name
            max_value: Maximum value for gauge
            hours: Number of hours to analyze
            
        Returns:
            Chart data
        """
        cutoff_time = time.time() - (hours * 3600)
        data = self.metric_collector.get_metric_data(metric_name, start_time=cutoff_time)
        
        if not data:
            return ChartData(labels=[], datasets=[])
        
        # Get latest value
        latest_value = data[-1].value if data else 0
        
        if not isinstance(latest_value, (int, float)):
            latest_value = 0
        
        # Calculate percentage
        if max_value is None:
            max_value = max(d.value for d in data if isinstance(d.value, (int, float))) if data else 100
        
        percentage = (latest_value / max_value) * 100 if max_value > 0 else 0
        
        return ChartData(
            labels=["Current", "Max"],
            datasets=[{
                "data": [latest_value, max_value],
                "backgroundColor": ["#3b82f6", "#e5e7eb"],
                "borderWidth": 0
            }],
            metadata={
                "percentage": percentage,
                "current_value": latest_value,
                "max_value": max_value
            }
        )
    
    def _group_data_by_interval(
        self,
        data: List[MetricData],
        group_by: str
    ) -> Dict[str, float]:
        """Group data by time interval.
        
        Args:
            data: Metric data points
            group_by: Grouping interval
            
        Returns:
            Grouped data
        """
        grouped = defaultdict(list)
        
        for point in data:
            dt = datetime.fromtimestamp(point.timestamp)
            
            if group_by == "minute":
                key = dt.strftime("%Y-%m-%d %H:%M")
            elif group_by == "hour":
                key = dt.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = dt.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m-%d %H:%M")
            
            if isinstance(point.value, (int, float)):
                grouped[key].append(point.value)
            else:
                grouped[key].append(1)
        
        # Calculate averages
        result = {}
        for key, values in grouped.items():
            result[key] = statistics.mean(values)
        
        return result
    
    def _generate_colors(self, count: int) -> List[str]:
        """Generate colors for charts.
        
        Args:
            count: Number of colors needed
            
        Returns:
            List of color codes
        """
        colors = [
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
            "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#6366f1"
        ]
        
        if count <= len(colors):
            return colors[:count]
        
        # Generate additional colors
        result = colors[:]
        for i in range(len(colors), count):
            hue = (i * 137.5) % 360  # Golden angle
            result.append(f"hsl({hue}, 70%, 50%)")
        
        return result


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.lock = threading.RLock()
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add alert rule.
        
        Args:
            rule: Alert rule
        """
        with self.lock:
            self.alert_rules[rule.rule_id] = rule
            self.logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove alert rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                self.logger.info(f"Removed alert rule: {rule_id}")
                return True
            return False
    
    def check_alerts(self, metric_name: str, value: Union[int, float]) -> List[Dict[str, Any]]:
        """Check alerts for metric value.
        
        Args:
            metric_name: Metric name
            value: Current value
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        with self.lock:
            for rule in self.alert_rules.values():
                if not rule.enabled or rule.metric != metric_name:
                    continue
                
                # Simple condition evaluation
                if self._evaluate_condition(value, rule.condition, rule.threshold):
                    alert = {
                        "alert_id": str(uuid.uuid4()),
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "metric": metric_name,
                        "value": value,
                        "threshold": rule.threshold,
                        "severity": rule.severity,
                        "timestamp": time.time(),
                        "notification_channels": rule.notification_channels
                    }
                    
                    triggered_alerts.append(alert)
                    self.alert_history.append(alert)
                    
                    # Store as active alert
                    self.active_alerts[alert["alert_id"]] = alert
                    
                    self.logger.warning(f"Alert triggered: {rule.name} - {metric_name} = {value}")
        
        return triggered_alerts
    
    def _evaluate_condition(
        self,
        value: Union[int, float],
        condition: str,
        threshold: Union[int, float]
    ) -> bool:
        """Evaluate alert condition.
        
        Args:
            value: Current value
            threshold: Threshold value
            condition: Condition string
            
        Returns:
            True if condition is met
        """
        try:
            # Simple condition evaluation
            if condition == "value > threshold":
                return value > threshold
            elif condition == "value < threshold":
                return value < threshold
            elif condition == "value >= threshold":
                return value >= threshold
            elif condition == "value <= threshold":
                return value <= threshold
            elif condition == "value == threshold":
                return value == threshold
            else:
                # Try to evaluate as Python expression
                return eval(condition.replace("value", str(value)).replace("threshold", str(threshold)))
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts.
        
        Returns:
            List of active alerts
        """
        with self.lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history.
        
        Args:
            limit: Maximum number of alerts
            
        Returns:
            List of historical alerts
        """
        with self.lock:
            return list(self.alert_history)[-limit:]
    
    def clear_alert(self, alert_id: str) -> bool:
        """Clear active alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if cleared, False if not found
        """
        with self.lock:
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                self.logger.info(f"Cleared alert: {alert_id}")
                return True
            return False


class DashboardManager:
    """Manages dashboards and widgets."""
    
    def __init__(self):
        """Initialize dashboard manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.dashboards: Dict[str, Dashboard] = {}
        self.metric_collector = MetricCollector()
        self.chart_generator = ChartGenerator(self.metric_collector)
        self.alert_manager = AlertManager()
        self.lock = threading.RLock()
        
        # Create default dashboards
        self._create_default_dashboards()
    
    def _create_default_dashboards(self) -> None:
        """Create default dashboards."""
        # Overview Dashboard
        overview_dashboard = Dashboard(
            dashboard_id="overview",
            name="Overview",
            dashboard_type=DashboardType.OVERVIEW,
            description="System overview dashboard",
            widgets=[
                WidgetConfig(
                    widget_id="total_requests",
                    widget_type=WidgetType.METRIC,
                    title="Total Requests",
                    position=(0, 0),
                    size=(3, 2),
                    config={"metric": "requests_total"}
                ),
                WidgetConfig(
                    widget_id="active_workers",
                    widget_type=WidgetType.METRIC,
                    title="Active Workers",
                    position=(3, 0),
                    size=(3, 2),
                    config={"metric": "workers_active"}
                ),
                WidgetConfig(
                    widget_id="request_rate",
                    widget_type=WidgetType.CHART,
                    title="Request Rate",
                    position=(0, 2),
                    size=(6, 4),
                    config={
                        "metric": "requests_per_second",
                        "chart_type": "line"
                    }
                )
            ]
        )
        
        self.dashboards["overview"] = overview_dashboard
    
    def create_dashboard(
        self,
        name: str,
        dashboard_type: DashboardType,
        description: str = "",
        owner_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dashboard:
        """Create new dashboard.
        
        Args:
            name: Dashboard name
            dashboard_type: Dashboard type
            description: Dashboard description
            owner_id: Owner user ID
            tenant_id: Tenant ID
            
        Returns:
            Created dashboard
        """
        with self.lock:
            dashboard_id = str(uuid.uuid4())
            
            dashboard = Dashboard(
                dashboard_id=dashboard_id,
                name=name,
                dashboard_type=dashboard_type,
                description=description,
                owner_id=owner_id,
                tenant_id=tenant_id
            )
            
            self.dashboards[dashboard_id] = dashboard
            self.logger.info(f"Created dashboard: {name} ({dashboard_id})")
            
            return dashboard
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID.
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Dashboard or None
        """
        with self.lock:
            return self.dashboards.get(dashboard_id)
    
    def update_dashboard(self, dashboard_id: str, **kwargs) -> bool:
        """Update dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        with self.lock:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            
            # Update allowed fields
            allowed_fields = ['name', 'description', 'widgets', 'is_public']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(dashboard, field, value)
            
            dashboard.updated_at = time.time()
            self.logger.info(f"Updated dashboard: {dashboard_id}")
            
            return True
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if dashboard_id not in self.dashboards:
                return False
            
            del self.dashboards[dashboard_id]
            self.logger.info(f"Deleted dashboard: {dashboard_id}")
            return True
    
    def add_widget(
        self,
        dashboard_id: str,
        widget: WidgetConfig
    ) -> bool:
        """Add widget to dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            widget: Widget configuration
            
        Returns:
            True if added, False if dashboard not found
        """
        with self.lock:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            dashboard.widgets.append(widget)
            dashboard.updated_at = time.time()
            
            self.logger.info(f"Added widget {widget.widget_id} to dashboard {dashboard_id}")
            return True
    
    def remove_widget(
        self,
        dashboard_id: str,
        widget_id: str
    ) -> bool:
        """Remove widget from dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            widget_id: Widget ID
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if dashboard_id not in self.dashboards:
                return False
            
            dashboard = self.dashboards[dashboard_id]
            
            for i, widget in enumerate(dashboard.widgets):
                if widget.widget_id == widget_id:
                    del dashboard.widgets[i]
                    dashboard.updated_at = time.time()
                    self.logger.info(f"Removed widget {widget_id} from dashboard {dashboard_id}")
                    return True
            
            return False
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data with widget data.
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Dashboard data with widget data
        """
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return {}
            
            dashboard_data = {
                "dashboard_id": dashboard.dashboard_id,
                "name": dashboard.name,
                "type": dashboard.dashboard_type.value,
                "description": dashboard.description,
                "widgets": []
            }
            
            # Generate widget data
            for widget in dashboard.widgets:
                if not widget.enabled:
                    continue
                
                widget_data = {
                    "widget_id": widget.widget_id,
                    "type": widget.widget_type.value,
                    "title": widget.title,
                    "position": widget.position,
                    "size": widget.size,
                    "data": self._generate_widget_data(widget)
                }
                
                dashboard_data["widgets"].append(widget_data)
            
            return dashboard_data
    
    def _generate_widget_data(self, widget: WidgetConfig) -> Dict[str, Any]:
        """Generate data for widget.
        
        Args:
            widget: Widget configuration
            
        Returns:
            Widget data
        """
        try:
            if widget.widget_type == WidgetType.METRIC:
                metric_name = widget.config.get("metric")
                if metric_name:
                    summary = self.metric_collector.get_metric_summary(metric_name)
                    return {
                        "value": summary.get("latest_value", 0),
                        "trend": summary.get("trend", "stable"),
                        "change": summary.get("avg", 0)
                    }
            
            elif widget.widget_type == WidgetType.CHART:
                metric_name = widget.config.get("metric")
                chart_type = widget.config.get("chart_type", "line")
                
                if metric_name:
                    if chart_type == "line":
                        return self.chart_generator.generate_line_chart(metric_name)
                    elif chart_type == "bar":
                        return self.chart_generator.generate_bar_chart(metric_name)
                    elif chart_type == "pie":
                        return self.chart_generator.generate_pie_chart(metric_name)
                    elif chart_type == "gauge":
                        return self.chart_generator.generate_gauge_chart(metric_name)
            
            elif widget.widget_type == WidgetType.ALERT:
                return {
                    "alerts": self.alert_manager.get_active_alerts()
                }
            
            elif widget.widget_type == WidgetType.TABLE:
                # Generate table data based on configuration
                return {
                    "headers": widget.config.get("headers", []),
                    "rows": widget.config.get("rows", [])
                }
            
        except Exception as e:
            self.logger.error(f"Failed to generate widget data for {widget.widget_id}: {e}")
            return {}
        
        return {}
    
    def record_metric(
        self,
        metric_name: str,
        value: Union[int, float, str],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record metric.
        
        Args:
            metric_name: Metric name
            value: Metric value
            labels: Optional labels
            metadata: Optional metadata
        """
        self.metric_collector.record_metric(metric_name, value, labels, metadata)
        
        # Check for alerts
        if isinstance(value, (int, float)):
            self.alert_manager.check_alerts(metric_name, value)
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add alert rule.
        
        Args:
            rule: Alert rule
        """
        self.alert_manager.add_alert_rule(rule)
    
    def get_dashboard_list(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of dashboards.
        
        Args:
            tenant_id: Optional tenant ID filter
            
        Returns:
            List of dashboard summaries
        """
        with self.lock:
            dashboards = list(self.dashboards.values())
            
            if tenant_id:
                dashboards = [d for d in dashboards if d.tenant_id == tenant_id]
            
            return [
                {
                    "dashboard_id": d.dashboard_id,
                    "name": d.name,
                    "type": d.dashboard_type.value,
                    "description": d.description,
                    "widget_count": len(d.widgets),
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    "is_public": d.is_public
                }
                for d in dashboards
            ]
