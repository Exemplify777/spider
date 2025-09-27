"""
Explainability Manager

Comprehensive model explainability management system that orchestrates
SHAP, LIME, feature importance, and other explainability tools.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

from .shap_explainer import SHAPExplainer, SHAPConfig, SHAPResult
from .lime_explainer import LIMEExplainer, LIMEConfig, LIMEResult
from .feature_importance import FeatureImportanceAnalyzer, ImportanceConfig, ImportanceResult

logger = logging.getLogger(__name__)


class ExplainabilityMethod(str, Enum):
    """Explainability method enumeration."""
    SHAP = "shap"
    LIME = "lime"
    FEATURE_IMPORTANCE = "feature_importance"
    COMBINED = "combined"
    COMPARATIVE = "comparative"


class ExplanationScope(str, Enum):
    """Explanation scope enumeration."""
    GLOBAL = "global"
    LOCAL = "local"
    BOTH = "both"


@dataclass
class ExplainabilityConfig:
    """Explainability configuration."""
    methods: List[ExplainabilityMethod] = field(default_factory=lambda: [ExplainabilityMethod.SHAP])
    scope: ExplanationScope = ExplanationScope.BOTH
    max_features: int = 20
    max_samples: int = 1000
    random_state: int = 42
    enable_plots: bool = True
    enable_comparison: bool = True
    save_explanations: bool = True
    custom_configs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplainabilityResult:
    """Comprehensive explainability result."""
    explanation_id: str
    model_type: str
    explanations: Dict[str, Any]
    feature_importance: Dict[str, float]
    feature_rankings: List[str]
    global_explanations: Dict[str, Any] = field(default_factory=dict)
    local_explanations: Dict[str, Any] = field(default_factory=dict)
    comparison_analysis: Dict[str, Any] = field(default_factory=dict)
    plots: Dict[str, Any] = field(default_factory=dict)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExplainabilityManager:
    """
    Comprehensive explainability management system.
    
    Features:
    - Multiple explanation methods (SHAP, LIME, Feature Importance)
    - Global and local explanations
    - Comparative analysis across methods
    - Visualization and reporting
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize explainability manager."""
        self.shap_explainer = SHAPExplainer()
        self.lime_explainer = LIMEExplainer()
        self.feature_importance_analyzer = FeatureImportanceAnalyzer()
        self.explanation_cache = {}
        self.explanation_history = []
    
    async def explain_model(self, model: BaseEstimator, X: pd.DataFrame, y: pd.Series,
                           config: ExplainabilityConfig) -> ExplainabilityResult:
        """
        Generate comprehensive model explanations.
        
        Args:
            model: Trained model to explain
            X: Feature data
            y: Target data
            config: Explainability configuration
            
        Returns:
            Comprehensive explainability result
        """
        explanation_id = f"explain_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            explanations = {}
            feature_importance = {}
            feature_rankings = []
            global_explanations = {}
            local_explanations = {}
            comparison_analysis = {}
            plots = {}
            summary_stats = {}
            
            # Generate explanations based on selected methods
            for method in config.methods:
                if method == ExplainabilityMethod.SHAP:
                    shap_result = await self._generate_shap_explanations(model, X, y, config)
                    explanations["shap"] = shap_result
                    
                    if config.scope in [ExplanationScope.GLOBAL, ExplanationScope.BOTH]:
                        global_explanations["shap"] = shap_result
                    
                    if config.scope in [ExplanationScope.LOCAL, ExplanationScope.BOTH]:
                        local_explanations["shap"] = shap_result
                
                elif method == ExplainabilityMethod.LIME:
                    lime_result = await self._generate_lime_explanations(model, X, y, config)
                    explanations["lime"] = lime_result
                    
                    if config.scope in [ExplanationScope.LOCAL, ExplanationScope.BOTH]:
                        local_explanations["lime"] = lime_result
                
                elif method == ExplainabilityMethod.FEATURE_IMPORTANCE:
                    importance_result = await self._generate_feature_importance(model, X, y, config)
                    explanations["feature_importance"] = importance_result
                    feature_importance = importance_result.feature_importance
                    feature_rankings = importance_result.feature_rankings
                    
                    if config.scope in [ExplanationScope.GLOBAL, ExplanationScope.BOTH]:
                        global_explanations["feature_importance"] = importance_result
            
            # Generate comparative analysis if multiple methods are used
            if len(config.methods) > 1 and config.enable_comparison:
                comparison_analysis = await self._generate_comparative_analysis(explanations, config)
            
            # Generate combined plots
            if config.enable_plots:
                plots = await self._generate_combined_plots(explanations, config)
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_stats(explanations, feature_importance, config)
            
            # Create comprehensive result
            result = ExplainabilityResult(
                explanation_id=explanation_id,
                model_type=model.__class__.__name__,
                explanations=explanations,
                feature_importance=feature_importance,
                feature_rankings=feature_rankings,
                global_explanations=global_explanations,
                local_explanations=local_explanations,
                comparison_analysis=comparison_analysis,
                plots=plots,
                summary_stats=summary_stats,
                metadata={
                    "n_features": len(X.columns),
                    "n_samples": len(X),
                    "methods_used": [method.value for method in config.methods],
                    "scope": config.scope.value,
                    "config": config.__dict__
                }
            )
            
            # Store in history
            self.explanation_history.append({
                "explanation_id": explanation_id,
                "model_type": model.__class__.__name__,
                "methods_used": [method.value for method in config.methods],
                "scope": config.scope.value,
                "n_features": len(X.columns),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Cache result if enabled
            if config.save_explanations:
                self.explanation_cache[explanation_id] = result
            
            logger.info(f"Comprehensive explainability analysis completed: {explanation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Explainability analysis failed: {e}")
            raise
    
    async def _generate_shap_explanations(self, model: BaseEstimator, X: pd.DataFrame, 
                                         y: pd.Series, config: ExplainabilityConfig) -> SHAPResult:
        """Generate SHAP explanations."""
        # Get SHAP config from custom configs or use defaults
        shap_config = config.custom_configs.get("shap", {})
        shap_config = SHAPConfig(
            max_samples=config.max_samples,
            random_state=config.random_state,
            feature_names=list(X.columns),
            **shap_config
        )
        
        # Determine explanation type based on scope
        if config.scope == ExplanationScope.GLOBAL:
            shap_config.explanation_type = "global"
        elif config.scope == ExplanationScope.LOCAL:
            shap_config.explanation_type = "local"
        else:
            shap_config.explanation_type = "local"  # Default to local for combined
        
        return await self.shap_explainer.explain_model(model, X, shap_config)
    
    async def _generate_lime_explanations(self, model: BaseEstimator, X: pd.DataFrame, 
                                         y: pd.Series, config: ExplainabilityConfig) -> LIMEResult:
        """Generate LIME explanations."""
        # Get LIME config from custom configs or use defaults
        lime_config = config.custom_configs.get("lime", {})
        lime_config = LIMEConfig(
            num_features=config.max_features,
            random_state=config.random_state,
            feature_names=list(X.columns),
            **lime_config
        )
        
        # Determine explanation mode based on scope
        if config.scope == ExplanationScope.GLOBAL:
            lime_config.explanation_mode = "feature_importance"
        else:
            lime_config.explanation_mode = "single"
        
        # Select instances for explanation
        instances = list(range(min(5, len(X))))  # Explain first 5 instances
        
        return await self.lime_explainer.explain_model(model, X, lime_config, instances)
    
    async def _generate_feature_importance(self, model: BaseEstimator, X: pd.DataFrame, 
                                          y: pd.Series, config: ExplainabilityConfig) -> ImportanceResult:
        """Generate feature importance analysis."""
        # Get importance config from custom configs or use defaults
        importance_config = config.custom_configs.get("feature_importance", {})
        importance_config = ImportanceConfig(
            max_features=config.max_features,
            random_state=config.random_state,
            feature_names=list(X.columns),
            **importance_config
        )
        
        return await self.feature_importance_analyzer.analyze_importance(model, X, y, importance_config)
    
    async def _generate_comparative_analysis(self, explanations: Dict[str, Any], 
                                            config: ExplainabilityConfig) -> Dict[str, Any]:
        """Generate comparative analysis across explanation methods."""
        comparison = {
            "method_comparison": {},
            "feature_agreement": {},
            "ranking_correlation": {},
            "consensus_features": [],
            "disagreement_features": []
        }
        
        try:
            # Extract feature importance from different methods
            method_importances = {}
            
            if "shap" in explanations:
                shap_result = explanations["shap"]
                if hasattr(shap_result, 'feature_importance'):
                    method_importances["shap"] = shap_result.feature_importance
            
            if "lime" in explanations:
                lime_result = explanations["lime"]
                if hasattr(lime_result, 'explanations') and lime_result.explanations:
                    # Aggregate LIME explanations
                    lime_importance = {}
                    for exp in lime_result.explanations:
                        for feature, importance in exp.get("feature_importance", {}).items():
                            if feature not in lime_importance:
                                lime_importance[feature] = []
                            lime_importance[feature].append(importance)
                    
                    # Calculate mean importance
                    method_importances["lime"] = {
                        feature: np.mean(importances) 
                        for feature, importances in lime_importance.items()
                    }
            
            if "feature_importance" in explanations:
                importance_result = explanations["feature_importance"]
                method_importances["feature_importance"] = importance_result.feature_importance
            
            # Compare methods
            if len(method_importances) > 1:
                comparison["method_comparison"] = self._compare_methods(method_importances)
                comparison["feature_agreement"] = self._analyze_feature_agreement(method_importances)
                comparison["ranking_correlation"] = self._calculate_ranking_correlation(method_importances)
                comparison["consensus_features"] = self._find_consensus_features(method_importances)
                comparison["disagreement_features"] = self._find_disagreement_features(method_importances)
        
        except Exception as e:
            logger.warning(f"Comparative analysis failed: {e}")
            comparison["error"] = str(e)
        
        return comparison
    
    def _compare_methods(self, method_importances: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Compare feature importance across methods."""
        comparison = {}
        
        try:
            # Get common features
            all_features = set()
            for method, importances in method_importances.items():
                all_features.update(importances.keys())
            
            common_features = list(all_features)
            
            # Calculate correlation matrix
            method_names = list(method_importances.keys())
            correlation_matrix = np.zeros((len(method_names), len(method_names)))
            
            for i, method1 in enumerate(method_names):
                for j, method2 in enumerate(method_names):
                    if i == j:
                        correlation_matrix[i, j] = 1.0
                    else:
                        # Calculate correlation for common features
                        values1 = [method_importances[method1].get(f, 0.0) for f in common_features]
                        values2 = [method_importances[method2].get(f, 0.0) for f in common_features]
                        corr = np.corrcoef(values1, values2)[0, 1]
                        correlation_matrix[i, j] = corr if not np.isnan(corr) else 0.0
            
            comparison["correlation_matrix"] = correlation_matrix.tolist()
            comparison["method_names"] = method_names
            comparison["common_features"] = common_features
            
        except Exception as e:
            logger.warning(f"Method comparison failed: {e}")
            comparison["error"] = str(e)
        
        return comparison
    
    def _analyze_feature_agreement(self, method_importances: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Analyze agreement between methods on feature importance."""
        agreement = {}
        
        try:
            # Get common features
            all_features = set()
            for method, importances in method_importances.items():
                all_features.update(importances.keys())
            
            common_features = list(all_features)
            
            # Calculate agreement for each feature
            feature_agreement = {}
            for feature in common_features:
                values = []
                for method, importances in method_importances.items():
                    if feature in importances:
                        values.append(importances[feature])
                
                if len(values) > 1:
                    # Calculate coefficient of variation as disagreement measure
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    cv = std_val / mean_val if mean_val > 0 else 0
                    feature_agreement[feature] = {
                        "mean_importance": float(mean_val),
                        "std_importance": float(std_val),
                        "coefficient_of_variation": float(cv),
                        "agreement_score": float(1.0 - cv)  # Higher is better agreement
                    }
            
            agreement["feature_agreement"] = feature_agreement
            agreement["overall_agreement"] = float(np.mean([
                f["agreement_score"] for f in feature_agreement.values()
            ]))
        
        except Exception as e:
            logger.warning(f"Feature agreement analysis failed: {e}")
            agreement["error"] = str(e)
        
        return agreement
    
    def _calculate_ranking_correlation(self, method_importances: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Calculate ranking correlation between methods."""
        ranking_corr = {}
        
        try:
            method_names = list(method_importances.keys())
            
            if len(method_names) < 2:
                return ranking_corr
            
            # Calculate pairwise ranking correlations
            for i, method1 in enumerate(method_names):
                for j, method2 in enumerate(method_names[i+1:], i+1):
                    # Get common features
                    common_features = set(method_importances[method1].keys()) & set(method_importances[method2].keys())
                    
                    if len(common_features) > 1:
                        # Create rankings
                        features1 = sorted(common_features, key=lambda x: method_importances[method1][x], reverse=True)
                        features2 = sorted(common_features, key=lambda x: method_importances[method2][x], reverse=True)
                        
                        # Calculate Spearman correlation
                        from scipy.stats import spearmanr
                        ranks1 = [features1.index(f) for f in common_features]
                        ranks2 = [features2.index(f) for f in common_features]
                        
                        corr, p_value = spearmanr(ranks1, ranks2)
                        
                        ranking_corr[f"{method1}_vs_{method2}"] = {
                            "correlation": float(corr),
                            "p_value": float(p_value),
                            "n_features": len(common_features)
                        }
        
        except Exception as e:
            logger.warning(f"Ranking correlation calculation failed: {e}")
            ranking_corr["error"] = str(e)
        
        return ranking_corr
    
    def _find_consensus_features(self, method_importances: Dict[str, Dict[str, float]]) -> List[str]:
        """Find features that are important across all methods."""
        consensus_features = []
        
        try:
            # Get common features
            all_features = set()
            for method, importances in method_importances.items():
                all_features.update(importances.keys())
            
            common_features = list(all_features)
            
            # Find features that are in top 50% for all methods
            for feature in common_features:
                is_important = True
                for method, importances in method_importances.items():
                    if feature in importances:
                        # Get ranking for this method
                        method_features = sorted(importances.keys(), key=lambda x: importances[x], reverse=True)
                        feature_rank = method_features.index(feature)
                        
                        # Check if in top 50%
                        if feature_rank >= len(method_features) // 2:
                            is_important = False
                            break
                    else:
                        is_important = False
                        break
                
                if is_important:
                    consensus_features.append(feature)
        
        except Exception as e:
            logger.warning(f"Consensus feature finding failed: {e}")
        
        return consensus_features
    
    def _find_disagreement_features(self, method_importances: Dict[str, Dict[str, float]]) -> List[str]:
        """Find features where methods disagree significantly."""
        disagreement_features = []
        
        try:
            # Get common features
            all_features = set()
            for method, importances in method_importances.items():
                all_features.update(importances.keys())
            
            common_features = list(all_features)
            
            # Find features with high disagreement
            for feature in common_features:
                values = []
                for method, importances in method_importances.items():
                    if feature in importances:
                        values.append(importances[feature])
                
                if len(values) > 1:
                    # Calculate coefficient of variation
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    cv = std_val / mean_val if mean_val > 0 else 0
                    
                    # High disagreement if CV > 0.5
                    if cv > 0.5:
                        disagreement_features.append(feature)
        
        except Exception as e:
            logger.warning(f"Disagreement feature finding failed: {e}")
        
        return disagreement_features
    
    async def _generate_combined_plots(self, explanations: Dict[str, Any], 
                                      config: ExplainabilityConfig) -> Dict[str, Any]:
        """Generate combined plots across explanation methods."""
        plots = {}
        
        try:
            # Feature importance comparison plot
            plots["feature_importance_comparison"] = self._create_feature_importance_comparison_plot(explanations)
            
            # Method agreement plot
            plots["method_agreement"] = self._create_method_agreement_plot(explanations)
            
            # Consensus features plot
            plots["consensus_features"] = self._create_consensus_features_plot(explanations)
            
            # Individual method plots
            for method, result in explanations.items():
                if hasattr(result, 'plots'):
                    plots[f"{method}_plots"] = result.plots
        
        except Exception as e:
            logger.warning(f"Combined plot generation failed: {e}")
            plots["error"] = str(e)
        
        return plots
    
    def _create_feature_importance_comparison_plot(self, explanations: Dict[str, Any]) -> Dict[str, Any]:
        """Create feature importance comparison plot."""
        comparison_data = {
            "methods": [],
            "features": [],
            "importance_values": []
        }
        
        try:
            # Extract feature importance from different methods
            all_features = set()
            method_importances = {}
            
            for method, result in explanations.items():
                if hasattr(result, 'feature_importance'):
                    method_importances[method] = result.feature_importance
                    all_features.update(result.feature_importance.keys())
            
            common_features = list(all_features)
            
            for method, importances in method_importances.items():
                comparison_data["methods"].append(method)
                comparison_data["features"].append(common_features)
                comparison_data["importance_values"].append([
                    importances.get(f, 0.0) for f in common_features
                ])
        
        except Exception as e:
            comparison_data["error"] = str(e)
        
        return comparison_data
    
    def _create_method_agreement_plot(self, explanations: Dict[str, Any]) -> Dict[str, Any]:
        """Create method agreement plot."""
        # This would create a plot showing agreement between methods
        return {"type": "method_agreement", "data": "placeholder"}
    
    def _create_consensus_features_plot(self, explanations: Dict[str, Any]) -> Dict[str, Any]:
        """Create consensus features plot."""
        # This would create a plot showing consensus features
        return {"type": "consensus_features", "data": "placeholder"}
    
    def _calculate_summary_stats(self, explanations: Dict[str, Any], 
                                feature_importance: Dict[str, float], 
                                config: ExplainabilityConfig) -> Dict[str, Any]:
        """Calculate summary statistics for explainability analysis."""
        stats = {
            "n_methods": len(explanations),
            "n_features": len(feature_importance),
            "methods_used": list(explanations.keys()),
            "scope": config.scope.value
        }
        
        try:
            # Feature importance statistics
            if feature_importance:
                importance_values = list(feature_importance.values())
                stats["feature_importance"] = {
                    "mean": float(np.mean(importance_values)),
                    "std": float(np.std(importance_values)),
                    "min": float(np.min(importance_values)),
                    "max": float(np.max(importance_values))
                }
            
            # Method-specific statistics
            for method, result in explanations.items():
                if hasattr(result, 'summary_stats'):
                    stats[f"{method}_stats"] = result.summary_stats
        
        except Exception as e:
            logger.warning(f"Summary statistics calculation failed: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def get_explanation(self, explanation_id: str) -> Optional[ExplainabilityResult]:
        """Get explanation by ID."""
        return self.explanation_cache.get(explanation_id)
    
    def list_explanations(self) -> List[Dict[str, Any]]:
        """List all explanations."""
        return [
            {
                "explanation_id": result.explanation_id,
                "model_type": result.model_type,
                "methods_used": list(result.explanations.keys()),
                "n_features": len(result.feature_importance),
                "created_at": result.created_at.isoformat()
            }
            for result in self.explanation_cache.values()
        ]
    
    def get_explanation_history(self) -> List[Dict[str, Any]]:
        """Get explanation history."""
        return self.explanation_history
    
    def get_available_methods(self) -> List[str]:
        """Get available explainability methods."""
        return [method.value for method in ExplainabilityMethod]
    
    def get_available_scopes(self) -> List[str]:
        """Get available explanation scopes."""
        return [scope.value for scope in ExplanationScope]
    
    def clear_cache(self):
        """Clear explanation cache."""
        self.explanation_cache.clear()
        logger.info("Explainability cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "cached_explanations": len(self.explanation_cache),
            "cache_keys": list(self.explanation_cache.keys()),
            "total_explanations": len(self.explanation_history)
        }
    
    def get_explainability_statistics(self) -> Dict[str, Any]:
        """Get explainability statistics."""
        if not self.explanation_history:
            return {"total_explanations": 0}
        
        total_explanations = len(self.explanation_history)
        methods_used = []
        model_types = []
        
        for history in self.explanation_history:
            methods_used.extend(history["methods_used"])
            model_types.append(history["model_type"])
        
        return {
            "total_explanations": total_explanations,
            "method_distribution": {method: methods_used.count(method) for method in set(methods_used)},
            "model_type_distribution": {model_type: model_types.count(model_type) for model_type in set(model_types)},
            "last_explanation": self.explanation_history[-1]["timestamp"] if self.explanation_history else None
        }
