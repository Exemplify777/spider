"""Auto-scaling algorithms for SPIDER framework."""

import asyncio
import time
import math
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque
import statistics

from ..core.exceptions import SpiderError, MonitoringError
from ..core.logger import get_logger


class ScalingAction(Enum):
    """Scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


class ScalingStrategy(Enum):
    """Scaling strategies."""
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    REQUEST_BASED = "request_based"
    RESPONSE_TIME_BASED = "response_time_based"
    HYBRID = "hybrid"
    PREDICTIVE = "predictive"


class ScalingPolicy(Enum):
    """Scaling policies."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class ScalingMetric:
    """Scaling metric definition."""
    name: str
    weight: float
    threshold_up: float
    threshold_down: float
    window_size: int = 10  # Number of samples to consider
    enabled: bool = True


@dataclass
class ScalingConfig:
    """Auto-scaling configuration."""
    min_instances: int = 1
    max_instances: int = 10
    target_instances: int = 2
    strategy: ScalingStrategy = ScalingStrategy.HYBRID
    policy: ScalingPolicy = ScalingPolicy.BALANCED
    scale_up_cooldown: float = 300.0  # 5 minutes
    scale_down_cooldown: float = 600.0  # 10 minutes
    scale_up_threshold: float = 0.8  # 80%
    scale_down_threshold: float = 0.3  # 30%
    scale_factor: float = 0.5  # Scale by 50% of current instances
    enable_predictive_scaling: bool = False
    prediction_window: int = 300  # 5 minutes
    metrics: List[ScalingMetric] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.metrics:
            self.metrics = self._get_default_metrics()
    
    def _get_default_metrics(self) -> List[ScalingMetric]:
        """Get default scaling metrics."""
        return [
            ScalingMetric(
                name="cpu_usage",
                weight=0.4,
                threshold_up=0.8,
                threshold_down=0.3
            ),
            ScalingMetric(
                name="memory_usage",
                weight=0.3,
                threshold_up=0.85,
                threshold_down=0.4
            ),
            ScalingMetric(
                name="response_time",
                weight=0.2,
                threshold_up=2.0,  # 2 seconds
                threshold_down=0.5  # 0.5 seconds
            ),
            ScalingMetric(
                name="request_rate",
                weight=0.1,
                threshold_up=1000,  # requests per minute
                threshold_down=100
            )
        ]


@dataclass
class ScalingDecision:
    """Scaling decision."""
    action: ScalingAction
    current_instances: int
    target_instances: int
    reason: str
    confidence: float
    metrics: Dict[str, float]
    timestamp: float


@dataclass
class ScalingEvent:
    """Scaling event record."""
    timestamp: float
    action: ScalingAction
    from_instances: int
    to_instances: int
    reason: str
    success: bool
    duration: float = 0.0


