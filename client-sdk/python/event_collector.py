"""
Event Collector Utility for Python.

This module provides utilities for automatically collecting user behavior events
in Python applications, particularly useful for web scraping and automation tools.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from bot_detection_client import BotDetectionClient

logger = logging.getLogger(__name__)

class EventCollector:
    """Utility for collecting and sending user behavior events."""
    
    def __init__(self, client: BotDetectionClient, batch_size: int = 10, 
                 flush_interval: float = 5.0):
        """
        Initialize the event collector.
        
        Args:
            client: BotDetectionClient instance
            batch_size: Number of events to batch before sending
            flush_interval: Time interval in seconds to flush events
        """
        self.client = client
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.events = []
        self.lock = threading.Lock()
        self.running = False
        self.flush_thread = None
        
        # Device information
        self.screen_width = 1920
        self.screen_height = 1080
        self.viewport_width = 1920
        self.viewport_height = 937
        
        # Page information
        self.current_url = None
        self.current_title = None
        
        # Performance tracking
        self.page_load_start = None
    
    def start(self):
        """Start the event collector."""
        if self.running:
            return
        
        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()
        logger.info("Event collector started")
    
    def stop(self):
        """Stop the event collector and flush remaining events."""
        self.running = False
        if self.flush_thread:
            self.flush_thread.join()
        self.flush()
        logger.info("Event collector stopped")
    
    def set_device_info(self, screen_width: int, screen_height: int,
                       viewport_width: Optional[int] = None,
                       viewport_height: Optional[int] = None):
        """Set device information for events."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.viewport_width = viewport_width or screen_width
        self.viewport_height = viewport_height or (screen_height - 83)  # Approximate browser chrome
    
    def set_page_info(self, url: str, title: Optional[str] = None):
        """Set current page information."""
        self.current_url = url
        self.current_title = title
        self.page_load_start = time.time()
        
        # Create page load event
        load_time = None
        if self.page_load_start:
            load_time = (time.time() - self.page_load_start) * 1000
        
        self.add_event(self.client.create_page_load_event(
            url, title, load_time
        ))
    
    def add_event(self, event: Dict[str, Any]):
        """Add an event to the collection queue."""
        with self.lock:
            # Add device and page information
            event['screen_width'] = self.screen_width
            event['screen_height'] = self.screen_height
            event['viewport_width'] = self.viewport_width
            event['viewport_height'] = self.viewport_height
            event['page_url'] = self.current_url
            event['page_title'] = self.current_title
            
            self.events.append(event)
            
            # Flush if batch size reached
            if len(self.events) >= self.batch_size:
                self._flush_batch()
    
    def keystroke(self, key: str, element_id: Optional[str] = None,
                  element_type: Optional[str] = None):
        """Record a keystroke event."""
        event = self.client.create_keystroke_event(key, element_id, element_type)
        self.add_event(event)
    
    def mouse_click(self, x: int, y: int, button: int = 1,
                   element_id: Optional[str] = None,
                   element_type: Optional[str] = None):
        """Record a mouse click event."""
        event = self.client.create_mouse_click_event(x, y, button, element_id, element_type)
        self.add_event(event)
    
    def mouse_move(self, x: int, y: int):
        """Record a mouse move event."""
        event = self.client.create_mouse_move_event(x, y)
        self.add_event(event)
    
    def scroll(self, scroll_x: int, scroll_y: int):
        """Record a scroll event."""
        event = self.client.create_scroll_event(scroll_x, scroll_y)
        self.add_event(event)
    
    def focus(self, element_id: str, element_type: Optional[str] = None):
        """Record a focus event."""
        event = self.client.create_focus_event(element_id, element_type)
        self.add_event(event)
    
    def blur(self, element_id: str, element_type: Optional[str] = None):
        """Record a blur event."""
        event = self.client.create_blur_event(element_id, element_type)
        self.add_event(event)
    
    def _flush_batch(self):
        """Flush the current batch of events."""
        with self.lock:
            if not self.events:
                return
            
            events_to_send = self.events.copy()
            self.events.clear()
        
        try:
            self.client.send_events(events_to_send)
            logger.debug(f"Sent {len(events_to_send)} events")
        except Exception as e:
            logger.error(f"Failed to send events: {e}")
            # Re-add events to queue for retry
            with self.lock:
                self.events.extend(events_to_send)
    
    def _flush_loop(self):
        """Background thread for periodic flushing."""
        while self.running:
            time.sleep(self.flush_interval)
            self._flush_batch()
    
    def flush(self):
        """Manually flush all pending events."""
        self._flush_batch()
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get the current session status."""
        return self.client.get_session_status()
    
    def analyze_session(self) -> Dict[str, Any]:
        """Analyze the current session."""
        self.flush()  # Ensure all events are sent before analysis
        return self.client.analyze_session()

class WebDriverEventCollector(EventCollector):
    """Event collector specifically for Selenium WebDriver."""
    
    def __init__(self, client: BotDetectionClient, driver, **kwargs):
        """
        Initialize WebDriver event collector.
        
        Args:
            client: BotDetectionClient instance
            driver: Selenium WebDriver instance
            **kwargs: Additional arguments for EventCollector
        """
        super().__init__(client, **kwargs)
        self.driver = driver
        self._setup_driver_hooks()
    
    def _setup_driver_hooks(self):
        """Setup hooks for WebDriver events."""
        # This would require custom JavaScript injection or WebDriver events
        # For now, we'll provide manual methods
        pass
    
    def navigate_to(self, url: str):
        """Navigate to a URL and record page load."""
        self.driver.get(url)
        self.set_page_info(url, self.driver.title)
    
    def click_element(self, element, x: Optional[int] = None, y: Optional[int] = None):
        """Click an element and record the event."""
        if x is None or y is None:
            location = element.location
            x, y = location['x'], location['y']
        
        element_id = element.get_attribute('id')
        element_type = element.tag_name
        
        self.mouse_click(x, y, element_id=element_id, element_type=element_type)
        element.click()
    
    def type_text(self, element, text: str):
        """Type text into an element and record keystrokes."""
        element_id = element.get_attribute('id')
        element_type = element.tag_name
        
        self.focus(element_id, element_type)
        
        for char in text:
            self.keystroke(char, element_id, element_type)
            time.sleep(0.01)  # Simulate human typing speed
        
        element.send_keys(text)
        self.blur(element_id, element_type)
    
    def scroll_page(self, scroll_x: int = 0, scroll_y: int = 0):
        """Scroll the page and record the event."""
        self.driver.execute_script(f"window.scrollTo({scroll_x}, {scroll_y})")
        self.scroll(scroll_x, scroll_y)
    
    def get_device_info(self):
        """Get device information from WebDriver."""
        window_size = self.driver.get_window_size()
        self.set_device_info(
            window_size['width'],
            window_size['height']
        )

class PlaywrightEventCollector(EventCollector):
    """Event collector specifically for Playwright."""
    
    def __init__(self, client: BotDetectionClient, page, **kwargs):
        """
        Initialize Playwright event collector.
        
        Args:
            client: BotDetectionClient instance
            page: Playwright Page instance
            **kwargs: Additional arguments for EventCollector
        """
        super().__init__(client, **kwargs)
        self.page = page
        self._setup_page_hooks()
    
    def _setup_page_hooks(self):
        """Setup hooks for Playwright page events."""
        # Setup event listeners
        self.page.on('load', self._on_page_load)
        self.page.on('click', self._on_click)
        self.page.on('keydown', self._on_keydown)
        self.page.on('scroll', self._on_scroll)
    
    def _on_page_load(self):
        """Handle page load event."""
        self.set_page_info(self.page.url, self.page.title)
    
    def _on_click(self, event):
        """Handle click event."""
        self.mouse_click(event['x'], event['y'])
    
    def _on_keydown(self, event):
        """Handle keydown event."""
        self.keystroke(event['key'])
    
    def _on_scroll(self, event):
        """Handle scroll event."""
        # Playwright doesn't provide scroll coordinates directly
        # We'd need to get them from the page
        pass
    
    async def navigate_to(self, url: str):
        """Navigate to a URL."""
        await self.page.goto(url)
        self.set_page_info(url, self.page.title)
    
    async def click_element(self, selector: str):
        """Click an element by selector."""
        element = await self.page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            self.mouse_click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await element.click()
    
    async def type_text(self, selector: str, text: str):
        """Type text into an element."""
        element = await self.page.query_selector(selector)
        if element:
            element_id = await element.get_attribute('id')
            element_type = await element.evaluate('el => el.tagName.toLowerCase()')
            
            self.focus(element_id, element_type)
            
            for char in text:
                self.keystroke(char, element_id, element_type)
                await self.page.wait_for_timeout(10)  # 10ms delay
            
            await element.fill(text)
 