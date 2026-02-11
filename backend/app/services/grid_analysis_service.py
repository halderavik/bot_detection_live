"""
Grid Analysis Service for detecting patterns in grid/matrix question responses.

This service analyzes grid question responses to detect:
- Straight-lining (identical responses across rows)
- Response patterns (diagonal, zigzag, etc.)
- Response variance
- Satisficing behavior
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from datetime import datetime
import statistics
import logging

from app.models import SurveyQuestion, SurveyResponse, GridResponse, Session
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class GridAnalysisService:
    """Service for analyzing grid question responses."""
    
    def __init__(self):
        """Initialize grid analysis service."""
        self.straight_line_threshold = 0.8  # 80% of responses must be identical
    
    def detect_straight_lining(self, responses: List[Dict]) -> Dict[str, Any]:
        """
        Detect straight-lining pattern in grid responses.
        
        Straight-lining occurs when >80% of responses in a grid have identical values.
        
        Args:
            responses: List of response dictionaries with 'response_value' key
            
        Returns:
            Dict with 'is_straight_lined', 'percentage', 'common_value', 'confidence'
        """
        if not responses or len(responses) < 2:
            return {
                "is_straight_lined": False,
                "percentage": 0.0,
                "common_value": None,
                "confidence": 0.0
            }
        
        # Extract response values
        values = [r.get("response_value") for r in responses if r.get("response_value") is not None]
        
        if not values:
            return {
                "is_straight_lined": False,
                "percentage": 0.0,
                "common_value": None,
                "confidence": 0.0
            }
        
        # Count occurrences of each value
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1
        
        # Find most common value
        most_common_value = max(value_counts.items(), key=lambda x: x[1])
        common_value, count = most_common_value
        percentage = count / len(values)
        
        is_straight_lined = percentage >= self.straight_line_threshold
        
        # Confidence increases with percentage and number of responses
        confidence = min(percentage, 1.0) * min(len(values) / 10.0, 1.0)
        
        return {
            "is_straight_lined": is_straight_lined,
            "percentage": percentage,
            "common_value": common_value,
            "confidence": confidence,
            "total_responses": len(values),
            "unique_values": len(value_counts)
        }
    
    def detect_patterns(self, responses: List[Dict]) -> Dict[str, Any]:
        """
        Detect patterns in grid responses (diagonal, zigzag, etc.).
        
        Args:
            responses: List of response dictionaries with 'row_id', 'column_id', 'response_value'
            
        Returns:
            Dict with 'pattern_type', 'confidence', 'details'
        """
        if not responses or len(responses) < 3:
            return {
                "pattern_type": None,
                "confidence": 0.0,
                "details": {}
            }
        
        # Sort responses by row_id and column_id if available
        sorted_responses = sorted(
            responses,
            key=lambda r: (
                int(r.get("row_id", 0)) if str(r.get("row_id", "0")).isdigit() else 0,
                int(r.get("column_id", 0)) if str(r.get("column_id", "0")).isdigit() else 0
            )
        )
        
        # Extract numeric values if possible
        try:
            values = []
            for r in sorted_responses:
                val = r.get("response_value")
                if val is not None:
                    # Try to convert to number
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        # If not numeric, use position as value
                        values.append(len(values))
        except Exception:
            return {
                "pattern_type": None,
                "confidence": 0.0,
                "details": {}
            }
        
        if len(values) < 3:
            return {
                "pattern_type": None,
                "confidence": 0.0,
                "details": {}
            }
        
        # Check for diagonal pattern (1, 2, 3, 4...)
        is_diagonal = self._check_diagonal_pattern(values)
        if is_diagonal:
            return {
                "pattern_type": "diagonal",
                "confidence": 0.8,
                "details": {"values": values[:10]}  # First 10 values
            }
        
        # Check for reverse diagonal (descending)
        is_reverse_diagonal = self._check_reverse_diagonal_pattern(values)
        if is_reverse_diagonal:
            return {
                "pattern_type": "reverse_diagonal",
                "confidence": 0.8,
                "details": {"values": values[:10]}
            }
        
        # Check for zigzag pattern
        is_zigzag = self._check_zigzag_pattern(values)
        if is_zigzag:
            return {
                "pattern_type": "zigzag",
                "confidence": 0.7,
                "details": {"values": values[:10]}
            }
        
        # Check if all values are the same (straight line)
        if len(set(values)) == 1:
            return {
                "pattern_type": "straight_line",
                "confidence": 1.0,
                "details": {"value": values[0]}
            }
        
        return {
            "pattern_type": "random",
            "confidence": 0.5,
            "details": {}
        }
    
    def _check_diagonal_pattern(self, values: List[float]) -> bool:
        """Check if values follow diagonal pattern (increasing)."""
        if len(values) < 3:
            return False
        
        # Check if values are strictly increasing
        for i in range(1, len(values)):
            if values[i] <= values[i-1]:
                return False
        return True
    
    def _check_reverse_diagonal_pattern(self, values: List[float]) -> bool:
        """Check if values follow reverse diagonal pattern (decreasing)."""
        if len(values) < 3:
            return False
        
        # Check if values are strictly decreasing
        for i in range(1, len(values)):
            if values[i] >= values[i-1]:
                return False
        return True
    
    def _check_zigzag_pattern(self, values: List[float]) -> bool:
        """Check if values follow zigzag pattern (alternating up/down)."""
        if len(values) < 4:
            return False
        
        # Check if values alternate between increasing and decreasing
        direction = None
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                new_direction = "up"
            elif values[i] < values[i-1]:
                new_direction = "down"
            else:
                return False
            
            if direction is not None and direction == new_direction:
                return False
            direction = new_direction
        
        return True
    
    def calculate_variance(self, responses: List[Dict]) -> float:
        """
        Calculate response variance (0-1 scale).
        
        Args:
            responses: List of response dictionaries with 'response_value'
            
        Returns:
            Variance score normalized to 0-1 scale (0 = no variance, 1 = high variance)
        """
        if not responses or len(responses) < 2:
            return 0.0
        
        # Extract numeric values
        values = []
        for r in responses:
            val = r.get("response_value")
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    continue
        
        if len(values) < 2:
            return 0.0
        
        # Calculate standard deviation
        try:
            std_dev = statistics.stdev(values)
            mean_val = statistics.mean(values)
            
            # Normalize: coefficient of variation, capped at 1.0
            if mean_val == 0:
                variance_score = min(std_dev / 10.0, 1.0) if std_dev > 0 else 0.0
            else:
                cv = std_dev / abs(mean_val)  # Coefficient of variation
                variance_score = min(cv, 1.0)
            
            return variance_score
        except Exception as e:
            logger.warning(f"Error calculating variance: {e}")
            return 0.0
    
    def calculate_satisficing_score(self, responses: List[Dict]) -> float:
        """
        Calculate satisficing behavior score (0-1 scale).
        
        Satisficing behavior is indicated by:
        - Low response variance
        - Fast response times
        - Pattern consistency
        
        Args:
            responses: List of response dictionaries with 'response_value', 'response_time_ms'
            
        Returns:
            Satisficing score (0-1 scale, higher = more satisficing)
        """
        if not responses:
            return 0.0
        
        scores = []
        
        # Factor 1: Low variance (0-1, inverted so low variance = high satisficing)
        variance = self.calculate_variance(responses)
        variance_score = 1.0 - variance  # Invert: low variance = high satisficing
        scores.append(variance_score * 0.4)  # 40% weight
        
        # Factor 2: Fast response times
        response_times = [r.get("response_time_ms", 0) for r in responses if r.get("response_time_ms")]
        if response_times:
            avg_time = statistics.mean(response_times)
            # Normalize: < 2 seconds = high satisficing, > 10 seconds = low satisficing
            time_score = max(0.0, min(1.0, (10000 - avg_time) / 8000))
            scores.append(time_score * 0.3)  # 30% weight
        else:
            scores.append(0.0)
        
        # Factor 3: Pattern consistency (straight-lining or patterns)
        pattern_result = self.detect_patterns(responses)
        if pattern_result["pattern_type"] in ["straight_line", "diagonal", "reverse_diagonal"]:
            pattern_score = pattern_result.get("confidence", 0.0)
        else:
            pattern_score = 0.0
        scores.append(pattern_score * 0.3)  # 30% weight
        
        # Average the scores
        satisficing_score = sum(scores) / len(scores) if scores else 0.0
        return min(1.0, max(0.0, satisficing_score))
    
    async def analyze_grid_responses(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Analyze grid responses for a session.
        
        Args:
            session_id: Session ID to analyze
            db: Database session
            
        Returns:
            Dict with analysis results
        """
        try:
            # Get session to extract hierarchical fields
            session_result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get all grid questions for this session
            grid_questions_result = await db.execute(
                select(SurveyQuestion).where(
                    and_(
                        SurveyQuestion.session_id == session_id,
                        SurveyQuestion.question_type.in_(["grid", "matrix"])
                    )
                )
            )
            grid_questions = grid_questions_result.scalars().all()
            
            if not grid_questions:
                return {
                    "session_id": session_id,
                    "grid_questions_found": 0,
                    "analysis_results": []
                }
            
            analysis_results = []
            
            for question in grid_questions:
                # Get all responses for this grid question
                responses_result = await db.execute(
                    select(SurveyResponse).where(
                        SurveyResponse.question_id == question.id
                    )
                )
                responses = responses_result.scalars().all()
                
                if not responses:
                    continue
                
                # Convert to dict format for analysis
                response_dicts = []
                for resp in responses:
                    # Try to extract row/column from response_text or element_id
                    # For now, use response_text as response_value
                    response_dicts.append({
                        "response_value": resp.response_text,
                        "response_time_ms": resp.response_time_ms,
                        "row_id": None,  # Would need to be extracted from response structure
                        "column_id": None
                    })
                
                # Perform analysis
                straight_lining = self.detect_straight_lining(response_dicts)
                patterns = self.detect_patterns(response_dicts)
                variance = self.calculate_variance(response_dicts)
                satisficing = self.calculate_satisficing_score(response_dicts)
                
                # Store results
                analysis_result = {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "straight_lining": straight_lining,
                    "patterns": patterns,
                    "variance_score": variance,
                    "satisficing_score": satisficing,
                    "response_count": len(response_dicts)
                }
                
                analysis_results.append(analysis_result)
                
                # Store in database
                await self.store_grid_analysis(
                    session_id,
                    question.id,
                    response_dicts,
                    analysis_result,
                    db
                )
            
            return {
                "session_id": session_id,
                "survey_id": session.survey_id,
                "platform_id": session.platform_id,
                "respondent_id": session.respondent_id,
                "grid_questions_found": len(grid_questions),
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing grid responses for session {session_id}: {e}")
            raise
    
    async def store_grid_analysis(
        self,
        session_id: str,
        question_id: str,
        responses: List[Dict],
        analysis_result: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """
        Store grid analysis results in database.
        
        Args:
            session_id: Session ID
            question_id: Question ID
            responses: List of response dictionaries
            analysis_result: Analysis results dictionary
            db: Database session
        """
        try:
            # Get session for hierarchical fields
            session_result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                return
            
            # Delete existing grid responses for this question
            await db.execute(
                delete(GridResponse).where(
                    GridResponse.question_id == question_id
                )
            )
            
            # Create grid response records
            for idx, resp in enumerate(responses):
                grid_response = GridResponse(
                    session_id=session_id,
                    question_id=question_id,
                    survey_id=session.survey_id,
                    platform_id=session.platform_id,
                    respondent_id=session.respondent_id,
                    row_id=resp.get("row_id"),
                    column_id=resp.get("column_id"),
                    response_value=resp.get("response_value"),
                    response_time_ms=resp.get("response_time_ms"),
                    is_straight_lined=analysis_result["straight_lining"]["is_straight_lined"],
                    pattern_type=analysis_result["patterns"]["pattern_type"],
                    variance_score=analysis_result["variance_score"],
                    satisficing_score=analysis_result["satisficing_score"],
                    analyzed_at=datetime.utcnow()
                )
                db.add(grid_response)
            
            await db.commit()
            logger.info(f"Stored grid analysis for question {question_id}")
            
        except Exception as e:
            logger.error(f"Error storing grid analysis: {e}")
            await db.rollback()
            raise
