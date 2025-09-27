"""
Capacity Planning Module

This module implements intelligent capacity planning and resource scaling:
- Predictive resource scaling based on usage patterns
- Cost optimization strategies
- Load balancing recommendations
- Auto-scaling policies
- Resource utilization forecasting

Author: SPIDER Development Team
Version: 1.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import warnings
from collections import defaultdict, deque
import threading
import time
import math

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be scaled"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    INSTANCES = "instances"
    CONNECTIONS = "connections"


class ScalingAction(Enum):
    """Types of scaling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    NO_ACTION = "no_action"


class ScalingPolicy(Enum):
    """Scaling policy types"""
    REACTIVE = "reactive"
    PREDICTIVE = "predictive"
    SCHEDULED = "scheduled"
    HYBRID = "hybrid"


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    resource_type: ResourceType
    current_usage: float  # 0.0 to 1.0
    peak_usage: float
    average_usage: float
    capacity: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingRecommendation:
    """Resource scaling recommendation"""
    resource_type: ResourceType
    action: ScalingAction
    current_capacity: float
    recommended_capacity: float
    scaling_factor: float
    confidence: float
    reason: str
    estimated_cost_impact: Optional[float] = None
    time_to_scale: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapacityForecast:
    """Capacity utilization forecast"""
    resource_type: ResourceType
    current_usage: float
    forecasted_usage: List[float]
    timestamps: List[datetime]
    confidence_intervals: List[Tuple[float, float]]
    peak_usage_prediction: float
    time_to_capacity_exhaustion: Optional[timedelta] = None
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostOptimization:
    """Cost optimization recommendation"""
    current_cost: float
    optimized_cost: float
    savings_percentage: float
    recommendations: List[str]
    implementation_effort: str  # "low", "medium", "high"
    payback_period: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceMonitor:
    """Monitor resource utilization and trends"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.peak_usage = defaultdict(float)
        self.average_usage = defaultdict(float)
        self.lock = threading.Lock()
    
    def record_metrics(self, metrics: ResourceMetrics):
        """Record resource metrics"""
        with self.lock:
            self.metrics_history[metrics.resource_type].append(metrics)
            
            # Update peak usage
            if metrics.current_usage > self.peak_usage[metrics.resource_type]:
                self.peak_usage[metrics.resource_type] = metrics.current_usage
            
            # Update average usage
            recent_metrics = list(self.metrics_history[metrics.resource_type])[-100:]  # Last 100 readings
            if recent_metrics:
                self.average_usage[metrics.resource_type] = np.mean([
                    m.current_usage for m in recent_metrics
                ])
    
    def get_current_metrics(self, resource_type: ResourceType) -> Optional[ResourceMetrics]:
        """Get most recent metrics for a resource type"""
        with self.lock:
            if resource_type not in self.metrics_history or not self.metrics_history[resource_type]:
                return None
            return self.metrics_history[resource_type][-1]
    
    def get_usage_trend(self, resource_type: ResourceType, hours: int = 24) -> List[float]:
        """Get usage trend for the specified time period"""
        with self.lock:
            if resource_type not in self.metrics_history:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.metrics_history[resource_type]
                if m.timestamp >= cutoff_time
            ]
            
            return [m.current_usage for m in recent_metrics]
    
    def get_peak_usage(self, resource_type: ResourceType) -> float:
        """Get peak usage for a resource type"""
        with self.lock:
            return self.peak_usage.get(resource_type, 0.0)
    
    def get_average_usage(self, resource_type: ResourceType) -> float:
        """Get average usage for a resource type"""
        with self.lock:
            return self.average_usage.get(resource_type, 0.0)


class PredictiveScaler:
    """Predictive resource scaling engine"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.scaling_thresholds = self.config.get('scaling_thresholds', {
            'cpu': {'scale_up': 0.8, 'scale_down': 0.3},
            'memory': {'scale_up': 0.85, 'scale_down': 0.4},
            'storage': {'scale_up': 0.9, 'scale_down': 0.5}
        })
        self.scaling_cooldown = self.config.get('scaling_cooldown', 300)  # 5 minutes
        self.last_scaling = defaultdict(lambda: datetime.min)
        self.scaling_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    async def analyze_scaling_need(
        self,
        resource_type: ResourceType,
        current_usage: float,
        usage_trend: List[float],
        capacity: float
    ) -> ScalingRecommendation:
        """Analyze if scaling is needed for a resource"""
        try:
            # Check cooldown period
            if self._is_in_cooldown(resource_type):
                return ScalingRecommendation(
                    resource_type=resource_type,
                    action=ScalingAction.NO_ACTION,
                    current_capacity=capacity,
                    recommended_capacity=capacity,
                    scaling_factor=1.0,
                    confidence=0.0,
                    reason="Scaling in cooldown period"
                )
            
            # Get scaling thresholds
            thresholds = self.scaling_thresholds.get(resource_type.value, {})
            scale_up_threshold = thresholds.get('scale_up', 0.8)
            scale_down_threshold = thresholds.get('scale_down', 0.3)
            
            # Analyze current usage
            if current_usage >= scale_up_threshold:
                return await self._recommend_scale_up(
                    resource_type, current_usage, usage_trend, capacity
                )
            elif current_usage <= scale_down_threshold and len(usage_trend) > 10:
                return await self._recommend_scale_down(
                    resource_type, current_usage, usage_trend, capacity
                )
            else:
                return ScalingRecommendation(
                    resource_type=resource_type,
                    action=ScalingAction.NO_ACTION,
                    current_capacity=capacity,
                    recommended_capacity=capacity,
                    scaling_factor=1.0,
                    confidence=0.5,
                    reason=f"Usage {current_usage:.2f} within normal range"
                )
                
        except Exception as e:
            logger.error(f"Error analyzing scaling need for {resource_type}: {e}")
            return ScalingRecommendation(
                resource_type=resource_type,
                action=ScalingAction.NO_ACTION,
                current_capacity=capacity,
                recommended_capacity=capacity,
                scaling_factor=1.0,
                confidence=0.0,
                reason=f"Error: {str(e)}"
            )
    
    async def _recommend_scale_up(
        self,
        resource_type: ResourceType,
        current_usage: float,
        usage_trend: List[float],
        capacity: float
    ) -> ScalingRecommendation:
        """Recommend scaling up a resource"""
        # Calculate scaling factor based on usage
        target_usage = 0.6  # Target 60% usage after scaling
        scaling_factor = current_usage / target_usage
        
        # Apply safety margin
        scaling_factor = min(scaling_factor * 1.2, 3.0)  # Max 3x scaling
        
        recommended_capacity = capacity * scaling_factor
        
        # Calculate confidence based on trend
        confidence = self._calculate_scaling_confidence(usage_trend, True)
        
        # Determine scaling action
        if scaling_factor > 2.0:
            action = ScalingAction.SCALE_OUT
            reason = f"High usage ({current_usage:.2f}), recommend horizontal scaling"
        else:
            action = ScalingAction.SCALE_UP
            reason = f"High usage ({current_usage:.2f}), recommend vertical scaling"
        
        recommendation = ScalingRecommendation(
            resource_type=resource_type,
            action=action,
            current_capacity=capacity,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            confidence=confidence,
            reason=reason,
            time_to_scale=timedelta(minutes=5)  # Estimated scaling time
        )
        
        # Record scaling recommendation
        with self.lock:
            self.scaling_history.append(recommendation)
        
        return recommendation
    
    async def _recommend_scale_down(
        self,
        resource_type: ResourceType,
        current_usage: float,
        usage_trend: List[float],
        capacity: float
    ) -> ScalingRecommendation:
        """Recommend scaling down a resource"""
        # Calculate scaling factor based on usage
        target_usage = 0.6  # Target 60% usage after scaling
        scaling_factor = current_usage / target_usage
        
        # Apply safety margin
        scaling_factor = max(scaling_factor * 0.8, 0.5)  # Min 50% scaling
        
        recommended_capacity = capacity * scaling_factor
        
        # Calculate confidence based on trend
        confidence = self._calculate_scaling_confidence(usage_trend, False)
        
        # Determine scaling action
        if scaling_factor < 0.7:
            action = ScalingAction.SCALE_IN
            reason = f"Low usage ({current_usage:.2f}), recommend horizontal scaling down"
        else:
            action = ScalingAction.SCALE_DOWN
            reason = f"Low usage ({current_usage:.2f}), recommend vertical scaling down"
        
        recommendation = ScalingRecommendation(
            resource_type=resource_type,
            action=action,
            current_capacity=capacity,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            confidence=confidence,
            reason=reason,
            time_to_scale=timedelta(minutes=10)  # Estimated scaling time
        )
        
        # Record scaling recommendation
        with self.lock:
            self.scaling_history.append(recommendation)
        
        return recommendation
    
    def _calculate_scaling_confidence(
        self,
        usage_trend: List[float],
        is_scale_up: bool
    ) -> float:
        """Calculate confidence in scaling recommendation"""
        if len(usage_trend) < 5:
            return 0.5
        
        # Calculate trend direction
        recent_trend = usage_trend[-5:]
        trend_slope = np.polyfit(range(len(recent_trend)), recent_trend, 1)[0]
        
        # Calculate variance
        trend_variance = np.var(recent_trend)
        
        # Base confidence on trend consistency
        if is_scale_up:
            # Higher confidence if trend is increasing
            confidence = min(0.5 + abs(trend_slope) * 10, 1.0)
        else:
            # Higher confidence if trend is decreasing
            confidence = min(0.5 + abs(trend_slope) * 10, 1.0)
        
        # Reduce confidence for high variance
        confidence *= max(0.5, 1.0 - trend_variance)
        
        return confidence
    
    def _is_in_cooldown(self, resource_type: ResourceType) -> bool:
        """Check if resource is in scaling cooldown period"""
        with self.lock:
            last_scaling = self.last_scaling[resource_type]
            return (datetime.now() - last_scaling).total_seconds() < self.scaling_cooldown
    
    def record_scaling_action(self, resource_type: ResourceType):
        """Record that a scaling action was taken"""
        with self.lock:
            self.last_scaling[resource_type] = datetime.now()
    
    def get_scaling_history(self, limit: int = 100) -> List[ScalingRecommendation]:
        """Get recent scaling history"""
        with self.lock:
            return list(self.scaling_history)[-limit:]


