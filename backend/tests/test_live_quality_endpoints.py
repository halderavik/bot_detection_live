"""
Live quality endpoints against a real (SQLite) database.

Sessions are created and analysed through the API the way the tracker does, then
the dashboard, rules, CSV export, and data merge are read back.
"""

import io
import json

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("pandas")

import pandas as pd  # noqa: E402

from app.services import live_quality  # noqa: E402
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


@pytest.fixture(autouse=True)
def _fresh_cache():
    live_quality._CACHE.clear()
    yield
    live_quality._CACHE.clear()


async def _two_respondents(api):
    """One person (4 pages of 20 s) and one script, both analysed."""
    human = await start(api, respondent="person-1")
    await send(api, human, human_events(t0()))
    await analyze(api, human)
    bot = await start(api, ip="198.51.100.7", respondent="script-1")
    await send(api, bot, script_events(t0()))
    await analyze(api, bot)
    return human, bot


@pytest.mark.asyncio
async def test_results_judge_each_session_and_read_page_times(api):
    human, bot = await _two_respondents(api)
    response = await api.get("/quality/results", params={"survey_id": SURVEY})
    assert response.status_code == 200, response.text
    body = response.json()
    rows = {row["session_id"]: row for row in body["respondents"]}
    assert body["totals"]["sessions"] == 2 and body["totals"]["checked"] == 2
    assert rows[bot]["verdict"] == "bot" and "Bot-like behaviour" in rows[bot]["flags"]
    assert rows[human]["verdict"] == "human"
    assert rows[human]["pages"] == 4 and rows[human]["seconds"] == 80.0
    assert body["rules"]["bot_threshold"] == 0.7
    assert len(body["flag_counts"]) == 9 and body["trend"]["buckets"]

    surveys = (await api.get("/quality/surveys")).json()["surveys"]
    entry = next(item for item in surveys if item["survey_id"] == SURVEY)
    assert entry["sessions"] == 2 and entry["custom_rules"] is False


@pytest.mark.asyncio
async def test_rules_are_saved_per_survey_and_change_the_verdicts(api):
    human, bot = await _two_respondents(api)
    url, params = "/quality/rules", {"survey_id": SURVEY}
    state = (await api.get(url, params=params)).json()
    assert state["rules"] == state["defaults"] and state["changed"] == []

    # No decisive signal counts and the threshold is out of reach: nobody is a bot.
    edited = {**state["rules"], "bot_signals": [], "bot_threshold": 0.99}
    saved = await api.put(url, params=params, json=edited)
    assert saved.status_code == 200, saved.text
    assert sorted(saved.json()["changed"]) == ["bot_signals", "bot_threshold"]
    live_quality._CACHE.clear()
    body = (await api.get("/quality/results", params=params)).json()
    assert body["totals"]["bots"] == 0

    other = (await api.get(url, params={"survey_id": "Another survey"})).json()
    assert other["changed"] == []  # rules belong to one survey
    surveys = (await api.get("/quality/surveys")).json()["surveys"]
    assert next(item for item in surveys if item["survey_id"] == SURVEY)["custom_rules"] is True

    assert (await api.put(url, params=params, json={**edited, "bot_signals": ["telepathy"]})).status_code == 422
    assert (await api.put(url, params=params, json={**edited, "bot_threshold": 1.5})).status_code == 422
    reset = (await api.delete(url, params=params)).json()
    assert reset["rules"] == reset["defaults"]


@pytest.mark.asyncio
async def test_export_is_csv_with_one_row_per_session(api):
    await _two_respondents(api)
    response = await api.get("/quality/export", params={"survey_id": SURVEY})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="quality-Live_Flow_Test.csv"' in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0].startswith("respondent_id,session_id") and len(lines) == 3


@pytest.mark.asyncio
async def test_merge_returns_the_file_with_lq_variables_and_a_report(api):
    human, bot = await _two_respondents(api)
    data = f"record,QOS_SESSION,uuid\n1,{human},\n2,,script-1\n3,,someone-else\n4,,\n"
    response = await api.post(
        "/quality/merge",
        params={"survey_id": SURVEY},
        files={"file": ("wave1.csv", data.encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert 'filename="wave1_quality.csv"' in response.headers["content-disposition"]
    report = json.loads(response.headers["x-quality-report"])
    assert report["tracked"] == 3 and report["matched"] == 2 and report["unmatched"] == 1
    assert report["bots"] == 1
    back = pd.read_csv(io.BytesIO(response.content), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert list(back["LQ_MATCHED"]) == ["1.0", "1.0", "0.0", "0.0"]
    assert list(back["LQ_F_BOT"][:2]) == ["0.0", "1.0"]


@pytest.mark.asyncio
async def test_merge_refuses_unusable_input(api):
    params = {"survey_id": SURVEY}
    empty = await api.post("/quality/merge", params=params, files={"file": ("d.csv", b"record,QOS_SESSION\n1,x\n", "text/csv")})
    assert empty.status_code == 422 and "no live quality results" in empty.json()["detail"]
    await _two_respondents(api)
    live_quality._CACHE.clear()  # the empty result above is cached for a few seconds
    wrong = await api.post("/quality/merge", params=params, files={"file": ("d.json", b"{}", "application/json")})
    assert wrong.status_code == 422
    plain = await api.post("/quality/merge", params=params, files={"file": ("d.csv", b"record\n1\n", "text/csv")})
    assert plain.status_code == 422 and "nothing to match" in plain.json()["detail"]
    blank = await api.get("/quality/results", params={"survey_id": "  "})
    assert blank.status_code == 422


@pytest.mark.asyncio
async def test_report_has_period_results_survey_details_and_rules(api):
    await _two_respondents(api)
    body = (await api.get("/quality/report", params={"survey_id": SURVEY})).json()
    assert body["totals"]["sessions"] == 2 and body["survey"]["survey_id"] == SURVEY
    assert body["rules_state"]["rules"]["bot_threshold"] == 0.7 and body["rules_state"]["changed"] == []
    assert body["period"] == {"from": None, "to": None}
    future = (await api.get("/quality/report", params={"survey_id": SURVEY, "date_from": "2099-01-01T00:00:00"})).json()
    assert future["totals"]["sessions"] == 0 and future["respondents"] == []
    wrong = await api.get("/quality/report", params={"survey_id": SURVEY, "date_from": "2026-12-02", "date_to": "2026-12-01"})
    assert wrong.status_code == 422
