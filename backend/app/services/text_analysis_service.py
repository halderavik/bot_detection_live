"""
Text Analysis Service using OpenAI GPT-4o-mini.

This service provides comprehensive text quality analysis for survey responses
including gibberish detection, copy-paste detection, topic relevance checking,
generic answer detection, and overall quality scoring.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from app.services.openai_service import openai_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TextAnalysisResult:
    """Result of text analysis."""
    quality_score: float  # 0-100
    is_flagged: bool
    flag_reasons: Dict[str, Any]
    gibberish_score: float  # 0-1
    copy_paste_score: float  # 0-1
    relevance_score: float  # 0-1
    generic_score: float  # 0-1
    analysis_details: Dict[str, Any]
    confidence: float  # 0-1 overall confidence

class TextAnalysisService:
    """Service for analyzing text quality using OpenAI GPT-4o-mini."""
    
    def __init__(self):
        """Initialize text analysis service."""
        self.openai_service = openai_service
        
        # Log availability status
        if not self.openai_service.is_available:
            logger.warning("Text analysis service initialized without OpenAI - will use fallback analysis mode")
        
        # Prompt templates for different analysis types
        self.prompts = {
            "gibberish": """
Analyze if this text is gibberish, meaningless, or nonsensical. Consider:
- Random character sequences
- Incoherent word combinations
- Text that doesn't form meaningful sentences
- Repeated characters or patterns

Text: "{text}"

Return JSON with: {{"is_gibberish": bool, "confidence": 0.0-1.0, "reason": "explanation"}}
""",
            
            "copy_paste": """
Analyze if this text appears to be copy-pasted from another source. Look for:
- Formal language inconsistent with casual survey context
- Complete sentences or paragraphs that seem pre-written
- Technical jargon or marketing language
- Text that doesn't directly answer the question
- Generic responses that could apply to any question

Text: "{text}"

Return JSON with: {{"is_copypaste": bool, "confidence": 0.0-1.0, "reason": "explanation"}}
""",
            
            "relevance": """
Given this question and answer, determine if the answer is relevant and directly addresses the question.

Question: "{question}"
Answer: "{text}"

Consider:
- Does the answer directly respond to what was asked?
- Is the content appropriate for the question type?
- Does it show understanding of the question?

Return JSON with: {{"is_relevant": bool, "confidence": 0.0-1.0, "reason": "explanation"}}
""",
            
            "generic": """
Analyze if this is a generic, low-effort, or lazy response. Look for:
- Very short responses like "idk", "nothing", "good", "fine", "okay"
- Responses that don't provide useful information
- One-word answers where more detail would be expected
- Responses that seem dismissive or uninterested

Text: "{text}"

Return JSON with: {{"is_generic": bool, "confidence": 0.0-1.0, "reason": "explanation"}}
""",
            
            "quality": """
Rate this survey response's overall quality from 0-100 considering:
- Coherence and clarity
- Relevance to the question
- Effort and thoughtfulness
- Completeness of response
- Grammar and readability

Text: "{text}"

