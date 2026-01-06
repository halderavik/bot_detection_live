"""
Unit tests for configuration sanitization.

These tests ensure environment variables that come from secrets (often with a
trailing newline/CRLF) are sanitized to avoid runtime failures.
"""

from app.config import Settings


def test_database_url_strips_crlf_and_whitespace() -> None:
    """DATABASE_URL should be sanitized for whitespace/CRLF."""
    s = Settings(
        SECRET_KEY="unit-test-secret",
        DATABASE_URL="postgresql+asyncpg://u:p@h/db\r\n",
    )
    assert s.DATABASE_URL == "postgresql+asyncpg://u:p@h/db"


def test_openai_api_key_strips_crlf_and_whitespace() -> None:
    """OPENAI_API_KEY should be sanitized for whitespace/CRLF."""
    s = Settings(
        SECRET_KEY="unit-test-secret",
        OPENAI_API_KEY="sk-test-abc123\r\n",
    )
    assert s.OPENAI_API_KEY == "sk-test-abc123"

