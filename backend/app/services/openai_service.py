"""
OpenAI API service wrapper with rate limiting, caching, and error handling.

This service provides a robust wrapper around the OpenAI API with features like
rate limiting, response caching, retry logic, and cost tracking.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

import openai
from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class UsageStats:
    """Track OpenAI API usage statistics."""
    total_requests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    estimated_cost: float = 0.0
    errors: int = 0
    cache_hits: int = 0

class RateLimiter:
    """Token bucket rate limiter for OpenAI API calls."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_minutes: Time window in minutes
        """
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Try to acquire a request slot.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]
            
            # Check if we can make another request
            if len(self.requests) >= self.max_requests:
                return False
            
            # Add current request
            self.requests.append(now)
            return True

class ResponseCache:
    """Simple in-memory cache for OpenAI responses."""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize response cache.
        
        Args:
            ttl_hours: Time-to-live for cached responses in hours
        """
        self.cache = {}
        self.ttl_seconds = ttl_hours * 3600
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt and model."""
        return f"{model}:{hash(prompt)}"
    
    def get(self, prompt: str, model: str) -> Optional[Dict]:
        """
        Get cached response if available and not expired.
        
        Args:
            prompt: The prompt used
            model: The model used
            
        Returns:
            Cached response or None
        """
        key = self._get_cache_key(prompt, model)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return cached_data
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, prompt: str, model: str, response: Dict):
        """
        Cache a response.
        
        Args:
            prompt: The prompt used
            model: The model used
            response: The response to cache
        """
        key = self._get_cache_key(prompt, model)
        self.cache[key] = (response, time.time())

class OpenAIService:
    """OpenAI API service with rate limiting, caching, and error handling."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.is_available = bool(settings.OPENAI_API_KEY)
        
        if self.is_available:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"OpenAI service initialized with model: {settings.OPENAI_MODEL}")
        else:
            self.client = None
            logger.warning("OpenAI service initialized without API key - text analysis will use fallback mode")
        
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.timeout = settings.OPENAI_TIMEOUT
        self.max_retries = settings.OPENAI_MAX_RETRIES
        
        # Initialize components
        self.rate_limiter = RateLimiter(max_requests=100, window_minutes=1)
        self.cache = ResponseCache(ttl_hours=24)
        self.usage_stats = UsageStats()
        
        # Token costs (GPT-4o-mini pricing)
        self.input_cost_per_1k = 0.00015  # $0.15 per 1M tokens
        self.output_cost_per_1k = 0.0006   # $0.60 per 1M tokens
    
    async def analyze_text(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze text using OpenAI API with caching and rate limiting.
        
        Args:
            text: Text to analyze
            prompt_template: Prompt template to use
            
        Returns:
            Analysis result dictionary
            
        Raises:
            Exception: If analysis fails after retries or OpenAI is unavailable
        """
        # Check if OpenAI is available
        if not self.is_available or not self.client:
            raise Exception("OpenAI unavailable: missing OPENAI_API_KEY")
        
        # Check cache first
        prompt = prompt_template.format(text=text)
        cached_result = self.cache.get(prompt, self.model)
        if cached_result:
            self.usage_stats.cache_hits += 1
            logger.debug("Cache hit for text analysis")
            return cached_result
        
        # Rate limiting
        if not await self.rate_limiter.acquire():
            raise Exception("Rate limit exceeded. Please try again later.")
        
        # Prepare request
        messages = [{"role": "user", "content": prompt}]
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"OpenAI API call attempt {attempt + 1}")
                
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        response_format={"type": "json_object"}
                    ),
                    timeout=self.timeout
                )
                
                # Parse response
                result = json.loads(response.choices[0].message.content)
                
                # Update usage statistics
                self.usage_stats.total_requests += 1
                if response.usage:
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    self.usage_stats.total_tokens_input += input_tokens
                    self.usage_stats.total_tokens_output += output_tokens
                    
                    # Calculate cost
                    input_cost = (input_tokens / 1000) * self.input_cost_per_1k
                    output_cost = (output_tokens / 1000) * self.output_cost_per_1k
                    self.usage_stats.estimated_cost += input_cost + output_cost
                
                # Cache successful response
                self.cache.set(prompt, self.model, result)
                
                logger.debug(f"OpenAI analysis completed successfully")
                return result
                
            except asyncio.TimeoutError:
                last_exception = Exception(f"OpenAI API timeout after {self.timeout}s")
                logger.warning(f"OpenAI API timeout on attempt {attempt + 1}")
                
            except openai.APIError as e:
                last_exception = Exception(f"OpenAI API error: {e}")
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                self.usage_stats.errors += 1
                
                # Don't retry on certain errors
                if "rate_limit" in str(e).lower() or "quota" in str(e).lower():
                    raise last_exception
                    
            except Exception as e:
                last_exception = Exception(f"Unexpected error: {e}")
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                self.usage_stats.errors += 1
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        raise last_exception or Exception("OpenAI analysis failed after all retries")
    
    async def batch_analyze(self, texts: List[str], prompt_template: str) -> List[Dict]:
        """
        Analyze multiple texts in parallel with rate limiting.
        
        Args:
            texts: List of texts to analyze
            prompt_template: Prompt template to use
            
        Returns:
            List of analysis results
        """
        # Limit concurrent requests to avoid overwhelming the API
        semaphore = asyncio.Semaphore(5)
        
        async def analyze_single(text: str) -> Dict:
            async with semaphore:
                return await self.analyze_text(text, prompt_template)
        
        tasks = [analyze_single(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch analysis failed for text {i}: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_requests": self.usage_stats.total_requests,
            "total_tokens_input": self.usage_stats.total_tokens_input,
            "total_tokens_output": self.usage_stats.total_tokens_output,
            "estimated_cost": round(self.usage_stats.estimated_cost, 4),
            "errors": self.usage_stats.errors,
            "cache_hits": self.usage_stats.cache_hits,
            "cache_hit_rate": round(
                self.usage_stats.cache_hits / max(self.usage_stats.total_requests, 1) * 100, 2
            )
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage_stats = UsageStats()
        logger.info("OpenAI usage statistics reset")

# Global instance
openai_service = OpenAIService()