Return JSON with: {{"score": 0-100, "reasoning": "detailed explanation"}}
"""
        }
        
        logger.info("Text analysis service initialized")
    
    async def analyze_response(self, question: str, answer: str) -> TextAnalysisResult:
        """
        Perform comprehensive text analysis on a survey response.
        
        Args:
            question: The survey question text
            answer: The user's response text
            
        Returns:
            TextAnalysisResult with all analysis metrics
        """
        logger.debug(f"Analyzing response: {answer[:100]}...")
        
        # Skip analysis for very short responses
        if len(answer.strip()) < 3:
            return TextAnalysisResult(
                quality_score=0.0,
                is_flagged=True,
                flag_reasons={"too_short": {"confidence": 1.0, "reason": "Response too short to analyze"}},
                gibberish_score=0.0,
                copy_paste_score=0.0,
                relevance_score=0.0,
                generic_score=1.0,
                analysis_details={"error": "Response too short"},
                confidence=1.0
            )
        
        # Run all analyses in parallel
        tasks = [
            self._analyze_gibberish(answer),
            self._analyze_copy_paste(answer),
            self._analyze_relevance(question, answer),
            self._analyze_generic(answer),
            self._analyze_quality(answer)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            gibberish_result = results[0] if not isinstance(results[0], Exception) else {"is_gibberish": False, "confidence": 0.0, "reason": "Analysis failed"}
            copy_paste_result = results[1] if not isinstance(results[1], Exception) else {"is_copypaste": False, "confidence": 0.0, "reason": "Analysis failed"}
            relevance_result = results[2] if not isinstance(results[2], Exception) else {"is_relevant": True, "confidence": 0.5, "reason": "Analysis failed"}
            generic_result = results[3] if not isinstance(results[3], Exception) else {"is_generic": False, "confidence": 0.0, "reason": "Analysis failed"}
            quality_result = results[4] if not isinstance(results[4], Exception) else {"score": 50, "reasoning": "Analysis failed"}
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            # Return default result on failure
            return TextAnalysisResult(
                quality_score=50.0,
                is_flagged=False,
                flag_reasons={},
                gibberish_score=0.0,
                copy_paste_score=0.0,
                relevance_score=0.5,
                generic_score=0.0,
                analysis_details={"error": str(e)},
                confidence=0.0
            )
        
        # Extract scores
        gibberish_score = gibberish_result.get("confidence", 0.0) if gibberish_result.get("is_gibberish", False) else 0.0
        copy_paste_score = copy_paste_result.get("confidence", 0.0) if copy_paste_result.get("is_copypaste", False) else 0.0
        # Relevance: high confidence in relevance = low risk score, high confidence in irrelevance = high risk score
        relevance_score = (1.0 - relevance_result.get("confidence", 0.5)) if relevance_result.get("is_relevant", True) else relevance_result.get("confidence", 0.5)
        generic_score = generic_result.get("confidence", 0.0) if generic_result.get("is_generic", False) else 0.0
        quality_score = quality_result.get("score", 50)
        
        # Determine if response should be flagged
        flag_reasons = {}
        is_flagged = False
        
        if gibberish_score > 0.7:
            flag_reasons["gibberish"] = gibberish_result
            is_flagged = True
        
        if copy_paste_score >= 0.7:
            flag_reasons["copy_paste"] = copy_paste_result
            is_flagged = True
        
        if relevance_score > 0.7:  # High score means low relevance
            flag_reasons["irrelevant"] = relevance_result
            is_flagged = True
        
        if generic_score > 0.7:
            flag_reasons["generic"] = generic_result
            is_flagged = True
        
        if quality_score < 30:
            flag_reasons["low_quality"] = {"confidence": 1.0, "reason": f"Quality score {quality_score} is very low"}
            is_flagged = True
        
        # Calculate overall confidence
        confidences = [
            gibberish_result.get("confidence", 0.5),
            copy_paste_result.get("confidence", 0.5),
            relevance_result.get("confidence", 0.5),
            generic_result.get("confidence", 0.5)
        ]
        overall_confidence = sum(confidences) / len(confidences)
        
        # Prepare analysis details
        analysis_details = {
            "gibberish": gibberish_result,
            "copy_paste": copy_paste_result,
            "relevance": relevance_result,
            "generic": generic_result,
            "quality": quality_result
        }
        
        logger.debug(f"Analysis complete - Quality: {quality_score}, Flagged: {is_flagged}")
        
        return TextAnalysisResult(
            quality_score=float(quality_score),
            is_flagged=is_flagged,
            flag_reasons=flag_reasons,
            gibberish_score=gibberish_score,
            copy_paste_score=copy_paste_score,
            relevance_score=relevance_score,
            generic_score=generic_score,
            analysis_details=analysis_details,
            confidence=overall_confidence
        )
    
    async def _analyze_gibberish(self, text: str) -> Dict[str, Any]:
        """Analyze if text is gibberish."""
        prompt = self.prompts["gibberish"].format(text=text)
        return await self.openai_service.analyze_text(text, prompt)
    
    async def _analyze_copy_paste(self, text: str) -> Dict[str, Any]:
        """Analyze if text appears to be copy-pasted."""
        prompt = self.prompts["copy_paste"].format(text=text)
        return await self.openai_service.analyze_text(text, prompt)
    
    async def _analyze_relevance(self, question: str, text: str) -> Dict[str, Any]:
        """Analyze if text is relevant to the question."""
        prompt = self.prompts["relevance"].format(question=question, text=text)
        return await self.openai_service.analyze_text(text, prompt)
    
    async def _analyze_generic(self, text: str) -> Dict[str, Any]:
        """Analyze if text is a generic response."""
        prompt = self.prompts["generic"].format(text=text)
        return await self.openai_service.analyze_text(text, prompt)
    
    async def _analyze_quality(self, text: str) -> Dict[str, Any]:
        """Analyze overall quality of the text."""
        prompt = self.prompts["quality"].format(text=text)
        return await self.openai_service.analyze_text(text, prompt)
    
    async def batch_analyze_responses(self, questions_and_answers: List[tuple]) -> List[TextAnalysisResult]:
        """
        Analyze multiple question-answer pairs in parallel.
        
        Args:
            questions_and_answers: List of (question, answer) tuples
            
        Returns:
            List of TextAnalysisResult objects
        """
        tasks = [self.analyze_response(q, a) for q, a in questions_and_answers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch analysis failed for item {i}: {result}")
                processed_results.append(TextAnalysisResult(
                    quality_score=50.0,
                    is_flagged=False,
                    flag_reasons={"error": {"confidence": 1.0, "reason": str(result)}},
                    gibberish_score=0.0,
                    copy_paste_score=0.0,
                    relevance_score=0.5,
                    generic_score=0.0,
                    analysis_details={"error": str(result)},
                    confidence=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_analysis_summary(self, results: List[TextAnalysisResult]) -> Dict[str, Any]:
        """
        Get summary statistics for a batch of analysis results.
        
        Args:
            results: List of TextAnalysisResult objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {}
        
        total_responses = len(results)
        flagged_responses = sum(1 for r in results if r.is_flagged)
        quality_scores = [r.quality_score for r in results if r.quality_score is not None]
        
        summary = {
            "total_responses": total_responses,
            "flagged_responses": flagged_responses,
            "flagged_percentage": round(flagged_responses / total_responses * 100, 2),
            "average_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
            "min_quality_score": min(quality_scores) if quality_scores else 0,
            "max_quality_score": max(quality_scores) if quality_scores else 0,
            "flag_breakdown": {}
        }
        
        # Count flag types
        flag_counts = {}
        for result in results:
            for flag_type in result.flag_reasons.keys():
                flag_counts[flag_type] = flag_counts.get(flag_type, 0) + 1
        
        summary["flag_breakdown"] = flag_counts
        
        return summary

# Global instance
text_analysis_service = TextAnalysisService()
