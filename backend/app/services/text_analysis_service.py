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

# The combined check returns five short parts; leave room for them.
COMBINED_MAX_TOKENS = 700

@dataclass
class TextAnalysisResult:
    """Result of text analysis."""
    quality_score: Optional[float]  # 0-100; None when the answer could not be checked
    is_flagged: bool
    flag_reasons: Dict[str, Any]
    gibberish_score: Optional[float]  # 0-1
    copy_paste_score: Optional[float]  # 0-1
    relevance_score: Optional[float]  # 0-1
    generic_score: Optional[float]  # 0-1
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

NOTE: Do NOT flag as generic if the text is:
- Gibberish or random characters (that's a different category)
- Completely off-topic or irrelevant (that's a different category)

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
        
        # All five checks in one request (the separate prompts above document each check).
        self.prompts["combined"] = """
You check one open-ended survey answer. Judge it against the question.

Question: "{question}"
Answer: "{text}"

Return JSON with exactly these keys, each reason under 20 words:
{{
  "gibberish": {{"is_gibberish": bool, "confidence": 0.0-1.0, "reason": "..."}},
  "copy_paste": {{"is_copypaste": bool, "confidence": 0.0-1.0, "reason": "..."}},
  "relevance": {{"is_relevant": bool, "confidence": 0.0-1.0, "reason": "..."}},
  "generic": {{"is_generic": bool, "confidence": 0.0-1.0, "reason": "..."}},
  "quality": {{"score": 0-100, "reasoning": "..."}}
}}

- gibberish: random characters, keyboard mashing, incoherent words, repeated characters.
- copy_paste: reads as pasted or pre-written: formal, marketing or encyclopedic language unlike a casual survey answer, or text that could answer any question.
- relevance: does the answer address what the question asks?
- generic: low effort, such as "idk", "nothing", "good", "fine", "n/a", or one word where detail is expected. Do not mark gibberish or off-topic answers as generic.
- quality: overall 0-100 for coherence, relevance to the question, effort and detail. A specific, on-topic answer of a sentence or two is good quality even if short.
"""

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
        
        # One request answers all five checks; five separate calls per answer ran into
        # the per-minute limit as soon as a survey had a few respondents at once.
        prompt = self.prompts["combined"].format(question=question, text=answer)
        try:
            combined = await self.openai_service.analyze_with_formatted_prompt(prompt, max_tokens=COMBINED_MAX_TOKENS)
            parts = self._split_combined(combined)
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return self.unchecked_result(str(e))
        gibberish_result = parts["gibberish"]
        copy_paste_result = parts["copy_paste"]
        relevance_result = parts["relevance"]
        generic_result = parts["generic"]
        quality_result = parts["quality"]

        # Extract scores
        gibberish_score = gibberish_result.get("confidence", 0.0) if gibberish_result.get("is_gibberish", False) else 0.0
        copy_paste_score = copy_paste_result.get("confidence", 0.0) if copy_paste_result.get("is_copypaste", False) else 0.0
        
        # Relevance: Calculate irrelevance risk score
        # When is_relevant=True, use (1 - confidence) as risk score (low risk)
        # When is_relevant=False, use high risk score based on confidence
        if relevance_result.get("is_relevant", True):
            relevance_score = 1.0 - relevance_result.get("confidence", 0.5)
        else:
            # Not relevant - higher confidence in irrelevance = higher risk score
            # Use 1.0 as base since we know it's irrelevant
            relevance_score = max(0.7, 1.0 - relevance_result.get("confidence", 0.0))
        
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
        
        if relevance_score >= 0.7:  # High score means low relevance
            flag_reasons["irrelevant"] = relevance_result
            is_flagged = True
        
        if generic_score > 0.7:
            flag_reasons["generic"] = generic_result
            is_flagged = True
        
        if quality_score < 30:
            flag_reasons["low_quality"] = {"confidence": 1.0, "reason": f"Quality score {quality_score} is very low"}
            is_flagged = True
        
        # Apply priority filtering to prevent over-flagging
        # Priority order: gibberish > irrelevant > copy_paste > generic > low_quality
        if "gibberish" in flag_reasons:
            # Gibberish takes precedence - remove generic and low_quality flags
            flag_reasons.pop("generic", None)
            flag_reasons.pop("low_quality", None)
        elif "irrelevant" in flag_reasons:
            # Irrelevant takes precedence over generic
            flag_reasons.pop("generic", None)
        
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
    
    @staticmethod
    def _split_combined(combined: Any) -> Dict[str, Dict[str, Any]]:
        """Check the combined reply has all five parts in the expected shape."""
        if not isinstance(combined, dict):
            raise ValueError("The text check returned no JSON object")
        needed = {"gibberish": "is_gibberish", "copy_paste": "is_copypaste", "relevance": "is_relevant",
                  "generic": "is_generic", "quality": "score"}
        parts = {}
        for name, key in needed.items():
            part = combined.get(name)
            if not isinstance(part, dict) or key not in part:
                raise ValueError(f"The text check left out {name}")
            parts[name] = part
        try:
            parts["quality"]["score"] = max(0.0, min(100.0, float(parts["quality"]["score"])))
        except (TypeError, ValueError):
            raise ValueError("The text check gave no quality score")
        return parts

    @staticmethod
    def unchecked_result(reason: str) -> TextAnalysisResult:
        """An answer the AI check could not score: no score and no flags, marked as not checked.

        It is not given a middle score, so it never passes as a checked, acceptable answer.
        """
        return TextAnalysisResult(
            quality_score=None,
            is_flagged=False,
            flag_reasons={},
            gibberish_score=None,
            copy_paste_score=None,
            relevance_score=None,
            generic_score=None,
            analysis_details={"unchecked": True, "error": reason[:300]},
            confidence=0.0,
        )

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
                processed_results.append(self.unchecked_result(str(result)))
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
