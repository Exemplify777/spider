"""
Behavioral pattern simulation for anti-bot protection.

This module implements human-like behavioral patterns to make web scraping
appear more natural and avoid detection by anti-bot systems.
"""

import asyncio
import random
import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import stats


class BehaviorPattern(Enum):
    """Types of behavioral patterns."""
    HUMAN_LIKE = "human_like"
    RESEARCHER = "researcher"
    CUSTOMER = "customer"
    CRAWLER = "crawler"
    RANDOM = "random"


@dataclass
class MouseMovement:
    """Represents a mouse movement pattern."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    duration: float
    curve_points: List[Tuple[float, float]]


@dataclass
class ScrollBehavior:
    """Represents scrolling behavior."""
    scroll_direction: str  # "up", "down", "random"
    scroll_amount: int
    scroll_speed: float
    pause_duration: float


@dataclass
class TypingPattern:
    """Represents typing behavior."""
    text: str
    typing_speed: float  # characters per second
    pause_probability: float
    backspace_probability: float


class BehaviorSimulator:
    """Simulates human-like behavior patterns for web scraping."""
    
    def __init__(self, pattern: BehaviorPattern = BehaviorPattern.HUMAN_LIKE):
        """Initialize the behavior simulator.
        
        Args:
            pattern: The behavioral pattern to simulate
        """
        self.pattern = pattern
        self.session_data = {
            'start_time': time.time(),
            'actions': [],
            'mouse_movements': [],
            'scroll_events': [],
            'typing_events': []
        }
        
        # Pattern-specific configurations
        self._configure_pattern()
    
    def _configure_pattern(self):
        """Configure behavior parameters based on the selected pattern."""
        if self.pattern == BehaviorPattern.HUMAN_LIKE:
            self.config = {
                'mouse_speed_range': (0.5, 2.0),
                'scroll_speed_range': (0.3, 1.5),
                'typing_speed_range': (2.0, 8.0),
                'pause_probability': 0.15,
                'backspace_probability': 0.05,
                'action_delay_range': (0.5, 3.0),
                'scroll_frequency': 0.3
            }
        elif self.pattern == BehaviorPattern.RESEARCHER:
            self.config = {
                'mouse_speed_range': (0.8, 1.5),
                'scroll_speed_range': (0.5, 1.2),
                'typing_speed_range': (3.0, 6.0),
                'pause_probability': 0.1,
                'backspace_probability': 0.02,
                'action_delay_range': (0.2, 1.5),
                'scroll_frequency': 0.4
            }
        elif self.pattern == BehaviorPattern.CUSTOMER:
            self.config = {
                'mouse_speed_range': (0.3, 1.0),
                'scroll_speed_range': (0.2, 0.8),
                'typing_speed_range': (1.5, 4.0),
                'pause_probability': 0.25,
                'backspace_probability': 0.1,
                'action_delay_range': (1.0, 5.0),
                'scroll_frequency': 0.2
            }
        elif self.pattern == BehaviorPattern.CRAWLER:
            self.config = {
                'mouse_speed_range': (3.0, 6.0),
                'scroll_speed_range': (1.0, 3.0),
                'typing_speed_range': (10.0, 20.0),
                'pause_probability': 0.01,
                'backspace_probability': 0.001,
                'action_delay_range': (0.1, 0.5),
                'scroll_frequency': 0.8
            }
        else:  # RANDOM
            self.config = {
                'mouse_speed_range': (0.1, 5.0),
                'scroll_speed_range': (0.1, 3.0),
                'typing_speed_range': (1.0, 15.0),
                'pause_probability': random.uniform(0.01, 0.3),
                'backspace_probability': random.uniform(0.001, 0.15),
                'action_delay_range': (0.1, 5.0),
                'scroll_frequency': random.uniform(0.1, 0.8)
            }
    
    async def simulate_mouse_movement(self, start_x: float, start_y: float, 
                                    end_x: float, end_y: float) -> MouseMovement:
        """Simulate human-like mouse movement with natural curves.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            
        Returns:
            MouseMovement object with curve points
        """
        # Calculate distance and duration (much faster)
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        base_duration = distance / (random.uniform(*self.config['mouse_speed_range']) * 100)  # Scale down
        
        # Add human-like variation
        duration = base_duration * random.uniform(0.8, 1.2)
        
        # Generate bezier curve points for natural movement
        curve_points = self._generate_bezier_curve(
            start_x, start_y, end_x, end_y, max(10, int(duration * 20))
        )
        
        # Add micro-movements and jitter
        curve_points = self._add_micro_movements(curve_points)
        
        movement = MouseMovement(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration=duration,
            curve_points=curve_points
        )
        
        self.session_data['mouse_movements'].append(movement)
        
        # Simulate the movement with delays
        await self._execute_mouse_movement(movement)
        
        return movement
    
    def _generate_bezier_curve(self, start_x: float, start_y: float, 
                              end_x: float, end_y: float, num_points: int) -> List[Tuple[float, float]]:
        """Generate a bezier curve for natural mouse movement."""
        # Control points for bezier curve
        mid_x = (start_x + end_x) / 2 + random.uniform(-20, 20)
        mid_y = (start_y + end_y) / 2 + random.uniform(-20, 20)
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            
            # Quadratic bezier curve
            x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y
            
            points.append((x, y))
        
        # Ensure first and last points are exact
        if points:
            points[0] = (start_x, start_y)
            points[-1] = (end_x, end_y)
        
        return points
    
    def _add_micro_movements(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Add small random movements to simulate hand tremor."""
        jittered_points = []
        for i, (x, y) in enumerate(points):
            # Don't jitter the first and last points
            if i == 0 or i == len(points) - 1:
                jittered_points.append((x, y))
            else:
                jitter_x = x + random.uniform(-0.5, 0.5)
                jitter_y = y + random.uniform(-0.5, 0.5)
                jittered_points.append((jitter_x, jitter_y))
        
        return jittered_points
    
    async def _execute_mouse_movement(self, movement: MouseMovement):
        """Execute the mouse movement with realistic timing."""
        for i, (x, y) in enumerate(movement.curve_points):
            # Calculate delay between points
            if i > 0:
                delay = movement.duration / len(movement.curve_points)
                # Add random variation to timing
                delay *= random.uniform(0.8, 1.2)
                await asyncio.sleep(delay)
    
    async def simulate_scroll(self, direction: str = "random", 
                            amount: Optional[int] = None) -> ScrollBehavior:
        """Simulate human-like scrolling behavior.
        
        Args:
            direction: Scroll direction ("up", "down", "random")
            amount: Number of pixels to scroll (random if None)
            
        Returns:
            ScrollBehavior object
        """
        if direction == "random":
            direction = random.choice(["up", "down"])
        
        if amount is None:
            # Human-like scroll amounts
            if self.pattern == BehaviorPattern.CUSTOMER:
                amount = random.randint(100, 300)
            elif self.pattern == BehaviorPattern.RESEARCHER:
                amount = random.randint(200, 500)
            else:
                amount = random.randint(150, 400)
        
        scroll_speed = random.uniform(*self.config['scroll_speed_range'])
        pause_duration = random.uniform(0.1, 0.5)
        
        behavior = ScrollBehavior(
            scroll_direction=direction,
            scroll_amount=amount,
            scroll_speed=scroll_speed,
            pause_duration=pause_duration
        )
        
        self.session_data['scroll_events'].append(behavior)
        
        # Simulate scroll with realistic timing
        await self._execute_scroll(behavior)
        
        return behavior
    
    async def _execute_scroll(self, behavior: ScrollBehavior):
        """Execute scrolling with realistic timing."""
        # Simulate gradual scrolling
        steps = max(1, int(behavior.scroll_amount / 50))
        step_amount = behavior.scroll_amount / steps
        
        for _ in range(steps):
            await asyncio.sleep(behavior.scroll_speed / 1000)
        
        # Add pause after scrolling
        await asyncio.sleep(behavior.pause_duration)
    
    async def simulate_typing(self, text: str) -> TypingPattern:
        """Simulate human-like typing behavior.
        
        Args:
            text: Text to type
            
        Returns:
            TypingPattern object
        """
        typing_speed = random.uniform(*self.config['typing_speed_range'])
        
        pattern = TypingPattern(
            text=text,
            typing_speed=typing_speed,
            pause_probability=self.config['pause_probability'],
            backspace_probability=self.config['backspace_probability']
        )
        
        self.session_data['typing_events'].append(pattern)
        
        # Simulate typing with realistic timing
        await self._execute_typing(pattern)
        
        return pattern
    
    async def _execute_typing(self, pattern: TypingPattern):
        """Execute typing with realistic timing and errors."""
        for i, char in enumerate(pattern.text):
            # Calculate delay between characters
            base_delay = 1.0 / pattern.typing_speed
            
            # Add variation based on character type
            if char.isalpha():
                delay = base_delay * random.uniform(0.8, 1.2)
            elif char.isdigit():
                delay = base_delay * random.uniform(0.9, 1.1)
            elif char in '.,!?':
                delay = base_delay * random.uniform(1.2, 2.0)
            else:
                delay = base_delay * random.uniform(0.7, 1.3)
            
            # Add random pauses
            if random.random() < pattern.pause_probability:
                delay += random.uniform(0.1, 0.5)
            
            # Simulate backspace errors
            if random.random() < pattern.backspace_probability and i > 0:
                await asyncio.sleep(delay * 0.5)  # Quick backspace
                await asyncio.sleep(delay)  # Type correct character
            
            await asyncio.sleep(delay)
    
    async def simulate_page_interaction(self, page_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate realistic page interaction patterns.
        
        Args:
            page_elements: List of page elements to interact with
            
        Returns:
            Dictionary of interaction results
        """
        interactions = {
            'mouse_movements': [],
            'scrolls': [],
            'clicks': [],
            'typing': [],
            'total_duration': 0
        }
        
        start_time = time.time()
        
        # Randomize interaction order
        random.shuffle(page_elements)
        
        for element in page_elements:
            # Add random delay between actions
            delay = random.uniform(*self.config['action_delay_range'])
            await asyncio.sleep(delay)
            
            # Simulate different types of interactions
            interaction_type = random.choice(['hover', 'click', 'scroll', 'type'])
            
            if interaction_type == 'hover' and 'position' in element:
                movement = await self.simulate_mouse_movement(
                    random.uniform(0, 100), random.uniform(0, 100),
                    element['position']['x'], element['position']['y']
                )
                interactions['mouse_movements'].append(movement)
            
            elif interaction_type == 'click' and 'position' in element:
                # Move to element first
                movement = await self.simulate_mouse_movement(
                    random.uniform(0, 100), random.uniform(0, 100),
                    element['position']['x'], element['position']['y']
                )
                interactions['mouse_movements'].append(movement)
                
                # Simulate click delay
                await asyncio.sleep(random.uniform(0.1, 0.3))
                interactions['clicks'].append(element)
            
            elif interaction_type == 'scroll':
                scroll = await self.simulate_scroll()
                interactions['scrolls'].append(scroll)
            
            elif interaction_type == 'type' and 'input_text' in element:
                typing = await self.simulate_typing(element['input_text'])
                interactions['typing'].append(typing)
        
        interactions['total_duration'] = time.time() - start_time
        return interactions
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current session's behavior.
        
        Returns:
            Dictionary of session statistics
        """
        total_actions = len(self.session_data['actions'])
        total_mouse_movements = len(self.session_data['mouse_movements'])
        total_scrolls = len(self.session_data['scroll_events'])
        total_typing = len(self.session_data['typing_events'])
        
        session_duration = time.time() - self.session_data['start_time']
        
        return {
            'pattern': self.pattern.value,
            'session_duration': session_duration,
            'total_actions': total_actions,
            'mouse_movements': total_mouse_movements,
            'scroll_events': total_scrolls,
            'typing_events': total_typing,
            'actions_per_minute': total_actions / (session_duration / 60) if session_duration > 0 else 0,
            'average_mouse_speed': self._calculate_average_mouse_speed(),
            'average_typing_speed': self._calculate_average_typing_speed()
        }
    
    def _calculate_average_mouse_speed(self) -> float:
        """Calculate average mouse movement speed."""
        if not self.session_data['mouse_movements']:
            return 0.0
        
        total_distance = 0
        total_duration = 0
        
        for movement in self.session_data['mouse_movements']:
            distance = math.sqrt(
                (movement.end_x - movement.start_x)**2 + 
                (movement.end_y - movement.start_y)**2
            )
            total_distance += distance
            total_duration += movement.duration
        
        return total_distance / total_duration if total_duration > 0 else 0.0
    
    def _calculate_average_typing_speed(self) -> float:
        """Calculate average typing speed."""
        if not self.session_data['typing_events']:
            return 0.0
        
        total_chars = sum(len(event.text) for event in self.session_data['typing_events'])
        total_duration = sum(len(event.text) / event.typing_speed for event in self.session_data['typing_events'])
        
        return total_chars / total_duration if total_duration > 0 else 0.0
    
    def reset_session(self):
        """Reset the current session data."""
        self.session_data = {
            'start_time': time.time(),
            'actions': [],
            'mouse_movements': [],
            'scroll_events': [],
            'typing_events': []
        }


class BehaviorManager:
    """Manages multiple behavior simulators and patterns."""
    
    def __init__(self):
        """Initialize the behavior manager."""
        self.simulators: Dict[str, BehaviorSimulator] = {}
        self.active_patterns: Dict[str, BehaviorPattern] = {}
    
    def create_simulator(self, session_id: str, pattern: BehaviorPattern = BehaviorPattern.HUMAN_LIKE) -> BehaviorSimulator:
        """Create a new behavior simulator for a session.
        
        Args:
            session_id: Unique identifier for the session
            pattern: Behavioral pattern to use
            
        Returns:
            BehaviorSimulator instance
        """
        simulator = BehaviorSimulator(pattern)
        self.simulators[session_id] = simulator
        self.active_patterns[session_id] = pattern
        return simulator
    
    def get_simulator(self, session_id: str) -> Optional[BehaviorSimulator]:
        """Get a behavior simulator by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            BehaviorSimulator instance or None
        """
        return self.simulators.get(session_id)
    
    def switch_pattern(self, session_id: str, new_pattern: BehaviorPattern):
        """Switch the behavioral pattern for a session.
        
        Args:
            session_id: Session identifier
            new_pattern: New behavioral pattern
        """
        if session_id in self.simulators:
            self.simulators[session_id].pattern = new_pattern
            self.simulators[session_id]._configure_pattern()
            self.active_patterns[session_id] = new_pattern
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all active sessions.
        
        Returns:
            Dictionary of session statistics
        """
        stats = {}
        for session_id, simulator in self.simulators.items():
            stats[session_id] = simulator.get_session_statistics()
        return stats
    
    def cleanup_session(self, session_id: str):
        """Clean up a session and remove its simulator.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.simulators:
            del self.simulators[session_id]
        if session_id in self.active_patterns:
            del self.active_patterns[session_id]