class CapacityForecaster:
    """Forecast future capacity needs"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.forecast_horizon = self.config.get('forecast_horizon', 24)  # hours
        self.forecast_accuracy_threshold = self.config.get('forecast_accuracy_threshold', 0.8)
        self.forecast_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    async def forecast_capacity_usage(
        self,
        resource_type: ResourceType,
        historical_data: List[Tuple[datetime, float]],
        forecast_hours: int = 24
    ) -> CapacityForecast:
        """Forecast future capacity usage"""
        try:
            if len(historical_data) < 10:
                return CapacityForecast(
                    resource_type=resource_type,
                    current_usage=0.0,
                    forecasted_usage=[0.0] * forecast_hours,
                    timestamps=[datetime.now() + timedelta(hours=i) for i in range(1, forecast_hours + 1)],
                    confidence_intervals=[(0.0, 0.0)] * forecast_hours,
                    peak_usage_prediction=0.0,
                    recommendations=["Insufficient historical data for forecasting"]
                )
            
            # Prepare data
            timestamps = [item[0] for item in historical_data]
            values = [item[1] for item in historical_data]
            
            # Create time series features
            df = pd.DataFrame({
                'timestamp': timestamps,
                'value': values
            })
            df = df.sort_values('timestamp')
            
            # Generate time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['time_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
            
            # Simple linear regression for forecasting
            X = df[['hour', 'day_of_week', 'time_since_start']].values
            y = df['value'].values
            
            # Fit linear model
            coeffs = np.polyfit(df['time_since_start'], y, 1)
            
            # Generate forecast
            last_timestamp = timestamps[-1]
            forecast_timestamps = []
            forecast_values = []
            confidence_intervals = []
            
            for i in range(1, forecast_hours + 1):
                future_time = last_timestamp + timedelta(hours=i)
                future_time_since = (future_time - timestamps[0]).total_seconds()
                
                # Predict value
                predicted_value = coeffs[0] * future_time_since + coeffs[1]
                predicted_value = max(0.0, min(1.0, predicted_value))  # Clamp to [0, 1]
                
                forecast_timestamps.append(future_time)
                forecast_values.append(predicted_value)
                
                # Calculate confidence interval
                std_error = np.std(y) * 0.1  # Simple error estimation
                confidence_intervals.append((
                    max(0.0, predicted_value - 1.96 * std_error),
                    min(1.0, predicted_value + 1.96 * std_error)
                ))
            
            # Find peak usage prediction
            peak_usage = max(forecast_values)
            
            # Calculate time to capacity exhaustion
            time_to_exhaustion = None
            if peak_usage > 0.9:  # If peak usage exceeds 90%
                # Find when usage first exceeds 90%
                for i, value in enumerate(forecast_values):
                    if value > 0.9:
                        time_to_exhaustion = timedelta(hours=i + 1)
                        break
            
            # Generate recommendations
            recommendations = []
            if peak_usage > 0.9:
                recommendations.append("Immediate scaling required - peak usage exceeds 90%")
            elif peak_usage > 0.8:
                recommendations.append("Consider proactive scaling - peak usage exceeds 80%")
            
            if time_to_exhaustion:
                recommendations.append(f"Capacity exhaustion predicted in {time_to_exhaustion}")
            
            # Calculate trend
            if len(forecast_values) > 1:
                trend_slope = (forecast_values[-1] - forecast_values[0]) / len(forecast_values)
                if trend_slope > 0.01:
                    recommendations.append("Upward trend detected - consider scaling up")
                elif trend_slope < -0.01:
                    recommendations.append("Downward trend detected - consider scaling down")
            
            forecast = CapacityForecast(
                resource_type=resource_type,
                current_usage=values[-1],
                forecasted_usage=forecast_values,
                timestamps=forecast_timestamps,
                confidence_intervals=confidence_intervals,
                peak_usage_prediction=peak_usage,
                time_to_capacity_exhaustion=time_to_exhaustion,
                recommendations=recommendations,
                metadata={
                    'model_type': 'linear_regression',
                    'trend_slope': coeffs[0],
                    'r_squared': self._calculate_r_squared(y, X, coeffs)
                }
            )
            
            # Store forecast
            with self.lock:
                self.forecast_history.append(forecast)
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error forecasting capacity for {resource_type}: {e}")
            return CapacityForecast(
                resource_type=resource_type,
                current_usage=0.0,
                forecasted_usage=[0.0] * forecast_hours,
                timestamps=[datetime.now() + timedelta(hours=i) for i in range(1, forecast_hours + 1)],
                confidence_intervals=[(0.0, 0.0)] * forecast_hours,
                peak_usage_prediction=0.0,
                recommendations=[f"Error in forecasting: {str(e)}"]
            )
    
    def _calculate_r_squared(self, y_true: np.ndarray, X: np.ndarray, coeffs: np.ndarray) -> float:
        """Calculate R-squared for the model"""
        try:
            y_pred = coeffs[0] * X[:, 2] + coeffs[1]  # Using time_since_start
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        except:
            return 0.0
    
    def get_forecast_history(self, limit: int = 100) -> List[CapacityForecast]:
        """Get recent forecast history"""
        with self.lock:
            return list(self.forecast_history)[-limit:]


class CostOptimizer:
    """Optimize resource costs"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cost_models = self.config.get('cost_models', {})
        self.optimization_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    async def optimize_costs(
        self,
        current_resources: Dict[ResourceType, float],
        usage_patterns: Dict[ResourceType, List[float]],
        cost_per_unit: Dict[ResourceType, float]
    ) -> CostOptimization:
        """Optimize resource costs based on usage patterns"""
        try:
            current_cost = sum(
                current_resources.get(rt, 0) * cost_per_unit.get(rt, 1.0)
                for rt in ResourceType
            )
            
            optimized_resources = {}
            recommendations = []
            
            for resource_type, usage_pattern in usage_patterns.items():
                if not usage_pattern:
                    continue
                
                current_capacity = current_resources.get(resource_type, 0)
                avg_usage = np.mean(usage_pattern)
                peak_usage = np.max(usage_pattern)
                
                # Calculate optimal capacity
                if peak_usage > 0.9:  # High peak usage
                    optimal_capacity = current_capacity * 1.2  # 20% buffer
                    recommendations.append(f"Scale up {resource_type.value} - peak usage {peak_usage:.2f}")
                elif avg_usage < 0.5 and peak_usage < 0.7:  # Low usage
                    optimal_capacity = current_capacity * 0.8  # 20% reduction
                    recommendations.append(f"Scale down {resource_type.value} - low usage (avg: {avg_usage:.2f})")
                else:
                    optimal_capacity = current_capacity
                
                optimized_resources[resource_type] = optimal_capacity
            
            # Calculate optimized cost
            optimized_cost = sum(
                optimized_resources.get(rt, current_resources.get(rt, 0)) * cost_per_unit.get(rt, 1.0)
                for rt in ResourceType
            )
            
            # Calculate savings
            savings = current_cost - optimized_cost
            savings_percentage = (savings / current_cost * 100) if current_cost > 0 else 0.0
            
            # Determine implementation effort
            if savings_percentage > 20:
                effort = "high"
            elif savings_percentage > 10:
                effort = "medium"
            else:
                effort = "low"
            
            # Calculate payback period (simplified)
            payback_period = None
            if savings > 0:
                # Assume monthly cost reduction
                monthly_savings = savings * 30  # 30 days
                implementation_cost = current_cost * 0.1  # 10% of current cost
                if monthly_savings > 0:
                    payback_days = implementation_cost / monthly_savings
                    payback_period = timedelta(days=payback_days)
            
            optimization = CostOptimization(
                current_cost=current_cost,
                optimized_cost=optimized_cost,
                savings_percentage=savings_percentage,
                recommendations=recommendations,
                implementation_effort=effort,
                payback_period=payback_period,
                metadata={
                    'current_resources': {rt.value: v for rt, v in current_resources.items()},
                    'optimized_resources': {rt.value: v for rt, v in optimized_resources.items()},
                    'cost_per_unit': {rt.value: v for rt, v in cost_per_unit.items()}
                }
            )
            
            # Store optimization
            with self.lock:
                self.optimization_history.append(optimization)
            
            return optimization
            
        except Exception as e:
            logger.error(f"Error optimizing costs: {e}")
            return CostOptimization(
                current_cost=0.0,
                optimized_cost=0.0,
                savings_percentage=0.0,
                recommendations=[f"Error in cost optimization: {str(e)}"],
                implementation_effort="high"
            )
    
    def get_optimization_history(self, limit: int = 100) -> List[CostOptimization]:
        """Get recent optimization history"""
        with self.lock:
            return list(self.optimization_history)[-limit:]


