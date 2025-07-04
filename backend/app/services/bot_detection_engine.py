"""
Bot Detection Engine Service.

This service implements rule-based bot detection algorithms analyzing
user behavior patterns including keystrokes, mouse movements, timing,
and device characteristics.
"""

import time
import statistics
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging

from app.utils.logger import setup_logger
from app.utils.helpers import calculate_confidence_score, determine_risk_level
from app.models import BehaviorData, DetectionResult

logger = setup_logger(__name__)

class BotDetectionEngine:
    """Engine for detecting bot behavior patterns."""
    
    def __init__(self):
        """Initialize the bot detection engine with thresholds."""
        # Keystroke analysis thresholds
        self.KEYSTROKE_MIN_INTERVAL = 50  # milliseconds
        self.KEYSTROKE_MAX_INTERVAL = 2000  # milliseconds
        self.KEYSTROKE_PATTERN_THRESHOLD = 0.8
        
        # Mouse analysis thresholds
        self.MOUSE_MIN_MOVEMENT = 5  # pixels
        self.MOUSE_MAX_SPEED = 1000  # pixels per second
        self.MOUSE_CLICK_THRESHOLD = 0.7
        
        # Timing analysis thresholds
        self.MIN_SESSION_DURATION = 10  # seconds
        self.MAX_EVENTS_PER_SECOND = 50
        
        # Device analysis thresholds
        self.SCREEN_SIZE_THRESHOLD = 0.9
        self.USER_AGENT_SUSPICIOUS_PATTERNS = [
            'bot', 'crawler', 'spider', 'scraper', 'headless'
        ]
    
    async def analyze_session(self, behavior_data: List[BehaviorData]) -> DetectionResult:
        """
        Analyze a session's behavior data for bot detection.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            DetectionResult: Analysis result with confidence scores
        """
        start_time = time.time()
        
        if not behavior_data:
            logger.warning("No behavior data provided for analysis")
            # Return None or raise an exception since we need session_id
            raise ValueError("No behavior data provided for analysis")
        
        # Perform individual analyses
        keystroke_score = self._analyze_keystrokes(behavior_data)
        mouse_score = self._analyze_mouse_behavior(behavior_data)
        timing_score = self._analyze_timing_patterns(behavior_data)
        device_score = self._analyze_device_characteristics(behavior_data)
        network_score = self._analyze_network_patterns(behavior_data)
        
        # Combine scores
        method_scores = {
            'keystroke_analysis': keystroke_score,
            'mouse_analysis': mouse_score,
            'timing_analysis': timing_score,
            'device_analysis': device_score,
            'network_analysis': network_score
        }
        
        confidence_score = calculate_confidence_score(method_scores)
        
        # Determine if it's a bot (threshold-based)
        is_bot = confidence_score > 0.7
        risk_level = determine_risk_level(confidence_score, is_bot)
        
        # Create detection result
        result = DetectionResult(
            session_id=behavior_data[0].session_id,
            is_bot=is_bot,
            confidence_score=confidence_score,
            risk_level=risk_level,
            detection_methods=list(method_scores.keys()),
            method_scores=method_scores,
            processing_time_ms=(time.time() - start_time) * 1000,
            event_count=len(behavior_data),
            analysis_summary=self._generate_analysis_summary(method_scores, is_bot),
            flagged_patterns=self._get_flagged_patterns(behavior_data, method_scores)
        )
        
        logger.info(f"Analysis completed: is_bot={is_bot}, confidence={confidence_score:.3f}")
        return result
    
    def _analyze_keystrokes(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze keystroke patterns for bot detection.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        keystroke_events = [event for event in behavior_data if event.is_keystroke_event]
        
        if len(keystroke_events) < 5:
            return 0.5  # Insufficient data
        
        # Analyze timing intervals
        intervals = []
        for i in range(1, len(keystroke_events)):
            interval = (keystroke_events[i].timestamp - keystroke_events[i-1].timestamp).total_seconds() * 1000
            intervals.append(interval)
        
        # Check for suspicious patterns
        suspicious_patterns = 0
        
        # Too regular intervals (bot-like)
        if intervals:
            std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
            if std_dev < 10:  # Very consistent timing
                suspicious_patterns += 1
        
        # Too fast typing
        avg_interval = statistics.mean(intervals) if intervals else 0
        if avg_interval < self.KEYSTROKE_MIN_INTERVAL:
            suspicious_patterns += 1
        
        # Too slow typing (suspicious)
        if avg_interval > self.KEYSTROKE_MAX_INTERVAL:
            suspicious_patterns += 1
        
        # Perfect timing (impossible for humans)
        perfect_intervals = sum(1 for interval in intervals if interval % 10 == 0)
        if perfect_intervals > len(intervals) * 0.8:
            suspicious_patterns += 1
        
        return min(suspicious_patterns / 4, 1.0)
    
    def _analyze_mouse_behavior(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze mouse movement patterns for bot detection.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        mouse_events = [event for event in behavior_data if event.is_mouse_event]
        
        if len(mouse_events) < 3:
            return 0.5  # Insufficient data
        
        suspicious_patterns = 0
        
        # Analyze movement patterns
        for event in mouse_events:
            event_data = event.event_data
            
            # Check for straight-line movements (bot-like)
            if 'movement_type' in event_data and event_data['movement_type'] == 'linear':
                suspicious_patterns += 1
            
            # Check for unrealistic speeds
            if 'speed' in event_data:
                speed = event_data['speed']
                if speed > self.MOUSE_MAX_SPEED:
                    suspicious_patterns += 1
            
            # Check for perfect precision (impossible for humans)
            if 'precision' in event_data and event_data['precision'] > 0.99:
                suspicious_patterns += 1
        
        # Check for lack of natural variation
        if len(mouse_events) > 10:
            movements = [event.event_data.get('distance', 0) for event in mouse_events]
            if movements:
                std_dev = statistics.stdev(movements) if len(movements) > 1 else 0
                if std_dev < 5:  # Very consistent movement distances
                    suspicious_patterns += 1
        
        return min(suspicious_patterns / (len(mouse_events) + 1), 1.0)
    
    def _analyze_timing_patterns(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze timing patterns across all events.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        if len(behavior_data) < 5:
            return 0.5
        
        suspicious_patterns = 0
        
        # Check session duration
        session_duration = (behavior_data[-1].timestamp - behavior_data[0].timestamp).total_seconds()
        if session_duration < self.MIN_SESSION_DURATION:
            suspicious_patterns += 1
        
        # Check event frequency
        events_per_second = len(behavior_data) / session_duration
        if events_per_second > self.MAX_EVENTS_PER_SECOND:
            suspicious_patterns += 1
        
        # Check for regular intervals (bot-like)
        intervals = []
        for i in range(1, len(behavior_data)):
            interval = (behavior_data[i].timestamp - behavior_data[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if intervals:
            std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
            if std_dev < 0.1:  # Very regular timing
                suspicious_patterns += 1
        
        return min(suspicious_patterns / 3, 1.0)
    
    def _analyze_device_characteristics(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze device characteristics for suspicious patterns.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        if not behavior_data:
            return 0.5
        
        suspicious_patterns = 0
        
        # Check screen size consistency
        screen_sizes = set()
        for event in behavior_data:
            if event.screen_width and event.screen_height:
                screen_sizes.add((event.screen_width, event.screen_height))
        
        if len(screen_sizes) > 1:
            suspicious_patterns += 1  # Multiple screen sizes in same session
        
        # Check for common bot screen sizes
        common_bot_sizes = [(1920, 1080), (1366, 768), (1440, 900)]
        for event in behavior_data:
            if (event.screen_width, event.screen_height) in common_bot_sizes:
                suspicious_patterns += 0.5
        
        # Check viewport consistency
        viewport_sizes = set()
        for event in behavior_data:
            if event.viewport_width and event.viewport_height:
                viewport_sizes.add((event.viewport_width, event.viewport_height))
        
        if len(viewport_sizes) > 1:
            suspicious_patterns += 1
        
        return min(suspicious_patterns / 3, 1.0)
    
    def _analyze_network_patterns(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze network and request patterns.
        
        Args:
            behavior_data: List of behavior data events
            
        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        # This would typically analyze network requests, headers, etc.
        # For now, return a neutral score
        return 0.5
    
    def _create_empty_result(self, session_id: str, event_count: int, start_time: float) -> DetectionResult:
        """Create an empty detection result for insufficient data."""
        return DetectionResult(
            session_id=session_id,
            is_bot=False,
            confidence_score=0.5,
            risk_level="medium",
            detection_methods=[],
            method_scores={},
            processing_time_ms=(time.time() - start_time) * 1000,
            event_count=event_count,
            analysis_summary="Insufficient data for analysis",
            flagged_patterns={}
        )
    
    def _generate_analysis_summary(self, method_scores: Dict[str, float], is_bot: bool) -> str:
        """Generate a human-readable analysis summary."""
        if is_bot:
            high_scores = [method for method, score in method_scores.items() if score > 0.7]
            if high_scores:
                return f"Bot detected with high confidence in: {', '.join(high_scores)}"
            else:
                return "Bot detected with moderate confidence across multiple indicators"
        else:
            return "Human behavior detected with normal patterns"
    
    def _get_flagged_patterns(self, behavior_data: List[BehaviorData], method_scores: Dict[str, float]) -> Dict[str, Any]:
        """Get specific patterns that were flagged during analysis."""
        flagged = {}
        
        # Add high-scoring methods
        for method, score in method_scores.items():
            if score > 0.7:
                flagged[method] = {
                    'score': score,
                    'severity': 'high' if score > 0.9 else 'medium'
                }
        
        # Add event type counts
        event_counts = {}
        for event in behavior_data:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        flagged['event_distribution'] = event_counts
        
        return flagged 