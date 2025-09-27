"""
Tests for adaptive anti-detection strategies.

This module tests the adaptive anti-detection functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.adaptive_anti_detection import (
    DetectionAnalyzer, AdaptiveAntiDetectionManager, LearningAntiDetection,
    DetectionEvent, AdaptationAction, DetectionPattern, DetectionType,
    DetectionSeverity, AdaptationStrategy
)


class TestDetectionEvent:
    """Test DetectionEvent data structure."""
    
    def test_detection_event_creation(self):
        """Test creating a detection event."""
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={"Server": "nginx", "X-Captcha": "required"},
            response_body="<html>CAPTCHA required</html>",
            request_headers={"User-Agent": "Mozilla/5.0"},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ip_address="192.168.1.1",
            session_id="session123",
            metadata={"attempt": 1, "retry_count": 0}
        )
        
        assert event.detection_type == DetectionType.CAPTCHA
        assert event.severity == DetectionSeverity.HIGH
        assert event.response_code == 403
        assert event.url == "https://example.com/login"
        assert event.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        assert event.metadata["attempt"] == 1


class TestAdaptationAction:
    """Test AdaptationAction data structure."""
    
    def test_adaptation_action_creation(self):
        """Test creating an adaptation action."""
        action = AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={"proxy_rotation": True, "delay": 30},
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.1,
            timestamp=time.time(),
            description="Rotate proxies and add delay"
        )
        
        assert action.strategy == AdaptationStrategy.ROTATION
        assert action.parameters["proxy_rotation"] is True
        assert action.confidence == 0.8
        assert action.expected_effectiveness == 0.7
        assert action.cost == 0.1


class TestDetectionPattern:
    """Test DetectionPattern data structure."""
    
    def test_detection_pattern_creation(self):
        """Test creating a detection pattern."""
        pattern = DetectionPattern(
            pattern_id="captcha_example_com",
            detection_type=DetectionType.CAPTCHA,
            frequency=5,
            success_rate=0.6,
            average_response_time=2.5,
            common_characteristics={
                "response_code": 403,
                "user_agent": "Mozilla/5.0",
                "severity": "high"
            },
            last_seen=time.time(),
            confidence=0.8
        )
        
        assert pattern.pattern_id == "captcha_example_com"
        assert pattern.detection_type == DetectionType.CAPTCHA
        assert pattern.frequency == 5
        assert pattern.success_rate == 0.6
        assert pattern.confidence == 0.8


class TestDetectionAnalyzer:
    """Test detection analyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = DetectionAnalyzer(max_events=1000)
        
        assert analyzer.max_events == 1000
        assert len(analyzer.detection_events) == 0
        assert len(analyzer.patterns) == 0
        assert analyzer.analyzer_stats['total_detections'] == 0
    
    def test_record_detection(self):
        """Test recording detection events."""
        analyzer = DetectionAnalyzer()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        analyzer.record_detection(event)
        
        assert len(analyzer.detection_events) == 1
        assert analyzer.analyzer_stats['total_detections'] == 1
        assert analyzer.analyzer_stats['detection_types']['captcha'] == 1
        assert analyzer.analyzer_stats['severity_levels']['high'] == 1
    
    def test_record_multiple_detections(self):
        """Test recording multiple detection events."""
        analyzer = DetectionAnalyzer()
        
        # Record different types of detections
        events = [
            DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            ),
            DetectionEvent(
                detection_type=DetectionType.RATE_LIMIT,
                severity=DetectionSeverity.MEDIUM,
                timestamp=time.time(),
                url="https://example.com/api",
                response_code=429,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
        ]
        
        for event in events:
            analyzer.record_detection(event)
        
        assert len(analyzer.detection_events) == 2
        assert analyzer.analyzer_stats['total_detections'] == 2
        assert analyzer.analyzer_stats['detection_types']['captcha'] == 1
        assert analyzer.analyzer_stats['detection_types']['rate_limit'] == 1
    
    def test_get_detection_patterns(self):
        """Test getting detection patterns."""
        analyzer = DetectionAnalyzer()
        
        # Record some detections to create patterns
        for i in range(3):
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            analyzer.record_detection(event)
        
        patterns = analyzer.get_detection_patterns()
        
        assert len(patterns) == 1  # Same URL pattern
        assert patterns[0].detection_type == DetectionType.CAPTCHA
        assert patterns[0].frequency == 3
    
    def test_get_patterns_by_type(self):
        """Test getting patterns by detection type."""
        analyzer = DetectionAnalyzer()
        
        # Record different types of detections
        events = [
            DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            ),
            DetectionEvent(
                detection_type=DetectionType.RATE_LIMIT,
                severity=DetectionSeverity.MEDIUM,
                timestamp=time.time(),
                url="https://example.com/api",
                response_code=429,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
        ]
        
        for event in events:
            analyzer.record_detection(event)
        
        captcha_patterns = analyzer.get_patterns_by_type(DetectionType.CAPTCHA)
        rate_limit_patterns = analyzer.get_patterns_by_type(DetectionType.RATE_LIMIT)
        
        assert len(captcha_patterns) == 1
        assert len(rate_limit_patterns) == 1
        assert captcha_patterns[0].detection_type == DetectionType.CAPTCHA
        assert rate_limit_patterns[0].detection_type == DetectionType.RATE_LIMIT
    
    def test_get_recent_patterns(self):
        """Test getting recent patterns."""
        analyzer = DetectionAnalyzer()
        
        # Record an old detection
        old_event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time() - 86400,  # 24 hours ago
            url="https://example.com/old",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        analyzer.record_detection(old_event)
        
        # Record a recent detection
        recent_event = DetectionEvent(
            detection_type=DetectionType.RATE_LIMIT,
            severity=DetectionSeverity.MEDIUM,
            timestamp=time.time(),
            url="https://example.com/recent",
            response_code=429,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        analyzer.record_detection(recent_event)
        
        recent_patterns = analyzer.get_recent_patterns(hours=12)
        
        # Should only include the recent pattern
        assert len(recent_patterns) == 1
        assert recent_patterns[0].detection_type == DetectionType.RATE_LIMIT
    
    def test_analyze_detection_trends(self):
        """Test detection trend analysis."""
        analyzer = DetectionAnalyzer()
        
        # Record some detections
        for i in range(5):
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time() - (i * 3600),  # Spread over 5 hours
                url=f"https://example.com/page{i}",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            analyzer.record_detection(event)
        
        trends = analyzer.analyze_detection_trends()
        
        assert 'last_hour' in trends
        assert 'last_24_hours' in trends
        assert 'last_week' in trends
        
        # Should have detections in last 24 hours
        assert trends['last_24_hours']['total_detections'] == 5
        assert trends['last_24_hours']['detection_types']['captcha'] == 5
    
    def test_get_adaptation_recommendations(self):
        """Test getting adaptation recommendations."""
        analyzer = DetectionAnalyzer()
        
        # Record frequent detections to trigger recommendations
        for i in range(5):
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            analyzer.record_detection(event)
        
        recommendations = analyzer.get_adaptation_recommendations()
        
        assert len(recommendations) > 0
        assert all(isinstance(rec, AdaptationAction) for rec in recommendations)
        assert all(rec.strategy == AdaptationStrategy.ROTATION for rec in recommendations)


class TestAdaptiveAntiDetectionManager:
    """Test adaptive anti-detection manager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = AdaptiveAntiDetectionManager()
        
        assert manager.analyzer is not None
        assert len(manager.active_strategies) == 0
        assert len(manager.strategy_history) == 0
        assert manager.learning_model is None
        assert len(manager.adaptation_rules) > 0
    
    @pytest.mark.asyncio
    async def test_handle_detection_captcha(self):
        """Test handling CAPTCHA detection."""
        manager = AdaptiveAntiDetectionManager()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        actions = await manager.handle_detection(event)
        
        assert len(actions) > 0
        assert all(isinstance(action, AdaptationAction) for action in actions)
        assert any(action.strategy == AdaptationStrategy.ROTATION for action in actions)
        
        # Check that event was recorded
        assert manager.analyzer.analyzer_stats['total_detections'] == 1
    
    @pytest.mark.asyncio
    async def test_handle_detection_rate_limit(self):
        """Test handling rate limit detection."""
        manager = AdaptiveAntiDetectionManager()
        
        event = DetectionEvent(
            detection_type=DetectionType.RATE_LIMIT,
            severity=DetectionSeverity.MEDIUM,
            timestamp=time.time(),
            url="https://example.com/api",
            response_code=429,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        actions = await manager.handle_detection(event)
        
        assert len(actions) > 0
        assert any(action.strategy == AdaptationStrategy.PASSIVE for action in actions)
    
    @pytest.mark.asyncio
    async def test_handle_detection_ip_block(self):
        """Test handling IP block detection."""
        manager = AdaptiveAntiDetectionManager()
        
        event = DetectionEvent(
            detection_type=DetectionType.IP_BLOCK,
            severity=DetectionSeverity.CRITICAL,
            timestamp=time.time(),
            url="https://example.com/blocked",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        actions = await manager.handle_detection(event)
        
        assert len(actions) > 0
        assert any(action.strategy == AdaptationStrategy.ROTATION for action in actions)
    
    @pytest.mark.asyncio
    async def test_handle_detection_behavior_analysis(self):
        """Test handling behavior analysis detection."""
        manager = AdaptiveAntiDetectionManager()
        
        event = DetectionEvent(
            detection_type=DetectionType.BEHAVIOR_ANALYSIS,
            severity=DetectionSeverity.MEDIUM,
            timestamp=time.time(),
            url="https://example.com/analyzed",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        actions = await manager.handle_detection(event)
        
        assert len(actions) > 0
        assert any(action.strategy == AdaptationStrategy.MIMICRY for action in actions)
    
    def test_get_adaptation_statistics(self):
        """Test getting adaptation statistics."""
        manager = AdaptiveAntiDetectionManager()
        
        # Add some strategy history
        action1 = AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={},
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.1,
            timestamp=time.time(),
            description="Test action 1"
        )
        action2 = AdaptationAction(
            strategy=AdaptationStrategy.PASSIVE,
            parameters={},
            confidence=0.9,
            expected_effectiveness=0.8,
            cost=0.05,
            timestamp=time.time(),
            description="Test action 2"
        )
        
        manager.strategy_history = [action1, action2]
        manager.active_strategies = {"rotation": action1}
        
        stats = manager.get_adaptation_statistics()
        
        assert stats['total_adaptations'] == 2
        assert stats['strategy_distribution']['rotation'] == 1
        assert stats['strategy_distribution']['passive'] == 1
        assert stats['success_rate'] > 0
        assert stats['average_effectiveness'] > 0
        assert stats['active_strategies'] == 1
    
    def test_get_detection_analysis(self):
        """Test getting detection analysis."""
        manager = AdaptiveAntiDetectionManager()
        
        # Record some detections
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        manager.analyzer.record_detection(event)
        
        analysis = manager.get_detection_analysis()
        
        assert 'analyzer_stats' in analysis
        assert 'trends' in analysis
        assert 'patterns' in analysis
        assert 'recent_patterns' in analysis
        assert analysis['patterns'] == 1
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        manager = AdaptiveAntiDetectionManager()
        
        # Add old data
        old_time = time.time() - 200 * 3600  # 200 hours ago
        
        old_action = AdaptationAction(
            strategy=AdaptationStrategy.ROTATION,
            parameters={},
            confidence=0.8,
            expected_effectiveness=0.7,
            cost=0.1,
            timestamp=old_time,
            description="Old action"
        )
        manager.strategy_history = [old_action]
        
        old_event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=old_time,
            url="https://example.com/old",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        manager.analyzer.record_detection(old_event)
        
        # Cleanup data older than 1 week (168 hours)
        manager.cleanup_old_data(max_age_hours=168)
        
        # Old data should be removed
        assert len(manager.strategy_history) == 0
        assert len(manager.analyzer.patterns) == 0


class TestLearningAntiDetection:
    """Test learning anti-detection functionality."""
    
    def test_learning_initialization(self):
        """Test learning system initialization."""
        learning = LearningAntiDetection()
        
        assert learning.feature_scaler is not None
        assert learning.detection_classifier is None
        assert learning.adaptation_predictor is None
        assert len(learning.training_data) == 0
        assert learning.is_trained is False
    
    def test_add_training_sample(self):
        """Test adding training samples."""
        learning = LearningAntiDetection()
        
        features = [1.0, 2.0, 3.0, 4.0, 5.0]
        learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        
        assert len(learning.training_data) == 1
        assert learning.training_data[0]['features'] == features
        assert learning.training_data[0]['detection_type'] == DetectionType.CAPTCHA
        assert learning.training_data[0]['adaptation_success'] is True
    
    def test_extract_features(self):
        """Test feature extraction from detection events."""
        learning = LearningAntiDetection()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={"Server": "nginx"},
            response_body="<html>CAPTCHA</html>",
            request_headers={"User-Agent": "Mozilla/5.0"},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        features = learning.extract_features(event)
        
        assert isinstance(features, list)
        assert len(features) > 0
        assert all(isinstance(f, (int, float)) for f in features)
        assert features[0] == 403  # Response code
        assert features[1] == 1.0  # Is 403
        assert features[2] == 0.0  # Is not 429
        assert features[3] == 0.0  # Is not 503
    
    def test_train_model_insufficient_data(self):
        """Test training model with insufficient data."""
        learning = LearningAntiDetection()
        
        # Add only a few training samples
        for i in range(5):
            features = [1.0, 2.0, 3.0, 4.0, 5.0]
            learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        
        result = learning.train_model()
        
        assert result is False
        assert learning.is_trained is False
    
    def test_train_model_sufficient_data(self):
        """Test training model with sufficient data."""
        learning = LearningAntiDetection()
        
        # Add enough training samples with correct feature count
        for i in range(150):
            # Use the same feature extraction as the actual system
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            features = learning.extract_features(event)
            learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        
        result = learning.train_model()
        
        assert result is True
        assert learning.is_trained is True
    
    def test_predict_detection_probability_not_trained(self):
        """Test prediction when model is not trained."""
        learning = LearningAntiDetection()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        probabilities = learning.predict_detection_probability(event)
        
        assert DetectionType.UNKNOWN in probabilities
        assert probabilities[DetectionType.UNKNOWN] == 1.0
    
    def test_predict_detection_probability_trained(self):
        """Test prediction when model is trained."""
        learning = LearningAntiDetection()
        
        # Train the model
        for i in range(150):
            features = [1.0, 2.0, 3.0, 4.0, 5.0]
            learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        learning.train_model()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        probabilities = learning.predict_detection_probability(event)
        
        assert len(probabilities) > 0
        assert all(0.0 <= prob <= 1.0 for prob in probabilities.values())
        assert abs(sum(probabilities.values()) - 1.0) < 0.01  # Should sum to 1
    
    def test_recommend_adaptation(self):
        """Test adaptation recommendations."""
        learning = LearningAntiDetection()
        
        # Train the model
        for i in range(150):
            features = [1.0, 2.0, 3.0, 4.0, 5.0]
            learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        learning.train_model()
        
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        recommendations = learning.recommend_adaptation(event)
        
        assert isinstance(recommendations, list)
        assert all(isinstance(rec, AdaptationAction) for rec in recommendations)


class TestAdaptiveAntiDetectionIntegration:
    """Integration tests for adaptive anti-detection."""
    
    @pytest.mark.asyncio
    async def test_complete_detection_handling_workflow(self):
        """Test complete detection handling workflow."""
        manager = AdaptiveAntiDetectionManager()
        
        # Simulate different types of detections
        detections = [
            DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            ),
            DetectionEvent(
                detection_type=DetectionType.RATE_LIMIT,
                severity=DetectionSeverity.MEDIUM,
                timestamp=time.time(),
                url="https://example.com/api",
                response_code=429,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
        ]
        
        all_actions = []
        for detection in detections:
            actions = await manager.handle_detection(detection)
            all_actions.extend(actions)
        
        # Should have generated adaptation actions
        assert len(all_actions) > 0
        assert all(isinstance(action, AdaptationAction) for action in all_actions)
        
        # Should have recorded detections
        assert manager.analyzer.analyzer_stats['total_detections'] == 2
    
    @pytest.mark.asyncio
    async def test_learning_integration(self):
        """Test integration with learning system."""
        learning = LearningAntiDetection()
        manager = AdaptiveAntiDetectionManager()
        
        # Add training data with correct feature count
        for i in range(150):
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            features = learning.extract_features(event)
            learning.add_training_sample(features, DetectionType.CAPTCHA, True)
        
        # Train the model
        learning.train_model()
        
        # Create detection event
        event = DetectionEvent(
            detection_type=DetectionType.CAPTCHA,
            severity=DetectionSeverity.HIGH,
            timestamp=time.time(),
            url="https://example.com/login",
            response_code=403,
            response_headers={},
            response_body="",
            request_headers={},
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            session_id="session1"
        )
        
        # Get ML recommendations
        ml_recommendations = learning.recommend_adaptation(event)
        
        # Get manager recommendations
        manager_actions = await manager.handle_detection(event)
        
        # Both should provide recommendations
        assert len(ml_recommendations) > 0
        assert len(manager_actions) > 0
        assert all(isinstance(action, AdaptationAction) for action in ml_recommendations)
        assert all(isinstance(action, AdaptationAction) for action in manager_actions)
    
    def test_pattern_learning_and_adaptation(self):
        """Test pattern learning and adaptation."""
        analyzer = DetectionAnalyzer()
        
        # Record multiple similar detections to create a pattern
        for i in range(10):
            event = DetectionEvent(
                detection_type=DetectionType.CAPTCHA,
                severity=DetectionSeverity.HIGH,
                timestamp=time.time(),
                url="https://example.com/login",
                response_code=403,
                response_headers={},
                response_body="",
                request_headers={},
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.1",
                session_id="session1"
            )
            analyzer.record_detection(event)
        
        # Should have created a pattern
        patterns = analyzer.get_detection_patterns()
        assert len(patterns) == 1
        assert patterns[0].frequency == 10
        assert patterns[0].detection_type == DetectionType.CAPTCHA
        
        # Should have recommendations
        recommendations = analyzer.get_adaptation_recommendations()
        assert len(recommendations) > 0
        assert all(rec.strategy == AdaptationStrategy.ROTATION for rec in recommendations)
    
    def test_adaptation_effectiveness_tracking(self):
        """Test tracking adaptation effectiveness."""
        manager = AdaptiveAntiDetectionManager()
        
        # Add some strategy history with different effectiveness levels
        actions = [
            AdaptationAction(
                strategy=AdaptationStrategy.ROTATION,
                parameters={},
                confidence=0.8,
                expected_effectiveness=0.7,
                cost=0.1,
                timestamp=time.time(),
                description="High effectiveness action"
            ),
            AdaptationAction(
                strategy=AdaptationStrategy.PASSIVE,
                parameters={},
                confidence=0.6,
                expected_effectiveness=0.4,
                cost=0.05,
                timestamp=time.time(),
                description="Low effectiveness action"
            )
        ]
        
        manager.strategy_history = actions
        
        stats = manager.get_adaptation_statistics()
        
        assert stats['total_adaptations'] == 2
        assert stats['average_effectiveness'] == 0.55  # (0.7 + 0.4) / 2
        assert stats['success_rate'] == 0.5  # 1 out of 2 > 0.5
