"""
Settings changed from the dashboard's Settings page.

One row per setting. A row overrides the environment variable of the same name;
deleting it goes back to the environment value. Secret values (API keys, the
tracking secret) are stored encrypted with a key derived from SECRET_KEY.
"""

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.database import Base


class AppSetting(Base):
    """One setting override."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    is_secret = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