class CapacityPlanningManager:
    """Main capacity planning manager"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.resource_monitor = ResourceMonitor(config)
        self.predictive_scaler = PredictiveScaler(config)
        self.capacity_forecaster = CapacityForecaster(config)
        self.cost_optimizer = CostOptimizer(config)
        self.planning_active = False
        self.planning_task = None
        self.alert_callbacks = []
        self.lock = threading.Lock()
    
    async def start_planning(self, interval: float = 300.0):  # 5 minutes
        """Start capacity planning"""
        if self.planning_active:
            logger.warning("Capacity planning already active")
            return
        
        self.planning_active = True
        self.planning_task = asyncio.create_task(
            self._planning_loop(interval)
        )
        logger.info("Capacity planning started")
    
    async def stop_planning(self):
        """Stop capacity planning"""
        self.planning_active = False
        if self.planning_task:
            self.planning_task.cancel()
            try:
                await self.planning_task
            except asyncio.CancelledError:
                pass
        logger.info("Capacity planning stopped")
    
    async def _planning_loop(self, interval: float):
        """Main planning loop"""
        while self.planning_active:
            try:
                await self._run_capacity_planning()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in capacity planning loop: {e}")
                await asyncio.sleep(interval)
    
    async def _run_capacity_planning(self):
        """Run comprehensive capacity planning"""
        try:
            # Get current metrics for all resource types
            resource_types = [ResourceType.CPU, ResourceType.MEMORY, ResourceType.STORAGE]
            
            for resource_type in resource_types:
                current_metrics = self.resource_monitor.get_current_metrics(resource_type)
                if not current_metrics:
                    continue
                
                # Get usage trend
                usage_trend = self.resource_monitor.get_usage_trend(resource_type, 24)
                
                # Analyze scaling needs
                scaling_recommendation = await self.predictive_scaler.analyze_scaling_need(
                    resource_type,
                    current_metrics.current_usage,
                    usage_trend,
                    current_metrics.capacity
                )
                
                # Trigger alerts for high-confidence recommendations
                if scaling_recommendation.confidence > 0.8:
                    await self._handle_scaling_recommendation(scaling_recommendation)
                
                # Generate capacity forecast
                historical_data = [
                    (m.timestamp, m.current_usage)
                    for m in self.resource_monitor.metrics_history[resource_type]
                ]
                
                if len(historical_data) >= 10:
                    forecast = await self.capacity_forecaster.forecast_capacity_usage(
                        resource_type, historical_data
                    )
                    
                    if forecast.time_to_capacity_exhaustion:
                        await self._handle_capacity_forecast(forecast)
            
        except Exception as e:
            logger.error(f"Error in capacity planning: {e}")
    
    async def _handle_scaling_recommendation(self, recommendation: ScalingRecommendation):
        """Handle scaling recommendations"""
        logger.info(f"Scaling recommendation: {recommendation.reason}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback('scaling_recommendation', recommendation)
            except Exception as e:
                logger.error(f"Error in scaling recommendation callback: {e}")
    
    async def _handle_capacity_forecast(self, forecast: CapacityForecast):
        """Handle capacity forecasts"""
        logger.info(f"Capacity forecast: {forecast.recommendations}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback('capacity_forecast', forecast)
            except Exception as e:
                logger.error(f"Error in capacity forecast callback: {e}")
    
    def add_alert_callback(self, callback):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def record_resource_metrics(
        self,
        resource_type: ResourceType,
        current_usage: float,
        capacity: float,
        timestamp: Optional[datetime] = None
    ):
        """Record resource metrics"""
        if timestamp is None:
            timestamp = datetime.now()
        
        metrics = ResourceMetrics(
            resource_type=resource_type,
            current_usage=current_usage,
            peak_usage=current_usage,  # Will be updated by monitor
            average_usage=current_usage,  # Will be updated by monitor
            capacity=capacity,
            timestamp=timestamp
        )
        
        self.resource_monitor.record_metrics(metrics)
    
    async def get_scaling_recommendations(
        self,
        resource_type: ResourceType
    ) -> Optional[ScalingRecommendation]:
        """Get scaling recommendations for a resource type"""
        current_metrics = self.resource_monitor.get_current_metrics(resource_type)
        if not current_metrics:
            return None
        
        usage_trend = self.resource_monitor.get_usage_trend(resource_type, 24)
        
        return await self.predictive_scaler.analyze_scaling_need(
            resource_type,
            current_metrics.current_usage,
            usage_trend,
            current_metrics.capacity
        )
    
    async def get_capacity_forecast(
        self,
        resource_type: ResourceType,
        hours: int = 24
    ) -> Optional[CapacityForecast]:
        """Get capacity forecast for a resource type"""
        historical_data = [
            (m.timestamp, m.current_usage)
            for m in self.resource_monitor.metrics_history[resource_type]
        ]
        
        if len(historical_data) < 10:
            return None
        
        return await self.capacity_forecaster.forecast_capacity_usage(
            resource_type, historical_data, hours
        )
    
    async def optimize_costs(
        self,
        cost_per_unit: Dict[ResourceType, float]
    ) -> CostOptimization:
        """Optimize resource costs"""
        current_resources = {}
        usage_patterns = {}
        
        for resource_type in ResourceType:
            current_metrics = self.resource_monitor.get_current_metrics(resource_type)
            if current_metrics:
                current_resources[resource_type] = current_metrics.capacity
                usage_patterns[resource_type] = self.resource_monitor.get_usage_trend(
                    resource_type, 168  # 1 week
                )
        
        return await self.cost_optimizer.optimize_costs(
            current_resources, usage_patterns, cost_per_unit
        )
    
    def get_planning_status(self) -> Dict[str, Any]:
        """Get current planning status"""
        return {
            'planning_active': self.planning_active,
            'monitored_resources': list(self.resource_monitor.metrics_history.keys()),
            'scaling_recommendations': len(self.predictive_scaler.get_scaling_history()),
            'capacity_forecasts': len(self.capacity_forecaster.get_forecast_history()),
            'cost_optimizations': len(self.cost_optimizer.get_optimization_history())
        }
