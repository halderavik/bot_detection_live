"""
End-to-end checks of a live survey against a real (SQLite) database.

Each test drives the HTTP API the way the survey tracker does: create a session,
send events, register questions and answers, then run /analyze and
/composite-analyze and read the reports.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

pytest.importorskip("aiosqlite")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.controllers import text_analysis_controller  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.services.text_analysis_service import TextAnalysisResult  # noqa: E402
from app.utils.helpers import client_ip, determine_risk_level  # noqa: E402
from main import create_app  # noqa: E402

DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DESKTOP_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
HEADLESS = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/130.0 Safari/537.36"
SURVEY = "Live Flow Test"


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    """The real app on a fresh SQLite database, with text scoring stubbed out."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'live.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def db():
        async with maker() as session:
            yield session

    async def fake_score(question, answer):
        bad = len(answer.split()) < 3
        return TextAnalysisResult(
            quality_score=10.0 if bad else 80.0, is_flagged=bad,
            flag_reasons={"generic": {"score": 0.9}} if bad else {},
            gibberish_score=0.0, copy_paste_score=0.0, relevance_score=0.0, generic_score=0.9 if bad else 0.0,
            analysis_details={}, confidence=0.9,
        )

    monkeypatch.setattr(text_analysis_controller.text_analysis_service, "analyze_response", fake_score)
    app = create_app()
    app.dependency_overrides[get_db] = db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        client.engine = engine
        yield client
    await engine.dispose()


async def start(api, agent=DESKTOP, ip="203.0.113.10", respondent="r1"):
    response = await api.post(
        f"/detection/sessions?survey_id={SURVEY}&platform_id=decipher&respondent_id={respondent}",
        headers={"user-agent": agent, "x-forwarded-for": ip},
    )
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def stamp(start, ms):
    return (start + timedelta(milliseconds=ms)).isoformat()


def human_events(t0, pages=4, page_ms=20000):
    """A person: curved mouse paths, uneven typing, trusted clicks, a page every 20 s."""
    events = [{"event_type": "page_load", "timestamp": stamp(t0, 0), "screen_width": 1536, "screen_height": 864,
               "webdriver": False, "touch_points": 0}]
    clock = 0
    for page in range(pages):
        x, y = 300, 200
        for step in range(25):
            clock += 90 + (step * 37) % 70
            x += 9 + (step * 7) % 11
            y += (step % 5) - 1 + (step * 3) % 4
            events.append({"event_type": "mouse_move", "timestamp": stamp(t0, clock), "x": x, "y": y})
        clock += 400
        events.append({"event_type": "mouse_click", "timestamp": stamp(t0, clock), "x": x, "y": y,
                       "trusted": True, "pointer": "mouse"})
        for key in range(12):
            clock += 110 + (key * 53) % 140
            events.append({"event_type": "keystroke", "timestamp": stamp(t0, clock), "key": "char", "trusted": True})
        clock = (page + 1) * page_ms
        events.append({"event_type": "form_submit", "timestamp": stamp(t0, clock), "element_id": f"qos-page:{page_ms}"})
    return events


def script_events(t0, pages=4):
    """A naive script: element.click() on every answer, no pointer, no typing, 2 s a page."""
    events = [{"event_type": "page_load", "timestamp": stamp(t0, 0), "screen_width": 1920, "screen_height": 1080}]
    clock = 0
    for page in range(pages):
        for answer in range(3):
            clock += 150
            events.append({"event_type": "mouse_click", "timestamp": stamp(t0, clock), "x": 0, "y": 0, "trusted": False})
        clock = (page + 1) * 2000
        events.append({"event_type": "form_submit", "timestamp": stamp(t0, clock)})
    return events


async def send(api, sid, events):
    response = await api.post(f"/detection/sessions/{sid}/events", json=events)
    assert response.status_code == 200, response.text


async def analyze(api, sid):
    response = await api.post(f"/detection/sessions/{sid}/analyze")
    assert response.status_code == 200, response.text
    return response.json()


def t0():
    return datetime.now(timezone.utc) - timedelta(minutes=5)


# ------------------------------------------------------------------ verdicts

@pytest.mark.asyncio
async def test_person_is_human_with_low_risk(api):
    sid = await start(api)
    await send(api, sid, human_events(t0()))
    result = await analyze(api, sid)
    assert result["is_bot"] is False
    assert result["risk_level"] == "low"
    assert result["confidence_score"] < 0.5
    assert result["method_scores"]["network_analysis"] == 0.0


@pytest.mark.asyncio
async def test_scripted_clicks_are_a_bot(api):
    sid = await start(api)
    await send(api, sid, script_events(t0()))
    result = await analyze(api, sid)
    assert result["is_bot"] is True
    assert result["risk_level"] in ("high", "critical")
    assert result["flagged_patterns"]["decisive_signals"]
    assert "Bot detected" in result["analysis_summary"]


