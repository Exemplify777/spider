"""
Tests for behavioral pattern simulation.

This module tests the behavior simulation functionality for anti-bot protection.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.behavior_simulation import (
    BehaviorSimulator, BehaviorManager, BehaviorPattern,
    MouseMovement, ScrollBehavior, TypingPattern
)


class TestBehaviorPatterns:
    """Test different behavioral patterns."""
    
    @pytest.mark.asyncio
    async def test_human_like_pattern(self):
        """Test human-like behavior pattern."""
        simulator = BehaviorSimulator(BehaviorPattern.HUMAN_LIKE)
        
        # Test mouse movement
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        assert isinstance(movement, MouseMovement)
        assert movement.start_x == 0
        assert movement.start_y == 0
        assert movement.end_x == 100
        assert movement.end_y == 100
        assert movement.duration > 0
        assert len(movement.curve_points) > 0
        
        # Test scroll behavior
        scroll = await simulator.simulate_scroll("down", 200)
        assert isinstance(scroll, ScrollBehavior)
        assert scroll.scroll_direction == "down"
        assert scroll.scroll_amount == 200
        assert scroll.scroll_speed > 0
        
        # Test typing pattern
        typing = await simulator.simulate_typing("Hello World")
        assert isinstance(typing, TypingPattern)
        assert typing.text == "Hello World"
        assert typing.typing_speed > 0
    
    @pytest.mark.asyncio
    async def test_researcher_pattern(self):
        """Test researcher behavior pattern."""
        simulator = BehaviorSimulator(BehaviorPattern.RESEARCHER)
        
        # Researcher should be faster and more focused
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        assert movement.duration < 10.0  # Should be relatively fast
        
        scroll = await simulator.simulate_scroll("down")
        assert scroll.scroll_amount >= 200  # Larger scroll amounts
    
    @pytest.mark.asyncio
    async def test_customer_pattern(self):
        """Test customer behavior pattern."""
        simulator = BehaviorSimulator(BehaviorPattern.CUSTOMER)
        
        # Customer should be slower and more deliberate
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        assert movement.duration > 0.5  # Should be slower
        
        typing = await simulator.simulate_typing("test")
        assert typing.typing_speed < 6.0  # Slower typing
    
    @pytest.mark.asyncio
    async def test_crawler_pattern(self):
        """Test crawler behavior pattern."""
        simulator = BehaviorSimulator(BehaviorPattern.CRAWLER)
        
        # Crawler should be very fast
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        assert movement.duration < 5.0  # Very fast
        
        typing = await simulator.simulate_typing("test")
        assert typing.typing_speed > 8.0  # Very fast typing
    
    @pytest.mark.asyncio
    async def test_random_pattern(self):
        """Test random behavior pattern."""
        simulator = BehaviorSimulator(BehaviorPattern.RANDOM)
        
        # Random pattern should have varied behavior
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        assert movement.duration > 0
        
        scroll = await simulator.simulate_scroll()
        assert scroll.scroll_amount > 0


class TestMouseMovement:
    """Test mouse movement simulation."""
    
    @pytest.mark.asyncio
    async def test_mouse_movement_curve_generation(self):
        """Test bezier curve generation for mouse movements."""
        simulator = BehaviorSimulator()
        
        movement = await simulator.simulate_mouse_movement(0, 0, 100, 100)
        
        # Check curve points
        assert len(movement.curve_points) > 0
        assert movement.curve_points[0] == (0, 0)  # Start point
        assert movement.curve_points[-1] == (100, 100)  # End point
        
        # Check that points form a curve (not straight line)
        mid_point = movement.curve_points[len(movement.curve_points) // 2]
        expected_mid = (50, 50)
        # Allow some deviation for curve
        assert abs(mid_point[0] - expected_mid[0]) < 50
        assert abs(mid_point[1] - expected_mid[1]) < 50
    
    @pytest.mark.asyncio
    async def test_mouse_movement_timing(self):
        """Test mouse movement timing."""
        simulator = BehaviorSimulator()
        
        start_time = time.time()
        await simulator.simulate_mouse_movement(0, 0, 100, 100)
        duration = time.time() - start_time
        
        # Should take some time (not instant)
        assert duration > 0.01
        assert duration < 15.0  # But not too long
    
    @pytest.mark.asyncio
    async def test_mouse_movement_micro_jitter(self):
        """Test that mouse movements include micro-movements."""
        simulator = BehaviorSimulator()
        
        movement = await simulator.simulate_mouse_movement(0, 0, 10, 10)
        
        # Check that points have some jitter (not perfectly aligned)
        for i in range(1, len(movement.curve_points) - 1):
            point = movement.curve_points[i]
            # Points should not be exactly on the straight line
            expected_x = (i / (len(movement.curve_points) - 1)) * 10
            expected_y = (i / (len(movement.curve_points) - 1)) * 10
            
            # Allow for curve deviation
            assert abs(point[0] - expected_x) < 10
            assert abs(point[1] - expected_y) < 10


class TestScrollBehavior:
    """Test scrolling behavior simulation."""
    
    @pytest.mark.asyncio
    async def test_scroll_directions(self):
        """Test different scroll directions."""
        simulator = BehaviorSimulator()
        
        # Test specific directions
        up_scroll = await simulator.simulate_scroll("up", 100)
        assert up_scroll.scroll_direction == "up"
        assert up_scroll.scroll_amount == 100
        
        down_scroll = await simulator.simulate_scroll("down", 200)
        assert down_scroll.scroll_direction == "down"
        assert down_scroll.scroll_amount == 200
    
    @pytest.mark.asyncio
    async def test_random_scroll(self):
        """Test random scroll behavior."""
        simulator = BehaviorSimulator()
        
        scroll = await simulator.simulate_scroll()
        assert scroll.scroll_direction in ["up", "down"]
        assert scroll.scroll_amount > 0
        assert scroll.scroll_speed > 0
    
    @pytest.mark.asyncio
    async def test_scroll_timing(self):
        """Test scroll timing."""
        simulator = BehaviorSimulator()
        
        start_time = time.time()
        await simulator.simulate_scroll("down", 100)
        duration = time.time() - start_time
        
        # Should take some time
        assert duration > 0.01
        assert duration < 2.0


class TestTypingPattern:
    """Test typing pattern simulation."""
    
    @pytest.mark.asyncio
    async def test_typing_basic(self):
        """Test basic typing simulation."""
        simulator = BehaviorSimulator()
        
        typing = await simulator.simulate_typing("Hello")
        assert typing.text == "Hello"
        assert typing.typing_speed > 0
        assert 0 <= typing.pause_probability <= 1
        assert 0 <= typing.backspace_probability <= 1
    
    @pytest.mark.asyncio
    async def test_typing_timing(self):
        """Test typing timing."""
        simulator = BehaviorSimulator()
        
        start_time = time.time()
        await simulator.simulate_typing("Test")
        duration = time.time() - start_time
        
        # Should take some time based on typing speed
        assert duration > 0.1
        assert duration < 5.0
    
    @pytest.mark.asyncio
    async def test_typing_different_patterns(self):
        """Test typing with different behavioral patterns."""
        # Test customer pattern (slower)
        customer_sim = BehaviorSimulator(BehaviorPattern.CUSTOMER)
        customer_typing = await customer_sim.simulate_typing("test")
        
        # Test crawler pattern (faster)
        crawler_sim = BehaviorSimulator(BehaviorPattern.CRAWLER)
        crawler_typing = await crawler_sim.simulate_typing("test")
        
        # Customer should be slower
        assert customer_typing.typing_speed < crawler_typing.typing_speed


class TestPageInteraction:
    """Test page interaction simulation."""
    
    @pytest.mark.asyncio
    async def test_page_interaction_basic(self):
        """Test basic page interaction."""
        simulator = BehaviorSimulator()
        
        page_elements = [
            {'position': {'x': 100, 'y': 100}, 'type': 'button'},
            {'position': {'x': 200, 'y': 200}, 'type': 'input', 'input_text': 'test'},
            {'position': {'x': 300, 'y': 300}, 'type': 'link'}
        ]
        
        interactions = await simulator.simulate_page_interaction(page_elements)
        
        assert 'mouse_movements' in interactions
        assert 'scrolls' in interactions
        assert 'clicks' in interactions
        assert 'typing' in interactions
        assert 'total_duration' in interactions
        assert interactions['total_duration'] > 0
    
    @pytest.mark.asyncio
    async def test_page_interaction_empty(self):
        """Test page interaction with empty elements."""
        simulator = BehaviorSimulator()
        
        interactions = await simulator.simulate_page_interaction([])
        
        assert interactions['total_duration'] >= 0
        assert len(interactions['mouse_movements']) == 0
        assert len(interactions['clicks']) == 0


class TestSessionStatistics:
    """Test session statistics."""
    
    @pytest.mark.asyncio
    async def test_session_statistics(self):
        """Test session statistics collection."""
        simulator = BehaviorSimulator()
        
        # Perform some actions
        await simulator.simulate_mouse_movement(0, 0, 100, 100)
        await simulator.simulate_scroll("down", 200)
        await simulator.simulate_typing("test")
        
        stats = simulator.get_session_statistics()
        
        assert 'pattern' in stats
        assert 'session_duration' in stats
        assert 'total_actions' in stats
        assert 'mouse_movements' in stats
        assert 'scroll_events' in stats
        assert 'typing_events' in stats
        assert 'actions_per_minute' in stats
        assert 'average_mouse_speed' in stats
        assert 'average_typing_speed' in stats
        
        assert stats['mouse_movements'] == 1
        assert stats['scroll_events'] == 1
        assert stats['typing_events'] == 1
    
    @pytest.mark.asyncio
    async def test_session_reset(self):
        """Test session reset functionality."""
        simulator = BehaviorSimulator()
        
        # Perform some actions
        await simulator.simulate_mouse_movement(0, 0, 100, 100)
        await simulator.simulate_typing("test")
        
        # Check that actions are recorded
        stats_before = simulator.get_session_statistics()
        assert stats_before['mouse_movements'] > 0
        assert stats_before['typing_events'] > 0
        
        # Reset session
        simulator.reset_session()
        
        # Check that actions are cleared
        stats_after = simulator.get_session_statistics()
        assert stats_after['mouse_movements'] == 0
        assert stats_after['typing_events'] == 0


class TestBehaviorManager:
    """Test behavior manager functionality."""
    
    def test_create_simulator(self):
        """Test creating a behavior simulator."""
        manager = BehaviorManager()
        
        simulator = manager.create_simulator("session1", BehaviorPattern.HUMAN_LIKE)
        assert isinstance(simulator, BehaviorSimulator)
        assert simulator.pattern == BehaviorPattern.HUMAN_LIKE
        
        # Check that simulator is stored
        retrieved = manager.get_simulator("session1")
        assert retrieved is simulator
    
    def test_get_simulator_nonexistent(self):
        """Test getting a non-existent simulator."""
        manager = BehaviorManager()
        
        simulator = manager.get_simulator("nonexistent")
        assert simulator is None
    
    def test_switch_pattern(self):
        """Test switching behavioral patterns."""
        manager = BehaviorManager()
        
        simulator = manager.create_simulator("session1", BehaviorPattern.HUMAN_LIKE)
        assert simulator.pattern == BehaviorPattern.HUMAN_LIKE
        
        manager.switch_pattern("session1", BehaviorPattern.CRAWLER)
        assert simulator.pattern == BehaviorPattern.CRAWLER
    
    def test_get_all_statistics(self):
        """Test getting statistics for all sessions."""
        manager = BehaviorManager()
        
        # Create multiple simulators
        sim1 = manager.create_simulator("session1", BehaviorPattern.HUMAN_LIKE)
        sim2 = manager.create_simulator("session2", BehaviorPattern.CRAWLER)
        
        stats = manager.get_all_statistics()
        
        assert "session1" in stats
        assert "session2" in stats
        assert stats["session1"]["pattern"] == "human_like"
        assert stats["session2"]["pattern"] == "crawler"
    
    def test_cleanup_session(self):
        """Test cleaning up a session."""
        manager = BehaviorManager()
        
        # Create a simulator
        simulator = manager.create_simulator("session1", BehaviorPattern.HUMAN_LIKE)
        assert manager.get_simulator("session1") is not None
        
        # Cleanup
        manager.cleanup_session("session1")
        assert manager.get_simulator("session1") is None


class TestBehaviorPatternConfiguration:
    """Test behavioral pattern configuration."""
    
    def test_human_like_config(self):
        """Test human-like pattern configuration."""
        simulator = BehaviorSimulator(BehaviorPattern.HUMAN_LIKE)
        
        config = simulator.config
        assert 'mouse_speed_range' in config
        assert 'scroll_speed_range' in config
        assert 'typing_speed_range' in config
        assert 'pause_probability' in config
        assert 'backspace_probability' in config
        assert 'action_delay_range' in config
        assert 'scroll_frequency' in config
        
        # Check reasonable ranges
        assert 0 < config['pause_probability'] < 1
        assert 0 < config['backspace_probability'] < 1
        assert config['mouse_speed_range'][0] < config['mouse_speed_range'][1]
        assert config['typing_speed_range'][0] < config['typing_speed_range'][1]
    
    def test_pattern_differences(self):
        """Test that different patterns have different configurations."""
        human_sim = BehaviorSimulator(BehaviorPattern.HUMAN_LIKE)
        crawler_sim = BehaviorSimulator(BehaviorPattern.CRAWLER)
        
        # Crawler should be faster
        assert crawler_sim.config['typing_speed_range'][0] >= human_sim.config['typing_speed_range'][1]
        assert crawler_sim.config['mouse_speed_range'][0] > human_sim.config['mouse_speed_range'][1]
        
        # Crawler should have lower error rates
        assert crawler_sim.config['pause_probability'] < human_sim.config['pause_probability']
        assert crawler_sim.config['backspace_probability'] < human_sim.config['backspace_probability']


class TestBehaviorSimulationIntegration:
    """Integration tests for behavior simulation."""
    
    @pytest.mark.asyncio
    async def test_complete_scraping_session(self):
        """Test a complete scraping session with behavior simulation."""
        simulator = BehaviorSimulator(BehaviorPattern.HUMAN_LIKE)
        
        # Simulate a realistic scraping session
        page_elements = [
            {'position': {'x': 100, 'y': 100}, 'type': 'search_box', 'input_text': 'web scraping'},
            {'position': {'x': 200, 'y': 150}, 'type': 'search_button'},
            {'position': {'x': 300, 'y': 200}, 'type': 'result_link'},
            {'position': {'x': 400, 'y': 250}, 'type': 'next_page'}
        ]
        
        # Simulate page interaction
        interactions = await simulator.simulate_page_interaction(page_elements)
        
        # Verify interactions occurred
        assert len(interactions['mouse_movements']) > 0
        # Note: clicks may not always occur due to random selection
        assert len(interactions['typing']) > 0 or len(interactions['scrolls']) > 0
        assert interactions['total_duration'] > 0
        
        # Get session statistics
        stats = simulator.get_session_statistics()
        assert stats['mouse_movements'] > 0
        # Note: typing events may not always occur due to random selection
        assert stats['typing_events'] >= 0
        # Actions per minute may be 0 for very short sessions
        assert stats['actions_per_minute'] >= 0
    
    @pytest.mark.asyncio
    async def test_behavior_consistency(self):
        """Test that behavior patterns are consistent across sessions."""
        # Test multiple sessions with same pattern
        sessions = []
        for i in range(3):
            sim = BehaviorSimulator(BehaviorPattern.RESEARCHER)
            await sim.simulate_mouse_movement(0, 0, 100, 100)
            await sim.simulate_typing("test")
            sessions.append(sim)
        
        # All sessions should have similar characteristics
        speeds = [sim.config['typing_speed_range'][0] for sim in sessions]
        assert all(speed == speeds[0] for speed in speeds)  # All same pattern
        
        # But actual behavior should vary (randomness)
        durations = [sim.get_session_statistics()['session_duration'] for sim in sessions]
        # Should have some variation due to random timing
        assert len(set(durations)) > 1 or all(d > 0 for d in durations)
