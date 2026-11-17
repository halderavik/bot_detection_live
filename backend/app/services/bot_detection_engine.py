"""
Bot Detection Engine Service.

This service implements rule-based bot detection algorithms analyzing
user behavior patterns including keystrokes, mouse movements, timing,
and device characteristics.
"""

import time
import statistics
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging

from app.utils.logger import setup_logger
from app.utils.helpers import calculate_confidence_score, determine_risk_level
from app.models import BehaviorData, DetectionResult, SurveyResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
            'bot', 'crawler', 'spider', 'scraper', 'headless', 'phantomjs', 'puppeteer', 'playwright', 'selenium'
        ]
        self.MOBILE_PATTERNS = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'tablet', 'silk', 'kindle']

        # A session at or above this bot probability is classified as a bot.
        self.BOT_THRESHOLD = 0.7
    
    async def analyze_session(
        self, behavior_data: List[BehaviorData], user_agent: Optional[str] = None
    ) -> DetectionResult:
        """
        Analyze a session's behavior data for bot detection.

        Args:
            behavior_data: List of behavior data events
            user_agent: The session's user agent, used to recognise touch devices
                and headless browsers

        Returns:
            DetectionResult: Analysis result with confidence scores
        """
        start_time = time.time()

        if not behavior_data:
            logger.warning("No behavior data provided for analysis")
            raise ValueError("No behavior data provided for analysis")

        behavior_data = sorted(behavior_data, key=lambda event: event.timestamp)
        context = self._session_context(behavior_data, user_agent)

        method_scores = {
            'keystroke_analysis': self._analyze_keystrokes(behavior_data),
            'mouse_analysis': self._analyze_mouse_behavior(behavior_data, context),
            'timing_analysis': self._analyze_timing_patterns(behavior_data),
            'device_analysis': self._analyze_device_characteristics(behavior_data, context),
            'network_analysis': self._analyze_network_patterns(behavior_data),
        }

        confidence_score = calculate_confidence_score(method_scores)

        # Signals a person cannot produce. One lifts the score to 0.85, two or more to 0.95.
        decisive = self._decisive_signals(behavior_data, context)
        if decisive:
            confidence_score = max(confidence_score, 0.95 if len(decisive) > 1 else 0.85)
        confidence_score = round(min(confidence_score, 1.0), 4)

        is_bot = confidence_score >= self.BOT_THRESHOLD
        risk_level = determine_risk_level(confidence_score, is_bot)

        flagged = self._get_flagged_patterns(behavior_data, method_scores)
        if decisive:
            flagged['decisive_signals'] = decisive

        result = DetectionResult(
            session_id=behavior_data[0].session_id,
            is_bot=is_bot,
            confidence_score=confidence_score,
            risk_level=risk_level,
            detection_methods=list(method_scores.keys()),
            method_scores=method_scores,
            processing_time_ms=(time.time() - start_time) * 1000,
            event_count=len(behavior_data),
            analysis_summary=self._generate_analysis_summary(method_scores, is_bot, decisive),
            flagged_patterns=flagged,
        )

        logger.info(f"Analysis completed: is_bot={is_bot}, confidence={confidence_score:.3f}")
        return result

    async def calculate_composite_score(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Calculate unified composite score combining behavioral, text quality, and fraud detection analysis.
        
        Args:
            session_id: Session ID to analyze
            db: Database session
            
        Returns:
            Dictionary with composite scoring results
        """
        try:
            # Get behavioral analysis result (existing)
            behavior_result = await self._get_latest_behavioral_analysis(session_id, db)
            
            # Get text quality analysis results
            text_quality_result = await self._get_text_quality_analysis(session_id, db)
            
            # Get fraud detection results
            fraud_result = await self._get_latest_fraud_analysis(session_id, db)
            
            # Extract scores
            behavioral_score = behavior_result.get('confidence_score', 0.5) if behavior_result else 0.5
            avg_text_quality = text_quality_result.get('avg_quality_score', 50.0) if text_quality_result else 50.0
            
            # Normalize text quality score (0-100 -> 0-1, inverted so higher quality = lower risk)
            text_quality_normalized = 1.0 - (avg_text_quality / 100.0)
            
            # Get fraud score (0.0-1.0)
            fraud_score = fraud_result.get('fraud_score', 0.0) if fraud_result else 0.0
            
            # Calculate composite score (weighted combination: 40% behavioral, 30% text quality, 30% fraud)
            composite_score = (
                0.4 * behavioral_score +  # 40% weight on behavioral analysis
                0.3 * text_quality_normalized +  # 30% weight on text quality (inverted)
                0.3 * fraud_score  # 30% weight on fraud detection
            )
            
            # Determine risk level based on composite score
            if composite_score >= 0.8:
                risk_level = "CRITICAL"
            elif composite_score >= 0.6:
                risk_level = "HIGH"
            elif composite_score >= 0.4:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Determine if session is flagged as bot/fraud
            is_bot = composite_score >= 0.7
            
            logger.info(f"Composite score calculated: {composite_score:.3f}, risk: {risk_level}")
            
            return {
                'session_id': session_id,
                'composite_score': composite_score,
                'behavioral_score': behavioral_score,
                'text_quality_score': avg_text_quality,
                'text_quality_normalized': text_quality_normalized,
                'fraud_score': fraud_score,
                'risk_level': risk_level,
                'is_bot': is_bot,
                'behavioral_details': behavior_result,
                'text_quality_details': text_quality_result,
                'fraud_details': fraud_result
            }
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            # Fallback to behavioral score only
            behavior_result = await self._get_latest_behavioral_analysis(session_id, db)
            behavioral_score = behavior_result.get('confidence_score', 0.5) if behavior_result else 0.5
            
            return {
                'session_id': session_id,
                'composite_score': behavioral_score,
                'behavioral_score': behavioral_score,
                'text_quality_score': None,
                'text_quality_normalized': 0.5,
                'fraud_score': None,
                'risk_level': "HIGH" if behavioral_score >= 0.7 else "MEDIUM",
                'is_bot': behavioral_score >= 0.7,
                'behavioral_details': behavior_result,
                'text_quality_details': None,
                'fraud_details': None,
                'error': str(e)
            }
    
    async def _get_latest_behavioral_analysis(self, session_id: str, db: AsyncSession) -> Optional[Dict]:
        """Get the latest behavioral analysis result for a session."""
        try:
            from app.models import DetectionResult
            
            result = await db.execute(
                select(DetectionResult)
                .where(DetectionResult.session_id == session_id)
                .order_by(DetectionResult.created_at.desc())
                .limit(1)
            )
            detection_result = result.scalar_one_or_none()
            
            if detection_result:
                return {
                    'confidence_score': detection_result.confidence_score,
                    'is_bot': detection_result.is_bot,
                    'risk_level': detection_result.risk_level,
                    'method_scores': detection_result.method_scores,
                    'analysis_summary': detection_result.analysis_summary,
                    'created_at': detection_result.created_at.isoformat() if detection_result.created_at else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting behavioral analysis: {e}")
            return None
    
    async def _get_text_quality_analysis(self, session_id: str, db: AsyncSession) -> Optional[Dict]:
        """Get text quality analysis results for a session."""
        try:
            result = await db.execute(
                select(SurveyResponse)
                .where(SurveyResponse.session_id == session_id)
                .where(SurveyResponse.quality_score.isnot(None))
            )
            responses = result.scalars().all()
            
            if not responses:
                return None
            
            # Calculate aggregate statistics
            quality_scores = [r.quality_score for r in responses if r.quality_score is not None]
            flagged_responses = [r for r in responses if r.is_flagged]
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 50.0
            flagged_count = len(flagged_responses)
            total_responses = len(responses)
            
            # Analyze flag types
            flag_types = {}
            for response in flagged_responses:
                if response.flag_reasons:
                    for flag_type in response.flag_reasons.keys():
                        flag_types[flag_type] = flag_types.get(flag_type, 0) + 1
            
            return {
                'total_responses': total_responses,
                'avg_quality_score': avg_quality,
                'flagged_count': flagged_count,
                'flagged_percentage': (flagged_count / total_responses * 100) if total_responses > 0 else 0,
                'flag_types': flag_types,
                'quality_scores': quality_scores,
                'responses': [
                    {
                        'response_id': r.id,
                        'quality_score': r.quality_score,
                        'is_flagged': r.is_flagged,
                        'flag_reasons': r.flag_reasons or {}
                    }
                    for r in responses
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting text quality analysis: {e}")
            return None
    
    async def _get_latest_fraud_analysis(self, session_id: str, db: AsyncSession) -> Optional[Dict]:
        """Get the latest fraud detection analysis result for a session."""
        try:
            from app.models import FraudIndicator
            
            result = await db.execute(
                select(FraudIndicator)
                .where(FraudIndicator.session_id == session_id)
                .order_by(FraudIndicator.created_at.desc())
                .limit(1)
            )
            fraud_indicator = result.scalar_one_or_none()
            
            if fraud_indicator:
                return {
                    'fraud_score': float(fraud_indicator.overall_fraud_score) if fraud_indicator.overall_fraud_score else 0.0,
                    'is_duplicate': fraud_indicator.is_duplicate,
                    'risk_level': fraud_indicator.risk_level,
                    'ip_risk_score': float(fraud_indicator.ip_risk_score) if fraud_indicator.ip_risk_score else 0.0,
                    'fingerprint_risk_score': float(fraud_indicator.fingerprint_risk_score) if fraud_indicator.fingerprint_risk_score else 0.0,
                    'duplicate_risk_score': float(fraud_indicator.response_similarity_score) if fraud_indicator.response_similarity_score else 0.0,
                    'geolocation_risk_score': float(fraud_indicator.geolocation_risk_score) if fraud_indicator.geolocation_risk_score else 0.0,
                    'velocity_risk_score': float(fraud_indicator.velocity_risk_score) if fraud_indicator.velocity_risk_score else 0.0,
                    'flag_reasons': fraud_indicator.flag_reasons,
                    'created_at': fraud_indicator.created_at.isoformat() if fraud_indicator.created_at else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting fraud analysis: {e}")
            return None
    
    @staticmethod
    def _data(event: BehaviorData) -> Dict[str, Any]:
        return event.event_data if isinstance(event.event_data, dict) else {}

    def _session_context(self, behavior_data: List[BehaviorData], user_agent: Optional[str]) -> Dict[str, Any]:
        """Facts about the device and the session used by several checks."""
        agent = (user_agent or "").lower()
        touch = any(pattern in agent for pattern in self.MOBILE_PATTERNS)
        webdriver = False
        for event in behavior_data:
            data = self._data(event)
            if data.get('pointer') in ('touch', 'pen') or (data.get('touch_points') or 0) > 0:
                touch = True
            if data.get('webdriver') is True:
                webdriver = True
        return {
            'user_agent': agent,
            'touch': touch,
            'webdriver': webdriver,
            'moves': [e for e in behavior_data if e.event_type == 'mouse_move'],
            'clicks': [e for e in behavior_data if e.event_type == 'mouse_click'],
            'keys': [e for e in behavior_data if e.event_type == 'keystroke'],
            'submits': [e for e in behavior_data if e.event_type == 'form_submit'],
        }

    def _decisive_signals(self, behavior_data: List[BehaviorData], context: Dict[str, Any]) -> List[str]:
        """Patterns that real people do not produce, each described in plain words."""
        signals: List[str] = []
        if context['webdriver']:
            signals.append('Browser reports it is controlled by automation (navigator.webdriver)')
        if any(pattern in context['user_agent'] for pattern in self.USER_AGENT_SUSPICIOUS_PATTERNS):
            signals.append('User agent belongs to a headless or automated browser')

        submits = [self._data(e) for e in context['submits']]
        if any(data.get('honeypot') is True for data in submits):
            signals.append('Filled in a hidden field that people cannot see (honeypot)')
        untyped = sum(int(data.get('untyped_answers') or 0) for data in submits)
        if untyped:
            signals.append(f'{untyped} open-ended answer(s) appeared without any typing, pasting, or dictation')

        inputs = context['clicks'] + context['keys']
        flagged = [e for e in inputs if self._data(e).get('trusted') is False]
        if len(flagged) >= 3 and len(flagged) >= 0.5 * len(inputs):
            signals.append(f'{len(flagged)} of {len(inputs)} clicks and key presses were generated by script')

        pages = len(context['submits'])
        if not context['touch'] and pages >= 2:
            if not context['moves'] and not context['clicks'] and not context['keys']:
                signals.append(f'Answered {pages} pages with no mouse or keyboard activity')
            elif len(context['clicks']) >= 3 and not context['moves'] and not context['keys']:
                # Keyboard users click with Space/Enter, so key presses rule this out.
                signals.append(f"{len(context['clicks'])} clicks with no mouse movement or key presses")
        return signals

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
            return 0.3  # Too few key presses to judge; leans human

        intervals = []
        for i in range(1, len(keystroke_events)):
            interval = (keystroke_events[i].timestamp - keystroke_events[i - 1].timestamp).total_seconds() * 1000
            intervals.append(interval)

        suspicious_patterns = 0
        # Typing pauses are normal, so only within-burst intervals (< 2 s) say anything.
        bursts = [interval for interval in intervals if interval < self.KEYSTROKE_MAX_INTERVAL]
        if len(bursts) >= 4:
            if statistics.stdev(bursts) < 10:  # Machine-regular rhythm
                suspicious_patterns += 1
            if statistics.mean(bursts) < self.KEYSTROKE_MIN_INTERVAL:  # Faster than people type
                suspicious_patterns += 1
            if sum(1 for interval in bursts if interval % 10 == 0) > len(bursts) * 0.8:
                suspicious_patterns += 1  # Rounded timer intervals

        return min(suspicious_patterns / 3, 1.0)

    def _analyze_mouse_behavior(self, behavior_data: List[BehaviorData], context: Optional[Dict[str, Any]] = None) -> float:
        """
        Analyze mouse movement patterns for bot detection.

        Args:
            behavior_data: List of behavior data events
            context: Session facts from ``_session_context``

        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        context = context or self._session_context(behavior_data, None)
        moves = context['moves']
        clicks = context['clicks']

        if context['touch']:
            return 0.3  # Phones and tablets have no pointer to track

        if not moves:
            if context['keys']:
                return 0.4  # Keyboard-only respondents are rare but real
            if clicks or context['submits']:
                return 0.8  # Pages answered on a desktop without the mouse moving
            return 0.4

        suspicious = 0.0
        points = [(self._data(e).get('x'), self._data(e).get('y')) for e in moves]
        points = [(x, y) for x, y in points if isinstance(x, (int, float)) and isinstance(y, (int, float))]
        if len(points) >= 10:
            steps = [((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in zip(points, points[1:])]
            steps = [step for step in steps if step > 0]
            if len(steps) >= 5 and statistics.pstdev(steps) < 1:
                suspicious += 1  # Every step the same length
            turns = 0
            for a, b, c in zip(points, points[1:], points[2:]):
                cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
                if abs(cross) > 1:
                    turns += 1
            if turns == 0:
                suspicious += 1  # Perfectly straight path

        # Legacy SDK fields
        for event in moves:
            data = self._data(event)
            if data.get('movement_type') == 'linear' or (data.get('speed') or 0) > self.MOUSE_MAX_SPEED:
                suspicious += 1 / max(len(moves), 1)

        return min(suspicious / 2, 1.0)

    def _analyze_timing_patterns(self, behavior_data: List[BehaviorData]) -> float:
        """
        Analyze timing patterns across all events.

        Args:
            behavior_data: List of behavior data events

        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        if len(behavior_data) < 5:
            return 0.4

        suspicious_patterns = 0

        session_duration = (behavior_data[-1].timestamp - behavior_data[0].timestamp).total_seconds()
        if session_duration < self.MIN_SESSION_DURATION:
            suspicious_patterns += 1

        if session_duration > 0 and len(behavior_data) / session_duration > self.MAX_EVENTS_PER_SECOND:
            suspicious_patterns += 1

        intervals = [
            (behavior_data[i].timestamp - behavior_data[i - 1].timestamp).total_seconds()
            for i in range(1, len(behavior_data))
        ]
        if len(intervals) > 1 and statistics.stdev(intervals) < 0.1:
            suspicious_patterns += 1  # Clockwork regularity

        return min(suspicious_patterns / 3, 1.0)

    def _analyze_device_characteristics(self, behavior_data: List[BehaviorData], context: Optional[Dict[str, Any]] = None) -> float:
        """
        Analyze device characteristics for suspicious patterns.

        Args:
            behavior_data: List of behavior data events
            context: Session facts from ``_session_context``

        Returns:
            float: Bot probability score (0.0 to 1.0)
        """
        if not behavior_data:
            return 0.3
        context = context or self._session_context(behavior_data, None)
        if context['webdriver'] or any(p in context['user_agent'] for p in self.USER_AGENT_SUSPICIOUS_PATTERNS):
            return 1.0

        suspicious = 0.0
        screen_sizes = {
            (event.screen_width, event.screen_height)
            for event in behavior_data
            if event.screen_width and event.screen_height
        }
        if len(screen_sizes) > 1:
            suspicious += 1  # The physical screen changed mid-session
        if any(width == 0 or height == 0 for width, height in screen_sizes):
            suspicious += 1  # Headless browsers often report an empty screen
        if not screen_sizes and not context['touch']:
            suspicious += 0.5
        return min(suspicious / 2, 1.0)

    def _analyze_network_patterns(self, behavior_data: List[BehaviorData]) -> float:
        """
        Network analysis is not implemented yet. It returns 0.0 and carries no weight
        in the overall score (see ``calculate_confidence_score``).
        """
        return 0.0

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
    
    def _generate_analysis_summary(
        self, method_scores: Dict[str, float], is_bot: bool, decisive: Optional[List[str]] = None
    ) -> str:
        """Generate a human-readable analysis summary."""
        if is_bot:
            if decisive:
                return "Bot detected: " + "; ".join(decisive)
            high_scores = [method for method, score in method_scores.items() if score > 0.7]
            if high_scores:
                return f"Bot detected with high confidence in: {', '.join(high_scores)}"
            return "Bot detected with moderate confidence across multiple indicators"
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