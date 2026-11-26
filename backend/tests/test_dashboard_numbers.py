"""
Dashboard numbers agree across pages, and the session list carries each session's verdict.

Bot rate everywhere = bot sessions out of checked (analysed) sessions; a session
analysed twice counts once.
"""

import pytest

pytest.importorskip("aiosqlite")

from tests.test_live_survey_flow import (  # noqa: E402,F401  (api is a fixture)
    SURVEY,
    analyze,
    api,
    human_events,
    script_events,
    send,
    start,
    t0,
)


async def _survey(api):
    people = []
    for index in range(3):
        sid = await start(api, ip=f"203.0.113.{20 + index}", respondent=f"person-{index}")
        await send(api, sid, human_events(t0()))
        await analyze(api, sid)
        people.append(sid)
    bot = await start(api, ip="198.51.100.9", respondent="script-1")
    await send(api, bot, script_events(t0()))
    await analyze(api, bot)
    await analyze(api, bot)  # analysed twice: still one bot session
    waiting = await start(api, ip="203.0.113.99", respondent="not-yet")
    return people, bot, waiting


@pytest.mark.asyncio
async def test_bot_rate_is_the_same_on_every_page(api):
    await _survey(api)
    overview = (await api.get("/dashboard/overview", params={"days": 7})).json()["detections"]
    assert overview["checked"] == 4 and overview["bots_detected"] == 1 and overview["bot_rate"] == 25.0
    listed = next(s for s in (await api.get("/surveys")).json()["surveys"] if s["survey_id"] == SURVEY)
    assert listed["session_count"] == 5 and listed["checked_count"] == 4 and listed["bot_rate"] == 25.0
    details = (await api.get(f"/surveys/{SURVEY}")).json()["bot_detection"]
    assert details["total_detections"] == 4 and details["bot_count"] == 1 and details["bot_rate"] == 25.0
    trend = (await api.get("/dashboard/analytics/trends", params={"days": 1})).json()["trends"]
    assert sum(day["sessions"] for day in trend) == 5 and sum(day["bots"] for day in trend) == 1


@pytest.mark.asyncio
async def test_session_list_shows_verdicts_and_filters_work(api):
    people, bot, waiting = await _survey(api)
    body = (await api.get("/dashboard/sessions")).json()
    rows = {row["id"]: row for row in body["sessions"]}
    assert body["pagination"]["total"] == 5
    assert rows[bot]["is_bot"] is True and rows[bot]["risk_level"] in ("high", "critical")
    assert rows[people[0]]["is_bot"] is False and rows[people[0]]["risk_level"] == "low"
    assert rows[waiting]["analyzed"] is False and rows[waiting]["risk_level"] == "unknown"
    assert rows[bot]["platform"] == "decipher" and rows[bot]["event_count"] > 0

    bots = (await api.get("/dashboard/sessions", params={"is_bot": "true"})).json()
    assert [row["id"] for row in bots["sessions"]] == [bot] and bots["pagination"]["total"] == 1
    unknown = (await api.get("/dashboard/sessions", params={"risk_level": "unknown"})).json()
    assert [row["id"] for row in unknown["sessions"]] == [waiting]
    found = (await api.get("/dashboard/sessions", params={"search": "person-1"})).json()
    assert [row["respondent_id"] for row in found["sessions"]] == ["person-1"]
    paged = (await api.get("/dashboard/sessions", params={"limit": 2, "page": 3})).json()
    assert len(paged["sessions"]) == 1 and paged["pagination"]["pages"] == 3