class MetricsCollector:
    """Collects metrics for scaling decisions."""
    
    def __init__(self, window_size: int = 100):
        """Initialize metrics collector.
        
        Args:
            window_size: Size of rolling window for metrics
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def add_metric(self, name: str, value: float) -> None:
        """Add metric value.
        
        Args:
            name: Metric name
            value: Metric value
        """
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.window_size)
            
            self.metrics[name].append(value)
    
    def get_metric_average(self, name: str, window: Optional[int] = None) -> float:
        """Get average metric value.
        
        Args:
            name: Metric name
            window: Optional window size
            
        Returns:
            Average value
        """
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return 0.0
            
            values = list(self.metrics[name])
            if window:
                values = values[-window:]
            
            return statistics.mean(values) if values else 0.0
    
    def get_metric_trend(self, name: str, window: int = 10) -> float:
        """Get metric trend (positive = increasing, negative = decreasing).
        
        Args:
            name: Metric name
            window: Window size for trend calculation
            
        Returns:
            Trend value
        """
        with self._lock:
            if name not in self.metrics or len(self.metrics[name]) < 2:
                return 0.0
            
            values = list(self.metrics[name])[-window:]
            if len(values) < 2:
                return 0.0
            
            # Simple linear regression slope
            n = len(values)
            x = list(range(n))
            y = values
            
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(y)
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator


class PredictiveScaler:
    """Predictive scaling based on historical patterns."""
    
    def __init__(self, prediction_window: int = 300):
        """Initialize predictive scaler.
        
        Args:
            prediction_window: Prediction window in seconds
        """
        self.prediction_window = prediction_window
        self.logger = get_logger(self.__class__.__name__)
        self.historical_data: Dict[str, List[Tuple[float, float]]] = {}  # metric -> [(timestamp, value)]
        self._lock = threading.Lock()
    
    def add_data_point(self, metric: str, timestamp: float, value: float) -> None:
        """Add historical data point.
        
        Args:
            metric: Metric name
            timestamp: Timestamp
            value: Metric value
        """
        with self._lock:
            if metric not in self.historical_data:
                self.historical_data[metric] = []
            
            self.historical_data[metric].append((timestamp, value))
            
            # Keep only recent data (last 24 hours)
            cutoff = timestamp - 86400
            self.historical_data[metric] = [
                (ts, val) for ts, val in self.historical_data[metric]
                if ts > cutoff
            ]
    
    def predict_metric(self, metric: str, future_time: float) -> float:
        """Predict metric value at future time.
        
        Args:
            metric: Metric name
            future_time: Future timestamp
            
        Returns:
            Predicted value
        """
        with self._lock:
            if metric not in self.historical_data or len(self.historical_data[metric]) < 2:
                return 0.0
            
            data = self.historical_data[metric]
            
            # Simple linear prediction
            recent_data = data[-10:]  # Use last 10 points
            if len(recent_data) < 2:
                return 0.0
            
            # Calculate trend
            timestamps = [point[0] for point in recent_data]
            values = [point[1] for point in recent_data]
            
            # Linear regression
            n = len(timestamps)
            x_mean = statistics.mean(timestamps)
            y_mean = statistics.mean(values)
            
            numerator = sum((timestamps[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((timestamps[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return y_mean
            
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Predict future value
            predicted_value = slope * future_time + intercept
            
            return max(0, predicted_value)  # Ensure non-negative
    
    def get_scaling_recommendation(
        self, 
        current_instances: int,
        config: ScalingConfig
    ) -> ScalingDecision:
        """Get scaling recommendation based on predictions.
        
        Args:
            current_instances: Current number of instances
            config: Scaling configuration
            
        Returns:
            Scaling decision
        """
        future_time = time.time() + self.prediction_window
        
        # Predict metrics
        predicted_metrics = {}
        for metric in config.metrics:
            if metric.enabled:
                predicted_value = self.predict_metric(metric.name, future_time)
                predicted_metrics[metric.name] = predicted_value
        
        # Calculate scaling score
        scale_up_score = 0.0
        scale_down_score = 0.0
        
        for metric in config.metrics:
            if not metric.enabled or metric.name not in predicted_metrics:
                continue
            
            predicted_value = predicted_metrics[metric.name]
            
            # Check scale up condition
            if predicted_value > metric.threshold_up:
                scale_up_score += metric.weight * (predicted_value - metric.threshold_up) / metric.threshold_up
            
            # Check scale down condition
            if predicted_value < metric.threshold_down:
                scale_down_score += metric.weight * (metric.threshold_down - predicted_value) / metric.threshold_down
        
        # Make decision
        if scale_up_score > 0.5 and current_instances < config.max_instances:
            target_instances = min(
                config.max_instances,
                current_instances + max(1, int(current_instances * config.scale_factor))
            )
            return ScalingDecision(
                action=ScalingAction.SCALE_UP,
                current_instances=current_instances,
                target_instances=target_instances,
                reason=f"Predictive scaling up based on predicted metrics",
                confidence=min(1.0, scale_up_score),
                metrics=predicted_metrics,
                timestamp=time.time()
            )
        elif scale_down_score > 0.5 and current_instances > config.min_instances:
            target_instances = max(
                config.min_instances,
                current_instances - max(1, int(current_instances * config.scale_factor))
            )
            return ScalingDecision(
                action=ScalingAction.SCALE_DOWN,
                current_instances=current_instances,
                target_instances=target_instances,
                reason=f"Predictive scaling down based on predicted metrics",
                confidence=min(1.0, scale_down_score),
                metrics=predicted_metrics,
                timestamp=time.time()
            )
        else:
            return ScalingDecision(
                action=ScalingAction.NO_ACTION,
                current_instances=current_instances,
                target_instances=current_instances,
                reason="No scaling needed based on predictions",
                confidence=1.0 - max(scale_up_score, scale_down_score),
                metrics=predicted_metrics,
                timestamp=time.time()
            )


class AutoScaler:
    """Auto-scaler for SPIDER framework."""
    
    def __init__(self, config: ScalingConfig):
        """Initialize auto-scaler.
        
        Args:
            config: Scaling configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.metrics_collector = MetricsCollector()
        self.predictive_scaler = PredictiveScaler(config.prediction_window)
        self.current_instances = config.target_instances
        self.last_scale_up = 0.0
        self.last_scale_down = 0.0
        self.scaling_events: List[ScalingEvent] = []
        self._lock = threading.RLock()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._scaling_callbacks: List[Callable[[ScalingDecision], None]] = []
    
    def add_scaling_callback(self, callback: Callable[[ScalingDecision], None]) -> None:
        """Add scaling callback.
        
        Args:
            callback: Callback function for scaling events
        """
        self._scaling_callbacks.append(callback)
    
    def add_metric(self, name: str, value: float) -> None:
        """Add metric value.
        
        Args:
            name: Metric name
            value: Metric value
        """
        timestamp = time.time()
        self.metrics_collector.add_metric(name, value)
        self.predictive_scaler.add_data_point(name, timestamp, value)
    
    async def start_monitoring(self, interval: float = 30.0) -> None:
        """Start auto-scaling monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            self.logger.warning("Auto-scaling monitoring is already running")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self.logger.info(f"Started auto-scaling monitoring with {interval}s interval")
    
    async def stop_monitoring(self) -> None:
        """Stop auto-scaling monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped auto-scaling monitoring")
    
    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        try:
            while self._monitoring:
                decision = await self._make_scaling_decision()
                if decision.action != ScalingAction.NO_ACTION:
                    await self._execute_scaling(decision)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in auto-scaling monitoring: {e}")
    
    async def _make_scaling_decision(self) -> ScalingDecision:
        """Make scaling decision based on current metrics.
        
        Returns:
            Scaling decision
        """
        with self._lock:
            # Check cooldowns
            current_time = time.time()
            
            if (self.config.strategy == ScalingStrategy.PREDICTIVE and 
                self.config.enable_predictive_scaling):
                return self.predictive_scaler.get_scaling_recommendation(
                    self.current_instances, self.config
                )
            
            # Collect current metrics
            current_metrics = {}
            for metric in self.config.metrics:
                if metric.enabled:
                    current_metrics[metric.name] = self.metrics_collector.get_metric_average(
                        metric.name, metric.window_size
                    )
            
            # Calculate scaling scores
            scale_up_score = 0.0
            scale_down_score = 0.0
            
            for metric in self.config.metrics:
                if not metric.enabled or metric.name not in current_metrics:
                    continue
                
                current_value = current_metrics[metric.name]
                
                # Check scale up condition
                if current_value > metric.threshold_up:
                    scale_up_score += metric.weight * (current_value - metric.threshold_up) / metric.threshold_up
                
                # Check scale down condition
                if current_value < metric.threshold_down:
                    scale_down_score += metric.weight * (metric.threshold_down - current_value) / metric.threshold_down
            
            # Apply policy adjustments
            if self.config.policy == ScalingPolicy.CONSERVATIVE:
                scale_up_score *= 1.5  # Require higher score
                scale_down_score *= 0.5  # Require lower score
            elif self.config.policy == ScalingPolicy.AGGRESSIVE:
                scale_up_score *= 0.7  # Require lower score
                scale_down_score *= 1.5  # Require higher score
            
            # Make decision
            if (scale_up_score > 0.5 and 
                self.current_instances < self.config.max_instances and
                current_time - self.last_scale_up > self.config.scale_up_cooldown):
                
                target_instances = min(
                    self.config.max_instances,
                    self.current_instances + max(1, int(self.current_instances * self.config.scale_factor))
                )
                
                return ScalingDecision(
                    action=ScalingAction.SCALE_UP,
                    current_instances=self.current_instances,
                    target_instances=target_instances,
                    reason=f"Scale up triggered by metrics: {current_metrics}",
                    confidence=min(1.0, scale_up_score),
                    metrics=current_metrics,
                    timestamp=current_time
                )
            
            elif (scale_down_score > 0.5 and 
                  self.current_instances > self.config.min_instances and
                  current_time - self.last_scale_down > self.config.scale_down_cooldown):
                
                target_instances = max(
                    self.config.min_instances,
                    self.current_instances - max(1, int(self.current_instances * self.config.scale_factor))
                )
                
                return ScalingDecision(
                    action=ScalingAction.SCALE_DOWN,
                    current_instances=self.current_instances,
                    target_instances=target_instances,
                    reason=f"Scale down triggered by metrics: {current_metrics}",
                    confidence=min(1.0, scale_down_score),
                    metrics=current_metrics,
                    timestamp=current_time
                )
            
            else:
                return ScalingDecision(
                    action=ScalingAction.NO_ACTION,
                    current_instances=self.current_instances,
                    target_instances=self.current_instances,
                    reason="No scaling needed",
                    confidence=1.0 - max(scale_up_score, scale_down_score),
                    metrics=current_metrics,
                    timestamp=current_time
                )
    
    async def _execute_scaling(self, decision: ScalingDecision) -> None:
        """Execute scaling decision.
        
        Args:
            decision: Scaling decision
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing scaling: {decision.action.value} from {decision.current_instances} to {decision.target_instances}")
            
            # Update instance count
            with self._lock:
                self.current_instances = decision.target_instances
                
                if decision.action == ScalingAction.SCALE_UP:
                    self.last_scale_up = time.time()
                elif decision.action == ScalingAction.SCALE_DOWN:
                    self.last_scale_down = time.time()
            
            # Notify callbacks
            for callback in self._scaling_callbacks:
                try:
                    callback(decision)
                except Exception as e:
                    self.logger.error(f"Error in scaling callback: {e}")
            
            # Record event
            duration = time.time() - start_time
            event = ScalingEvent(
                timestamp=time.time(),
                action=decision.action,
                from_instances=decision.current_instances,
                to_instances=decision.target_instances,
                reason=decision.reason,
                success=True,
                duration=duration
            )
            
            with self._lock:
                self.scaling_events.append(event)
                # Keep only last 100 events
                if len(self.scaling_events) > 100:
                    self.scaling_events = self.scaling_events[-100:]
            
            self.logger.info(f"Scaling completed successfully in {duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Scaling failed: {e}")
            
            # Record failed event
            event = ScalingEvent(
                timestamp=time.time(),
                action=decision.action,
                from_instances=decision.current_instances,
                to_instances=decision.target_instances,
                reason=decision.reason,
                success=False,
                duration=time.time() - start_time
            )
            
            with self._lock:
                self.scaling_events.append(event)
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics.
        
        Returns:
            Scaling statistics
        """
        with self._lock:
            total_events = len(self.scaling_events)
            successful_events = len([e for e in self.scaling_events if e.success])
            failed_events = total_events - successful_events
            
            scale_up_events = len([e for e in self.scaling_events if e.action == ScalingAction.SCALE_UP])
            scale_down_events = len([e for e in self.scaling_events if e.action == ScalingAction.SCALE_DOWN])
            
            return {
                "current_instances": self.current_instances,
                "min_instances": self.config.min_instances,
                "max_instances": self.config.max_instances,
                "total_scaling_events": total_events,
                "successful_events": successful_events,
                "failed_events": failed_events,
                "scale_up_events": scale_up_events,
                "scale_down_events": scale_down_events,
                "success_rate": (successful_events / total_events * 100) if total_events > 0 else 100.0,
                "last_scale_up": self.last_scale_up,
                "last_scale_down": self.last_scale_down,
                "monitoring_active": self._monitoring
            }
    
    def get_recent_events(self, hours: int = 24) -> List[ScalingEvent]:
        """Get recent scaling events.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Recent scaling events
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            return [
                event for event in self.scaling_events
                if event.timestamp > cutoff_time
            ]
    
    def cleanup(self) -> None:
        """Cleanup auto-scaler."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        
        with self._lock:
            self.scaling_events.clear()
            self._scaling_callbacks.clear()
        
        self.logger.info("Auto-scaler cleaned up")
