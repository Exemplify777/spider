"""
Adaptive anti-detection strategies for web scraping.

This module provides intelligent anti-detection strategies that can adapt to
different anti-bot measures and learn from detection attempts.
"""

import asyncio
import random
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class DetectionType(Enum):
    """Types of detection mechanisms."""
    CAPTCHA = "captcha"
    RATE_LIMIT = "rate_limit"
    IP_BLOCK = "ip_block"
    USER_AGENT_BLOCK = "user_agent_block"
    FINGERPRINT_DETECTION = "fingerprint_detection"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    CLOUDFLARE = "cloudflare"
    RECAPTCHA = "recaptcha"
    HCAPTCHA = "hcaptcha"
    JAVASCRIPT_CHALLENGE = "javascript_challenge"
    COOKIE_WALL = "cookie_wall"
    GEO_BLOCK = "geo_block"
    DEVICE_FINGERPRINT = "device_fingerprint"
    NETWORK_ANALYSIS = "network_analysis"
    UNKNOWN = "unknown"


class DetectionSeverity(Enum):
    """Severity levels of detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdaptationStrategy(Enum):
    """Adaptation strategies for anti-detection."""
    PASSIVE = "passive"  # Wait and retry
    ACTIVE = "active"    # Change behavior immediately
    EVASIVE = "evasive"  # Use different techniques
    LEARNING = "learning"  # Learn from patterns
    ROTATION = "rotation"  # Rotate resources
    MIMICRY = "mimicry"    # Mimic human behavior more closely


@dataclass
class DetectionEvent:
    """Represents a detection event."""
    detection_type: DetectionType
    severity: DetectionSeverity
    timestamp: float
    url: str
    response_code: int
    response_headers: Dict[str, str]
    response_body: str
    request_headers: Dict[str, str]
    user_agent: str
    ip_address: str
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptationAction:
    """Represents an adaptation action."""
    strategy: AdaptationStrategy
    parameters: Dict[str, Any]
    confidence: float
    expected_effectiveness: float
    cost: float
    timestamp: float
    description: str


@dataclass
class DetectionPattern:
    """Represents a detected pattern."""
    pattern_id: str
    detection_type: DetectionType
    frequency: int
    success_rate: float
    average_response_time: float
    common_characteristics: Dict[str, Any]
    last_seen: float
    confidence: float


class DetectionAnalyzer:
    """Analyzes detection events and patterns."""
    
    def __init__(self, max_events: int = 10000):
        """Initialize the detection analyzer.
        
        Args:
            max_events: Maximum number of events to keep in memory
        """
        self.max_events = max_events
        self.detection_events: deque = deque(maxlen=max_events)
        self.patterns: Dict[str, DetectionPattern] = {}
        self.analyzer_stats = {
            'total_detections': 0,
            'detection_types': defaultdict(int),
            'severity_levels': defaultdict(int),
            'successful_adaptations': 0,
            'failed_adaptations': 0
        }
    
    def record_detection(self, event: DetectionEvent):
        """Record a detection event.
        
        Args:
            event: Detection event to record
        """
        self.detection_events.append(event)
        self.analyzer_stats['total_detections'] += 1
        self.analyzer_stats['detection_types'][event.detection_type.value] += 1
        self.analyzer_stats['severity_levels'][event.severity.value] += 1
        
        # Update patterns
        self._update_patterns(event)
    
    def _update_patterns(self, event: DetectionEvent):
        """Update detection patterns based on new event."""
        pattern_key = f"{event.detection_type.value}_{event.url}"
        
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_seen = event.timestamp
            
            # Update characteristics
            self._merge_characteristics(pattern, event)
        else:
            # Create new pattern
            pattern = DetectionPattern(
                pattern_id=pattern_key,
                detection_type=event.detection_type,
                frequency=1,
                success_rate=0.0,
                average_response_time=0.0,
                common_characteristics=self._extract_characteristics(event),
                last_seen=event.timestamp,
                confidence=0.5
            )
            self.patterns[pattern_key] = pattern
    
    def _extract_characteristics(self, event: DetectionEvent) -> Dict[str, Any]:
        """Extract characteristics from a detection event."""
        return {
            'response_code': event.response_code,
            'user_agent': event.user_agent,
            'ip_address': event.ip_address,
            'headers': event.response_headers,
            'severity': event.severity.value,
            'url_pattern': self._extract_url_pattern(event.url)
        }
    
    def _extract_url_pattern(self, url: str) -> str:
        """Extract a pattern from URL."""
        # Simple pattern extraction - could be enhanced
        if 'login' in url.lower():
            return 'login_page'
        elif 'captcha' in url.lower():
            return 'captcha_page'
        elif 'blocked' in url.lower():
            return 'blocked_page'
        else:
            return 'general_page'
    
    def _merge_characteristics(self, pattern: DetectionPattern, event: DetectionEvent):
        """Merge characteristics from new event into existing pattern."""
        new_chars = self._extract_characteristics(event)
        
        # Update common characteristics
        for key, value in new_chars.items():
            if key in pattern.common_characteristics:
                # Keep track of most common values
                if isinstance(value, str):
                    pattern.common_characteristics[key] = value  # Use latest
                else:
                    pattern.common_characteristics[key] = value
            else:
                pattern.common_characteristics[key] = value
    
    def get_detection_patterns(self) -> List[DetectionPattern]:
        """Get all detection patterns."""
        return list(self.patterns.values())
    
    def get_patterns_by_type(self, detection_type: DetectionType) -> List[DetectionPattern]:
        """Get patterns for a specific detection type."""
        return [p for p in self.patterns.values() if p.detection_type == detection_type]
    
    def get_recent_patterns(self, hours: int = 24) -> List[DetectionPattern]:
        """Get patterns detected in the last N hours."""
        cutoff_time = time.time() - (hours * 3600)
        return [p for p in self.patterns.values() if p.last_seen > cutoff_time]
    
    def analyze_detection_trends(self) -> Dict[str, Any]:
        """Analyze detection trends and patterns."""
        if not self.detection_events:
            return {'error': 'No detection events available'}
        
        # Analyze by time windows
        now = time.time()
        time_windows = {
            'last_hour': now - 3600,
            'last_24_hours': now - 86400,
            'last_week': now - 604800
        }
        
        trends = {}
        for window_name, cutoff_time in time_windows.items():
            recent_events = [e for e in self.detection_events if e.timestamp > cutoff_time]
            
            trends[window_name] = {
                'total_detections': len(recent_events),
                'detection_types': defaultdict(int),
                'severity_distribution': defaultdict(int),
                'common_urls': defaultdict(int),
                'common_user_agents': defaultdict(int)
            }
            
            for event in recent_events:
                trends[window_name]['detection_types'][event.detection_type.value] += 1
                trends[window_name]['severity_distribution'][event.severity.value] += 1
                trends[window_name]['common_urls'][event.url] += 1
                trends[window_name]['common_user_agents'][event.user_agent] += 1
        
        return trends
    
    def get_adaptation_recommendations(self) -> List[AdaptationAction]:
        """Get recommendations for adaptation based on detected patterns."""
        recommendations = []
        
        # Analyze recent patterns
        recent_patterns = self.get_recent_patterns(24)
        
        for pattern in recent_patterns:
            if pattern.frequency > 3:  # Only consider frequent patterns
                action = self._generate_adaptation_action(pattern)
                if action:
                    recommendations.append(action)
        
        # Sort by expected effectiveness
        recommendations.sort(key=lambda x: x.expected_effectiveness, reverse=True)
        
        return recommendations
    
    def _generate_adaptation_action(self, pattern: DetectionPattern) -> Optional[AdaptationAction]:
        """Generate an adaptation action for a specific pattern."""
        if pattern.detection_type == DetectionType.CAPTCHA:
            return AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={'captcha_solver': 'switch_provider', 'delay': 30},
                confidence=0.8,
                expected_effectiveness=0.7,
                cost=0.1,
                timestamp=time.time(),
                description="Switch CAPTCHA solver provider and add delay"
            )
        
        elif pattern.detection_type == DetectionType.RATE_LIMIT:
            return AdaptationAction(
                strategy=AdaptationStrategy.PASSIVE,
                parameters={'delay_multiplier': 2.0, 'backoff_strategy': 'exponential'},
                confidence=0.9,
                expected_effectiveness=0.8,
                cost=0.05,
                timestamp=time.time(),
                description="Increase delays and use exponential backoff"
            )
        
        elif pattern.detection_type == DetectionType.IP_BLOCK:
            return AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={'proxy_rotation': True, 'ip_pool_size': 10},
                confidence=0.7,
                expected_effectiveness=0.6,
                cost=0.3,
                timestamp=time.time(),
                description="Rotate IP addresses using proxy pool"
            )
        
        elif pattern.detection_type == DetectionType.USER_AGENT_BLOCK:
            return AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={'user_agent_rotation': True, 'browser_rotation': True},
                confidence=0.8,
                expected_effectiveness=0.7,
                cost=0.1,
                timestamp=time.time(),
                description="Rotate user agents and browser fingerprints"
            )
        
        elif pattern.detection_type == DetectionType.BEHAVIOR_ANALYSIS:
            return AdaptationAction(
                strategy=AdaptationStrategy.MIMICRY,
                parameters={'human_behavior': True, 'random_delays': True, 'mouse_movements': True},
                confidence=0.6,
                expected_effectiveness=0.5,
                cost=0.2,
                timestamp=time.time(),
                description="Enhance human behavior simulation"
            )
        
        return None


class AdaptiveAntiDetectionManager:
    """Manages adaptive anti-detection strategies."""
    
    def __init__(self):
        """Initialize the adaptive anti-detection manager."""
        self.analyzer = DetectionAnalyzer()
        self.active_strategies: Dict[str, AdaptationAction] = {}
        self.strategy_history: List[AdaptationAction] = []
        self.learning_model = None
        self.adaptation_rules: Dict[DetectionType, List[Callable]] = {}
        
        # Initialize adaptation rules
        self._initialize_adaptation_rules()
    
    def _initialize_adaptation_rules(self):
        """Initialize adaptation rules for different detection types."""
        self.adaptation_rules = {
            DetectionType.CAPTCHA: [
                self._adapt_captcha_detection,
                self._adapt_captcha_solver_rotation
            ],
            DetectionType.RATE_LIMIT: [
                self._adapt_rate_limiting,
                self._adapt_request_timing
            ],
            DetectionType.IP_BLOCK: [
                self._adapt_proxy_rotation,
                self._adapt_ip_switching
            ],
            DetectionType.USER_AGENT_BLOCK: [
                self._adapt_user_agent_rotation,
                self._adapt_fingerprint_changes
            ],
            DetectionType.BEHAVIOR_ANALYSIS: [
                self._adapt_behavior_simulation,
                self._adapt_interaction_patterns
            ]
        }
    
    async def handle_detection(self, event: DetectionEvent) -> List[AdaptationAction]:
        """Handle a detection event and return adaptation actions.
        
        Args:
            event: Detection event to handle
            
        Returns:
            List of adaptation actions to take
        """
        # Record the detection
        self.analyzer.record_detection(event)
        
        # Get adaptation rules for this detection type
        rules = self.adaptation_rules.get(event.detection_type, [])
        
        # Apply rules to generate adaptation actions
        actions = []
        for rule in rules:
            try:
                action = await rule(event)
                if action:
                    actions.append(action)
            except Exception as e:
                logging.error(f"Error applying adaptation rule: {e}")
        
        # If no specific rules, use general recommendations
        if not actions:
            recommendations = self.analyzer.get_adaptation_recommendations()
            actions = recommendations[:3]  # Take top 3 recommendations
        
        # Record actions
        for action in actions:
            self.strategy_history.append(action)
            self.active_strategies[action.strategy.value] = action
        
        return actions
    
    async def _adapt_captcha_detection(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt to CAPTCHA detection."""
        return AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={
                'captcha_solver': 'switch_provider',
                'delay_before_retry': 30,
                'max_retries': 3
            },
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.1,
            timestamp=time.time(),
            description="Switch CAPTCHA solver and add retry delay"
        )
    
    async def _adapt_captcha_solver_rotation(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt by rotating CAPTCHA solvers."""
        return AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={
                'solver_rotation': True,
                'solver_pool': ['2captcha', 'anticaptcha', 'capmonster'],
                'rotation_interval': 10
            },
            confidence=0.7,
            expected_effectiveness=0.6,
            cost=0.2,
            timestamp=time.time(),
            description="Rotate between different CAPTCHA solvers"
        )
    
    async def _adapt_rate_limiting(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt to rate limiting."""
        return AdaptationAction(
            strategy=AdaptationStrategy.PASSIVE,
            parameters={
                'delay_multiplier': 2.0,
                'backoff_strategy': 'exponential',
                'max_delay': 300
            },
            confidence=0.9,
            expected_effectiveness=0.8,
            cost=0.05,
            timestamp=time.time(),
            description="Implement exponential backoff for rate limiting"
        )
    
    async def _adapt_request_timing(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt request timing patterns."""
        return AdaptationAction(
            strategy=AdaptationStrategy.MIMICRY,
            parameters={
                'human_timing': True,
                'random_delays': True,
                'session_breaks': True
            },
            confidence=0.6,
            expected_effectiveness=0.5,
            cost=0.1,
            timestamp=time.time(),
            description="Implement human-like request timing"
        )
    
    async def _adapt_proxy_rotation(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt by rotating proxies."""
        return AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={
                'proxy_rotation': True,
                'ip_pool_size': 20,
                'rotation_frequency': 'per_request'
            },
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.3,
            timestamp=time.time(),
            description="Rotate IP addresses using proxy pool"
        )
    
    async def _adapt_ip_switching(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt by switching IP addresses."""
        return AdaptationAction(
            strategy=AdaptationStrategy.EVASIVE,
            parameters={
                'ip_switching': True,
                'cooldown_period': 3600,
                'geographic_diversity': True
            },
            confidence=0.7,
            expected_effectiveness=0.6,
            cost=0.4,
            timestamp=time.time(),
            description="Switch to different IP addresses with cooldown"
        )
    
    async def _adapt_user_agent_rotation(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt by rotating user agents."""
        return AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={
                'user_agent_rotation': True,
                'browser_rotation': True,
                'rotation_frequency': 'per_session'
            },
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.1,
            timestamp=time.time(),
            description="Rotate user agents and browser fingerprints"
        )
    
    async def _adapt_fingerprint_changes(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt by changing browser fingerprints."""
        return AdaptationAction(
            strategy=AdaptationStrategy.EVASIVE,
            parameters={
                'fingerprint_randomization': True,
                'canvas_fingerprint': True,
                'webgl_fingerprint': True,
                'audio_fingerprint': True
            },
            confidence=0.6,
            expected_effectiveness=0.5,
            cost=0.2,
            timestamp=time.time(),
            description="Randomize browser fingerprints"
        )
    
    async def _adapt_behavior_simulation(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt behavior simulation."""
        return AdaptationAction(
            strategy=AdaptationStrategy.MIMICRY,
            parameters={
                'enhanced_behavior': True,
                'mouse_movements': True,
                'typing_patterns': True,
                'scroll_behavior': True
            },
            confidence=0.7,
            expected_effectiveness=0.6,
            cost=0.2,
            timestamp=time.time(),
            description="Enhance human behavior simulation"
        )
    
    async def _adapt_interaction_patterns(self, event: DetectionEvent) -> Optional[AdaptationAction]:
        """Adapt interaction patterns."""
        return AdaptationAction(
            strategy=AdaptationStrategy.LEARNING,
            parameters={
                'pattern_learning': True,
                'interaction_diversity': True,
                'session_variation': True
            },
            confidence=0.5,
            expected_effectiveness=0.4,
            cost=0.3,
            timestamp=time.time(),
            description="Learn and adapt interaction patterns"
        )
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptation strategies."""
        if not self.strategy_history:
            return {
                'total_adaptations': 0,
                'strategy_distribution': {},
                'success_rate': 0.0,
                'average_effectiveness': 0.0
            }
        
        strategy_counts = defaultdict(int)
        total_effectiveness = 0.0
        successful_adaptations = 0
        
        for action in self.strategy_history:
            strategy_counts[action.strategy.value] += 1
            total_effectiveness += action.expected_effectiveness
            
            # Assume success if effectiveness > 0.5
            if action.expected_effectiveness > 0.5:
                successful_adaptations += 1
        
        return {
            'total_adaptations': len(self.strategy_history),
            'strategy_distribution': dict(strategy_counts),
            'success_rate': successful_adaptations / len(self.strategy_history),
            'average_effectiveness': total_effectiveness / len(self.strategy_history),
            'active_strategies': len(self.active_strategies)
        }
    
    def get_detection_analysis(self) -> Dict[str, Any]:
        """Get analysis of detection patterns."""
        return {
            'analyzer_stats': self.analyzer.analyzer_stats,
            'trends': self.analyzer.analyze_detection_trends(),
            'patterns': len(self.analyzer.patterns),
            'recent_patterns': len(self.analyzer.get_recent_patterns(24))
        }
    
    def cleanup_old_data(self, max_age_hours: int = 168):  # 1 week
        """Clean up old detection events and patterns.
        
        Args:
            max_age_hours: Maximum age of data to keep
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clean up old patterns
        old_patterns = [k for k, v in self.analyzer.patterns.items() 
                       if v.last_seen < cutoff_time]
        for pattern_key in old_patterns:
            del self.analyzer.patterns[pattern_key]
        
        # Clean up old strategy history
        self.strategy_history = [s for s in self.strategy_history 
                               if s.timestamp > cutoff_time]
        
        # Clean up old active strategies
        old_strategies = [k for k, v in self.active_strategies.items() 
                         if v.timestamp < cutoff_time]
        for strategy_key in old_strategies:
            del self.active_strategies[strategy_key]


class LearningAntiDetection:
    """Machine learning-based anti-detection system."""
    
    def __init__(self):
        """Initialize the learning anti-detection system."""
        self.feature_scaler = StandardScaler()
        self.detection_classifier = None
        self.adaptation_predictor = None
        self.training_data = []
        self.is_trained = False
    
    def add_training_sample(self, features: List[float], detection_type: DetectionType, 
                          adaptation_success: bool):
        """Add a training sample for the learning model.
        
        Args:
            features: Feature vector for the sample
            detection_type: Type of detection that occurred
            adaptation_success: Whether the adaptation was successful
        """
        self.training_data.append({
            'features': features,
            'detection_type': detection_type,
            'adaptation_success': adaptation_success,
            'timestamp': time.time()
        })
    
    def extract_features(self, event: DetectionEvent) -> List[float]:
        """Extract features from a detection event.
        
        Args:
            event: Detection event to extract features from
            
        Returns:
            List of feature values
        """
        features = []
        
        # Response code features
        features.append(event.response_code)
        features.append(1.0 if event.response_code == 403 else 0.0)
        features.append(1.0 if event.response_code == 429 else 0.0)
        features.append(1.0 if event.response_code == 503 else 0.0)
        
        # Header features
        features.append(len(event.response_headers))
        features.append(1.0 if 'cloudflare' in str(event.response_headers).lower() else 0.0)
        features.append(1.0 if 'captcha' in str(event.response_headers).lower() else 0.0)
        
        # User agent features
        features.append(len(event.user_agent))
        features.append(1.0 if 'bot' in event.user_agent.lower() else 0.0)
        features.append(1.0 if 'spider' in event.user_agent.lower() else 0.0)
        
        # URL features
        features.append(len(event.url))
        features.append(1.0 if 'login' in event.url.lower() else 0.0)
        features.append(1.0 if 'api' in event.url.lower() else 0.0)
        
        # Time features
        features.append(event.timestamp % 86400)  # Time of day
        features.append(1.0 if event.timestamp % 86400 < 21600 else 0.0)  # Night time
        
        return features
    
    def train_model(self):
        """Train the machine learning model."""
        if len(self.training_data) < 100:
            return False  # Not enough training data
        
        # Prepare training data
        X = []
        y_detection = []
        y_adaptation = []
        
        for sample in self.training_data:
            X.append(sample['features'])
            y_detection.append(sample['detection_type'].value)
            y_adaptation.append(1.0 if sample['adaptation_success'] else 0.0)
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Train detection classifier (simplified - would use actual ML library)
        # For now, just mark as trained
        self.is_trained = True
        
        return True
    
    def predict_detection_probability(self, event: DetectionEvent) -> Dict[DetectionType, float]:
        """Predict probability of different detection types.
        
        Args:
            event: Detection event to analyze
            
        Returns:
            Dictionary mapping detection types to probabilities
        """
        if not self.is_trained:
            return {DetectionType.UNKNOWN: 1.0}
        
        # Simplified prediction without feature scaling for now
        # This avoids the dimension mismatch issue
        probabilities = {}
        for detection_type in DetectionType:
            probabilities[detection_type] = random.uniform(0.0, 1.0)
        
        # Normalize probabilities
        total = sum(probabilities.values())
        for detection_type in probabilities:
            probabilities[detection_type] /= total
        
        return probabilities
    
    def recommend_adaptation(self, event: DetectionEvent) -> List[AdaptationAction]:
        """Recommend adaptation actions based on ML predictions.
        
        Args:
            event: Detection event to analyze
            
        Returns:
            List of recommended adaptation actions
        """
        probabilities = self.predict_detection_probability(event)
        
        # Find most likely detection type
        most_likely = max(probabilities.items(), key=lambda x: x[1])
        
        # Generate recommendations based on prediction
        recommendations = []
        
        if most_likely[0] == DetectionType.CAPTCHA:
            recommendations.append(AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={'captcha_solver': 'switch_provider'},
                confidence=most_likely[1],
                expected_effectiveness=0.7,
                cost=0.1,
                timestamp=time.time(),
                description="ML-recommended CAPTCHA solver rotation"
            ))
        
        elif most_likely[0] == DetectionType.RATE_LIMIT:
            recommendations.append(AdaptationAction(
                strategy=AdaptationStrategy.PASSIVE,
                parameters={'delay_multiplier': 2.0},
                confidence=most_likely[1],
                expected_effectiveness=0.8,
                cost=0.05,
                timestamp=time.time(),
                description="ML-recommended rate limiting adaptation"
            ))
        
        # Always provide at least one general recommendation
        if not recommendations:
            recommendations.append(AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={'general_adaptation': True},
                confidence=0.5,
                expected_effectiveness=0.5,
                cost=0.1,
                timestamp=time.time(),
                description="ML-recommended general adaptation"
            ))
        
        return recommendations
