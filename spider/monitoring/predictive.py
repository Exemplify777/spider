"""
Predictive Monitoring Module

This module implements intelligent predictive monitoring systems that can:
- Predict potential system issues before they occur
- Detect anomalies in real-time
- Forecast performance trends
- Provide early warning systems
- Enable proactive capacity planning

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

# Optional ML dependencies
try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.neural_network import MLPRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Dummy classes for when sklearn is not available
    class IsolationForest:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([1] * len(args[0]))
    
    class RandomForestRegressor:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([0.5] * len(args[0]))
    
    class StandardScaler:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def transform(self, *args, **kwargs): return args[0]
        def fit_transform(self, *args, **kwargs): return args[0]
    
    class DBSCAN:
        def __init__(self, *args, **kwargs): pass
        def fit_predict(self, *args, **kwargs): return np.array([0] * len(args[0]))
    
    class LinearRegression:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([0.5] * len(args[0]))
    
    class MLPRegressor:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([0.5] * len(args[0]))

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions that can be made"""
    ANOMALY = "anomaly"
    FAILURE = "failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CAPACITY_EXHAUSTION = "capacity_exhaustion"
    SECURITY_THREAT = "security_threat"
    RESOURCE_SCALING = "resource_scaling"
    MAINTENANCE_WINDOW = "maintenance_window"


