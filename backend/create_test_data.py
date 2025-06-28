"""
Create test data for bot detection API.

This script creates sample sessions, behavior data, and detection results
for testing the dashboard and detection endpoints.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Session, BehaviorData, DetectionResult

async def create_test_data():
    """Create test data for the bot detection API."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Create test sessions
            sessions = []
            for i in range(5):
                session = Session(
                    id=str(uuid.uuid4()),
                    user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    ip_address=f"192.168.1.{100 + i}",
                    referrer="https://example.com/survey",
                    platform="qualtrics",
                    survey_id=f"survey_{i+1}",
                    respondent_id=f"respondent_{i+1}",
                    created_at=datetime.utcnow() - timedelta(hours=i),
                    last_activity=datetime.utcnow() - timedelta(minutes=i*10),
                    is_active=i < 3,  # First 3 sessions are active
                    is_completed=i >= 2  # Last 3 sessions are completed
                )
                sessions.append(session)
                db.add(session)
            
            await db.commit()
            
            # Create behavior data for each session
            for session in sessions:
                for j in range(3):  # 3 events per session
                    event_type = "click" if j % 2 == 0 else "scroll"
                    event_data = {}
                    if event_type == "click":
                        event_data = {"mouse_x": 100 + j*50, "mouse_y": 200 + j*30}
                    elif event_type == "scroll":
                        event_data = {"scroll_x": 0, "scroll_y": j*100}
                    behavior = BehaviorData(
                        session_id=session.id,
                        event_type=event_type,
                        timestamp=datetime.utcnow() - timedelta(minutes=j*5),
                        element_id=f"element_{j}",
                        element_type="button" if j % 2 == 0 else "div",
                        page_url=f"https://example.com/survey/page_{j+1}",
                        screen_width=1920,
                        screen_height=1080,
                        event_data=event_data
                    )
                    db.add(behavior)
            
            await db.commit()
            
            # Create detection results for each session
            for session in sessions:
                detection = DetectionResult(
                    session_id=session.id,
                    is_bot=i % 3 == 0,  # Every 3rd session is a bot
                    confidence_score=0.85 + (i * 0.05),
                    risk_level="high" if i % 3 == 0 else "low",
                    detection_methods=["pattern_analysis", "behavior_analysis"],
                    processing_time_ms=150 + i*10,
                    event_count=3,
                    analysis_summary=f"Analysis for session {session.id}",
                    method_scores={"pattern_analysis": 0.8, "behavior_analysis": 0.9},
                    flagged_patterns=["rapid_clicking", "linear_movement"],
                    analyzed_at=datetime.utcnow() - timedelta(minutes=i*5)
                )
                db.add(detection)
            
            await db.commit()
            
            print("✅ Test data created successfully!")
            print(f"Created {len(sessions)} sessions with behavior data and detection results")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            await db.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_data()) 