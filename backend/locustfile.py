"""
Locust Load Testing for Bot Detection API

This file provides load testing scenarios for the bot detection API
using Locust framework for realistic load simulation.
"""

from locust import HttpUser, task, between
import random
import json
from datetime import datetime, timedelta

class BotDetectionUser(HttpUser):
    """Simulates a user interacting with the bot detection API."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    session_ids = []
    
    def on_start(self):
        """Initialize user session."""
        # Create a session for this user
        response = self.client.post("/api/v1/detection/sessions")
        if response.status_code == 200:
            data = response.json()
            self.session_ids.append(data.get('session_id'))
    
    @task(3)
    def health_check(self):
        """Health check endpoint - high frequency."""
        self.client.get("/health")
    
    @task(2)
    def create_session(self):
        """Create new session - medium frequency."""
        response = self.client.post("/api/v1/detection/sessions")
        if response.status_code == 200:
            data = response.json()
            self.session_ids.append(data.get('session_id'))
    
    @task(5)
    def send_events(self):
        """Send events to existing session - high frequency."""
        if not self.session_ids:
            return
        
        session_id = random.choice(self.session_ids)
        events = self._generate_events(5)  # Send 5 events per request
        
        self.client.post(
            f"/api/v1/detection/sessions/{session_id}/events",
            json=events,
            headers={"Content-Type": "application/json"}
        )
    
    @task(1)
    def analyze_session(self):
        """Analyze session - low frequency."""
        if not self.session_ids:
            return
        
        session_id = random.choice(self.session_ids)
        self.client.post(f"/api/v1/detection/sessions/{session_id}/analyze")
    
    @task(2)
    def get_session_status(self):
        """Get session status - medium frequency."""
        if not self.session_ids:
            return
        
        session_id = random.choice(self.session_ids)
        self.client.get(f"/api/v1/detection/sessions/{session_id}/status")
    
    @task(1)
    def dashboard_overview(self):
        """Get dashboard overview - low frequency."""
        self.client.get("/api/v1/dashboard/overview")
    
    @task(1)
    def dashboard_sessions(self):
        """Get sessions list - low frequency."""
        self.client.get("/api/v1/dashboard/sessions")
    
    def _generate_events(self, count):
        """Generate realistic events for testing."""
        event_types = ['keystroke', 'mouse_move', 'mouse_click', 'scroll', 'focus']
        events = []
        
        for i in range(count):
            event = {
                "event_type": random.choice(event_types),
                "timestamp": (datetime.now() + timedelta(seconds=i)).isoformat(),
                "element_id": f"element-{random.randint(1, 100)}",
                "element_type": random.choice(['input', 'button', 'div', 'span']),
                "page_url": "https://example.com/survey",
                "screen_width": 1920,
                "screen_height": 1080,
                "viewport_width": 1920,
                "viewport_height": 937
            }
            
            if event["event_type"] == "keystroke":
                event["key"] = random.choice("abcdefghijklmnopqrstuvwxyz")
            elif event["event_type"] in ["mouse_move", "mouse_click"]:
                event["x"] = random.randint(0, 1920)
                event["y"] = random.randint(0, 1080)
            
            events.append(event)
        
        return events

class DashboardUser(HttpUser):
    """Simulates dashboard users with read-only operations."""
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between requests
    
    @task(3)
    def dashboard_overview(self):
        """Get dashboard overview."""
        self.client.get("/api/v1/dashboard/overview")
    
    @task(2)
    def dashboard_sessions(self):
        """Get sessions list."""
        self.client.get("/api/v1/dashboard/sessions")
    
    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health")
    
    @task(1)
    def analytics_trends(self):
        """Get analytics trends."""
        self.client.get("/api/v1/dashboard/analytics/trends")

class IntegrationUser(HttpUser):
    """Simulates integration webhook calls."""
    
    wait_time = between(5, 15)  # Wait 5-15 seconds between requests
    
    @task(1)
    def qualtrics_webhook(self):
        """Simulate Qualtrics webhook."""
        webhook_data = {
            "responseId": f"R_{random.randint(100000, 999999)}",
            "surveyId": f"SV_{random.randint(100000, 999999)}",
            "respondentId": f"RESP_{random.randint(100000, 999999)}",
            "embeddedData": {
                "bot_detection_session_id": f"session-{random.randint(100000, 999999)}"
            }
        }
        
        self.client.post(
            "/api/v1/integrations/webhooks/qualtrics",
            json=webhook_data,
            headers={"Content-Type": "application/json"}
        )
    
    @task(1)
    def decipher_webhook(self):
        """Simulate Decipher webhook."""
        webhook_data = {
            "responseId": f"R_{random.randint(100000, 999999)}",
            "surveyId": f"SURVEY_{random.randint(100000, 999999)}",
            "respondentId": f"RESP_{random.randint(100000, 999999)}",
            "systemVariables": {
                "bot_detection_session_id": f"session-{random.randint(100000, 999999)}"
            }
        }
        
        self.client.post(
            "/api/v1/integrations/webhooks/decipher",
            json=webhook_data,
            headers={"Content-Type": "application/json"}
        ) 