class SeverityLevel(Enum):
    """Severity levels for predictions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PredictionResult:
    """Result of a predictive analysis"""
    prediction_type: PredictionType
    severity: SeverityLevel
    confidence: float  # 0.0 to 1.0
    predicted_value: Optional[float] = None
    predicted_timestamp: Optional[datetime] = None
    time_horizon: Optional[timedelta] = None
    features_used: List[str] = field(default_factory=list)
    explanation: str = ""
    recommended_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Import AnomalyDetectionResult from anomaly_detection module
from .anomaly_detection import AnomalyDetectionResult


@dataclass
class PerformanceForecast:
    """Performance forecast result"""
    metric_name: str
    current_value: float
    predicted_values: List[float]
    timestamps: List[datetime]
    confidence_intervals: List[Tuple[float, float]]
    trend: str  # "increasing", "decreasing", "stable"
    r_squared: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PredictiveAnalyticsEngine:
    """Main predictive analytics engine"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.prediction_history = deque(maxlen=1000)
        self.anomaly_detectors = {}
        self.forecast_models = {}
        self.lock = threading.Lock()
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for different prediction types"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, using dummy models")
            return
        
        # Anomaly detection models
        self.anomaly_detectors = {
            'isolation_forest': IsolationForest(
                contamination=0.1,
                random_state=42
            ),
            'dbscan': DBSCAN(eps=0.5, min_samples=5)
        }
        
        # Performance forecasting models
        self.forecast_models = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                random_state=42
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(50, 25),
                max_iter=500,
                random_state=42
            )
        }
        
        # Feature scalers
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': StandardScaler()  # Using StandardScaler as placeholder
        }
    
    async def predict_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        model_name: str = 'isolation_forest'
    ) -> AnomalyDetectionResult:
        """Predict if data contains anomalies"""
        try:
            with self.lock:
                if model_name not in self.anomaly_detectors:
                    raise ValueError(f"Unknown model: {model_name}")
                
                model = self.anomaly_detectors[model_name]
                
                # Ensure data is 2D
                if data.ndim == 1:
                    data = data.reshape(1, -1)
                
                if model_name == 'isolation_forest':
                    anomaly_scores = model.decision_function(data)
                    predictions = model.predict(data)
                    is_anomaly = predictions[0] == -1
                    anomaly_score = abs(anomaly_scores[0])
                else:  # DBSCAN
                    predictions = model.fit_predict(data)
                    is_anomaly = predictions[0] == -1
                    anomaly_score = 0.5  # Placeholder for DBSCAN
                
                explanation = self._generate_anomaly_explanation(
                    is_anomaly, anomaly_score, features
                )
                
                from .anomaly_detection import AnomalyType, DetectionMethod
                result = AnomalyDetectionResult(
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score,
                    anomaly_type=AnomalyType.ISOLATION,
                    detection_method=DetectionMethod.ISOLATION_FOREST,
                    features=features,
                    explanation=explanation,
                    timestamp=datetime.now()
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Error in anomaly prediction: {e}")
            from .anomaly_detection import AnomalyType, DetectionMethod
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.ISOLATION_FOREST,
                features=features,
                explanation=f"Error in prediction: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def predict_failure(
        self,
        metrics: Dict[str, float],
        time_horizon: timedelta = timedelta(hours=1)
    ) -> PredictionResult:
        """Predict potential system failures"""
        try:
            # Extract features from metrics
            features = list(metrics.keys())
            values = np.array(list(metrics.values())).reshape(1, -1)
            
            # Simple heuristic-based failure prediction
            failure_indicators = {
                'cpu_usage': 0.9,
                'memory_usage': 0.9,
                'disk_usage': 0.9,
                'error_rate': 0.1,
                'response_time': 5.0
            }
            
            risk_score = 0.0
            explanations = []
            
            for metric, value in metrics.items():
                if metric in failure_indicators:
                    threshold = failure_indicators[metric]
                    if value > threshold:
                        risk_score += (value - threshold) / (1.0 - threshold)
                        explanations.append(
                            f"{metric} ({value:.2f}) exceeds threshold ({threshold})"
                        )
            
            # Normalize risk score
            risk_score = min(risk_score / len(failure_indicators), 1.0)
            
            # Determine severity
            if risk_score > 0.8:
                severity = SeverityLevel.CRITICAL
            elif risk_score > 0.6:
                severity = SeverityLevel.HIGH
            elif risk_score > 0.4:
                severity = SeverityLevel.MEDIUM
            else:
                severity = SeverityLevel.LOW
            
            # Generate recommendations
            recommendations = self._generate_failure_recommendations(metrics, risk_score)
            
            result = PredictionResult(
                prediction_type=PredictionType.FAILURE,
                severity=severity,
                confidence=risk_score,
                predicted_timestamp=datetime.now() + time_horizon,
                time_horizon=time_horizon,
                features_used=features,
                explanation="; ".join(explanations) if explanations else "No immediate risk indicators",
                recommended_actions=recommendations
            )
            
            self.prediction_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in failure prediction: {e}")
            return PredictionResult(
                prediction_type=PredictionType.FAILURE,
                severity=SeverityLevel.LOW,
                confidence=0.0,
                explanation=f"Error in prediction: {str(e)}"
            )
    
    async def forecast_performance(
        self,
        metric_name: str,
        historical_data: List[Tuple[datetime, float]],
        forecast_hours: int = 24
    ) -> PerformanceForecast:
        """Forecast performance metrics"""
        try:
            if len(historical_data) < 10:
                raise ValueError("Insufficient historical data for forecasting")
            
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
            
            # Prepare training data
            X = df[['hour', 'day_of_week', 'time_since_start']].values
            y = df['value'].values
            
            # Train model
            model = self.forecast_models['linear_regression']
            model.fit(X, y)
            
            # Generate forecast
            last_timestamp = timestamps[-1]
            forecast_timestamps = []
            forecast_values = []
            confidence_intervals = []
            
            for i in range(1, forecast_hours + 1):
                future_time = last_timestamp + timedelta(hours=i)
                future_hour = future_time.hour
                future_dow = future_time.weekday()
                future_time_since = (future_time - timestamps[0]).total_seconds()
                
                X_future = np.array([[future_hour, future_dow, future_time_since]])
                prediction = model.predict(X_future)[0]
                
                forecast_timestamps.append(future_time)
                forecast_values.append(prediction)
                
                # Simple confidence interval (placeholder)
                std_error = np.std(y) * 0.1
                confidence_intervals.append((
                    prediction - 1.96 * std_error,
                    prediction + 1.96 * std_error
                ))
            
            # Calculate trend
            if len(forecast_values) > 1:
                trend_slope = (forecast_values[-1] - forecast_values[0]) / len(forecast_values)
                if trend_slope > 0.1:
                    trend = "increasing"
                elif trend_slope < -0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            # Calculate R-squared
            y_pred = model.predict(X)
            r_squared = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
            
            return PerformanceForecast(
                metric_name=metric_name,
                current_value=values[-1],
                predicted_values=forecast_values,
                timestamps=forecast_timestamps,
                confidence_intervals=confidence_intervals,
                trend=trend,
                r_squared=max(0, min(1, r_squared)),
                metadata={'model_used': 'linear_regression'}
            )
            
        except Exception as e:
            logger.error(f"Error in performance forecasting: {e}")
            # Return dummy forecast
            return PerformanceForecast(
                metric_name=metric_name,
                current_value=0.0,
                predicted_values=[0.0] * forecast_hours,
                timestamps=[datetime.now() + timedelta(hours=i) for i in range(1, forecast_hours + 1)],
                confidence_intervals=[(0.0, 0.0)] * forecast_hours,
                trend="stable",
                r_squared=0.0,
                metadata={'error': str(e)}
            )
    
    async def predict_capacity_exhaustion(
        self,
        resource_usage: Dict[str, float],
        growth_rates: Dict[str, float],
        time_horizon: timedelta = timedelta(days=7)
    ) -> PredictionResult:
        """Predict when resources will be exhausted"""
        try:
            exhaustion_predictions = {}
            explanations = []
            
            for resource, current_usage in resource_usage.items():
                if resource in growth_rates:
                    growth_rate = growth_rates[resource]
                    if growth_rate > 0:
                        # Calculate time to exhaustion
                        remaining_capacity = 1.0 - current_usage
                        if remaining_capacity > 0:
                            time_to_exhaustion = remaining_capacity / growth_rate
                            exhaustion_predictions[resource] = time_to_exhaustion
                            
                            if time_to_exhaustion <= time_horizon.total_seconds() / 3600:  # Convert to hours
                                explanations.append(
                                    f"{resource} will be exhausted in {time_to_exhaustion:.1f} hours"
                                )
            
            if not exhaustion_predictions:
                return PredictionResult(
                    prediction_type=PredictionType.CAPACITY_EXHAUSTION,
                    severity=SeverityLevel.LOW,
                    confidence=0.0,
                    explanation="No capacity exhaustion predicted within time horizon"
                )
            
            # Find the most critical resource
            most_critical = min(exhaustion_predictions.items(), key=lambda x: x[1])
            critical_resource, time_to_exhaustion = most_critical
            
            # Determine severity
            if time_to_exhaustion < 24:  # Less than 1 day
                severity = SeverityLevel.CRITICAL
            elif time_to_exhaustion < 72:  # Less than 3 days
                severity = SeverityLevel.HIGH
            elif time_to_exhaustion < 168:  # Less than 1 week
                severity = SeverityLevel.MEDIUM
            else:
                severity = SeverityLevel.LOW
            
            # Generate recommendations
            recommendations = [
                f"Scale up {critical_resource} capacity immediately",
                "Implement resource monitoring alerts",
                "Consider horizontal scaling strategies"
            ]
            
            return PredictionResult(
                prediction_type=PredictionType.CAPACITY_EXHAUSTION,
                severity=severity,
                confidence=0.8,
                predicted_timestamp=datetime.now() + timedelta(hours=time_to_exhaustion),
                time_horizon=time_horizon,
                features_used=list(resource_usage.keys()),
                explanation="; ".join(explanations),
                recommended_actions=recommendations,
                metadata={'exhaustion_times': exhaustion_predictions}
            )
            
        except Exception as e:
            logger.error(f"Error in capacity exhaustion prediction: {e}")
            return PredictionResult(
                prediction_type=PredictionType.CAPACITY_EXHAUSTION,
                severity=SeverityLevel.LOW,
                confidence=0.0,
                explanation=f"Error in prediction: {str(e)}"
            )
    
    def _generate_anomaly_explanation(
        self,
        is_anomaly: bool,
        anomaly_score: float,
        features: List[str]
    ) -> str:
        """Generate human-readable explanation for anomaly detection"""
        if not is_anomaly:
            return "No anomalies detected in the data"
        
        if anomaly_score > 0.8:
            return f"High-confidence anomaly detected (score: {anomaly_score:.2f}) in features: {', '.join(features)}"
        elif anomaly_score > 0.5:
            return f"Medium-confidence anomaly detected (score: {anomaly_score:.2f}) in features: {', '.join(features)}"
        else:
            return f"Low-confidence anomaly detected (score: {anomaly_score:.2f}) in features: {', '.join(features)}"
    
    def _generate_failure_recommendations(
        self,
        metrics: Dict[str, float],
        risk_score: float
    ) -> List[str]:
        """Generate recommendations based on failure prediction"""
        recommendations = []
        
        if metrics.get('cpu_usage', 0) > 0.8:
            recommendations.append("Scale up CPU resources or optimize CPU-intensive operations")
        
        if metrics.get('memory_usage', 0) > 0.8:
            recommendations.append("Increase memory allocation or optimize memory usage")
        
        if metrics.get('disk_usage', 0) > 0.8:
            recommendations.append("Clean up disk space or expand storage capacity")
        
        if metrics.get('error_rate', 0) > 0.05:
            recommendations.append("Investigate and fix error sources")
        
        if metrics.get('response_time', 0) > 2.0:
            recommendations.append("Optimize response time or scale horizontally")
        
        if risk_score > 0.7:
            recommendations.append("Implement immediate monitoring and alerting")
            recommendations.append("Prepare rollback procedures")
        
        return recommendations
    
    async def train_models(self, training_data: Dict[str, List[Tuple[datetime, float]]]):
        """Train ML models with historical data"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("Cannot train models without scikit-learn")
                return
            
            with self.lock:
                for metric_name, data in training_data.items():
                    if len(data) < 10:
                        continue
                    
                    # Prepare data
                    timestamps = [item[0] for item in data]
                    values = [item[1] for item in data]
                    
                    df = pd.DataFrame({
                        'timestamp': timestamps,
                        'value': values
                    })
                    df = df.sort_values('timestamp')
                    
                    # Generate features
                    df['hour'] = df['timestamp'].dt.hour
                    df['day_of_week'] = df['timestamp'].dt.dayofweek
                    df['time_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
                    
                    X = df[['hour', 'day_of_week', 'time_since_start']].values
                    y = df['value'].values
                    
                    # Train forecasting models
                    for model_name, model in self.forecast_models.items():
                        try:
                            model.fit(X, y)
                            logger.info(f"Trained {model_name} for {metric_name}")
                        except Exception as e:
                            logger.error(f"Error training {model_name} for {metric_name}: {e}")
                    
                    # Train anomaly detection models
                    for model_name, model in self.anomaly_detectors.items():
                        try:
                            if model_name == 'isolation_forest':
                                model.fit(X)
                                logger.info(f"Trained {model_name} for {metric_name}")
                        except Exception as e:
                            logger.error(f"Error training {model_name} for {metric_name}: {e}")
            
            logger.info("Model training completed")
            
        except Exception as e:
            logger.error(f"Error in model training: {e}")
    
    def get_prediction_history(self, limit: int = 100) -> List[PredictionResult]:
        """Get recent prediction history"""
        with self.lock:
            return list(self.prediction_history)[-limit:]
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for trained models"""
        performance = {}
        
        for model_name, model in self.forecast_models.items():
            try:
                if hasattr(model, 'score'):
                    performance[model_name] = {
                        'type': 'forecast',
                        'score': getattr(model, 'score', lambda x, y: 0.0)([], []),
                        'trained': True
                    }
                else:
                    performance[model_name] = {
                        'type': 'forecast',
                        'score': 0.0,
                        'trained': False
                    }
            except Exception as e:
                performance[model_name] = {
                    'type': 'forecast',
                    'score': 0.0,
                    'trained': False,
                    'error': str(e)
                }
        
        return performance