@pytest.mark.asyncio
async def test_no_input_at_all_is_a_bot(api):
    sid = await start(api)
    start_time = t0()
    events = [{"event_type": "page_load", "timestamp": stamp(start_time, 0), "screen_width": 1920, "screen_height": 1080}]
    events += [{"event_type": "form_submit", "timestamp": stamp(start_time, 3000 * (i + 1))} for i in range(4)]
    await send(api, sid, events)
    result = await analyze(api, sid)
    assert result["is_bot"] is True
    assert any("no mouse or keyboard" in s for s in result["flagged_patterns"]["decisive_signals"])


@pytest.mark.asyncio
async def test_headless_or_webdriver_browser_is_a_bot(api):
    sid = await start(api, agent=HEADLESS)
    await send(api, sid, human_events(t0()))
    assert (await analyze(api, sid))["is_bot"] is True

    sid = await start(api, agent=DESKTOP, respondent="r2")
    events = human_events(t0())
    events[0]["webdriver"] = True
    await send(api, sid, events)
    assert (await analyze(api, sid))["is_bot"] is True


@pytest.mark.asyncio
async def test_phone_without_mouse_is_human(api):
    sid = await start(api, agent=IPHONE)
    start_time = t0()
    events = [{"event_type": "page_load", "timestamp": stamp(start_time, 0), "screen_width": 390, "screen_height": 844,
               "touch_points": 5}]
    clock = 0
    for page in range(4):
        for tap in range(3):
            clock += 1800 + tap * 700
            events.append({"event_type": "mouse_click", "timestamp": stamp(start_time, clock), "x": 120 + tap * 40,
                           "y": 300 + page * 10, "trusted": True, "pointer": "touch"})
        clock = (page + 1) * 15000
        events.append({"event_type": "form_submit", "timestamp": stamp(start_time, clock)})
    await send(api, sid, events)
    result = await analyze(api, sid)
    assert result["is_bot"] is False
    assert result["risk_level"] == "low"


@pytest.mark.asyncio
async def test_ipad_touch_with_desktop_agent_is_human(api):
    """iPadOS Safari reports a Mac user agent; the touch pointer still marks it as a touch device."""
    sid = await start(api, agent=DESKTOP_MAC)
    start_time = t0()
    events = [{"event_type": "page_load", "timestamp": stamp(start_time, 0), "screen_width": 1024, "screen_height": 1366,
               "touch_points": 5}]
    for page in range(3):
        events.append({"event_type": "mouse_click", "timestamp": stamp(start_time, page * 9000 + 4000), "x": 200,
                       "y": 400, "trusted": True, "pointer": "touch"})
        events.append({"event_type": "form_submit", "timestamp": stamp(start_time, (page + 1) * 9000)})
    await send(api, sid, events)
    assert (await analyze(api, sid))["is_bot"] is False


@pytest.mark.asyncio
async def test_keyboard_only_respondent_is_human(api):
    sid = await start(api)
    start_time = t0()
    events = [{"event_type": "page_load", "timestamp": stamp(start_time, 0), "screen_width": 1536, "screen_height": 864}]
    clock = 0
    for page in range(4):
        for key in range(6):
            clock += 250 + (key * 61) % 300
            events.append({"event_type": "keystroke", "timestamp": stamp(start_time, clock), "key": "Tab", "trusted": True})
        events.append({"event_type": "mouse_click", "timestamp": stamp(start_time, clock + 30), "x": 0, "y": 0,
                       "trusted": True})
        clock = (page + 1) * 18000
        events.append({"event_type": "form_submit", "timestamp": stamp(start_time, clock)})
    await send(api, sid, events)
    assert (await analyze(api, sid))["is_bot"] is False


def test_risk_level_follows_bot_probability():
    assert determine_risk_level(0.1, False) == "low"
    assert determine_risk_level(0.55, False) == "medium"
    assert determine_risk_level(0.75, True) == "high"
    assert determine_risk_level(0.95, True) == "critical"


# ------------------------------------------------------------------ composite, grid, timing

async def register(api, sid, text, kind):
    response = await api.post("/text-analysis/questions", json={"session_id": sid, "question_text": text, "question_type": kind})
    assert response.status_code == 200, response.text
    return response.json()["question_id"]


async def answer(api, sid, qid, text, ms):
    response = await api.post("/text-analysis/responses",
                              json={"session_id": sid, "question_id": qid, "response_text": text, "response_time_ms": ms})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_composite_after_analyze_includes_grid_and_timing(api):
    sid = await start(api)
    await send(api, sid, human_events(t0()))
    await analyze(api, sid)  # used to make composite fail with a 500

    grid = await register(api, sid, "Rate each feature", "grid")
    for _ in range(5):
        stored = await answer(api, sid, grid, "4", 1500)
        assert stored["quality_score"] is None  # grid rows are not text-scored
    open_end = await register(api, sid, "Why did you choose that?", "open_ended")
    scored = await answer(api, sid, open_end, "good", 9000)
    assert scored["is_flagged"] is True

    response = await api.post(f"/detection/sessions/{sid}/composite-analyze")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grid_details"]["straight_lined_questions"] == 1
    assert body["timing_details"]["speeders"] >= 1
    assert body["text_quality_details"]["total_responses"] == 1  # the grid rows are not counted as text

    # Running it twice must also work
    assert (await api.post(f"/detection/sessions/{sid}/composite-analyze")).status_code == 200

    report = (await api.get(f"/reports/detailed/{SURVEY}?include_inactive=true")).json()
    row = next(r for r in report["respondents"] if r["session_id"] == sid)
    assert row["grid_straight_lining"] is True
    assert row["timing_speeder"] is True
    assert row["text_response_count"] == 1
    assert row["risk_level"] == "low"
    assert row["total_events"] == len(human_events(t0()))


