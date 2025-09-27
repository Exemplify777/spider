"""
AI-Powered Analytics and Insights

This module provides advanced AI-powered analytics and insights for the SPIDER Framework,
including predictive analytics, anomaly detection, trend analysis, and intelligent reporting.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
import pandas as pd
from pathlib import Path
import pickle
import joblib
from collections import defaultdict, deque

# Set up logger
logger = logging.getLogger(__name__)

# Analytics libraries
# scikit-learn is imported as sklearn
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
try:
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("Statsmodels not available. Some time series features will be limited.")
try:
    import prophet
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Some forecasting features will be limited.")

# Deep learning for analytics - optional imports
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Some deep learning features will be limited.")
if TORCH_AVAILABLE:
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Some deep learning features will be limited.")

# Visualization - optional imports
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available. Some visualization features will be limited.")

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("Seaborn not available. Some visualization features will be limited.")

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Some interactive visualization features will be limited.")
if PLOTLY_AVAILABLE:
    import plotly.express as px
    from plotly.subplots import make_subplots

# Time series analysis
import pandas as pd
from pandas.plotting import autocorrelation_plot

try:
    import scipy.stats as stats
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("SciPy not available. Some statistical features will be limited.")


class AnalyticsType(Enum):
    """Analytics types"""
    PREDICTIVE = "predictive"
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_ANALYSIS = "trend_analysis"
    CLUSTERING = "clustering"
    CORRELATION = "correlation"
    FORECASTING = "forecasting"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class InsightType(Enum):
    """Insight types"""
    PERFORMANCE = "performance"
    ANOMALY = "anomaly"
    TREND = "trend"
    PATTERN = "pattern"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"


@dataclass
class AnalyticsResult:
    """Analytics result"""
    result_id: str
    analytics_type: AnalyticsType
    data_source: str
    insights: List[Dict[str, Any]]
    visualizations: List[Dict[str, Any]]
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Insight:
    """Analytics insight"""
    insight_id: str
    type: InsightType
    title: str
    description: str
    confidence: float
    impact: str  # high, medium, low
    recommendations: List[str]
    data_points: List[Dict[str, Any]]
    created_at: datetime


class AIAnalytics:
    """
    AI-powered analytics and insights system
    """
    
    def __init__(self):
        self.analytics_results: Dict[str, AnalyticsResult] = {}
        self.insights: Dict[str, Insight] = {}
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize analytics components"""
        try:
            # Initialize visualization settings
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # Initialize device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            logger.info("AI analytics components initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing analytics components: {e}")
    
    async def analyze_data(
        self,
        data: np.ndarray,
        analytics_type: AnalyticsType,
        config: Optional[Dict[str, Any]] = None
    ) -> AnalyticsResult:
        """Analyze data using specified analytics type"""
        try:
            result_id = f"analytics_{analytics_type.value}_{int(time.time())}"
            
            # Perform analysis based on type
            if analytics_type == AnalyticsType.PREDICTIVE:
                insights, visualizations = await self._predictive_analysis(data, config)
            elif analytics_type == AnalyticsType.ANOMALY_DETECTION:
                insights, visualizations = await self._anomaly_detection(data, config)
            elif analytics_type == AnalyticsType.TREND_ANALYSIS:
                insights, visualizations = await self._trend_analysis(data, config)
            elif analytics_type == AnalyticsType.CLUSTERING:
                insights, visualizations = await self._clustering_analysis(data, config)
            elif analytics_type == AnalyticsType.CORRELATION:
                insights, visualizations = await self._correlation_analysis(data, config)
            elif analytics_type == AnalyticsType.FORECASTING:
                insights, visualizations = await self._forecasting_analysis(data, config)
            else:
                raise ValueError(f"Unsupported analytics type: {analytics_type}")
            
            # Create analytics result
            result = AnalyticsResult(
                result_id=result_id,
                analytics_type=analytics_type,
                data_source="input_data",
                insights=insights,
                visualizations=visualizations,
                confidence=np.mean([insight.get("confidence", 0.5) for insight in insights]),
                created_at=datetime.now(),
                metadata=config or {}
            )
            
            # Store result
            self.analytics_results[result_id] = result
            
            logger.info(f"Completed {analytics_type.value} analysis: {result_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            raise
    
    async def _predictive_analysis(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform predictive analysis"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            
            # Split data for training/testing
            split_idx = int(len(data) * 0.8)
            train_data = data[:split_idx]
            test_data = data[split_idx:]
            
            # Create predictive model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            X_train = train_data[:-1]
            y_train = train_data[1:].flatten()
            model.fit(X_train, y_train)
            
            # Make predictions
            predictions = model.predict(test_data[:-1])
            actual = test_data[1:].flatten()
            
            # Calculate metrics
            mse = np.mean((predictions - actual) ** 2)
            mae = np.mean(np.abs(predictions - actual))
            r2 = model.score(test_data[:-1], test_data[1:].flatten())
            
            # Create insights
            insights.append({
                "type": "prediction_accuracy",
                "title": "Prediction Accuracy",
                "description": f"Model achieves {r2:.3f} R² score with {mse:.3f} MSE",
                "confidence": min(r2, 1.0),
                "impact": "high" if r2 > 0.8 else "medium" if r2 > 0.5 else "low",
                "metrics": {"r2_score": r2, "mse": mse, "mae": mae}
            })
            
            # Create visualizations
            visualizations.append({
                "type": "prediction_plot",
                "title": "Predictions vs Actual",
                "data": {
                    "actual": actual.tolist(),
                    "predictions": predictions.tolist(),
                    "indices": list(range(len(actual)))
                }
            })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            return [], []
    
    async def _anomaly_detection(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform anomaly detection"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            
            # Use Isolation Forest for anomaly detection
            model = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = model.fit_predict(data)
            anomaly_scores = model.decision_function(data)
            
            # Find anomalies
            anomalies = data[anomaly_labels == -1]
            normal_data = data[anomaly_labels == 1]
            
            # Create insights
            anomaly_count = len(anomalies)
            total_count = len(data)
            anomaly_rate = anomaly_count / total_count
            
            insights.append({
                "type": "anomaly_summary",
                "title": "Anomaly Detection Summary",
                "description": f"Found {anomaly_count} anomalies out of {total_count} data points ({anomaly_rate:.2%})",
                "confidence": 0.8,
                "impact": "high" if anomaly_rate > 0.1 else "medium" if anomaly_rate > 0.05 else "low",
                "metrics": {
                    "anomaly_count": anomaly_count,
                    "total_count": total_count,
                    "anomaly_rate": anomaly_rate
                }
            })
            
            # Create visualizations
            visualizations.append({
                "type": "anomaly_plot",
                "title": "Anomaly Detection Results",
                "data": {
                    "normal_data": normal_data.tolist(),
                    "anomalies": anomalies.tolist(),
                    "anomaly_scores": anomaly_scores.tolist()
                }
            })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return [], []
    
    async def _trend_analysis(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform trend analysis"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) > 1:
                data = data.flatten()
            
            # Calculate trend metrics
            x = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
            
            # Determine trend direction
            if slope > 0.01:
                trend_direction = "increasing"
                trend_strength = "strong" if abs(r_value) > 0.7 else "moderate" if abs(r_value) > 0.4 else "weak"
            elif slope < -0.01:
                trend_direction = "decreasing"
                trend_strength = "strong" if abs(r_value) > 0.7 else "moderate" if abs(r_value) > 0.4 else "weak"
            else:
                trend_direction = "stable"
                trend_strength = "weak"
            
            # Create insights
            insights.append({
                "type": "trend_analysis",
                "title": "Trend Analysis",
                "description": f"Data shows {trend_strength} {trend_direction} trend (slope: {slope:.4f}, R²: {r_value**2:.3f})",
                "confidence": abs(r_value),
                "impact": "high" if abs(r_value) > 0.7 else "medium" if abs(r_value) > 0.4 else "low",
                "metrics": {
                    "slope": slope,
                    "r_squared": r_value**2,
                    "p_value": p_value,
                    "trend_direction": trend_direction,
                    "trend_strength": trend_strength
                }
            })
            
            # Create visualizations
            trend_line = slope * x + intercept
            visualizations.append({
                "type": "trend_plot",
                "title": "Trend Analysis",
                "data": {
                    "x": x.tolist(),
                    "y": data.tolist(),
                    "trend_line": trend_line.tolist()
                }
            })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return [], []
    
    async def _clustering_analysis(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform clustering analysis"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            
            # Determine optimal number of clusters
            max_clusters = min(10, len(data) // 2)
            silhouette_scores = []
            
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42)
                cluster_labels = kmeans.fit_predict(data)
                silhouette_avg = silhouette_score(data, cluster_labels)
                silhouette_scores.append(silhouette_avg)
            
            # Find optimal k
            optimal_k = np.argmax(silhouette_scores) + 2
            best_silhouette = max(silhouette_scores)
            
            # Perform final clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42)
            cluster_labels = kmeans.fit_predict(data)
            cluster_centers = kmeans.cluster_centers_
            
            # Create insights
            insights.append({
                "type": "clustering_summary",
                "title": "Clustering Analysis",
                "description": f"Data naturally forms {optimal_k} clusters with silhouette score of {best_silhouette:.3f}",
                "confidence": best_silhouette,
                "impact": "high" if best_silhouette > 0.7 else "medium" if best_silhouette > 0.5 else "low",
                "metrics": {
                    "optimal_clusters": optimal_k,
                    "silhouette_score": best_silhouette,
                    "cluster_sizes": [np.sum(cluster_labels == i) for i in range(optimal_k)]
                }
            })
            
            # Create visualizations
            if data.shape[1] <= 2:
                visualizations.append({
                    "type": "cluster_plot",
                    "title": "Cluster Visualization",
                    "data": {
                        "x": data[:, 0].tolist(),
                        "y": data[:, 1].tolist() if data.shape[1] > 1 else [0] * len(data),
                        "clusters": cluster_labels.tolist(),
                        "centers": cluster_centers.tolist()
                    }
                })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}")
            return [], []
    
    async def _correlation_analysis(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform correlation analysis"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            
            # Calculate correlation matrix
            if data.shape[1] > 1:
                corr_matrix = np.corrcoef(data.T)
                
                # Find strong correlations
                strong_correlations = []
                for i in range(len(corr_matrix)):
                    for j in range(i + 1, len(corr_matrix)):
                        corr_value = corr_matrix[i, j]
                        if abs(corr_value) > 0.7:
                            strong_correlations.append({
                                "feature_1": i,
                                "feature_2": j,
                                "correlation": corr_value
                            })
                
                # Create insights
                insights.append({
                    "type": "correlation_summary",
                    "title": "Correlation Analysis",
                    "description": f"Found {len(strong_correlations)} strong correlations (|r| > 0.7) among {data.shape[1]} features",
                    "confidence": 0.8,
                    "impact": "high" if len(strong_correlations) > 0 else "low",
                    "metrics": {
                        "total_features": data.shape[1],
                        "strong_correlations": len(strong_correlations),
                        "correlation_matrix": corr_matrix.tolist()
                    }
                })
                
                # Create visualizations
                visualizations.append({
                    "type": "correlation_heatmap",
                    "title": "Correlation Matrix",
                    "data": {
                        "correlation_matrix": corr_matrix.tolist(),
                        "feature_names": [f"Feature_{i}" for i in range(data.shape[1])]
                    }
                })
            else:
                # Single feature - no correlation analysis possible
                insights.append({
                    "type": "correlation_summary",
                    "title": "Correlation Analysis",
                    "description": "Single feature data - correlation analysis not applicable",
                    "confidence": 1.0,
                    "impact": "low",
                    "metrics": {"total_features": 1}
                })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return [], []
    
    async def _forecasting_analysis(self, data: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform forecasting analysis"""
        try:
            insights = []
            visualizations = []
            
            # Prepare data
            if len(data.shape) > 1:
                data = data.flatten()
            
            # Create time series
            dates = pd.date_range(start='2023-01-01', periods=len(data), freq='D')
            ts_data = pd.Series(data, index=dates)
            
            # Split data
            split_idx = int(len(ts_data) * 0.8)
            train_data = ts_data[:split_idx]
            test_data = ts_data[split_idx:]
            
            # Simple ARIMA model
            model = ARIMA(train_data, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Make forecasts
            forecast_steps = len(test_data)
            forecast = fitted_model.forecast(steps=forecast_steps)
            forecast_ci = fitted_model.get_forecast(steps=forecast_steps).conf_int()
            
            # Calculate forecast accuracy
            mae = np.mean(np.abs(forecast - test_data))
            mape = np.mean(np.abs((test_data - forecast) / test_data)) * 100
            
            # Create insights
            insights.append({
                "type": "forecast_accuracy",
                "title": "Forecasting Accuracy",
                "description": f"Forecast achieves {mape:.2f}% MAPE with {mae:.3f} MAE",
                "confidence": max(0, 1 - mape / 100),
                "impact": "high" if mape < 10 else "medium" if mape < 20 else "low",
                "metrics": {
                    "mae": mae,
                    "mape": mape,
                    "forecast_periods": forecast_steps
                }
            })
            
            # Create visualizations
            visualizations.append({
                "type": "forecast_plot",
                "title": "Time Series Forecast",
                "data": {
                    "train_data": train_data.tolist(),
                    "test_data": test_data.tolist(),
                    "forecast": forecast.tolist(),
                    "forecast_ci_lower": forecast_ci.iloc[:, 0].tolist(),
                    "forecast_ci_upper": forecast_ci.iloc[:, 1].tolist(),
                    "dates": [d.isoformat() for d in dates]
                }
            })
            
            return insights, visualizations
        
        except Exception as e:
            logger.error(f"Error in forecasting analysis: {e}")
            return [], []
    
    async def generate_insights(self, analytics_result: AnalyticsResult) -> List[Insight]:
        """Generate actionable insights from analytics results"""
        try:
            insights = []
            
            for result_insight in analytics_result.insights:
                insight_id = f"insight_{analytics_result.result_id}_{len(insights)}"
                
                # Create insight
                insight = Insight(
                    insight_id=insight_id,
                    type=InsightType(result_insight.get("type", "pattern")),
                    title=result_insight.get("title", "Analytics Insight"),
                    description=result_insight.get("description", ""),
                    confidence=result_insight.get("confidence", 0.5),
                    impact=result_insight.get("impact", "low"),
                    recommendations=self._generate_recommendations(result_insight),
                    data_points=result_insight.get("metrics", {}),
                    created_at=datetime.now()
                )
                
                insights.append(insight)
                self.insights[insight_id] = insight
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    def _generate_recommendations(self, insight: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on insight"""
        try:
            recommendations = []
            insight_type = insight.get("type", "")
            impact = insight.get("impact", "low")
            
            if insight_type == "prediction_accuracy":
                if impact == "high":
                    recommendations.append("Model shows excellent predictive performance - consider deploying to production")
                elif impact == "medium":
                    recommendations.append("Model performance is acceptable - consider fine-tuning for better results")
                else:
                    recommendations.append("Model performance is poor - consider retraining with more data or different algorithms")
            
            elif insight_type == "anomaly_summary":
                if impact == "high":
                    recommendations.append("High anomaly rate detected - investigate root causes and implement monitoring")
                elif impact == "medium":
                    recommendations.append("Moderate anomaly rate - review data quality and consider automated alerts")
                else:
                    recommendations.append("Low anomaly rate - system appears stable")
            
            elif insight_type == "trend_analysis":
                if impact == "high":
                    recommendations.append("Strong trend detected - consider trend-based strategies")
                elif impact == "medium":
                    recommendations.append("Moderate trend - monitor for changes")
                else:
                    recommendations.append("Weak trend - data appears stable")
            
            elif insight_type == "clustering_summary":
                if impact == "high":
                    recommendations.append("Clear clusters identified - consider cluster-based segmentation")
                elif impact == "medium":
                    recommendations.append("Some clustering patterns - investigate cluster characteristics")
                else:
                    recommendations.append("Weak clustering - data appears homogeneous")
            
            elif insight_type == "correlation_summary":
                if impact == "high":
                    recommendations.append("Strong correlations found - consider feature selection or dimensionality reduction")
                else:
                    recommendations.append("Weak correlations - features appear independent")
            
            elif insight_type == "forecast_accuracy":
                if impact == "high":
                    recommendations.append("Accurate forecasts - suitable for planning and decision making")
                elif impact == "medium":
                    recommendations.append("Moderate forecast accuracy - consider model improvements")
                else:
                    recommendations.append("Poor forecast accuracy - review model and data quality")
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review analytics results for actionable insights"]
    
    async def create_visualization(self, analytics_result: AnalyticsResult, viz_type: str) -> Dict[str, Any]:
        """Create visualization for analytics result"""
        try:
            if viz_type not in [viz["type"] for viz in analytics_result.visualizations]:
                raise ValueError(f"Visualization type {viz_type} not found")
            
            # Find the visualization
            visualization = next(viz for viz in analytics_result.visualizations if viz["type"] == viz_type)
            
            # Create plot based on type
            if viz_type == "prediction_plot":
                return await self._create_prediction_plot(visualization)
            elif viz_type == "anomaly_plot":
                return await self._create_anomaly_plot(visualization)
            elif viz_type == "trend_plot":
                return await self._create_trend_plot(visualization)
            elif viz_type == "cluster_plot":
                return await self._create_cluster_plot(visualization)
            elif viz_type == "correlation_heatmap":
                return await self._create_correlation_heatmap(visualization)
            elif viz_type == "forecast_plot":
                return await self._create_forecast_plot(visualization)
            else:
                raise ValueError(f"Unsupported visualization type: {viz_type}")
        
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return {}
    
    async def _create_prediction_plot(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create prediction plot"""
        try:
            data = visualization["data"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data["indices"],
                y=data["actual"],
                mode='lines+markers',
                name='Actual',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=data["indices"],
                y=data["predictions"],
                mode='lines+markers',
                name='Predictions',
                line=dict(color='red')
            ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Index",
                yaxis_title="Value",
                hovermode='x unified'
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating prediction plot: {e}")
            return {}
    
    async def _create_anomaly_plot(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create anomaly plot"""
        try:
            data = visualization["data"]
            
            fig = go.Figure()
            
            # Add normal data
            if data["normal_data"]:
                normal_data = np.array(data["normal_data"])
                fig.add_trace(go.Scatter(
                    x=normal_data[:, 0],
                    y=normal_data[:, 1] if normal_data.shape[1] > 1 else [0] * len(normal_data),
                    mode='markers',
                    name='Normal',
                    marker=dict(color='blue', size=6)
                ))
            
            # Add anomalies
            if data["anomalies"]:
                anomaly_data = np.array(data["anomalies"])
                fig.add_trace(go.Scatter(
                    x=anomaly_data[:, 0],
                    y=anomaly_data[:, 1] if anomaly_data.shape[1] > 1 else [0] * len(anomaly_data),
                    mode='markers',
                    name='Anomalies',
                    marker=dict(color='red', size=8, symbol='x')
                ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Feature 1",
                yaxis_title="Feature 2" if len(data["normal_data"][0]) > 1 else "Value",
                hovermode='closest'
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating anomaly plot: {e}")
            return {}
    
    async def _create_trend_plot(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend plot"""
        try:
            data = visualization["data"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data["x"],
                y=data["y"],
                mode='lines+markers',
                name='Data',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=data["x"],
                y=data["trend_line"],
                mode='lines',
                name='Trend',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Index",
                yaxis_title="Value",
                hovermode='x unified'
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating trend plot: {e}")
            return {}
    
    async def _create_cluster_plot(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create cluster plot"""
        try:
            data = visualization["data"]
            
            fig = go.Figure()
            
            # Add data points
            fig.add_trace(go.Scatter(
                x=data["x"],
                y=data["y"],
                mode='markers',
                marker=dict(
                    color=data["clusters"],
                    colorscale='viridis',
                    size=6
                ),
                name='Data Points'
            ))
            
            # Add cluster centers
            if data["centers"]:
                centers = np.array(data["centers"])
                fig.add_trace(go.Scatter(
                    x=centers[:, 0],
                    y=centers[:, 1] if centers.shape[1] > 1 else [0] * len(centers),
                    mode='markers',
                    marker=dict(
                        color='red',
                        size=12,
                        symbol='x'
                    ),
                    name='Centers'
                ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Feature 1",
                yaxis_title="Feature 2" if len(data["x"]) > 0 and len(data["y"]) > 0 else "Value",
                hovermode='closest'
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating cluster plot: {e}")
            return {}
    
    async def _create_correlation_heatmap(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create correlation heatmap"""
        try:
            data = visualization["data"]
            
            fig = go.Figure(data=go.Heatmap(
                z=data["correlation_matrix"],
                x=data["feature_names"],
                y=data["feature_names"],
                colorscale='RdBu',
                zmid=0
            ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Features",
                yaxis_title="Features"
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            return {}
    
    async def _create_forecast_plot(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Create forecast plot"""
        try:
            data = visualization["data"]
            
            fig = go.Figure()
            
            # Add training data
            fig.add_trace(go.Scatter(
                x=data["dates"][:len(data["train_data"])],
                y=data["train_data"],
                mode='lines',
                name='Training Data',
                line=dict(color='blue')
            ))
            
            # Add test data
            fig.add_trace(go.Scatter(
                x=data["dates"][len(data["train_data"]):len(data["train_data"]) + len(data["test_data"])],
                y=data["test_data"],
                mode='lines',
                name='Test Data',
                line=dict(color='green')
            ))
            
            # Add forecast
            forecast_start_idx = len(data["train_data"])
            forecast_end_idx = forecast_start_idx + len(data["forecast"])
            fig.add_trace(go.Scatter(
                x=data["dates"][forecast_start_idx:forecast_end_idx],
                y=data["forecast"],
                mode='lines',
                name='Forecast',
                line=dict(color='red')
            ))
            
            # Add confidence interval
            fig.add_trace(go.Scatter(
                x=data["dates"][forecast_start_idx:forecast_end_idx],
                y=data["forecast_ci_upper"],
                mode='lines',
                line=dict(width=0),
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=data["dates"][forecast_start_idx:forecast_end_idx],
                y=data["forecast_ci_lower"],
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.2)',
                name='Confidence Interval'
            ))
            
            fig.update_layout(
                title=visualization["title"],
                xaxis_title="Date",
                yaxis_title="Value",
                hovermode='x unified'
            )
            
            return {
                "type": "plotly",
                "data": fig.to_dict(),
                "title": visualization["title"]
            }
        
        except Exception as e:
            logger.error(f"Error creating forecast plot: {e}")
            return {}
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return {
            "total_analyses": len(self.analytics_results),
            "total_insights": len(self.insights),
            "analytics_types": list(set([r.analytics_type.value for r in self.analytics_results.values()])),
            "insight_types": list(set([i.type.value for i in self.insights.values()])),
            "high_impact_insights": len([i for i in self.insights.values() if i.impact == "high"]),
            "average_confidence": np.mean([i.confidence for i in self.insights.values()]) if self.insights else 0.0,
            "last_analysis": max([r.created_at for r in self.analytics_results.values()]).isoformat() if self.analytics_results else None
        }
    
    async def get_analytics_result(self, result_id: str) -> Optional[AnalyticsResult]:
        """Get specific analytics result"""
        return self.analytics_results.get(result_id)
    
    async def get_insight(self, insight_id: str) -> Optional[Insight]:
        """Get specific insight"""
        return self.insights.get(insight_id)
    
    async def export_analytics(self, result_id: str, export_path: str) -> bool:
        """Export analytics results"""
        try:
            if result_id not in self.analytics_results:
                raise ValueError(f"Analytics result {result_id} not found")
            
            result = self.analytics_results[result_id]
            
            # Create export directory
            Path(export_path).mkdir(parents=True, exist_ok=True)
            
            # Export analytics result
            result_data = {
                "result_id": result.result_id,
                "analytics_type": result.analytics_type.value,
                "data_source": result.data_source,
                "insights": result.insights,
                "visualizations": result.visualizations,
                "confidence": result.confidence,
                "created_at": result.created_at.isoformat(),
                "metadata": result.metadata
            }
            
            # Save to JSON
            with open(Path(export_path) / f"{result_id}.json", 'w') as f:
                json.dump(result_data, f, indent=2)
            
            logger.info(f"Exported analytics result {result_id} to {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return False
