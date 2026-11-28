"""Shared test setup."""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "timeline: run the server-time check on claimed page times")


@pytest.fixture(autouse=True)
def _no_timeline_check_unless_asked(request, monkeypatch):
    """Integration tests post minutes of page time within milliseconds, which the
    timeline check rightly calls made up. Only tests marked ``timeline`` run it."""
    if request.node.get_closest_marker("timeline") is None:
        from app.services.bot_detection_engine import BotDetectionEngine

        monkeypatch.setattr(BotDetectionEngine, "TIMELINE_MIN_CLAIM_S", float("inf"))