class PredictiveMonitor:
    """Main predictive monitoring orchestrator"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.analytics_engine = PredictiveAnalyticsEngine(config)
        self.monitoring_active = False
        self.monitor_task = None
        self.alert_callbacks = []
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
    
    async def start_monitoring(self, interval: float = 60.0):
        """Start predictive monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
        logger.info("Predictive monitoring started")
    
    async def stop_monitoring(self):
        """Stop predictive monitoring"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Predictive monitoring stopped")
    
    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._run_predictive_analysis()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _run_predictive_analysis(self):
        """Run comprehensive predictive analysis"""
        try:
            # Get current metrics
            current_metrics = await self._collect_current_metrics()
            
            # Run anomaly detection
            if current_metrics:
                features = list(current_metrics.keys())
                values = np.array(list(current_metrics.values())).reshape(1, -1)
                
                anomaly_result = await self.analytics_engine.predict_anomaly(
                    values, features
                )
                
                if anomaly_result.is_anomaly:
                    await self._handle_anomaly(anomaly_result)
            
            # Run failure prediction
            failure_prediction = await self.analytics_engine.predict_failure(
                current_metrics
            )
            
            if failure_prediction.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                await self._handle_failure_prediction(failure_prediction)
            
            # Run capacity planning
            capacity_prediction = await self.analytics_engine.predict_capacity_exhaustion(
                current_metrics,
                await self._calculate_growth_rates()
            )
            
            if capacity_prediction.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                await self._handle_capacity_prediction(capacity_prediction)
            
        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
    
    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        # This would typically integrate with actual monitoring systems
        # For now, return simulated metrics
        return {
            'cpu_usage': np.random.uniform(0.1, 0.9),
            'memory_usage': np.random.uniform(0.2, 0.8),
            'disk_usage': np.random.uniform(0.3, 0.7),
            'error_rate': np.random.uniform(0.0, 0.1),
            'response_time': np.random.uniform(0.5, 3.0),
            'throughput': np.random.uniform(100, 1000)
        }
    
    async def _calculate_growth_rates(self) -> Dict[str, float]:
        """Calculate growth rates for different metrics"""
        growth_rates = {}
        
        for metric_name, buffer in self.metrics_buffer.items():
            if len(buffer) > 10:
                values = list(buffer)
                # Simple linear growth rate calculation
                x = np.arange(len(values))
                y = np.array(values)
                
                if len(y) > 1:
                    slope = np.polyfit(x, y, 1)[0]
                    growth_rates[metric_name] = max(0, slope)  # Only positive growth
        
        return growth_rates
    
    async def _handle_anomaly(self, anomaly_result: AnomalyDetectionResult):
        """Handle detected anomalies"""
        logger.warning(f"Anomaly detected: {anomaly_result.explanation}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback('anomaly', anomaly_result)
            except Exception as e:
                logger.error(f"Error in anomaly alert callback: {e}")
    
    async def _handle_failure_prediction(self, prediction: PredictionResult):
        """Handle failure predictions"""
        logger.warning(f"Failure prediction: {prediction.explanation}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback('failure_prediction', prediction)
            except Exception as e:
                logger.error(f"Error in failure prediction callback: {e}")
    
    async def _handle_capacity_prediction(self, prediction: PredictionResult):
        """Handle capacity predictions"""
        logger.warning(f"Capacity prediction: {prediction.explanation}")
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback('capacity_prediction', prediction)
            except Exception as e:
                logger.error(f"Error in capacity prediction callback: {e}")
    
    def add_alert_callback(self, callback):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a metric for analysis"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.metrics_buffer[metric_name].append((timestamp, value))
    
    async def get_forecast(
        self,
        metric_name: str,
        hours: int = 24
    ) -> Optional[PerformanceForecast]:
        """Get performance forecast for a metric"""
        try:
            with self.lock:
                if metric_name not in self.metrics_buffer:
                    return None
                
                historical_data = list(self.metrics_buffer[metric_name])
            
            if len(historical_data) < 10:
                return None
            
            return await self.analytics_engine.forecast_performance(
                metric_name, historical_data, hours
            )
            
        except Exception as e:
            logger.error(f"Error getting forecast for {metric_name}: {e}")
            return None
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'monitoring_active': self.monitoring_active,
            'metrics_tracked': list(self.metrics_buffer.keys()),
            'buffer_sizes': {
                name: len(buffer) for name, buffer in self.metrics_buffer.items()
            },
            'model_performance': self.analytics_engine.get_model_performance(),
            'recent_predictions': len(self.analytics_engine.get_prediction_history())
        }
