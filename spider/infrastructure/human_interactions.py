"""
Human-like interaction patterns for web scraping.

This module provides sophisticated human-like interaction patterns that build upon
behavioral simulation to create more realistic web scraping behavior.
"""

import asyncio
import random
import time
import math
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from urllib.parse import urlparse, urljoin


class InteractionType(Enum):
    """Types of human interactions."""
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"
    DRAG = "drag"
    SWIPE = "swipe"
    PINCH = "pinch"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    LONG_PRESS = "long_press"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    FORM_FILL = "form_fill"
    SEARCH = "search"
    NAVIGATION = "navigation"
    READING = "reading"
    BROWSING = "browsing"


class InteractionContext(Enum):
    """Context for interactions."""
    GENERAL = "general"
    E_COMMERCE = "e_commerce"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    SEARCH_ENGINE = "search_engine"
    BLOG = "blog"
    FORUM = "forum"
    DOCUMENTATION = "documentation"
    GALLERY = "gallery"
    VIDEO = "video"
    FORM = "form"
    DASHBOARD = "dashboard"
    CATALOG = "catalog"


@dataclass
class InteractionEvent:
    """Represents a human interaction event."""
    interaction_type: InteractionType
    element: Dict[str, Any]
    coordinates: Tuple[int, int]
    timestamp: float
    duration: float
    context: InteractionContext
    metadata: Dict[str, Any]


@dataclass
class InteractionSequence:
    """Represents a sequence of human interactions."""
    events: List[InteractionEvent]
    total_duration: float
    context: InteractionContext
    user_intent: str
    success: bool