@pytest.mark.asyncio
async def test_composite_without_analyze_scores_behaviour(api):
    sid = await start(api)
    await send(api, sid, script_events(t0()))
    body = (await api.post(f"/detection/sessions/{sid}/composite-analyze")).json()
    assert body["behavioral_score"] >= 0.85  # not the old neutral 0.5
    report = (await api.get(f"/reports/detailed/{SURVEY}?include_inactive=true")).json()
    assert next(r for r in report["respondents"] if r["session_id"] == sid)["is_bot"] is True


# ------------------------------------------------------------------ fraud

@pytest.mark.asyncio
async def test_shared_network_is_not_ip_reuse_but_same_device_is(api):
    office = "198.51.100.7"
    agents = [DESKTOP, DESKTOP_MAC, IPHONE, DESKTOP.replace("130.0", "129.0"), DESKTOP.replace("130.0", "128.0"), HEADLESS]
    sids = []
    for index, agent in enumerate(agents[:5]):
        sid = await start(api, agent=agent, ip=office, respondent=f"office-{index}")
        await send(api, sid, human_events(t0()))
        sids.append(sid)
    for sid in sids:
        body = (await api.post(f"/detection/sessions/{sid}/composite-analyze")).json()
    flags = body["fraud_details"]["flag_reasons"] or {}
    assert "ip_reuse" not in flags and "high_velocity" not in flags

    repeat = []
    for index in range(3):
        sid = await start(api, agent=DESKTOP, ip="192.0.2.44", respondent=f"repeat-{index}")
        await send(api, sid, human_events(t0()))
        repeat.append((await api.post(f"/detection/sessions/{sid}/composite-analyze")).json())
    assert "device_reuse" in (repeat[-1]["fraud_details"]["flag_reasons"] or {})


@pytest.mark.asyncio
async def test_other_surveys_do_not_count_as_reuse(api):
    for index in range(6):
        response = await api.post(f"/detection/sessions?survey_id=Other{index}&platform_id=decipher&respondent_id=x{index}",
                                  headers={"user-agent": DESKTOP, "x-forwarded-for": "192.0.2.99"})
        sid = response.json()["session_id"]
        await send(api, sid, human_events(t0()))
        await api.post(f"/detection/sessions/{sid}/composite-analyze")
    sid = await start(api, ip="192.0.2.99")
    await send(api, sid, human_events(t0()))
    body = (await api.post(f"/detection/sessions/{sid}/composite-analyze")).json()
    assert not (body["fraud_details"]["flag_reasons"] or {})


def test_client_ip_uses_the_last_public_forwarded_address():
    def request(header, host="169.254.1.1"):
        return SimpleNamespace(headers={"x-forwarded-for": header} if header else {}, client=SimpleNamespace(host=host))

    assert client_ip(request("1.2.3.4, 8.8.8.8")) == "8.8.8.8"  # left entry is client-supplied
    assert client_ip(request("8.8.4.4, 10.0.0.2")) == "8.8.4.4"  # private hops skipped
    assert client_ip(request("")) == "169.254.1.1"


# ------------------------------------------------------------------ reports at scale

@pytest.mark.asyncio
async def test_detailed_report_uses_a_fixed_number_of_queries(api):
    for index in range(40):
        sid = await start(api, respondent=f"bulk-{index}")
        await send(api, sid, human_events(t0(), pages=1))
        await analyze(api, sid)

    statements = []
    listener = lambda *args: statements.append(1)  # noqa: E731
    event.listen(api.engine.sync_engine, "before_cursor_execute", listener)
    try:
        report = await api.get(f"/reports/detailed/{SURVEY}?include_inactive=true")
        summary = await api.get(f"/reports/summary/{SURVEY}?include_inactive=true")
    finally:
        event.remove(api.engine.sync_engine, "before_cursor_execute", listener)

    assert report.status_code == 200 and summary.status_code == 200
    assert report.json()["total_respondents"] == 40
    assert summary.json()["total_sessions"] == 40
    assert len(statements) < 25  # was several queries per respondent


@pytest.mark.asyncio
async def test_session_details_include_event_data(api):
    sid = await start(api)
    await send(api, sid, human_events(t0(), pages=1))
    details = (await api.get(f"/dashboard/sessions/{sid}/details")).json()
    submit = next(e for e in details["behavior_data"] if e["event_type"] == "form_submit")
    assert submit["element_id"].startswith("qos-page:")
    move = next(e for e in details["behavior_data"] if e["event_type"] == "mouse_move")
    assert "x" in move["event_data"] and "timestamp" not in move["event_data"]
