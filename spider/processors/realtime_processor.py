"""Real-time data processing for SPIDER framework."""

import asyncio
import time
import json
import threading
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import statistics
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import weakref

from ..core.exceptions import SpiderError, ProcessingError
from ..core.logger import get_logger


class ProcessingMode(Enum):
    """Processing modes."""
    STREAMING = "streaming"
    BATCH = "batch"
    MICRO_BATCH = "micro_batch"
    WINDOWED = "windowed"


class WindowType(Enum):
    """Window types for windowed processing."""
    TUMBLING = "tumbling"
    SLIDING = "sliding"
    SESSION = "session"


class ProcessingStatus(Enum):
    """Processing status."""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ProcessingConfig:
    """Real-time processing configuration."""
    mode: ProcessingMode = ProcessingMode.STREAMING
    window_size: int = 1000
    window_duration: float = 60.0  # seconds
    batch_size: int = 100
    max_workers: int = 4
    buffer_size: int = 10000
    timeout: Optional[float] = None
    retry_count: int = 3
    error_handling: str = "skip"  # skip, fail, retry


@dataclass
class ProcessingEvent:
    """Processing event."""
    timestamp: float
    data: Any
    event_id: str
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Processing result."""
    event_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WindowData:
    """Window data for windowed processing."""
    window_id: str
    start_time: float
    end_time: float
    data: List[ProcessingEvent]
    processed: bool = False


class DataBuffer:
    """Thread-safe data buffer for real-time processing."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize data buffer.
        
        Args:
            max_size: Maximum buffer size
        """
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self.logger = get_logger(self.__class__.__name__)
    
    def put(self, event: ProcessingEvent) -> bool:
        """Put event into buffer.
        
        Args:
            event: Processing event
            
        Returns:
            True if added, False if buffer full
        """
        with self.lock:
            if len(self.buffer) >= self.max_size:
                return False
            
            self.buffer.append(event)
            return True
    
    def get(self, timeout: Optional[float] = None) -> Optional[ProcessingEvent]:
        """Get event from buffer.
        
        Args:
            timeout: Optional timeout
            
        Returns:
            Event or None if timeout
        """
        with self.lock:
            if self.buffer:
                return self.buffer.popleft()
            return None
    
    def get_batch(self, size: int) -> List[ProcessingEvent]:
        """Get batch of events.
        
        Args:
            size: Batch size
            
        Returns:
            List of events
        """
        with self.lock:
            batch = []
            for _ in range(min(size, len(self.buffer))):
                if self.buffer:
                    batch.append(self.buffer.popleft())
            return batch
    
    def size(self) -> int:
        """Get current buffer size.
        
        Returns:
            Buffer size
        """
        with self.lock:
            return len(self.buffer)
    
    def clear(self) -> None:
        """Clear buffer."""
        with self.lock:
            self.buffer.clear()


class WindowManager:
    """Manages windows for windowed processing."""
    
    def __init__(self, window_type: WindowType, window_duration: float):
        """Initialize window manager.
        
        Args:
            window_type: Type of window
            window_duration: Window duration in seconds
        """
        self.window_type = window_type
        self.window_duration = window_duration
        self.windows: Dict[str, WindowData] = {}
        self.lock = threading.RLock()
        self.logger = get_logger(self.__class__.__name__)
    
    def add_event(self, event: ProcessingEvent) -> List[WindowData]:
        """Add event to appropriate windows.
        
        Args:
            event: Processing event
            
        Returns:
            List of completed windows
        """
        with self.lock:
            completed_windows = []
            
            if self.window_type == WindowType.TUMBLING:
                window_id = self._get_tumbling_window_id(event.timestamp)
                self._add_to_window(window_id, event)
                
                # Check if window is complete
                if self._is_window_complete(window_id):
                    completed_windows.append(self.windows[window_id])
            
            elif self.window_type == WindowType.SLIDING:
                # Add to all active windows
                for window_id, window in self.windows.items():
                    if self._is_event_in_window(event, window):
                        self._add_to_window(window_id, event)
                
                # Create new window if needed
                new_window_id = self._get_sliding_window_id(event.timestamp)
                if new_window_id not in self.windows:
                    self._create_window(new_window_id, event.timestamp)
                    self._add_to_window(new_window_id, event)
                
                # Check for completed windows
                for window_id, window in list(self.windows.items()):
                    if self._is_window_complete(window_id):
                        completed_windows.append(window)
                        del self.windows[window_id]
            
            elif self.window_type == WindowType.SESSION:
                # Session windows based on event gaps
                session_window = self._find_or_create_session_window(event)
                self._add_to_window(session_window.window_id, event)
                
                # Check if session is complete
                if self._is_session_complete(session_window):
                    completed_windows.append(session_window)
            
            return completed_windows
    
    def _get_tumbling_window_id(self, timestamp: float) -> str:
        """Get tumbling window ID for timestamp.
        
        Args:
            timestamp: Event timestamp
            
        Returns:
            Window ID
        """
        window_start = int(timestamp // self.window_duration) * self.window_duration
        return f"tumbling_{window_start}_{window_start + self.window_duration}"
    
    def _get_sliding_window_id(self, timestamp: float) -> str:
        """Get sliding window ID for timestamp.
        
        Args:
            timestamp: Event timestamp
            
        Returns:
            Window ID
        """
        window_start = timestamp - self.window_duration
        return f"sliding_{window_start}_{timestamp}"
    
    def _create_window(self, window_id: str, start_time: float) -> None:
        """Create new window.
        
        Args:
            window_id: Window ID
            start_time: Window start time
        """
        window = WindowData(
            window_id=window_id,
            start_time=start_time,
            end_time=start_time + self.window_duration,
            data=[]
        )
        self.windows[window_id] = window
    
    def _add_to_window(self, window_id: str, event: ProcessingEvent) -> None:
        """Add event to window.
        
        Args:
            window_id: Window ID
            event: Processing event
        """
        if window_id not in self.windows:
            self._create_window(window_id, event.timestamp)
        
        self.windows[window_id].data.append(event)
    
    def _is_event_in_window(self, event: ProcessingEvent, window: WindowData) -> bool:
        """Check if event is in window.
        
        Args:
            event: Processing event
            window: Window data
            
        Returns:
            True if event is in window
        """
        return window.start_time <= event.timestamp <= window.end_time
    
    def _is_window_complete(self, window_id: str) -> bool:
        """Check if window is complete.
        
        Args:
            window_id: Window ID
            
        Returns:
            True if window is complete
        """
        if window_id not in self.windows:
            return False
        
        window = self.windows[window_id]
        return time.time() > window.end_time
    
    def _find_or_create_session_window(self, event: ProcessingEvent) -> WindowData:
        """Find or create session window for event.
        
        Args:
            event: Processing event
            
        Returns:
            Session window
        """
        # Simple session window implementation
        # In practice, this would be more sophisticated
        session_gap = 30.0  # 30 seconds gap for session
        
        for window in self.windows.values():
            if not window.processed and window.data:
                last_event = max(window.data, key=lambda e: e.timestamp)
                if event.timestamp - last_event.timestamp <= session_gap:
                    return window
        
        # Create new session window
        window_id = f"session_{event.timestamp}"
        self._create_window(window_id, event.timestamp)
        return self.windows[window_id]
    
    def _is_session_complete(self, window: WindowData) -> bool:
        """Check if session window is complete.
        
        Args:
            window: Window data
            
        Returns:
            True if session is complete
        """
        if not window.data:
            return False
        
        last_event = max(window.data, key=lambda e: e.timestamp)
        session_gap = 30.0  # 30 seconds gap for session
        
        return time.time() - last_event.timestamp > session_gap


class StreamProcessor:
    """Stream processor for real-time data processing."""
    
    def __init__(self, config: ProcessingConfig):
        """Initialize stream processor.
        
        Args:
            config: Processing configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.status = ProcessingStatus.STOPPED
        self.buffer = DataBuffer(config.buffer_size)
        self.window_manager = WindowManager(WindowType.TUMBLING, config.window_duration)
        self.processors: List[Callable] = []
        self.results: deque = deque(maxlen=10000)
        self.performance_stats: Dict[str, List[float]] = defaultdict(list)
        self._stop_event = threading.Event()
        self._processing_task: Optional[asyncio.Task] = None
    
    def add_processor(self, processor: Callable) -> None:
        """Add data processor.
        
        Args:
            processor: Processing function
        """
        self.processors.append(processor)
        self.logger.info(f"Added processor: {processor.__name__}")
    
    def remove_processor(self, processor: Callable) -> bool:
        """Remove data processor.
        
        Args:
            processor: Processing function
            
        Returns:
            True if removed, False if not found
        """
        if processor in self.processors:
            self.processors.remove(processor)
            self.logger.info(f"Removed processor: {processor.__name__}")
            return True
        return False
    
    async def start(self) -> None:
        """Start stream processing."""
        if self.status == ProcessingStatus.RUNNING:
            self.logger.warning("Stream processor is already running")
            return
        
        self.status = ProcessingStatus.RUNNING
        self._stop_event.clear()
        self._processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Started stream processing")
    
    async def stop(self) -> None:
        """Stop stream processing."""
        self.status = ProcessingStatus.STOPPED
        self._stop_event.set()
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped stream processing")
    
    async def pause(self) -> None:
        """Pause stream processing."""
        self.status = ProcessingStatus.PAUSED
        self.logger.info("Paused stream processing")
    
    async def resume(self) -> None:
        """Resume stream processing."""
        self.status = ProcessingStatus.RUNNING
        self.logger.info("Resumed stream processing")
    
    async def _processing_loop(self) -> None:
        """Main processing loop."""
        try:
            while not self._stop_event.is_set():
                if self.status == ProcessingStatus.PAUSED:
                    await asyncio.sleep(0.1)
                    continue
                
                if self.config.mode == ProcessingMode.STREAMING:
                    await self._process_streaming()
                elif self.config.mode == ProcessingMode.BATCH:
                    await self._process_batch()
                elif self.config.mode == ProcessingMode.MICRO_BATCH:
                    await self._process_micro_batch()
                elif self.config.mode == ProcessingMode.WINDOWED:
                    await self._process_windowed()
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                
        except Exception as e:
            self.logger.error(f"Processing loop error: {e}")
            self.status = ProcessingStatus.ERROR
        finally:
            self.logger.info("Processing loop ended")
    
    async def _process_streaming(self) -> None:
        """Process data in streaming mode."""
        event = self.buffer.get(timeout=0.1)
        if event:
            await self._process_event(event)
    
    async def _process_batch(self) -> None:
        """Process data in batch mode."""
        batch = self.buffer.get_batch(self.config.batch_size)
        if batch:
            await self._process_batch_events(batch)
    
    async def _process_micro_batch(self) -> None:
        """Process data in micro-batch mode."""
        batch = self.buffer.get_batch(self.config.batch_size // 10)
        if batch:
            await self._process_batch_events(batch)
    
    async def _process_windowed(self) -> None:
        """Process data in windowed mode."""
        # Get events from buffer
        events = self.buffer.get_batch(self.config.batch_size)
        
        # Add events to windows
        for event in events:
            completed_windows = self.window_manager.add_event(event)
            
            # Process completed windows
            for window in completed_windows:
                await self._process_window(window)
    
    async def _process_event(self, event: ProcessingEvent) -> None:
        """Process single event.
        
        Args:
            event: Processing event
        """
        start_time = time.time()
        
        try:
            result = event.data
            
            # Apply all processors
            for processor in self.processors:
                result = await self._apply_processor(processor, result, event)
            
            # Create processing result
            processing_result = ProcessingResult(
                event_id=event.event_id,
                success=True,
                result=result,
                processing_time=time.time() - start_time,
                metadata={
                    "timestamp": event.timestamp,
                    "source": event.source
                }
            )
            
            self.results.append(processing_result)
            
        except Exception as e:
            error_msg = f"Event processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            processing_result = ProcessingResult(
                event_id=event.event_id,
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
            
            self.results.append(processing_result)
    
    async def _process_batch_events(self, events: List[ProcessingEvent]) -> None:
        """Process batch of events.
        
        Args:
            events: List of events
        """
        if not events:
            return
        
        start_time = time.time()
        
        try:
            # Process events in parallel
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                
                for event in events:
                    future = executor.submit(self._process_event_sync, event)
                    futures.append(future)
                
                # Wait for completion
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        self.results.append(result)
                    except Exception as e:
                        self.logger.error(f"Batch processing error: {e}")
            
            batch_duration = time.time() - start_time
            self.performance_stats["batch_processing"].append(batch_duration)
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
    
    def _process_event_sync(self, event: ProcessingEvent) -> ProcessingResult:
        """Synchronous event processing for thread pool.
        
        Args:
            event: Processing event
            
        Returns:
            Processing result
        """
        start_time = time.time()
        
        try:
            result = event.data
            
            # Apply all processors
            for processor in self.processors:
                result = processor(result)
            
            return ProcessingResult(
                event_id=event.event_id,
                success=True,
                result=result,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            return ProcessingResult(
                event_id=event.event_id,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    async def _process_window(self, window: WindowData) -> None:
        """Process window data.
        
        Args:
            window: Window data
        """
        start_time = time.time()
        
        try:
            # Process all events in window
            window_results = []
            
            for event in window.data:
                result = event.data
                
                # Apply all processors
                for processor in self.processors:
                    result = await self._apply_processor(processor, result, event)
                
                window_results.append(result)
            
            # Create window processing result
            window_result = ProcessingResult(
                event_id=f"window_{window.window_id}",
                success=True,
                result=window_results,
                processing_time=time.time() - start_time,
                metadata={
                    "window_id": window.window_id,
                    "window_start": window.start_time,
                    "window_end": window.end_time,
                    "event_count": len(window.data)
                }
            )
            
            self.results.append(window_result)
            window.processed = True
            
        except Exception as e:
            self.logger.error(f"Window processing failed: {e}")
    
    async def _apply_processor(self, processor: Callable, data: Any, event: ProcessingEvent) -> Any:
        """Apply processor to data.
        
        Args:
            processor: Processing function
            data: Input data
            event: Processing event
            
        Returns:
            Processed data
        """
        try:
            if asyncio.iscoroutinefunction(processor):
                return await processor(data, event)
            else:
                return processor(data, event)
        except Exception as e:
            self.logger.error(f"Processor {processor.__name__} failed: {e}")
            raise
    
    def add_event(self, data: Any, event_id: Optional[str] = None, source: str = "unknown") -> bool:
        """Add event to processing queue.
        
        Args:
            data: Event data
            event_id: Optional event ID
            source: Event source
            
        Returns:
            True if added, False if buffer full
        """
        if event_id is None:
            event_id = f"event_{int(time.time() * 1000)}"
        
        event = ProcessingEvent(
            timestamp=time.time(),
            data=data,
            event_id=event_id,
            source=source
        )
        
        return self.buffer.put(event)
    
    def get_results(self, limit: int = 100) -> List[ProcessingResult]:
        """Get processing results.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of processing results
        """
        return list(self.results)[-limit:]
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics.
        
        Returns:
            Performance statistics
        """
        stats = {}
        
        for operation, durations in self.performance_stats.items():
            if durations:
                stats[operation] = {
                    "count": len(durations),
                    "avg_duration": statistics.mean(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations)
                }
        
        return stats
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status.
        
        Returns:
            Status information
        """
        return {
            "status": self.status.value,
            "buffer_size": self.buffer.size(),
            "processors_count": len(self.processors),
            "results_count": len(self.results),
            "config": {
                "mode": self.config.mode.value,
                "batch_size": self.config.batch_size,
                "max_workers": self.config.max_workers
            }
        }
    
    def cleanup(self) -> None:
        """Cleanup processor."""
        self.results.clear()
        self.performance_stats.clear()
        self.logger.info("Stream processor cleaned up")