class HumanInteractionSimulator:
    """Simulates human-like interactions for web scraping."""
    
    def __init__(self, context: InteractionContext = InteractionContext.GENERAL):
        """Initialize the human interaction simulator.
        
        Args:
            context: The context for interactions
        """
        self.context = context
        self.interaction_history = []
        self.current_session = None
        self.user_profile = self._generate_user_profile()
        
        # Load interaction patterns for different contexts
        self._load_interaction_patterns()
    
    def _generate_user_profile(self) -> Dict[str, Any]:
        """Generate a user profile for realistic interactions."""
        return {
            'expertise_level': random.choice(['beginner', 'intermediate', 'expert']),
            'patience_level': random.uniform(0.3, 1.0),
            'reading_speed': random.uniform(200, 600),  # words per minute
            'typing_speed': random.uniform(30, 80),  # words per minute
            'mouse_precision': random.uniform(0.7, 1.0),
            'preferred_interactions': random.sample(list(InteractionType), random.randint(3, 8)),
            'attention_span': random.uniform(30, 300),  # seconds
            'error_rate': random.uniform(0.01, 0.1),
            'retry_attempts': random.randint(1, 5)
        }
    
    def _load_interaction_patterns(self):
        """Load interaction patterns for different contexts."""
        self.patterns = {
            InteractionContext.E_COMMERCE: {
                'common_flows': [
                    ['search', 'browse', 'click', 'read', 'add_to_cart'],
                    ['browse', 'filter', 'sort', 'click', 'read', 'compare'],
                    ['search', 'click', 'read', 'navigate_back', 'search']
                ],
                'interaction_weights': {
                    InteractionType.CLICK: 0.4,
                    InteractionType.HOVER: 0.2,
                    InteractionType.SCROLL: 0.2,
                    InteractionType.TYPE: 0.1,
                    InteractionType.READING: 0.1
                }
            },
            InteractionContext.NEWS: {
                'common_flows': [
                    ['scroll', 'read', 'click', 'read', 'scroll'],
                    ['search', 'click', 'read', 'scroll', 'click'],
                    ['browse', 'click', 'read', 'navigate_back', 'browse']
                ],
                'interaction_weights': {
                    InteractionType.SCROLL: 0.3,
                    InteractionType.CLICK: 0.3,
                    InteractionType.READING: 0.2,
                    InteractionType.HOVER: 0.1,
                    InteractionType.TYPE: 0.1
                }
            },
            InteractionContext.SOCIAL_MEDIA: {
                'common_flows': [
                    ['scroll', 'hover', 'click', 'type', 'click'],
                    ['scroll', 'click', 'read', 'type', 'click'],
                    ['search', 'click', 'scroll', 'hover', 'click']
                ],
                'interaction_weights': {
                    InteractionType.SCROLL: 0.4,
                    InteractionType.CLICK: 0.3,
                    InteractionType.HOVER: 0.1,
                    InteractionType.TYPE: 0.1,
                    InteractionType.READING: 0.1
                }
            },
            InteractionContext.SEARCH_ENGINE: {
                'common_flows': [
                    ['type', 'click', 'read', 'scroll', 'click'],
                    ['type', 'click', 'read', 'navigate_back', 'type'],
                    ['type', 'click', 'scroll', 'click', 'read']
                ],
                'interaction_weights': {
                    InteractionType.TYPE: 0.3,
                    InteractionType.CLICK: 0.3,
                    InteractionType.READING: 0.2,
                    InteractionType.SCROLL: 0.1,
                    InteractionType.HOVER: 0.1
                }
            },
            InteractionContext.FORM: {
                'common_flows': [
                    ['type', 'click', 'type', 'click', 'type'],
                    ['click', 'type', 'hover', 'click', 'type'],
                    ['type', 'hover', 'type', 'click', 'type']
                ],
                'interaction_weights': {
                    InteractionType.TYPE: 0.5,
                    InteractionType.CLICK: 0.3,
                    InteractionType.HOVER: 0.1,
                    InteractionType.READING: 0.1
                }
            }
        }
    
    async def simulate_page_interaction(self, page_elements: List[Dict[str, Any]], 
                                      user_intent: str = None) -> InteractionSequence:
        """Simulate human-like interaction with a page.
        
        Args:
            page_elements: List of page elements to interact with
            user_intent: The user's intent (e.g., 'search', 'browse', 'purchase')
            
        Returns:
            InteractionSequence with all interaction events
        """
        if not user_intent:
            user_intent = self._determine_user_intent()
        
        # Generate interaction flow based on context and intent
        flow = self._generate_interaction_flow(user_intent)
        
        events = []
        start_time = time.time()
        
        for interaction_type in flow:
            # Find suitable elements for this interaction
            suitable_elements = self._find_suitable_elements(page_elements, interaction_type)
            
            if not suitable_elements:
                continue
            
            # Select element based on user profile and context
            element = self._select_element(suitable_elements, interaction_type)
            
            # Generate interaction event
            event = await self._generate_interaction_event(
                interaction_type, element, user_intent
            )
            
            events.append(event)
            
            # Add realistic delays between interactions
            await self._add_interaction_delay(interaction_type, event)
        
        total_duration = time.time() - start_time
        
        sequence = InteractionSequence(
            events=events,
            total_duration=total_duration,
            context=self.context,
            user_intent=user_intent,
            success=len(events) > 0
        )
        
        self.interaction_history.append(sequence)
        return sequence
    
    def _determine_user_intent(self) -> str:
        """Determine user intent based on context and profile."""
        intents = {
            InteractionContext.E_COMMERCE: ['browse', 'search', 'purchase', 'compare'],
            InteractionContext.NEWS: ['read', 'search', 'browse', 'share'],
            InteractionContext.SOCIAL_MEDIA: ['browse', 'interact', 'share', 'search'],
            InteractionContext.SEARCH_ENGINE: ['search', 'find', 'explore'],
            InteractionContext.FORM: ['fill', 'submit', 'complete']
        }
        
        available_intents = intents.get(self.context, ['browse', 'read', 'search'])
        return random.choice(available_intents)
    
    def _generate_interaction_flow(self, user_intent: str) -> List[InteractionType]:
        """Generate a realistic interaction flow based on intent and context."""
        if self.context in self.patterns:
            pattern = self.patterns[self.context]
            common_flows = pattern['common_flows']
            
            # Select a flow based on user intent
            suitable_flows = [flow for flow in common_flows if user_intent in flow]
            if suitable_flows:
                flow = random.choice(suitable_flows)
            else:
                flow = random.choice(common_flows)
            
            # Convert string flow to InteractionType enum
            interaction_flow = []
            for interaction_str in flow:
                try:
                    interaction_type = InteractionType(interaction_str)
                    interaction_flow.append(interaction_type)
                except ValueError:
                    # Map string to closest InteractionType
                    mapping = {
                        'search': InteractionType.SEARCH,
                        'browse': InteractionType.BROWSING,
                        'read': InteractionType.READING,
                        'navigate_back': InteractionType.NAVIGATION,
                        'add_to_cart': InteractionType.CLICK,
                        'compare': InteractionType.HOVER,
                        'filter': InteractionType.CLICK,
                        'sort': InteractionType.CLICK,
                        'share': InteractionType.CLICK,
                        'interact': InteractionType.CLICK,
                        'find': InteractionType.SEARCH,
                        'explore': InteractionType.BROWSING,
                        'fill': InteractionType.FORM_FILL,
                        'submit': InteractionType.CLICK,
                        'complete': InteractionType.FORM_FILL
                    }
                    if interaction_str in mapping:
                        interaction_flow.append(mapping[interaction_str])
        else:
            # Default flow
            interaction_flow = [
                InteractionType.BROWSING,
                InteractionType.CLICK,
                InteractionType.READING,
                InteractionType.SCROLL
            ]
        
        # Add some randomness and human-like variations
        return self._add_human_variations(interaction_flow)
    
    def _add_human_variations(self, flow: List[InteractionType]) -> List[InteractionType]:
        """Add human-like variations to the interaction flow."""
        varied_flow = []
        
        for interaction in flow:
            # Sometimes skip interactions (distraction)
            if random.random() < 0.1:
                continue
            
            # Sometimes repeat interactions (hesitation)
            if random.random() < 0.05:
                varied_flow.append(interaction)
            
            varied_flow.append(interaction)
            
            # Sometimes add random interactions
            if random.random() < 0.15:
                random_interaction = random.choice(list(InteractionType))
                varied_flow.append(random_interaction)
        
        return varied_flow
    
    def _find_suitable_elements(self, page_elements: List[Dict[str, Any]], 
                               interaction_type: InteractionType) -> List[Dict[str, Any]]:
        """Find elements suitable for a specific interaction type."""
        suitable = []
        
        for element in page_elements:
            element_type = element.get('type', '').lower()
            
            if interaction_type == InteractionType.CLICK:
                if element_type in ['button', 'link', 'input', 'select', 'checkbox', 'radio']:
                    suitable.append(element)
            elif interaction_type == InteractionType.HOVER:
                if element_type in ['link', 'button', 'image', 'div', 'span']:
                    suitable.append(element)
            elif interaction_type == InteractionType.TYPE:
                if element_type in ['input', 'textarea']:
                    suitable.append(element)
            elif interaction_type == InteractionType.READING:
                if element_type in ['p', 'div', 'span', 'article', 'section']:
                    suitable.append(element)
            elif interaction_type == InteractionType.SCROLL:
                # All elements can be scrolled to
                suitable.append(element)
            elif interaction_type == InteractionType.SEARCH:
                if element_type in ['input', 'search']:
                    suitable.append(element)
            elif interaction_type == InteractionType.FORM_FILL:
                if element_type in ['input', 'textarea', 'select']:
                    suitable.append(element)
            else:
                # For other interaction types, consider all elements
                suitable.append(element)
        
        return suitable
    
    def _select_element(self, elements: List[Dict[str, Any]], 
                       interaction_type: InteractionType) -> Dict[str, Any]:
        """Select an element based on user profile and interaction type."""
        if not elements:
            return {}
        
        # Apply user profile preferences
        if self.user_profile['expertise_level'] == 'expert':
            # Experts are more likely to click on functional elements
            functional_elements = [e for e in elements if e.get('type', '').lower() in 
                                 ['button', 'link', 'input']]
            if functional_elements:
                elements = functional_elements
        elif self.user_profile['expertise_level'] == 'beginner':
            # Beginners are more likely to click on obvious elements
            obvious_elements = [e for e in elements if e.get('visible', True) and 
                               e.get('size', {}).get('width', 0) > 50]
            if obvious_elements:
                elements = obvious_elements
        
        # Weight selection based on element properties
        weights = []
        for element in elements:
            weight = 1.0
            
            # Prefer visible elements
            if element.get('visible', True):
                weight *= 2.0
            
            # Prefer larger elements
            size = element.get('size', {})
            if size.get('width', 0) > 100 and size.get('height', 0) > 30:
                weight *= 1.5
            
            # Prefer elements with text content
            if element.get('text', '').strip():
                weight *= 1.2
            
            # Prefer elements in viewport
            if element.get('in_viewport', True):
                weight *= 1.3
            
            weights.append(weight)
        
        # Select element based on weights
        total_weight = sum(weights)
        if total_weight > 0:
            r = random.uniform(0, total_weight)
            cumulative = 0
            for i, weight in enumerate(weights):
                cumulative += weight
                if r <= cumulative:
                    return elements[i]
        
        return random.choice(elements)
    
    async def _generate_interaction_event(self, interaction_type: InteractionType,
                                        element: Dict[str, Any], user_intent: str) -> InteractionEvent:
        """Generate a specific interaction event."""
        # Calculate coordinates
        position = element.get('position', {})
        x = position.get('x', 0) + random.randint(-5, 5)  # Add some randomness
        y = position.get('y', 0) + random.randint(-5, 5)
        
        # Calculate duration based on interaction type and user profile
        base_duration = self._get_base_duration(interaction_type)
        duration = base_duration * random.uniform(0.8, 1.2)
        
        # Add user profile variations
        if self.user_profile['patience_level'] < 0.5:
            duration *= 0.7  # Impatient users are faster
        elif self.user_profile['patience_level'] > 0.8:
            duration *= 1.3  # Patient users take their time
        
        # Generate metadata
        metadata = {
            'element_type': element.get('type', 'unknown'),
            'element_text': element.get('text', '')[:100],  # Truncate long text
            'element_id': element.get('id', ''),
            'element_class': element.get('class', ''),
            'user_expertise': self.user_profile['expertise_level'],
            'mouse_precision': self.user_profile['mouse_precision'],
            'error_probability': self.user_profile['error_rate']
        }
        
        return InteractionEvent(
            interaction_type=interaction_type,
            element=element,
            coordinates=(x, y),
            timestamp=time.time(),
            duration=duration,
            context=self.context,
            metadata=metadata
        )
    
    def _get_base_duration(self, interaction_type: InteractionType) -> float:
        """Get base duration for an interaction type."""
        durations = {
            InteractionType.CLICK: 0.2,
            InteractionType.HOVER: 0.5,
            InteractionType.SCROLL: 1.0,
            InteractionType.TYPE: 2.0,
            InteractionType.DRAG: 1.5,
            InteractionType.SWIPE: 0.8,
            InteractionType.PINCH: 1.2,
            InteractionType.DOUBLE_CLICK: 0.4,
            InteractionType.RIGHT_CLICK: 0.3,
            InteractionType.LONG_PRESS: 2.0,
            InteractionType.KEYBOARD_SHORTCUT: 0.1,
            InteractionType.FORM_FILL: 3.0,
            InteractionType.SEARCH: 2.5,
            InteractionType.NAVIGATION: 1.0,
            InteractionType.READING: 5.0,
            InteractionType.BROWSING: 2.0
        }
        return durations.get(interaction_type, 1.0)
    
    async def _add_interaction_delay(self, interaction_type: InteractionType, event: InteractionEvent):
        """Add realistic delays between interactions."""
        # Base delay based on interaction type
        base_delay = {
            InteractionType.CLICK: 0.5,
            InteractionType.HOVER: 0.3,
            InteractionType.SCROLL: 0.8,
            InteractionType.TYPE: 1.0,
            InteractionType.READING: 3.0,
            InteractionType.BROWSING: 1.5
        }.get(interaction_type, 1.0)
        
        # Add user profile variations
        if self.user_profile['patience_level'] < 0.5:
            base_delay *= 0.5
        elif self.user_profile['patience_level'] > 0.8:
            base_delay *= 1.5
        
        # Add random variation
        delay = base_delay * random.uniform(0.7, 1.3)
        
        # Sometimes add longer delays (thinking, distraction)
        if random.random() < 0.1:
            delay += random.uniform(2.0, 8.0)
        
        await asyncio.sleep(delay)
    
    async def simulate_form_filling(self, form_elements: List[Dict[str, Any]]) -> InteractionSequence:
        """Simulate realistic form filling behavior."""
        events = []
        start_time = time.time()
        
        # Sort form elements in a logical order
        sorted_elements = self._sort_form_elements(form_elements)
        
        for element in sorted_elements:
            element_type = element.get('type', '').lower()
            
            if element_type in ['input', 'textarea']:
                # Simulate typing
                text = self._generate_form_text(element)
                if text:
                    event = await self._simulate_typing_interaction(element, text)
                    events.append(event)
            
            elif element_type in ['select', 'checkbox', 'radio']:
                # Simulate selection
                event = await self._simulate_selection_interaction(element)
                events.append(event)
            
            # Add realistic delays between form fields
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        total_duration = time.time() - start_time
        
        return InteractionSequence(
            events=events,
            total_duration=total_duration,
            context=InteractionContext.FORM,
            user_intent='fill_form',
            success=len(events) > 0
        )
    
    def _sort_form_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort form elements in a logical filling order."""
        # Simple sorting by position (top to bottom, left to right)
        return sorted(elements, key=lambda e: (
            e.get('position', {}).get('y', 0),
            e.get('position', {}).get('x', 0)
        ))
    
    def _generate_form_text(self, element: Dict[str, Any]) -> str:
        """Generate realistic text for form fields."""
        field_name = element.get('name', '').lower()
        field_type = element.get('type', '').lower()
        placeholder = element.get('placeholder', '').lower()
        
        # Common form field patterns
        if 'email' in field_name or 'email' in placeholder:
            return f"user{random.randint(100, 999)}@example.com"
        elif 'phone' in field_name or 'phone' in placeholder:
            return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        elif 'name' in field_name or 'name' in placeholder:
            return random.choice(['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'])
        elif 'address' in field_name or 'address' in placeholder:
            return f"{random.randint(100, 9999)} Main St, City, State {random.randint(10000, 99999)}"
        elif 'password' in field_name or 'password' in placeholder:
            return "password123"
        elif field_type == 'textarea':
            return "This is a sample comment or message."
        else:
            return f"Sample text {random.randint(1, 100)}"
    
    async def _simulate_typing_interaction(self, element: Dict[str, Any], text: str) -> InteractionEvent:
        """Simulate realistic typing interaction."""
        # Calculate typing speed based on user profile
        typing_speed = self.user_profile['typing_speed']
        base_duration = len(text) / (typing_speed / 60)  # Convert to seconds
        
        # Add variations for realism
        duration = base_duration * random.uniform(0.8, 1.2)
        
        # Add occasional pauses (thinking, backspacing)
        if random.random() < 0.2:
            duration += random.uniform(0.5, 2.0)
        
        position = element.get('position', {})
        x = position.get('x', 0)
        y = position.get('y', 0)
        
        return InteractionEvent(
            interaction_type=InteractionType.TYPE,
            element=element,
            coordinates=(x, y),
            timestamp=time.time(),
            duration=duration,
            context=InteractionContext.FORM,
            metadata={
                'text_length': len(text),
                'typing_speed': typing_speed,
                'text_preview': text[:50]
            }
        )
    
    async def _simulate_selection_interaction(self, element: Dict[str, Any]) -> InteractionEvent:
        """Simulate selection interaction (dropdown, checkbox, radio)."""
        position = element.get('position', {})
        x = position.get('x', 0)
        y = position.get('y', 0)
        
        return InteractionEvent(
            interaction_type=InteractionType.CLICK,
            element=element,
            coordinates=(x, y),
            timestamp=time.time(),
            duration=0.3,
            context=InteractionContext.FORM,
            metadata={
                'selection_type': element.get('type', 'unknown'),
                'options_count': len(element.get('options', []))
            }
        )
    
    def get_interaction_statistics(self) -> Dict[str, Any]:
        """Get statistics about interaction patterns."""
        if not self.interaction_history:
            return {
                'total_sessions': 0,
                'total_events': 0,
                'average_session_duration': 0.0,
                'most_common_interactions': {},
                'success_rate': 0.0
            }
        
        total_sessions = len(self.interaction_history)
        total_events = sum(len(session.events) for session in self.interaction_history)
        total_duration = sum(session.total_duration for session in self.interaction_history)
        
        # Count interaction types
        interaction_counts = {}
        for session in self.interaction_history:
            for event in session.events:
                interaction_type = event.interaction_type.value
                interaction_counts[interaction_type] = interaction_counts.get(interaction_type, 0) + 1
        
        # Calculate success rate
        successful_sessions = sum(1 for session in self.interaction_history if session.success)
        success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0.0
        
        return {
            'total_sessions': total_sessions,
            'total_events': total_events,
            'average_session_duration': total_duration / total_sessions if total_sessions > 0 else 0.0,
            'most_common_interactions': dict(sorted(interaction_counts.items(), 
                                                   key=lambda x: x[1], reverse=True)[:5]),
            'success_rate': success_rate,
            'user_profile': self.user_profile
        }


class InteractionManager:
    """Manages multiple interaction simulators."""
    
    def __init__(self):
        """Initialize the interaction manager."""
        self.simulators: Dict[str, HumanInteractionSimulator] = {}
        self.session_interactions: Dict[str, List[InteractionSequence]] = {}
    
    def create_simulator(self, session_id: str, context: InteractionContext = InteractionContext.GENERAL) -> HumanInteractionSimulator:
        """Create a new interaction simulator for a session.
        
        Args:
            session_id: Unique identifier for the session
            context: Interaction context
            
        Returns:
            HumanInteractionSimulator instance
        """
        simulator = HumanInteractionSimulator(context)
        self.simulators[session_id] = simulator
        self.session_interactions[session_id] = []
        return simulator
    
    def get_simulator(self, session_id: str) -> Optional[HumanInteractionSimulator]:
        """Get an interaction simulator by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            HumanInteractionSimulator instance or None
        """
        return self.simulators.get(session_id)
    
    async def simulate_page_interaction(self, session_id: str, page_elements: List[Dict[str, Any]], 
                                      user_intent: str = None) -> InteractionSequence:
        """Simulate page interaction for a session.
        
        Args:
            session_id: Session identifier
            page_elements: List of page elements
            user_intent: User intent for the interaction
            
        Returns:
            InteractionSequence with interaction events
        """
        simulator = self.get_simulator(session_id)
        if not simulator:
            simulator = self.create_simulator(session_id)
        
        sequence = await simulator.simulate_page_interaction(page_elements, user_intent)
        self.session_interactions[session_id].append(sequence)
        
        return sequence
    
    async def simulate_form_filling(self, session_id: str, form_elements: List[Dict[str, Any]]) -> InteractionSequence:
        """Simulate form filling for a session.
        
        Args:
            session_id: Session identifier
            form_elements: List of form elements
            
        Returns:
            InteractionSequence with form filling events
        """
        simulator = self.get_simulator(session_id)
        if not simulator:
            simulator = self.create_simulator(session_id, InteractionContext.FORM)
        
        sequence = await simulator.simulate_form_filling(form_elements)
        self.session_interactions[session_id].append(sequence)
        
        return sequence
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get interaction statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary of session statistics
        """
        simulator = self.get_simulator(session_id)
        if not simulator:
            return {}
        
        return simulator.get_interaction_statistics()
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all sessions.
        
        Returns:
            Dictionary of all session statistics
        """
        all_stats = {}
        for session_id, simulator in self.simulators.items():
            all_stats[session_id] = simulator.get_interaction_statistics()
        return all_stats
    
    def cleanup_session(self, session_id: str):
        """Clean up a session and remove its data.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.simulators:
            del self.simulators[session_id]
        if session_id in self.session_interactions:
            del self.session_interactions[session_id]
