"""
Advanced Anomaly Detection Module

This module implements sophisticated anomaly detection algorithms for:
- Real-time anomaly detection in streaming data
- Statistical anomaly detection methods
- Machine learning-based anomaly detection
- Time series anomaly detection
- Multi-dimensional anomaly detection

Author: SPIDER Development Team
Version: 1.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import warnings
from collections import defaultdict, deque
import threading
import time
import math

# Optional ML dependencies
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.svm import OneClassSVM
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.covariance import EllipticEnvelope
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Dummy classes for when sklearn is not available
    class IsolationForest:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([1] * len(args[0]))
        def decision_function(self, *args, **kwargs): return np.array([0.5] * len(args[0]))
    
    class RandomForestClassifier:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([0] * len(args[0]))
    
    class StandardScaler:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def transform(self, *args, **kwargs): return args[0]
        def fit_transform(self, *args, **kwargs): return args[0]
    
    class DBSCAN:
        def __init__(self, *args, **kwargs): pass
        def fit_predict(self, *args, **kwargs): return np.array([0] * len(args[0]))
    
    class KMeans:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([0] * len(args[0]))
    
    class OneClassSVM:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([1] * len(args[0]))
        def decision_function(self, *args, **kwargs): return np.array([0.5] * len(args[0]))
    
    class LocalOutlierFactor:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def fit_predict(self, *args, **kwargs): return np.array([1] * len(args[0]))
        def decision_function(self, *args, **kwargs): return np.array([0.5] * len(args[0]))
    
    class EllipticEnvelope:
        def __init__(self, *args, **kwargs): pass
        def fit(self, *args, **kwargs): return self
        def predict(self, *args, **kwargs): return np.array([1] * len(args[0]))
        def decision_function(self, *args, **kwargs): return np.array([0.5] * len(args[0]))

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    PATTERN = "pattern"
    CLUSTER = "cluster"
    DENSITY = "density"
    ISOLATION = "isolation"


class DetectionMethod(Enum):
    """Anomaly detection methods"""
    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    DBSCAN = "dbscan"
    ELLIPTIC_ENVELOPE = "elliptic_envelope"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ARIMA = "arima"


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    anomaly_score: float  # 0.0 to 1.0
    anomaly_type: AnomalyType
    detection_method: DetectionMethod
    features: List[str]
    explanation: str
    timestamp: datetime
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyPattern:
    """Detected anomaly pattern"""
    pattern_type: str
    frequency: float
    severity: float
    duration: timedelta
    affected_features: List[str]
    description: str


class StatisticalAnomalyDetector:
    """Statistical-based anomaly detection"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.z_score_threshold = self.config.get('z_score_threshold', 3.0)
        self.iqr_multiplier = self.config.get('iqr_multiplier', 1.5)
        self.window_size = self.config.get('window_size', 100)
        self.data_buffer = defaultdict(lambda: deque(maxlen=self.window_size))
        self.lock = threading.Lock()
    
    async def detect_z_score_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        threshold: Optional[float] = None
    ) -> AnomalyDetectionResult:
        """Detect anomalies using Z-score method"""
        try:
            threshold = threshold or self.z_score_threshold
            
            if len(data) == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.STATISTICAL,
                    detection_method=DetectionMethod.Z_SCORE,
                    features=features,
                    explanation="No data provided",
                    timestamp=datetime.now()
                )
            
            # Calculate Z-scores
            mean = np.mean(data)
            std = np.std(data)
            
            if std == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.STATISTICAL,
                    detection_method=DetectionMethod.Z_SCORE,
                    features=features,
                    explanation="No variance in data",
                    timestamp=datetime.now()
                )
            
            z_scores = np.abs((data - mean) / std)
            max_z_score = np.max(z_scores)
            is_anomaly = bool(max_z_score > threshold)
            
            # Calculate anomaly score
            anomaly_score = float(min(float(max_z_score) / float(threshold), 1.0))
            
            # Find anomalous features
            anomalous_features = []
            for i, z_score in enumerate(z_scores):
                if z_score > threshold and i < len(features):
                    anomalous_features.append(features[i])
            
            explanation = self._generate_z_score_explanation(
                max_z_score, threshold, anomalous_features
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.Z_SCORE,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(min(anomaly_score, 1.0)),
                metadata={
                    'z_scores': z_scores.tolist(),
                    'mean': float(mean),
                    'std': float(std),
                    'threshold': float(threshold)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Z-score anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.Z_SCORE,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def detect_iqr_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        multiplier: Optional[float] = None
    ) -> AnomalyDetectionResult:
        """Detect anomalies using Interquartile Range (IQR) method"""
        try:
            multiplier = multiplier or self.iqr_multiplier
            
            if len(data) == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.STATISTICAL,
                    detection_method=DetectionMethod.IQR,
                    features=features,
                    explanation="No data provided",
                    timestamp=datetime.now()
                )
            
            # Calculate IQR
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            
            if iqr == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.STATISTICAL,
                    detection_method=DetectionMethod.IQR,
                    features=features,
                    explanation="No variance in data (IQR = 0)",
                    timestamp=datetime.now()
                )
            
            # Calculate bounds
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            
            # Find anomalies
            anomalies = (data < lower_bound) | (data > upper_bound)
            is_anomaly = bool(np.any(anomalies))
            
            # Calculate anomaly score
            if is_anomaly:
                max_deviation = 0
                for value in data:
                    if value < lower_bound:
                        deviation = (lower_bound - value) / iqr
                    elif value > upper_bound:
                        deviation = (value - upper_bound) / iqr
                    else:
                        deviation = 0
                    max_deviation = max(max_deviation, deviation)
                anomaly_score = float(min(float(max_deviation) / float(multiplier), 1.0))
            else:
                anomaly_score = 0.0
            
            # Find anomalous features
            anomalous_features = []
            for i, is_anomalous in enumerate(anomalies):
                if is_anomalous and i < len(features):
                    anomalous_features.append(features[i])
            
            explanation = self._generate_iqr_explanation(
                q1, q3, iqr, lower_bound, upper_bound, anomalous_features
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.IQR,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(min(anomaly_score, 1.0)),
                metadata={
                    'q1': float(q1),
                    'q3': float(q3),
                    'iqr': float(iqr),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'multiplier': float(multiplier)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in IQR anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.IQR,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _generate_z_score_explanation(
        self,
        max_z_score: float,
        threshold: float,
        anomalous_features: List[str]
    ) -> str:
        """Generate explanation for Z-score anomaly detection"""
        if max_z_score <= threshold:
            return f"No anomalies detected (max Z-score: {max_z_score:.2f} <= {threshold})"
        
        if anomalous_features:
            return f"Anomaly detected in {len(anomalous_features)} features: {', '.join(anomalous_features)} (max Z-score: {max_z_score:.2f} > {threshold})"
        else:
            return f"Anomaly detected (max Z-score: {max_z_score:.2f} > {threshold})"
    
    def _generate_iqr_explanation(
        self,
        q1: float,
        q3: float,
        iqr: float,
        lower_bound: float,
        upper_bound: float,
        anomalous_features: List[str]
    ) -> str:
        """Generate explanation for IQR anomaly detection"""
        if not anomalous_features:
            return f"No anomalies detected (data within bounds: [{lower_bound:.2f}, {upper_bound:.2f}])"
        
        return f"Anomaly detected in {len(anomalous_features)} features: {', '.join(anomalous_features)} (outside IQR bounds: [{lower_bound:.2f}, {upper_bound:.2f}])"


class MLAnomalyDetector:
    """Machine learning-based anomaly detection"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models = {}
        self.scalers = {}
        self.training_data = defaultdict(list)
        self.lock = threading.Lock()
        
        if SKLEARN_AVAILABLE:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for anomaly detection"""
        self.models = {
            'isolation_forest': IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            ),
            'one_class_svm': OneClassSVM(
                nu=0.1,
                kernel='rbf',
                gamma='scale'
            ),
            'local_outlier_factor': LocalOutlierFactor(
                n_neighbors=20,
                contamination=0.1
            ),
            'dbscan': DBSCAN(
                eps=0.5,
                min_samples=5
            ),
            'elliptic_envelope': EllipticEnvelope(
                contamination=0.1,
                random_state=42
            )
        }
        
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler()
        }
    
    async def detect_isolation_forest_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        contamination: float = 0.1
    ) -> AnomalyDetectionResult:
        """Detect anomalies using Isolation Forest"""
        try:
            if not SKLEARN_AVAILABLE:
                return self._dummy_anomaly_result(features, DetectionMethod.ISOLATION_FOREST)
            
            # Ensure data is 2D
            if data.ndim == 1:
                data = data.reshape(1, -1)
            
            # Scale data
            scaler = self.scalers['standard']
            data_scaled = scaler.fit_transform(data)
            
            # Train model if not already trained
            model_key = f'isolation_forest_{contamination}'
            if model_key not in self.models:
                self.models[model_key] = IsolationForest(
                    contamination=contamination,
                    random_state=42
                )
            
            model = self.models[model_key]
            
            # For single data point, we need historical data to train
            if len(self.training_data[tuple(features)]) < 10:
                # Use dummy training data
                dummy_data = np.random.normal(0, 1, (100, len(features)))
                model.fit(dummy_data)
            else:
                # Use historical data
                historical_data = np.array(self.training_data[tuple(features)])
                model.fit(historical_data)
            
            # Predict anomaly
            predictions = model.predict(data_scaled)
            anomaly_scores = model.decision_function(data_scaled)
            
            is_anomaly = bool(predictions[0] == -1)
            anomaly_score = float(abs(anomaly_scores[0]))
            
            # Normalize anomaly score
            anomaly_score = float(min(anomaly_score, 1.0))
            
            explanation = self._generate_ml_explanation(
                'Isolation Forest', is_anomaly, anomaly_score, features
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.ISOLATION,
                detection_method=DetectionMethod.ISOLATION_FOREST,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(anomaly_score),
                metadata={
                    'contamination': float(contamination),
                    'model_type': 'Isolation Forest'
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Isolation Forest anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.ISOLATION,
                detection_method=DetectionMethod.ISOLATION_FOREST,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def detect_one_class_svm_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        nu: float = 0.1
    ) -> AnomalyDetectionResult:
        """Detect anomalies using One-Class SVM"""
        try:
            if not SKLEARN_AVAILABLE:
                return self._dummy_anomaly_result(features, DetectionMethod.ONE_CLASS_SVM)
            
            # Ensure data is 2D
            if data.ndim == 1:
                data = data.reshape(1, -1)
            
            # Scale data
            scaler = self.scalers['standard']
            data_scaled = scaler.fit_transform(data)
            
            # Train model
            model = self.models['one_class_svm']
            model.nu = nu
            
            # For single data point, we need historical data to train
            if len(self.training_data[tuple(features)]) < 10:
                # Use dummy training data
                dummy_data = np.random.normal(0, 1, (100, len(features)))
                model.fit(dummy_data)
            else:
                # Use historical data
                historical_data = np.array(self.training_data[tuple(features)])
                model.fit(historical_data)
            
            # Predict anomaly
            predictions = model.predict(data_scaled)
            anomaly_scores = model.decision_function(data_scaled)
            
            is_anomaly = bool(predictions[0] == -1)
            anomaly_score = float(abs(anomaly_scores[0]))
            
            # Normalize anomaly score
            anomaly_score = float(min(anomaly_score, 1.0))
            
            explanation = self._generate_ml_explanation(
                'One-Class SVM', is_anomaly, anomaly_score, features
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.ISOLATION,
                detection_method=DetectionMethod.ONE_CLASS_SVM,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(anomaly_score),
                metadata={
                    'nu': float(nu),
                    'model_type': 'One-Class SVM'
                }
            )
            
        except Exception as e:
            logger.error(f"Error in One-Class SVM anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.ISOLATION,
                detection_method=DetectionMethod.ONE_CLASS_SVM,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def detect_local_outlier_factor_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        n_neighbors: int = 20
    ) -> AnomalyDetectionResult:
        """Detect anomalies using Local Outlier Factor"""
        try:
            if not SKLEARN_AVAILABLE:
                return self._dummy_anomaly_result(features, DetectionMethod.LOCAL_OUTLIER_FACTOR)
            
            # Ensure data is 2D
            if data.ndim == 1:
                data = data.reshape(1, -1)
            
            # Scale data
            scaler = self.scalers['standard']
            data_scaled = scaler.fit_transform(data)
            
            # Train model
            model = self.models['local_outlier_factor']
            model.n_neighbors = n_neighbors
            
            # For single data point, we need historical data to train
            if len(self.training_data[tuple(features)]) < 10:
                # Use dummy training data
                dummy_data = np.random.normal(0, 1, (100, len(features)))
                # Combine training data with current data for prediction
                combined_data = np.vstack([dummy_data, data_scaled])
                predictions = model.fit_predict(combined_data)
                anomaly_scores = model.decision_function(combined_data)
            else:
                # Use historical data
                historical_data = np.array(self.training_data[tuple(features)])
                # Combine historical data with current data for prediction
                combined_data = np.vstack([historical_data, data_scaled])
                predictions = model.fit_predict(combined_data)
                anomaly_scores = model.decision_function(combined_data)
            
            # Get prediction for the last data point (current data)
            predictions = predictions[-1:]  # Only the last prediction
            anomaly_scores = anomaly_scores[-1:]  # Only the last score
            
            is_anomaly = bool(predictions[0] == -1)
            anomaly_score = float(abs(anomaly_scores[0]))
            
            # Normalize anomaly score
            anomaly_score = float(min(anomaly_score, 1.0))
            
            explanation = self._generate_ml_explanation(
                'Local Outlier Factor', is_anomaly, anomaly_score, features
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.DENSITY,
                detection_method=DetectionMethod.LOCAL_OUTLIER_FACTOR,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(anomaly_score),
                metadata={
                    'n_neighbors': int(n_neighbors),
                    'model_type': 'Local Outlier Factor'
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Local Outlier Factor anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.DENSITY,
                detection_method=DetectionMethod.LOCAL_OUTLIER_FACTOR,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _dummy_anomaly_result(
        self,
        features: List[str],
        method: DetectionMethod
    ) -> AnomalyDetectionResult:
        """Return dummy result when ML libraries are not available"""
        return AnomalyDetectionResult(
            is_anomaly=False,
            anomaly_score=0.0,
            anomaly_type=AnomalyType.STATISTICAL,
            detection_method=method,
            features=features,
            explanation="ML libraries not available, using dummy result",
            timestamp=datetime.now()
        )
    
    def _generate_ml_explanation(
        self,
        model_name: str,
        is_anomaly: bool,
        anomaly_score: float,
        features: List[str]
    ) -> str:
        """Generate explanation for ML-based anomaly detection"""
        if not is_anomaly:
            return f"No anomalies detected using {model_name} (score: {anomaly_score:.2f})"
        
        return f"Anomaly detected using {model_name} in features: {', '.join(features)} (score: {anomaly_score:.2f})"
    
    def add_training_data(self, features: List[str], data: np.ndarray):
        """Add training data for ML models"""
        with self.lock:
            self.training_data[tuple(features)].extend(data.tolist())


class TimeSeriesAnomalyDetector:
    """Time series specific anomaly detection"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.window_size = self.config.get('window_size', 50)
        self.smoothing_factor = self.config.get('smoothing_factor', 0.3)
        self.data_buffer = defaultdict(lambda: deque(maxlen=self.window_size))
        self.lock = threading.Lock()
    
    async def detect_moving_average_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        window_size: Optional[int] = None
    ) -> AnomalyDetectionResult:
        """Detect anomalies using moving average method"""
        try:
            window_size = window_size or self.window_size
            
            if len(data) == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.TEMPORAL,
                    detection_method=DetectionMethod.MOVING_AVERAGE,
                    features=features,
                    explanation="No data provided",
                    timestamp=datetime.now()
                )
            
            # Calculate moving average
            if len(data) < window_size:
                # Not enough data for moving average
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.TEMPORAL,
                    detection_method=DetectionMethod.MOVING_AVERAGE,
                    features=features,
                    explanation=f"Insufficient data for moving average (need {window_size}, got {len(data)})",
                    timestamp=datetime.now()
                )
            
            # Calculate moving average and standard deviation
            moving_avg = np.mean(data[-window_size:])
            moving_std = np.std(data[-window_size:])
            
            if moving_std == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.TEMPORAL,
                    detection_method=DetectionMethod.MOVING_AVERAGE,
                    features=features,
                    explanation="No variance in moving window",
                    timestamp=datetime.now()
                )
            
            # Check current value against moving average
            current_value = data[-1]
            z_score = abs(current_value - moving_avg) / moving_std
            
            is_anomaly = bool(z_score > 2.0)  # 2-sigma threshold
            anomaly_score = float(min(z_score / 2.0, 1.0))
            
            explanation = self._generate_moving_average_explanation(
                current_value, moving_avg, moving_std, z_score, is_anomaly
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.TEMPORAL,
                detection_method=DetectionMethod.MOVING_AVERAGE,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(anomaly_score),
                metadata={
                    'window_size': int(window_size),
                    'moving_avg': float(moving_avg),
                    'moving_std': float(moving_std),
                    'z_score': float(z_score)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in moving average anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.TEMPORAL,
                detection_method=DetectionMethod.MOVING_AVERAGE,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def detect_exponential_smoothing_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        alpha: Optional[float] = None
    ) -> AnomalyDetectionResult:
        """Detect anomalies using exponential smoothing"""
        try:
            alpha = alpha or self.smoothing_factor
            
            if len(data) == 0:
                return AnomalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=AnomalyType.TEMPORAL,
                    detection_method=DetectionMethod.EXPONENTIAL_SMOOTHING,
                    features=features,
                    explanation="No data provided",
                    timestamp=datetime.now()
                )
            
            # Calculate exponential smoothing
            smoothed_values = []
            smoothed_values.append(data[0])
            
            for i in range(1, len(data)):
                smoothed = alpha * data[i] + (1 - alpha) * smoothed_values[i-1]
                smoothed_values.append(smoothed)
            
            # Calculate prediction error
            current_value = data[-1]
            predicted_value = smoothed_values[-2] if len(smoothed_values) > 1 else data[0]
            error = abs(current_value - predicted_value)
            
            # Calculate error threshold based on historical errors
            if len(data) > 1:
                historical_errors = []
                for i in range(1, len(data)):
                    hist_error = abs(data[i] - smoothed_values[i-1])
                    historical_errors.append(hist_error)
                
                error_threshold = np.mean(historical_errors) + 2 * np.std(historical_errors)
            else:
                error_threshold = abs(data[0]) * 0.1  # 10% of first value
            
            is_anomaly = bool(error > error_threshold)
            anomaly_score = float(min(error / error_threshold, 1.0)) if error_threshold > 0 else 0.0
            
            explanation = self._generate_exponential_smoothing_explanation(
                current_value, predicted_value, error, error_threshold, is_anomaly
            )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=AnomalyType.TEMPORAL,
                detection_method=DetectionMethod.EXPONENTIAL_SMOOTHING,
                features=features,
                explanation=explanation,
                timestamp=datetime.now(),
                confidence=float(anomaly_score),
                metadata={
                    'alpha': float(alpha),
                    'predicted_value': float(predicted_value),
                    'error': float(error),
                    'error_threshold': float(error_threshold)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in exponential smoothing anomaly detection: {e}")
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.TEMPORAL,
                detection_method=DetectionMethod.EXPONENTIAL_SMOOTHING,
                features=features,
                explanation=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _generate_moving_average_explanation(
        self,
        current_value: float,
        moving_avg: float,
        moving_std: float,
        z_score: float,
        is_anomaly: bool
    ) -> str:
        """Generate explanation for moving average anomaly detection"""
        if not is_anomaly:
            return f"Value {current_value:.2f} is within normal range (avg: {moving_avg:.2f}, std: {moving_std:.2f}, z-score: {z_score:.2f})"
        
        return f"Value {current_value:.2f} is anomalous (avg: {moving_avg:.2f}, std: {moving_std:.2f}, z-score: {z_score:.2f})"
    
    def _generate_exponential_smoothing_explanation(
        self,
        current_value: float,
        predicted_value: float,
        error: float,
        error_threshold: float,
        is_anomaly: bool
    ) -> str:
        """Generate explanation for exponential smoothing anomaly detection"""
        if not is_anomaly:
            return f"Value {current_value:.2f} is within expected range (predicted: {predicted_value:.2f}, error: {error:.2f} <= {error_threshold:.2f})"
        
        return f"Value {current_value:.2f} is anomalous (predicted: {predicted_value:.2f}, error: {error:.2f} > {error_threshold:.2f})"


class AnomalyDetectionManager:
    """Main anomaly detection manager"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.statistical_detector = StatisticalAnomalyDetector(config)
        self.ml_detector = MLAnomalyDetector(config)
        self.timeseries_detector = TimeSeriesAnomalyDetector(config)
        self.detection_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    async def detect_anomalies(
        self,
        data: np.ndarray,
        features: List[str],
        methods: Optional[List[DetectionMethod]] = None
    ) -> List[AnomalyDetectionResult]:
        """Detect anomalies using multiple methods"""
        if methods is None:
            methods = [
                DetectionMethod.Z_SCORE,
                DetectionMethod.IQR,
                DetectionMethod.ISOLATION_FOREST,
                DetectionMethod.MOVING_AVERAGE
            ]
        
        results = []
        
        for method in methods:
            try:
                if method == DetectionMethod.Z_SCORE:
                    result = await self.statistical_detector.detect_z_score_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.IQR:
                    result = await self.statistical_detector.detect_iqr_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.ISOLATION_FOREST:
                    result = await self.ml_detector.detect_isolation_forest_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.ONE_CLASS_SVM:
                    result = await self.ml_detector.detect_one_class_svm_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.LOCAL_OUTLIER_FACTOR:
                    result = await self.ml_detector.detect_local_outlier_factor_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.MOVING_AVERAGE:
                    result = await self.timeseries_detector.detect_moving_average_anomaly(
                        data, features
                    )
                elif method == DetectionMethod.EXPONENTIAL_SMOOTHING:
                    result = await self.timeseries_detector.detect_exponential_smoothing_anomaly(
                        data, features
                    )
                else:
                    continue
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error in {method.value} anomaly detection: {e}")
                continue
        
        # Store results
        with self.lock:
            self.detection_history.extend(results)
        
        return results
    
    async def get_consensus_anomaly(
        self,
        data: np.ndarray,
        features: List[str],
        methods: Optional[List[DetectionMethod]] = None,
        threshold: float = 0.5
    ) -> AnomalyDetectionResult:
        """Get consensus anomaly detection result"""
        results = await self.detect_anomalies(data, features, methods)
        
        if not results:
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=AnomalyType.STATISTICAL,
                detection_method=DetectionMethod.Z_SCORE,
                features=features,
                explanation="No detection methods available",
                timestamp=datetime.now()
            )
        
        # Calculate consensus
        anomaly_votes = sum(1 for r in results if r.is_anomaly)
        total_votes = len(results)
        consensus_score = anomaly_votes / total_votes
        
        # Calculate average anomaly score
        avg_anomaly_score = float(np.mean([r.anomaly_score for r in results]))
        
        is_anomaly = bool(consensus_score >= threshold)
        
        # Find the most confident detection method
        best_result = max(results, key=lambda r: r.confidence)
        
        explanation = f"Consensus: {anomaly_votes}/{total_votes} methods detected anomaly (score: {consensus_score:.2f})"
        
        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=avg_anomaly_score,
            anomaly_type=best_result.anomaly_type,
            detection_method=best_result.detection_method,
            features=features,
            explanation=explanation,
            timestamp=datetime.now(),
            confidence=float(consensus_score),
            metadata={
                'consensus_score': float(consensus_score),
                'total_methods': int(total_votes),
                'anomaly_votes': int(anomaly_votes),
                'individual_results': [
                    {
                        'method': r.detection_method.value,
                        'is_anomaly': bool(r.is_anomaly),
                        'score': float(r.anomaly_score)
                    } for r in results
                ]
            }
        )
    
    def get_detection_history(self, limit: int = 100) -> List[AnomalyDetectionResult]:
        """Get recent detection history"""
        with self.lock:
            return list(self.detection_history)[-limit:]
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        with self.lock:
            if not self.detection_history:
                return {
                    'total_detections': 0,
                    'anomaly_rate': 0.0,
                    'method_usage': {},
                    'feature_frequency': {}
                }
            
            total_detections = len(self.detection_history)
            anomaly_count = sum(1 for r in self.detection_history if r.is_anomaly)
            anomaly_rate = anomaly_count / total_detections
            
            # Method usage statistics
            method_usage = defaultdict(int)
            for result in self.detection_history:
                method_usage[result.detection_method.value] += 1
            
            # Feature frequency
            feature_frequency = defaultdict(int)
            for result in self.detection_history:
                for feature in result.features:
                    feature_frequency[feature] += 1
            
            return {
                'total_detections': total_detections,
                'anomaly_rate': anomaly_rate,
                'method_usage': dict(method_usage),
                'feature_frequency': dict(feature_frequency)
            }
