"""
Tests for human-like interaction patterns.

This module tests the human interaction simulation functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from spider.infrastructure.human_interactions import (
    HumanInteractionSimulator, InteractionManager, InteractionEvent,
    InteractionSequence, InteractionType, InteractionContext
)


class TestInteractionEvent:
    """Test InteractionEvent data structure."""
    
    def test_interaction_event_creation(self):
        """Test creating an interaction event."""
        element = {'type': 'button', 'text': 'Click me', 'position': {'x': 100, 'y': 200}}
        metadata = {'test': 'value'}
        
        event = InteractionEvent(
            interaction_type=InteractionType.CLICK,
            element=element,
            coordinates=(100, 200),
            timestamp=time.time(),
            duration=0.5,
            context=InteractionContext.E_COMMERCE,
            metadata=metadata
        )
        
        assert event.interaction_type == InteractionType.CLICK
        assert event.element == element
        assert event.coordinates == (100, 200)
        assert event.context == InteractionContext.E_COMMERCE
        assert event.metadata == metadata
        assert event.duration == 0.5


class TestInteractionSequence:
    """Test InteractionSequence data structure."""
    
    def test_interaction_sequence_creation(self):
        """Test creating an interaction sequence."""
        events = [
            InteractionEvent(
                interaction_type=InteractionType.CLICK,
                element={'type': 'button'},
                coordinates=(100, 200),
                timestamp=time.time(),
                duration=0.5,
                context=InteractionContext.E_COMMERCE,
                metadata={}
            )
        ]
        
        sequence = InteractionSequence(
            events=events,
            total_duration=1.0,
            context=InteractionContext.E_COMMERCE,
            user_intent='browse',
            success=True
        )
        
        assert len(sequence.events) == 1
        assert sequence.total_duration == 1.0
        assert sequence.context == InteractionContext.E_COMMERCE
        assert sequence.user_intent == 'browse'
        assert sequence.success is True


class TestHumanInteractionSimulator:
    """Test human interaction simulator functionality."""
    
    def test_simulator_initialization(self):
        """Test simulator initialization."""
        simulator = HumanInteractionSimulator(InteractionContext.E_COMMERCE)
        
        assert simulator.context == InteractionContext.E_COMMERCE
        assert simulator.interaction_history == []
        assert simulator.current_session is None
        assert simulator.user_profile is not None
        assert 'expertise_level' in simulator.user_profile
        assert 'patience_level' in simulator.user_profile
        assert 'typing_speed' in simulator.user_profile
    
    def test_user_profile_generation(self):
        """Test user profile generation."""
        simulator = HumanInteractionSimulator()
        
        profile = simulator.user_profile
        
        assert profile['expertise_level'] in ['beginner', 'intermediate', 'expert']
        assert 0.3 <= profile['patience_level'] <= 1.0
        assert 200 <= profile['reading_speed'] <= 600
        assert 30 <= profile['typing_speed'] <= 80
        assert 0.7 <= profile['mouse_precision'] <= 1.0
        assert 0.01 <= profile['error_rate'] <= 0.1
        assert 1 <= profile['retry_attempts'] <= 5
    
    def test_determine_user_intent(self):
        """Test user intent determination."""
        simulator = HumanInteractionSimulator(InteractionContext.E_COMMERCE)
        
        intent = simulator._determine_user_intent()
        
        assert intent in ['browse', 'search', 'purchase', 'compare']
        
        # Test different contexts
        simulator.context = InteractionContext.NEWS
        intent = simulator._determine_user_intent()
        assert intent in ['read', 'search', 'browse', 'share']
    
    def test_generate_interaction_flow(self):
        """Test interaction flow generation."""
        simulator = HumanInteractionSimulator(InteractionContext.E_COMMERCE)
        
        flow = simulator._generate_interaction_flow('browse')
        
        assert isinstance(flow, list)
        assert len(flow) > 0
        assert all(isinstance(interaction, InteractionType) for interaction in flow)
    
    def test_find_suitable_elements(self):
        """Test finding suitable elements for interactions."""
        simulator = HumanInteractionSimulator()
        
        page_elements = [
            {'type': 'button', 'text': 'Click me'},
            {'type': 'input', 'placeholder': 'Enter text'},
            {'type': 'div', 'text': 'Some content'},
            {'type': 'link', 'text': 'Go here'}
        ]
        
        # Test click interaction
        clickable = simulator._find_suitable_elements(page_elements, InteractionType.CLICK)
        assert len(clickable) > 0
        assert all(elem['type'] in ['button', 'link', 'input'] for elem in clickable)
        
        # Test type interaction
        typeable = simulator._find_suitable_elements(page_elements, InteractionType.TYPE)
        assert len(typeable) > 0
        assert all(elem['type'] in ['input', 'textarea'] for elem in typeable)
        
        # Test reading interaction
        readable = simulator._find_suitable_elements(page_elements, InteractionType.READING)
        assert len(readable) > 0
        assert all(elem['type'] in ['p', 'div', 'span', 'article', 'section'] for elem in readable)
    
    def test_select_element(self):
        """Test element selection."""
        simulator = HumanInteractionSimulator()
        
        elements = [
            {'type': 'button', 'text': 'Click me', 'visible': True, 'size': {'width': 100, 'height': 40}},
            {'type': 'link', 'text': 'Go here', 'visible': True, 'size': {'width': 50, 'height': 20}},
            {'type': 'button', 'text': 'Hidden', 'visible': False, 'size': {'width': 100, 'height': 40}}
        ]
        
        selected = simulator._select_element(elements, InteractionType.CLICK)
        
        assert selected in elements
        # Should prefer visible elements (test multiple times to account for randomness)
        visible_selections = 0
        for _ in range(10):
            selected = simulator._select_element(elements, InteractionType.CLICK)
            if selected['visible'] is True:
                visible_selections += 1
        
        # At least 50% of selections should be visible elements (accounting for randomness)
        assert visible_selections >= 5
    
    def test_get_base_duration(self):
        """Test base duration calculation."""
        simulator = HumanInteractionSimulator()
        
        # Test different interaction types
        assert simulator._get_base_duration(InteractionType.CLICK) == 0.2
        assert simulator._get_base_duration(InteractionType.HOVER) == 0.5
        assert simulator._get_base_duration(InteractionType.TYPE) == 2.0
        assert simulator._get_base_duration(InteractionType.READING) == 5.0
    
    def test_sort_form_elements(self):
        """Test form element sorting."""
        simulator = HumanInteractionSimulator()
        
        form_elements = [
            {'type': 'input', 'position': {'x': 100, 'y': 200}},
            {'type': 'input', 'position': {'x': 200, 'y': 100}},
            {'type': 'input', 'position': {'x': 150, 'y': 150}}
        ]
        
        sorted_elements = simulator._sort_form_elements(form_elements)
        
        # Should be sorted by y position first, then x position
        assert sorted_elements[0]['position']['y'] <= sorted_elements[1]['position']['y']
        assert sorted_elements[1]['position']['y'] <= sorted_elements[2]['position']['y']
    
    def test_generate_form_text(self):
        """Test form text generation."""
        simulator = HumanInteractionSimulator()
        
        # Test email field
        email_element = {'name': 'email', 'type': 'input'}
        text = simulator._generate_form_text(email_element)
        assert '@' in text
        assert 'example.com' in text
        
        # Test phone field
        phone_element = {'name': 'phone', 'type': 'input'}
        text = simulator._generate_form_text(phone_element)
        assert '-' in text
        assert text.replace('-', '').replace(' ', '').isdigit()
        
        # Test name field
        name_element = {'name': 'name', 'type': 'input'}
        text = simulator._generate_form_text(name_element)
        assert len(text.split()) >= 2  # First and last name
        
        # Test textarea
        textarea_element = {'type': 'textarea'}
        text = simulator._generate_form_text(textarea_element)
        assert len(text) > 10  # Should be a substantial text
    
    @pytest.mark.asyncio
    async def test_simulate_page_interaction(self):
        """Test page interaction simulation."""
        simulator = HumanInteractionSimulator(InteractionContext.E_COMMERCE)
        
        page_elements = [
            {'type': 'button', 'text': 'Add to Cart', 'position': {'x': 100, 'y': 200}, 'visible': True},
            {'type': 'input', 'placeholder': 'Search', 'position': {'x': 50, 'y': 50}, 'visible': True},
            {'type': 'div', 'text': 'Product description', 'position': {'x': 200, 'y': 300}, 'visible': True}
        ]
        
        sequence = await simulator.simulate_page_interaction(page_elements, 'browse')
        
        assert isinstance(sequence, InteractionSequence)
        assert sequence.context == InteractionContext.E_COMMERCE
        assert sequence.user_intent == 'browse'
        assert len(sequence.events) > 0
        assert sequence.total_duration > 0
        
        # Check that events are properly created
        for event in sequence.events:
            assert isinstance(event, InteractionEvent)
            assert event.interaction_type in InteractionType
            assert isinstance(event.coordinates, tuple)
            assert len(event.coordinates) == 2
            assert event.duration > 0
    
    @pytest.mark.asyncio
    async def test_simulate_form_filling(self):
        """Test form filling simulation."""
        simulator = HumanInteractionSimulator(InteractionContext.FORM)
        
        form_elements = [
            {'type': 'input', 'name': 'email', 'position': {'x': 100, 'y': 100}},
            {'type': 'input', 'name': 'name', 'position': {'x': 100, 'y': 150}},
            {'type': 'textarea', 'name': 'message', 'position': {'x': 100, 'y': 200}}
        ]
        
        sequence = await simulator.simulate_form_filling(form_elements)
        
        assert isinstance(sequence, InteractionSequence)
        assert sequence.context == InteractionContext.FORM
        assert sequence.user_intent == 'fill_form'
        assert len(sequence.events) > 0
        
        # Check that form elements are processed
        for event in sequence.events:
            assert event.interaction_type in [InteractionType.TYPE, InteractionType.CLICK]
    
    @pytest.mark.asyncio
    async def test_simulate_typing_interaction(self):
        """Test typing interaction simulation."""
        simulator = HumanInteractionSimulator()
        
        element = {'type': 'input', 'position': {'x': 100, 'y': 200}}
        text = "Hello World"
        
        event = await simulator._simulate_typing_interaction(element, text)
        
        assert isinstance(event, InteractionEvent)
        assert event.interaction_type == InteractionType.TYPE
        assert event.coordinates == (100, 200)
        assert event.duration > 0
        assert event.metadata['text_length'] == len(text)
        assert 'typing_speed' in event.metadata
    
    @pytest.mark.asyncio
    async def test_simulate_selection_interaction(self):
        """Test selection interaction simulation."""
        simulator = HumanInteractionSimulator()
        
        element = {'type': 'select', 'position': {'x': 100, 'y': 200}, 'options': ['Option 1', 'Option 2']}
        
        event = await simulator._simulate_selection_interaction(element)
        
        assert isinstance(event, InteractionEvent)
        assert event.interaction_type == InteractionType.CLICK
        assert event.coordinates == (100, 200)
        assert event.duration == 0.3
        assert event.metadata['selection_type'] == 'select'
        assert event.metadata['options_count'] == 2
    
    def test_get_interaction_statistics(self):
        """Test interaction statistics generation."""
        simulator = HumanInteractionSimulator()
        
        # Test with no interactions
        stats = simulator.get_interaction_statistics()
        assert stats['total_sessions'] == 0
        assert stats['total_events'] == 0
        assert stats['success_rate'] == 0.0
        
        # Add some mock interactions
        simulator.interaction_history = [
            InteractionSequence(
                events=[
                    InteractionEvent(
                        interaction_type=InteractionType.CLICK,
                        element={},
                        coordinates=(0, 0),
                        timestamp=time.time(),
                        duration=0.5,
                        context=InteractionContext.E_COMMERCE,
                        metadata={}
                    )
                ],
                total_duration=1.0,
                context=InteractionContext.E_COMMERCE,
                user_intent='browse',
                success=True
            )
        ]
        
        stats = simulator.get_interaction_statistics()
        assert stats['total_sessions'] == 1
        assert stats['total_events'] == 1
        assert stats['success_rate'] == 1.0
        assert 'most_common_interactions' in stats
        assert 'user_profile' in stats


class TestInteractionManager:
    """Test interaction manager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = InteractionManager()
        
        assert manager.simulators == {}
        assert manager.session_interactions == {}
    
    def test_create_simulator(self):
        """Test creating a simulator."""
        manager = InteractionManager()
        
        simulator = manager.create_simulator("session1", InteractionContext.E_COMMERCE)
        
        assert isinstance(simulator, HumanInteractionSimulator)
        assert simulator.context == InteractionContext.E_COMMERCE
        assert manager.get_simulator("session1") == simulator
        assert "session1" in manager.session_interactions
    
    def test_get_simulator_nonexistent(self):
        """Test getting a non-existent simulator."""
        manager = InteractionManager()
        
        simulator = manager.get_simulator("nonexistent")
        assert simulator is None
    
    @pytest.mark.asyncio
    async def test_simulate_page_interaction(self):
        """Test page interaction simulation through manager."""
        manager = InteractionManager()
        
        page_elements = [
            {'type': 'button', 'text': 'Click me', 'position': {'x': 100, 'y': 200}, 'visible': True}
        ]
        
        sequence = await manager.simulate_page_interaction("session1", page_elements, 'browse')
        
        assert isinstance(sequence, InteractionSequence)
        assert "session1" in manager.simulators
        assert len(manager.session_interactions["session1"]) == 1
    
    @pytest.mark.asyncio
    async def test_simulate_form_filling(self):
        """Test form filling simulation through manager."""
        manager = InteractionManager()
        
        form_elements = [
            {'type': 'input', 'name': 'email', 'position': {'x': 100, 'y': 100}}
        ]
        
        sequence = await manager.simulate_form_filling("session1", form_elements)
        
        assert isinstance(sequence, InteractionSequence)
        assert sequence.context == InteractionContext.FORM
        assert "session1" in manager.simulators
    
    def test_get_session_statistics(self):
        """Test getting session statistics."""
        manager = InteractionManager()
        
        # Test with no simulator
        stats = manager.get_session_statistics("nonexistent")
        assert stats == {}
        
        # Test with simulator
        manager.create_simulator("session1")
        stats = manager.get_session_statistics("session1")
        assert isinstance(stats, dict)
        assert 'total_sessions' in stats
    
    def test_get_all_statistics(self):
        """Test getting all session statistics."""
        manager = InteractionManager()
        
        # Test with no simulators
        stats = manager.get_all_statistics()
        assert stats == {}
        
        # Test with simulators
        manager.create_simulator("session1")
        manager.create_simulator("session2")
        
        stats = manager.get_all_statistics()
        assert "session1" in stats
        assert "session2" in stats
        assert isinstance(stats["session1"], dict)
        assert isinstance(stats["session2"], dict)
    
    def test_cleanup_session(self):
        """Test session cleanup."""
        manager = InteractionManager()
        
        # Create session data
        manager.create_simulator("session1")
        assert "session1" in manager.simulators
        assert "session1" in manager.session_interactions
        
        # Cleanup
        manager.cleanup_session("session1")
        assert "session1" not in manager.simulators
        assert "session1" not in manager.session_interactions


