"""
Predictive Analytics

Advanced predictive analytics capabilities including forecasting,
anomaly detection, and trend analysis for the SPIDER framework.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

# Set up logger
logger = logging.getLogger(__name__)

# Optional imports for advanced analytics
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available. Some time series features will be limited.")

try:
    import prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Some forecasting features will be limited.")

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Anomaly type enumeration."""
    POINT = "point"
    CONTEXTUAL = "contextual"
    COLLECTIVE = "collective"
    TREND = "trend"
    SEASONAL = "seasonal"


class ForecastType(str, Enum):
    """Forecast type enumeration."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    ARIMA = "arima"
    PROPHET = "prophet"
    MACHINE_LEARNING = "machine_learning"


@dataclass
class AnomalyResult:
    """Anomaly detection result."""
    timestamp: datetime
    value: float
    anomaly_score: float
    is_anomaly: bool
    anomaly_type: AnomalyType
    confidence: float
    context: Dict[str, Any] = None


@dataclass
class ForecastResult:
    """Forecast result."""
    timestamp: datetime
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float
    model_type: ForecastType
    features_used: List[str] = None


@dataclass
class TrendResult:
    """Trend analysis result."""
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    trend_duration: int  # periods
    change_rate: float  # per period
    confidence: float
    seasonal_pattern: bool
    cyclical_pattern: bool


class AnomalyDetector:
    """Advanced anomaly detection using multiple algorithms."""
    
    def __init__(self, method: str = "isolation_forest"):
        """
        Initialize anomaly detector.
        
        Args:
            method: Detection method ("isolation_forest", "dbscan", "statistical", "ensemble")
        """
        self.method = method
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        if method == "isolation_forest":
            self.model = IsolationForest(contamination=0.1, random_state=42)
        elif method == "dbscan":
            self.model = DBSCAN(eps=0.5, min_samples=5)
        elif method == "statistical":
            self.model = None  # Statistical methods don't need a model
        elif method == "ensemble":
            self.models = {
                "isolation_forest": IsolationForest(contamination=0.1, random_state=42),
                "dbscan": DBSCAN(eps=0.5, min_samples=5)
            }
    
    def fit(self, data: Union[np.ndarray, pd.DataFrame], 
            features: List[str] = None) -> None:
        """
        Fit the anomaly detector.
        
        Args:
            data: Training data
            features: Feature columns (for DataFrame)
        """
        if isinstance(data, pd.DataFrame):
            if features:
                X = data[features].values
            else:
                X = data.select_dtypes(include=[np.number]).values
        else:
            X = data
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        if self.method == "ensemble":
            for model in self.models.values():
                if hasattr(model, 'fit'):
                    model.fit(X_scaled)
        elif self.model and hasattr(self.model, 'fit'):
            self.model.fit(X_scaled)
        
        self.is_fitted = True
    
    def detect_anomalies(self, data: Union[np.ndarray, pd.DataFrame], 
                        timestamps: List[datetime] = None,
                        features: List[str] = None,
                        threshold: float = 0.5) -> List[AnomalyResult]:
        """
        Detect anomalies in data.
        
        Args:
            data: Input data
            timestamps: Timestamps for time series data
            features: Feature columns (for DataFrame)
            threshold: Anomaly threshold
            
        Returns:
            List of anomaly results
        """
        if not self.is_fitted:
            self.fit(data, features)
        
        if isinstance(data, pd.DataFrame):
            if features:
                X = data[features].values
            else:
                X = data.select_dtypes(include=[np.number]).values
        else:
            X = data
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        anomalies = []
        
        if self.method == "ensemble":
            # Combine results from multiple models
            anomaly_scores = np.zeros(len(X))
            for model in self.models.values():
                if hasattr(model, 'decision_function'):
                    scores = model.decision_function(X_scaled)
                    anomaly_scores += scores
                elif hasattr(model, 'predict'):
                    predictions = model.predict(X_scaled)
                    anomaly_scores += (predictions == -1).astype(int)
            
            anomaly_scores /= len(self.models)
        elif self.method == "statistical":
            anomaly_scores = self._statistical_anomaly_detection(X_scaled)
        else:
            if hasattr(self.model, 'decision_function'):
                anomaly_scores = self.model.decision_function(X_scaled)
            elif hasattr(self.model, 'predict'):
                predictions = self.model.predict(X_scaled)
                anomaly_scores = (predictions == -1).astype(float)
            else:
                anomaly_scores = np.zeros(len(X))
        
        # Create anomaly results
        for i, score in enumerate(anomaly_scores):
            is_anomaly = score < threshold if self.method != "dbscan" else score == -1
            
            timestamp = timestamps[i] if timestamps and i < len(timestamps) else datetime.utcnow()
            value = X[i, 0] if X.shape[1] > 0 else 0.0
            
            anomalies.append(AnomalyResult(
                timestamp=timestamp,
                value=value,
                anomaly_score=float(score),
                is_anomaly=bool(is_anomaly),
                anomaly_type=self._classify_anomaly_type(score, X_scaled[i]),
                confidence=abs(score),
                context={"feature_values": X[i].tolist()}
            ))
        
        return anomalies
    
    def _statistical_anomaly_detection(self, X: np.ndarray) -> np.ndarray:
        """Statistical anomaly detection using Z-score and IQR."""
        scores = np.zeros(len(X))
        
        for i in range(X.shape[1]):
            feature = X[:, i]
            mean = np.mean(feature)
            std = np.std(feature)
            
            if std > 0:
                z_scores = np.abs((feature - mean) / std)
                scores += z_scores
        
        return scores / X.shape[1]
    
    def _classify_anomaly_type(self, score: float, features: np.ndarray) -> AnomalyType:
        """Classify the type of anomaly."""
        if score < -2:
            return AnomalyType.POINT
        elif score < -1:
            return AnomalyType.CONTEXTUAL
        else:
            return AnomalyType.COLLECTIVE


class ForecastingEngine:
    """Advanced forecasting engine using multiple algorithms."""
    
    def __init__(self, method: str = "linear"):
        """
        Initialize forecasting engine.
        
        Args:
            method: Forecasting method ("linear", "exponential", "arima", "prophet", "ml")
        """
        self.method = method
        self.model = None
        self.is_fitted = False
        self.feature_columns = []
        
        if method == "linear":
            self.model = LinearRegression()
        elif method == "ml":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    def fit(self, data: pd.DataFrame, 
            target_column: str,
            feature_columns: List[str] = None,
            time_column: str = None) -> None:
        """
        Fit the forecasting model.
        
        Args:
            data: Training data
            target_column: Target variable column
            feature_columns: Feature columns
            time_column: Time column for time series
        """
        if time_column and time_column in data.columns:
            data = data.sort_values(time_column)
        
        if feature_columns:
            self.feature_columns = feature_columns
            X = data[feature_columns].values
        else:
            # Use lagged values for time series
            self.feature_columns = [f"lag_{i}" for i in range(1, 4)]
            X = self._create_lagged_features(data[target_column].values)
        
        y = data[target_column].values
        
        if self.method == "arima" and STATSMODELS_AVAILABLE:
            self._fit_arima(data[target_column].values)
        elif self.method == "prophet" and PROPHET_AVAILABLE:
            self._fit_prophet(data, target_column, time_column)
        else:
            self.model.fit(X, y)
        
        self.is_fitted = True
    
    def _create_lagged_features(self, values: np.ndarray, lags: int = 3) -> np.ndarray:
        """Create lagged features for time series."""
        X = []
        for i in range(lags, len(values)):
            X.append(values[i-lags:i])
        return np.array(X)
    
    def _fit_arima(self, values: np.ndarray) -> None:
        """Fit ARIMA model."""
        try:
            self.model = ARIMA(values, order=(1, 1, 1))
            self.model = self.model.fit()
        except Exception as e:
            logger.warning(f"ARIMA fitting failed: {e}")
            self.model = None
    
    def _fit_prophet(self, data: pd.DataFrame, target_column: str, time_column: str) -> None:
        """Fit Prophet model."""
        try:
            from prophet import Prophet
            
            prophet_data = data[[time_column, target_column]].copy()
            prophet_data.columns = ['ds', 'y']
            
            self.model = Prophet()
            self.model.fit(prophet_data)
        except Exception as e:
            logger.warning(f"Prophet fitting failed: {e}")
            self.model = None
    
    def forecast(self, periods: int, 
                future_features: np.ndarray = None) -> List[ForecastResult]:
        """
        Generate forecasts.
        
        Args:
            periods: Number of periods to forecast
            future_features: Future feature values
            
        Returns:
            List of forecast results
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before forecasting")
        
        forecasts = []
        
        if self.method == "arima" and self.model:
            return self._arima_forecast(periods)
        elif self.method == "prophet" and self.model:
            return self._prophet_forecast(periods)
        else:
            return self._ml_forecast(periods, future_features)
    
    def _arima_forecast(self, periods: int) -> List[ForecastResult]:
        """ARIMA forecasting."""
        try:
            forecast = self.model.forecast(steps=periods)
            conf_int = self.model.get_forecast(steps=periods).conf_int()
            
            forecasts = []
            for i in range(periods):
                forecasts.append(ForecastResult(
                    timestamp=datetime.utcnow() + timedelta(days=i),
                    predicted_value=float(forecast.iloc[i]),
                    lower_bound=float(conf_int.iloc[i, 0]),
                    upper_bound=float(conf_int.iloc[i, 1]),
                    confidence=0.8,  # ARIMA doesn't provide confidence directly
                    model_type=ForecastType.ARIMA
                ))
            
            return forecasts
        except Exception as e:
            logger.error(f"ARIMA forecasting failed: {e}")
            return []
    
    def _prophet_forecast(self, periods: int) -> List[ForecastResult]:
        """Prophet forecasting."""
        try:
            future = self.model.make_future_dataframe(periods=periods)
            forecast = self.model.predict(future)
            
            forecasts = []
            for i in range(periods):
                idx = len(forecast) - periods + i
                forecasts.append(ForecastResult(
                    timestamp=forecast.iloc[idx]['ds'],
                    predicted_value=float(forecast.iloc[idx]['yhat']),
                    lower_bound=float(forecast.iloc[idx]['yhat_lower']),
                    upper_bound=float(forecast.iloc[idx]['yhat_upper']),
                    confidence=0.8,
                    model_type=ForecastType.PROPHET
                ))
            
            return forecasts
        except Exception as e:
            logger.error(f"Prophet forecasting failed: {e}")
            return []
    
    def _ml_forecast(self, periods: int, future_features: np.ndarray = None) -> List[ForecastResult]:
        """Machine learning forecasting."""
        if future_features is not None:
            X_future = future_features
        else:
            # Generate simple future features (zeros for now)
            X_future = np.zeros((periods, len(self.feature_columns)))
        
        predictions = self.model.predict(X_future)
        
        forecasts = []
        for i in range(periods):
            forecasts.append(ForecastResult(
                timestamp=datetime.utcnow() + timedelta(days=i),
                predicted_value=float(predictions[i]),
                lower_bound=float(predictions[i] * 0.9),  # Simple bounds
                upper_bound=float(predictions[i] * 1.1),
                confidence=0.7,
                model_type=ForecastType.MACHINE_LEARNING,
                features_used=self.feature_columns
            ))
        
        return forecasts


