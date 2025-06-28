"""
Event Collector for Bot Detection.

This module provides utilities for collecting and managing
behavior events in Python applications.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from datetime import datetime


class EventCollector:
    """Event collector for gathering behavior data."""
    
    def __init__(self, max_events: int = 1000, batch_size: int = 10, 
                 batch_timeout: float = 5.0):
        """
        Initialize the event collector.
        
        Args:
            max_events: Maximum number of events to store
            batch_size: Number of events to send in a batch
            batch_timeout: Timeout for sending batches (seconds)
        """
        self.max_events = max_events
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        self.events = deque(maxlen=max_events)
        self.batch_callback = None
        self.batch_timer = None
        self.is_running = False
        self.lock = threading.Lock()
    
    def set_batch_callback(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """
        Set callback function for batch processing.
        
        Args:
            callback: Function to call with batch of events
        """
        self.batch_callback = callback
    
    def add_event(self, event: Dict[str, Any]):
        """
        Add an event to the collector.
        
        Args:
            event: Event data to add
        """
        with self.lock:
            self.events.append(event)
            
            # Send batch if full
            if len(self.events) >= self.batch_size:
                self._send_batch()
    
    def add_keystroke(self, key_code: int, key_char: str, 
                     element_id: Optional[str] = None,
                     element_type: Optional[str] = None,
                     page_url: Optional[str] = None):
        """
        Add a keystroke event.
        
        Args:
            key_code: Key code
            key_char: Key character
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
        """
        event = {
            'event_type': 'keystroke',
            'event_data': {
                'key_code': key_code,
                'key_char': key_char,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
        self.add_event(event)
    
    def add_mouse_click(self, x: int, y: int, button: int = 1,
                       element_id: Optional[str] = None,
                       element_type: Optional[str] = None,
                       page_url: Optional[str] = None):
        """
        Add a mouse click event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
        """
        event = {
            'event_type': 'mouse_click',
            'event_data': {
                'x': x,
                'y': y,
                'button': button,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
        self.add_event(event)
    
    def add_mouse_move(self, x: int, y: int, page_url: Optional[str] = None):
        """
        Add a mouse move event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            page_url: Page URL
        """
        event = {
            'event_type': 'mouse_move',
            'event_data': {
                'x': x,
                'y': y,
                'timestamp': time.time()
            },
            'page_url': page_url
        }
        self.add_event(event)
    
    def add_scroll(self, scroll_x: int, scroll_y: int, page_url: Optional[str] = None):
        """
        Add a scroll event.
        
        Args:
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position
            page_url: Page URL
        """
        event = {
            'event_type': 'scroll',
            'event_data': {
                'scroll_x': scroll_x,
                'scroll_y': scroll_y,
                'timestamp': time.time()
            },
            'page_url': page_url
        }
        self.add_event(event)
    
    def add_focus(self, event_type: str, element_id: Optional[str] = None,
                 element_type: Optional[str] = None, page_url: Optional[str] = None):
        """
        Add a focus event.
        
        Args:
            event_type: Event type (focus, blur)
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
        """
        event = {
            'event_type': f'focus_{event_type}',
            'event_data': {
                'element_id': element_id,
                'element_type': element_type,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
        self.add_event(event)
    
    def add_custom_event(self, event_type: str, event_data: Dict[str, Any],
                        element_id: Optional[str] = None,
                        element_type: Optional[str] = None,
                        page_url: Optional[str] = None):
        """
        Add a custom event.
        
        Args:
            event_type: Custom event type
            event_data: Event data
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
        """
        event = {
            'event_type': event_type,
            'event_data': event_data,
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
        self.add_event(event)
    
    def get_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get collected events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self.lock:
            events = list(self.events)
            if limit:
                events = events[-limit:]
            return events
    
    def clear_events(self):
        """Clear all collected events."""
        with self.lock:
            self.events.clear()
    
    def get_event_count(self) -> int:
        """
        Get number of collected events.
        
        Returns:
            Number of events
        """
        with self.lock:
            return len(self.events)
    
    def start_batch_timer(self):
        """Start the batch timer for periodic sending."""
        if self.is_running:
            return
        
        self.is_running = True
        self._schedule_batch()
    
    def stop_batch_timer(self):
        """Stop the batch timer."""
        self.is_running = False
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
    
    def force_send_batch(self):
        """Force send current batch of events."""
        with self.lock:
            self._send_batch()
    
    def _schedule_batch(self):
        """Schedule the next batch timer."""
        if not self.is_running:
            return
        
        self.batch_timer = threading.Timer(self.batch_timeout, self._batch_timer_callback)
        self.batch_timer.start()
    
    def _batch_timer_callback(self):
        """Callback for batch timer."""
        with self.lock:
            if self.events:
                self._send_batch()
        
        # Schedule next batch
        self._schedule_batch()
    
    def _send_batch(self):
        """Send current batch of events."""
        if not self.batch_callback or not self.events:
            return
        
        # Get batch of events
        batch = []
        for _ in range(min(self.batch_size, len(self.events))):
            if self.events:
                batch.append(self.events.popleft())
        
        if batch:
            try:
                self.batch_callback(batch)
            except Exception as e:
                # Put events back if callback fails
                for event in batch:
                    self.events.appendleft(event)
                raise e


class WebEventCollector(EventCollector):
    """Event collector specifically for web applications."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_info = {}
    
    def set_page_info(self, url: str, title: str, referrer: str = ""):
        """
        Set current page information.
        
        Args:
            url: Current page URL
            title: Page title
            referrer: Referrer URL
        """
        self.page_info = {
            'url': url,
            'title': title,
            'referrer': referrer
        }
    
    def add_keystroke(self, key_code: int, key_char: str, 
                     element_id: Optional[str] = None,
                     element_type: Optional[str] = None):
        """Add keystroke with current page info."""
        super().add_keystroke(
            key_code, key_char, element_id, element_type, 
            self.page_info.get('url')
        )
    
    def add_mouse_click(self, x: int, y: int, button: int = 1,
                       element_id: Optional[str] = None,
                       element_type: Optional[str] = None):
        """Add mouse click with current page info."""
        super().add_mouse_click(
            x, y, button, element_id, element_type,
            self.page_info.get('url')
        )
    
    def add_mouse_move(self, x: int, y: int):
        """Add mouse move with current page info."""
        super().add_mouse_move(x, y, self.page_info.get('url'))
    
    def add_scroll(self, scroll_x: int, scroll_y: int):
        """Add scroll with current page info."""
        super().add_scroll(scroll_x, scroll_y, self.page_info.get('url'))
    
    def add_focus(self, event_type: str, element_id: Optional[str] = None,
                 element_type: Optional[str] = None):
        """Add focus event with current page info."""
        super().add_focus(
            event_type, element_id, element_type,
            self.page_info.get('url')
        )


# Utility functions
def create_event_collector(max_events: int = 1000, batch_size: int = 10,
                          batch_timeout: float = 5.0) -> EventCollector:
    """
    Create a new event collector.
    
    Args:
        max_events: Maximum number of events to store
        batch_size: Number of events to send in a batch
        batch_timeout: Timeout for sending batches (seconds)
        
    Returns:
        EventCollector instance
    """
    return EventCollector(max_events, batch_size, batch_timeout)


def create_web_event_collector(max_events: int = 1000, batch_size: int = 10,
                              batch_timeout: float = 5.0) -> WebEventCollector:
    """
    Create a new web event collector.
    
    Args:
        max_events: Maximum number of events to store
        batch_size: Number of events to send in a batch
        batch_timeout: Timeout for sending batches (seconds)
        
    Returns:
        WebEventCollector instance
    """
    return WebEventCollector(max_events, batch_size, batch_timeout) 