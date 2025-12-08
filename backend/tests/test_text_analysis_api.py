"""
API tests for text analysis endpoints.

This module contains tests for the text analysis API endpoints
including fallback behavior when OpenAI is unavailable.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from main import app
from app.services.openai_service import openai_service

client = TestClient(app)

class TestTextAnalysisAPI:
    """Test cases for text analysis API endpoints."""
    
    def test_text_analysis_endpoints_exist(self):
        """Test that text analysis endpoints are accessible (not 404)."""
        # Test that endpoints exist and return proper error codes (not 404)
        response = client.get("/api/v1/text-analysis/stats")
        assert response.status_code != 404, "Text analysis endpoints should not return 404"
    
    @patch('app.services.text_analysis_service.openai_service')
    def test_submit_response_without_openai(self, mock_openai_service):
        """Test submitting a response when OpenAI is unavailable."""
        # Mock OpenAI service as unavailable - make methods raise exceptions
        mock_openai_service.is_available = False
        mock_openai_service.client = None
        mock_openai_service.analyze_text = AsyncMock(side_effect=Exception("OpenAI unavailable"))
        mock_openai_service.analyze_with_formatted_prompt = AsyncMock(side_effect=Exception("OpenAI unavailable"))
        
        # First create a session
        session_response = client.post("/api/v1/detection/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Submit a question
        question_data = {
            "session_id": session_id,
            "question_text": "What is your favorite color?",
            "question_type": "open_ended"
        }
        question_response = client.post("/api/v1/text-analysis/questions", json=question_data)
        assert question_response.status_code == 200
        question_id = question_response.json()["question_id"]
        
        # Submit a response - should work with fallback analysis
        response_data = {
            "session_id": session_id,
            "question_id": question_id,
            "response_text": "Blue is my favorite color"
        }
        response = client.post("/api/v1/text-analysis/responses", json=response_data)
        
        # Should succeed with fallback analysis
        assert response.status_code == 200
        result = response.json()
        assert "response_id" in result
        assert "quality_score" in result
        assert "is_flagged" in result
        assert "analysis_details" in result
    
    def test_text_analysis_stats_endpoint(self):
        """Test the text analysis stats endpoint."""
        response = client.get("/api/v1/text-analysis/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_requests" in stats
        assert "total_tokens_input" in stats
        assert "total_tokens_output" in stats
        assert "estimated_cost" in stats
        assert "errors" in stats
        assert "cache_hits" in stats
        assert "cache_hit_rate" in stats
    
    def test_batch_analyze_endpoint(self):
        """Test the batch analyze endpoint."""
        batch_data = [
            {"question": "What is your favorite color?", "answer": "Blue"},
            {"question": "What is your favorite food?", "answer": "Pizza"}
        ]
        
        response = client.post("/api/v1/text-analysis/batch-analyze", json=batch_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "summary" in result
        assert "results" in result
        assert len(result["results"]) == 2

if __name__ == "__main__":
    pytest.main([__file__])