class TrendAnalyzer:
    """Trend analysis and pattern detection."""
    
    def __init__(self):
        """Initialize trend analyzer."""
        pass
    
    def analyze_trend(self, data: pd.Series, 
                     time_column: str = None,
                     window_size: int = 7) -> TrendResult:
        """
        Analyze trend in time series data.
        
        Args:
            data: Time series data
            time_column: Time column name
            window_size: Window size for trend calculation
            
        Returns:
            Trend analysis result
        """
        values = data.values if isinstance(data, pd.Series) else data
        
        # Calculate trend direction and strength
        trend_direction, trend_strength = self._calculate_trend(values, window_size)
        
        # Calculate change rate
        change_rate = self._calculate_change_rate(values)
        
        # Detect seasonal patterns
        seasonal_pattern = self._detect_seasonal_pattern(values)
        
        # Detect cyclical patterns
        cyclical_pattern = self._detect_cyclical_pattern(values)
        
        # Calculate trend duration
        trend_duration = self._calculate_trend_duration(values, window_size)
        
        # Calculate confidence
        confidence = self._calculate_confidence(values, trend_strength)
        
        return TrendResult(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_duration=trend_duration,
            change_rate=change_rate,
            confidence=confidence,
            seasonal_pattern=seasonal_pattern,
            cyclical_pattern=cyclical_pattern
        )
    
    def _calculate_trend(self, values: np.ndarray, window_size: int) -> Tuple[str, float]:
        """Calculate trend direction and strength."""
        if len(values) < window_size:
            return "stable", 0.0
        
        # Calculate moving average
        moving_avg = pd.Series(values).rolling(window=window_size).mean()
        
        # Calculate trend slope
        x = np.arange(len(moving_avg.dropna()))
        y = moving_avg.dropna().values
        
        if len(x) < 2:
            return "stable", 0.0
        
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize slope to 0-1 range
        trend_strength = min(abs(slope) / np.std(y), 1.0)
        
        if slope > 0.1:
            trend_direction = "increasing"
        elif slope < -0.1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        return trend_direction, trend_strength
    
    def _calculate_change_rate(self, values: np.ndarray) -> float:
        """Calculate rate of change."""
        if len(values) < 2:
            return 0.0
        
        return (values[-1] - values[0]) / values[0] if values[0] != 0 else 0.0
    
    def _detect_seasonal_pattern(self, values: np.ndarray) -> bool:
        """Detect seasonal patterns."""
        if len(values) < 12:  # Need at least 12 periods for seasonal detection
            return False
        
        try:
            if STATSMODELS_AVAILABLE:
                # Use seasonal decomposition
                decomposition = seasonal_decompose(values, model='additive', period=12)
                seasonal_strength = np.var(decomposition.seasonal) / np.var(values)
                return seasonal_strength > 0.1
            else:
                # Simple autocorrelation check
                autocorr = np.corrcoef(values[:-12], values[12:])[0, 1]
                return abs(autocorr) > 0.3
        except:
            return False
    
    def _detect_cyclical_pattern(self, values: np.ndarray) -> bool:
        """Detect cyclical patterns."""
        if len(values) < 20:
            return False
        
        # Check for cycles using autocorrelation
        autocorr_values = []
        for lag in range(1, min(20, len(values) // 2)):
            if len(values) > lag:
                corr = np.corrcoef(values[:-lag], values[lag:])[0, 1]
                autocorr_values.append(abs(corr))
        
        return max(autocorr_values) > 0.5 if autocorr_values else False
    
    def _calculate_trend_duration(self, values: np.ndarray, window_size: int) -> int:
        """Calculate trend duration in periods."""
        if len(values) < window_size:
            return len(values)
        
        moving_avg = pd.Series(values).rolling(window=window_size).mean()
        trend_changes = 0
        
        for i in range(1, len(moving_avg.dropna())):
            if (moving_avg.iloc[i] > moving_avg.iloc[i-1]) != (moving_avg.iloc[i-1] > moving_avg.iloc[i-2]):
                trend_changes += 1
        
        return len(values) - trend_changes
    
    def _calculate_confidence(self, values: np.ndarray, trend_strength: float) -> float:
        """Calculate confidence in trend analysis."""
        # Base confidence on trend strength and data quality
        data_quality = 1.0 - (np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0.0
        return min(trend_strength * data_quality, 1.0)


class PredictiveAnalytics:
    """Main predictive analytics processor combining all capabilities."""
    
    def __init__(self):
        """Initialize predictive analytics processor."""
        self.anomaly_detector = AnomalyDetector()
        self.forecasting_engine = ForecastingEngine()
        self.trend_analyzer = TrendAnalyzer()
    
    async def analyze_data(self, data: pd.DataFrame,
                          target_column: str,
                          time_column: str = None,
                          feature_columns: List[str] = None,
                          anomaly_detection: bool = True,
                          forecasting: bool = True,
                          trend_analysis: bool = True,
                          forecast_periods: int = 30) -> Dict[str, Any]:
        """
        Comprehensive data analysis.
        
        Args:
            data: Input data
            target_column: Target variable column
            time_column: Time column for time series
            feature_columns: Feature columns
            anomaly_detection: Whether to perform anomaly detection
            forecasting: Whether to generate forecasts
            trend_analysis: Whether to analyze trends
            forecast_periods: Number of periods to forecast
            
        Returns:
            Analysis results
        """
        results = {
            "data_info": {
                "rows": len(data),
                "columns": list(data.columns),
                "target_column": target_column,
                "time_column": time_column
            },
            "anomalies": [],
            "forecasts": [],
            "trend_analysis": None,
            "summary": {}
        }
        
        # Anomaly detection
        if anomaly_detection:
            try:
                self.anomaly_detector.fit(data, feature_columns)
                timestamps = data[time_column].tolist() if time_column else None
                results["anomalies"] = self.anomaly_detector.detect_anomalies(
                    data, timestamps, feature_columns
                )
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")
        
        # Forecasting
        if forecasting:
            try:
                self.forecasting_engine.fit(data, target_column, feature_columns, time_column)
                results["forecasts"] = self.forecasting_engine.forecast(forecast_periods)
            except Exception as e:
                logger.error(f"Forecasting failed: {e}")
        
        # Trend analysis
        if trend_analysis:
            try:
                target_data = data[target_column]
                results["trend_analysis"] = self.trend_analyzer.analyze_trend(target_data, time_column)
            except Exception as e:
                logger.error(f"Trend analysis failed: {e}")
        
        # Summary
        results["summary"] = self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary."""
        summary = {
            "total_anomalies": len(results.get("anomalies", [])),
            "anomaly_rate": 0.0,
            "forecast_available": len(results.get("forecasts", [])) > 0,
            "trend_direction": "unknown",
            "trend_strength": 0.0,
            "data_quality": "good"
        }
        
        # Anomaly rate
        if results.get("anomalies"):
            total_points = len(results["anomalies"])
            anomaly_count = sum(1 for a in results["anomalies"] if a.is_anomaly)
            summary["anomaly_rate"] = anomaly_count / total_points
        
        # Trend information
        if results.get("trend_analysis"):
            trend = results["trend_analysis"]
            summary["trend_direction"] = trend.trend_direction
            summary["trend_strength"] = trend.trend_strength
        
        return summary
    
    def get_available_methods(self) -> Dict[str, List[str]]:
        """Get available analysis methods."""
        return {
            "anomaly_detection": ["isolation_forest", "dbscan", "statistical", "ensemble"],
            "forecasting": ["linear", "exponential", "arima", "prophet", "ml"],
            "trend_analysis": ["moving_average", "linear_regression", "seasonal_decomposition"]
        }