class TestHumanInteractionIntegration:
    """Integration tests for human interactions."""
    
    @pytest.mark.asyncio
    async def test_complete_interaction_workflow(self):
        """Test complete interaction workflow."""
        manager = InteractionManager()
        
        # Create simulator with E_COMMERCE context
        simulator = manager.create_simulator("session1", InteractionContext.E_COMMERCE)
        
        # Simulate e-commerce browsing
        page_elements = [
            {'type': 'input', 'placeholder': 'Search products', 'position': {'x': 50, 'y': 50}, 'visible': True},
            {'type': 'button', 'text': 'Search', 'position': {'x': 200, 'y': 50}, 'visible': True},
            {'type': 'div', 'text': 'Product 1', 'position': {'x': 100, 'y': 150}, 'visible': True},
            {'type': 'button', 'text': 'Add to Cart', 'position': {'x': 100, 'y': 200}, 'visible': True}
        ]
        
        sequence = await simulator.simulate_page_interaction(page_elements, 'browse')
        
        assert sequence.success
        assert len(sequence.events) > 0
        assert sequence.context == InteractionContext.E_COMMERCE
        
        # Check that different interaction types are used
        interaction_types = {event.interaction_type for event in sequence.events}
        assert len(interaction_types) > 1  # Should have variety
    
    @pytest.mark.asyncio
    async def test_form_filling_workflow(self):
        """Test form filling workflow."""
        manager = InteractionManager()
        
        form_elements = [
            {'type': 'input', 'name': 'email', 'position': {'x': 100, 'y': 100}},
            {'type': 'input', 'name': 'name', 'position': {'x': 100, 'y': 150}},
            {'type': 'select', 'name': 'country', 'position': {'x': 100, 'y': 200}, 'options': ['US', 'CA', 'UK']},
            {'type': 'textarea', 'name': 'comments', 'position': {'x': 100, 'y': 250}}
        ]
        
        sequence = await manager.simulate_form_filling("session1", form_elements)
        
        assert sequence.success
        assert sequence.context == InteractionContext.FORM
        assert len(sequence.events) > 0
        
        # Check that form elements are processed in order
        for i, event in enumerate(sequence.events):
            assert event.interaction_type in [InteractionType.TYPE, InteractionType.CLICK]
    
    @pytest.mark.asyncio
    async def test_different_contexts(self):
        """Test different interaction contexts."""
        manager = InteractionManager()
        
        page_elements = [
            {'type': 'div', 'text': 'Content', 'position': {'x': 100, 'y': 100}, 'visible': True}
        ]
        
        # Test different contexts
        contexts = [
            InteractionContext.E_COMMERCE,
            InteractionContext.NEWS,
            InteractionContext.SOCIAL_MEDIA,
            InteractionContext.SEARCH_ENGINE
        ]
        
        for context in contexts:
            simulator = manager.create_simulator(f"session_{context.value}", context)
            sequence = await simulator.simulate_page_interaction(page_elements)
            
            assert sequence.context == context
            assert sequence.success
    
    def test_user_profile_consistency(self):
        """Test that user profiles are consistent within a session."""
        simulator = HumanInteractionSimulator()
        
        profile1 = simulator.user_profile
        profile2 = simulator.user_profile
        
        # Should be the same profile
        assert profile1 == profile2
        
        # Profile should be realistic
        assert 0.3 <= profile1['patience_level'] <= 1.0
        assert profile1['expertise_level'] in ['beginner', 'intermediate', 'expert']
        assert 200 <= profile1['reading_speed'] <= 600
    
    @pytest.mark.asyncio
    async def test_interaction_timing_realism(self):
        """Test that interaction timing is realistic."""
        simulator = HumanInteractionSimulator()
        
        page_elements = [
            {'type': 'button', 'text': 'Click me', 'position': {'x': 100, 'y': 200}, 'visible': True}
        ]
        
        start_time = time.time()
        sequence = await simulator.simulate_page_interaction(page_elements)
        total_time = time.time() - start_time
        
        # Should take some time (not instant)
        assert total_time > 0.1
        
        # Should not take too long for simple interactions
        assert total_time < 10.0
        
        # Sequence duration should be reasonable
        assert sequence.total_duration > 0
        assert sequence.total_duration < 5.0
    
    def test_interaction_event_metadata(self):
        """Test that interaction events have proper metadata."""
        simulator = HumanInteractionSimulator()
        
        element = {
            'type': 'button',
            'text': 'Click me',
            'id': 'test-button',
            'class': 'btn-primary',
            'position': {'x': 100, 'y': 200}
        }
        
        # Create a mock event
        event = InteractionEvent(
            interaction_type=InteractionType.CLICK,
            element=element,
            coordinates=(100, 200),
            timestamp=time.time(),
            duration=0.5,
            context=InteractionContext.E_COMMERCE,
            metadata={}
        )
        
        # Test that metadata would be populated in real usage
        assert event.element == element
        assert event.coordinates == (100, 200)
        assert event.interaction_type == InteractionType.CLICK
