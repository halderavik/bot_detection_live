"""
Bot detection engine service.

This module contains the core bot detection logic using rule-based analysis
of user behavior patterns including keystrokes, mouse movements, scrolling, etc.
"""

import time
import statistics
from typing import Dict, List, Any, Tuple
from collections import defaultdict

from utils.logger import get_logger
from utils.helpers import calculate_bot_score, calculate_confidence_score
from config.config import settings

logger = get_logger(__name__)


class BotDetectionEngine:
    """Bot detection engine using rule-based analysis."""
    
    def __init__(self):
        """Initialize the bot detection engine."""
        self.logger = logger
        self.detection_threshold = settings.DETECTION_THRESHOLD
        
        # Bot detection rules and thresholds
        self.rules = {
            "keystroke_pattern": {
                "min_events": 5,
                "suspicious_intervals": [0, 50, 100],  # ms
                "max_typing_speed": 1000  # ms between keystrokes
            },
            "mouse_behavior": {
                "min_events": 3,
                "suspicious_patterns": ["linear", "grid", "random"],
                "max_click_speed": 500  # ms between clicks
            },
            "scroll_pattern": {
                "min_events": 2,
                "suspicious_speeds": [100, 200, 300],  # pixels per second
                "max_scroll_speed": 500
            },
            "focus_behavior": {
                "min_events": 2,
                "suspicious_patterns": ["rapid", "systematic"]
            },
            "timing_pattern": {
                "min_events": 10,
                "suspicious_intervals": [100, 200, 500, 1000]  # ms
            }
        }
    
    def analyze_session(self, events: List[Dict[str, Any]]) -> Tuple[float, float, bool, Dict[str, Any]]:
        """
        Analyze a session's events to detect bot behavior.
        
        Args:
            events: List of behavior events for the session
            
        Returns:
            Tuple containing (bot_score, confidence, is_bot, analysis_details)
        """
        start_time = time.time()
        
        if not events:
            return 0.0, 0.0, False, {"error": "No events provided"}
        
        # Group events by type
        events_by_type = self._group_events_by_type(events)
        
        # Analyze each behavior type
        analysis_results = {}
        
        # Keystroke analysis
        if "keystroke" in events_by_type:
            analysis_results["keystroke_pattern"] = self._analyze_keystrokes(
                events_by_type["keystroke"]
            )
        
        # Mouse behavior analysis
        mouse_events = self._get_mouse_events(events_by_type)
        if mouse_events:
            analysis_results["mouse_behavior"] = self._analyze_mouse_behavior(mouse_events)
        
        # Scroll pattern analysis
        if "scroll" in events_by_type:
            analysis_results["scroll_pattern"] = self._analyze_scroll_pattern(
                events_by_type["scroll"]
            )
        
        # Focus behavior analysis
        focus_events = self._get_focus_events(events_by_type)
        if focus_events:
            analysis_results["focus_behavior"] = self._analyze_focus_behavior(focus_events)
        
        # Timing pattern analysis
        analysis_results["timing_pattern"] = self._analyze_timing_pattern(events)
        
        # Calculate overall scores
        bot_score = calculate_bot_score(analysis_results)
        confidence = calculate_confidence_score(analysis_results, len(events))
        is_bot = bot_score >= self.detection_threshold
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Prepare analysis details
        analysis_details = {
            "individual_scores": analysis_results,
            "event_count": len(events),
            "processing_time_ms": processing_time,
            "detection_threshold": self.detection_threshold
        }
        
        self.logger.info(
            f"Session analysis completed - Bot Score: {bot_score:.3f}, "
            f"Confidence: {confidence:.3f}, Is Bot: {is_bot}"
        )
        
        return bot_score, confidence, is_bot, analysis_details
    
    def _group_events_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group events by their type."""
        grouped = defaultdict(list)
        for event in events:
            event_type = event.get("event_type", "unknown")
            grouped[event_type].append(event)
        return dict(grouped)
    
    def _analyze_keystrokes(self, keystroke_events: List[Dict[str, Any]]) -> float:
        """Analyze keystroke patterns for bot detection."""
        if len(keystroke_events) < self.rules["keystroke_pattern"]["min_events"]:
            return 0.0
        
        # Extract timing information
        timestamps = []
        for event in keystroke_events:
            event_data = event.get("event_data", {})
            timestamp = event_data.get("timestamp")
            if timestamp:
                timestamps.append(timestamp)
        
        if len(timestamps) < 2:
            return 0.0
        
        # Calculate intervals between keystrokes
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]) * 1000  # Convert to ms
            intervals.append(interval)
        
        # Analyze intervals for suspicious patterns
        suspicious_count = 0
        for interval in intervals:
            # Check for too regular intervals (bot-like)
            if interval in self.rules["keystroke_pattern"]["suspicious_intervals"]:
                suspicious_count += 1
            
            # Check for too fast typing
            if interval < self.rules["keystroke_pattern"]["max_typing_speed"]:
                suspicious_count += 1
        
        # Calculate suspicious ratio
        suspicious_ratio = suspicious_count / len(intervals) if intervals else 0.0
        
        # Check for perfect regularity (very suspicious)
        if len(set(intervals)) <= 2 and len(intervals) > 5:
            suspicious_ratio += 0.3
        
        return min(suspicious_ratio, 1.0)
    
    def _get_mouse_events(self, events_by_type: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract all mouse-related events."""
        mouse_events = []
        for event_type, events in events_by_type.items():
            if event_type.startswith("mouse_"):
                mouse_events.extend(events)
        return mouse_events
    
    def _analyze_mouse_behavior(self, mouse_events: List[Dict[str, Any]]) -> float:
        """Analyze mouse behavior patterns."""
        if len(mouse_events) < self.rules["mouse_behavior"]["min_events"]:
            return 0.0
        
        # Extract coordinates and timing
        coordinates = []
        timestamps = []
        
        for event in mouse_events:
            event_data = event.get("event_data", {})
            x = event_data.get("x")
            y = event_data.get("y")
            timestamp = event_data.get("timestamp")
            
            if x is not None and y is not None and timestamp is not None:
                coordinates.append((x, y))
                timestamps.append(timestamp)
        
        if len(coordinates) < 2:
            return 0.0
        
        # Analyze movement patterns
        suspicious_patterns = 0
        
        # Check for linear movement patterns
        if self._is_linear_movement(coordinates):
            suspicious_patterns += 1
        
        # Check for grid-like movement
        if self._is_grid_movement(coordinates):
            suspicious_patterns += 1
        
        # Check for too regular timing
        if self._has_regular_timing(timestamps):
            suspicious_patterns += 1
        
        # Check for too fast movements
        if self._has_fast_movements(coordinates, timestamps):
            suspicious_patterns += 1
        
        return min(suspicious_patterns / 4.0, 1.0)
    
    def _analyze_scroll_pattern(self, scroll_events: List[Dict[str, Any]]) -> float:
        """Analyze scroll behavior patterns."""
        if len(scroll_events) < self.rules["scroll_pattern"]["min_events"]:
            return 0.0
        
        # Extract scroll data
        scroll_speeds = []
        for event in scroll_events:
            event_data = event.get("event_data", {})
            scroll_x = event_data.get("scroll_x", 0)
            scroll_y = event_data.get("scroll_y", 0)
            timestamp = event_data.get("timestamp")
            
            if timestamp is not None:
                # Calculate scroll speed (pixels per second)
                speed = abs(scroll_x) + abs(scroll_y)
                scroll_speeds.append(speed)
        
        if not scroll_speeds:
            return 0.0
        
        # Check for suspicious scroll speeds
        suspicious_count = 0
        for speed in scroll_speeds:
            if speed in self.rules["scroll_pattern"]["suspicious_speeds"]:
                suspicious_count += 1
            if speed > self.rules["scroll_pattern"]["max_scroll_speed"]:
                suspicious_count += 1
        
        return min(suspicious_count / len(scroll_speeds), 1.0)
    
    def _get_focus_events(self, events_by_type: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract all focus-related events."""
        focus_events = []
        for event_type, events in events_by_type.items():
            if event_type.startswith("focus_"):
                focus_events.extend(events)
        return focus_events
    
    def _analyze_focus_behavior(self, focus_events: List[Dict[str, Any]]) -> float:
        """Analyze focus/blur behavior patterns."""
        if len(focus_events) < self.rules["focus_behavior"]["min_events"]:
            return 0.0
        
        # Extract timing information
        timestamps = []
        for event in focus_events:
            event_data = event.get("event_data", {})
            timestamp = event_data.get("timestamp")
            if timestamp:
                timestamps.append(timestamp)
        
        if len(timestamps) < 2:
            return 0.0
        
        # Check for rapid focus changes
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]) * 1000
            intervals.append(interval)
        
        # Rapid focus changes are suspicious
        rapid_changes = sum(1 for interval in intervals if interval < 100)
        return min(rapid_changes / len(intervals), 1.0) if intervals else 0.0
    
    def _analyze_timing_pattern(self, events: List[Dict[str, Any]]) -> float:
        """Analyze overall timing patterns across all events."""
        if len(events) < self.rules["timing_pattern"]["min_events"]:
            return 0.0
        
        # Extract all timestamps
        timestamps = []
        for event in events:
            event_data = event.get("event_data", {})
            timestamp = event_data.get("timestamp")
            if timestamp:
                timestamps.append(timestamp)
        
        if len(timestamps) < 2:
            return 0.0
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]) * 1000
            intervals.append(interval)
        
        # Check for suspicious timing patterns
        suspicious_count = 0
        
        # Check for too regular intervals
        if len(set(intervals)) <= 3 and len(intervals) > 10:
            suspicious_count += 1
        
        # Check for suspicious interval values
        for interval in intervals:
            if interval in self.rules["timing_pattern"]["suspicious_intervals"]:
                suspicious_count += 1
        
        return min(suspicious_count / (len(intervals) + 1), 1.0)
    
    def _is_linear_movement(self, coordinates: List[Tuple[int, int]]) -> bool:
        """Check if mouse movement follows a linear pattern."""
        if len(coordinates) < 3:
            return False
        
        # Calculate direction vectors
        vectors = []
        for i in range(1, len(coordinates)):
            dx = coordinates[i][0] - coordinates[i-1][0]
            dy = coordinates[i][1] - coordinates[i-1][1]
            vectors.append((dx, dy))
        
        # Check if vectors are mostly in the same direction
        if len(vectors) < 2:
            return False
        
        # Calculate angle consistency
        angles = []
        for i in range(1, len(vectors)):
            angle = abs(vectors[i][0] - vectors[i-1][0]) + abs(vectors[i][1] - vectors[i-1][1])
            angles.append(angle)
        
        # If angles are very consistent, it's suspicious
        avg_angle = statistics.mean(angles)
        return avg_angle < 10  # Threshold for linear movement
    
    def _is_grid_movement(self, coordinates: List[Tuple[int, int]]) -> bool:
        """Check if mouse movement follows a grid pattern."""
        if len(coordinates) < 4:
            return False
        
        # Check for horizontal and vertical movements only
        horizontal_moves = 0
        vertical_moves = 0
        
        for i in range(1, len(coordinates)):
            dx = abs(coordinates[i][0] - coordinates[i-1][0])
            dy = abs(coordinates[i][1] - coordinates[i-1][1])
            
            if dx > dy and dx > 5:  # Horizontal movement
                horizontal_moves += 1
            elif dy > dx and dy > 5:  # Vertical movement
                vertical_moves += 1
        
        total_moves = horizontal_moves + vertical_moves
        if total_moves == 0:
            return False
        
        # If most movements are strictly horizontal or vertical, it's suspicious
        return (horizontal_moves / total_moves > 0.8) or (vertical_moves / total_moves > 0.8)
    
    def _has_regular_timing(self, timestamps: List[float]) -> bool:
        """Check if events have very regular timing."""
        if len(timestamps) < 3:
            return False
        
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]) * 1000
            intervals.append(interval)
        
        # Check for very low variance in intervals
        if len(intervals) < 2:
            return False
        
        mean_interval = statistics.mean(intervals)
        variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        
        # Very low variance indicates regular timing
        return variance < (mean_interval * 0.1)  # Less than 10% variance
    
    def _has_fast_movements(self, coordinates: List[Tuple[int, int]], 
                           timestamps: List[float]) -> bool:
        """Check if mouse movements are suspiciously fast."""
        if len(coordinates) < 2 or len(timestamps) < 2:
            return False
        
        speeds = []
        for i in range(1, len(coordinates)):
            dx = coordinates[i][0] - coordinates[i-1][0]
            dy = coordinates[i][1] - coordinates[i-1][1]
            distance = (dx**2 + dy**2)**0.5
            
            time_diff = (timestamps[i] - timestamps[i-1]) * 1000
            if time_diff > 0:
                speed = distance / time_diff
                speeds.append(speed)
        
        if not speeds:
            return False
        
        # Check if average speed is suspiciously high
        avg_speed = statistics.mean(speeds)
        return avg_speed > 1000  # pixels per second threshold 