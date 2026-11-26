"""
The Decipher XML upload endpoint against a real (SQLite) database.

Upload → tracked XML → a session created with the token in that XML lands in
the survey the upload named, which is what the survey's dashboard reads.
"""

import re

import pytest

pytest.importorskip("aiosqlite")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.models import TrackedSurvey  # noqa: E402
from app.services.decipher_tracking import remove_tracking  # noqa: E402
from app.utils import rate_limit  # noqa: E402
from main import create_app  # noqa: E402

from tests.test_decipher_tracking import LOOPS, PLAIN  # noqa: E402


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'upload.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def db():
        async with maker() as session:
            yield session

    monkeypatch.setattr(rate_limit, "LIMITS", {"new_session": (100000, 60), "write": (100000, 60)})
    monkeypatch.setattr(settings, "TRACKING_TOKEN_SECRET", "coffee-secret")
    monkeypatch.setattr(settings, "TRACKER_API_BASE", "https://bot.example/api/v1")
    app = create_app()
    app.dependency_overrides[get_db] = db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        client.maker = maker
        yield client
    await engine.dispose()


async def upload(api, body, name="coffee.xml", **form):
    data = {key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in form.items()}
    return await api.post("/tracking/decipher", files={"file": (name, body.encode("utf-8"), "application/xml")}, data=data)


@pytest.mark.asyncio
async def test_upload_returns_tracked_xml_summary_and_dashboard(api):
    response = await upload(api, PLAIN)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["survey_id"] == "Coffee Machine Study"
    assert body["filename"] == "coffee_tracked.xml"
    assert body["dashboard_path"] == "/surveys/Coffee Machine Study"
    assert body["signed"] is True and body["new_survey_record"] is True
    assert body["survey"] == {"questions": 3, "pages": 3, "loops": 0, "blocks": 0}
    assert body["options"]["privacy_notice"] is True  # on by default
    assert "QOS_privacy" in body["xml"]
    assert remove_tracking(body["xml"]) == PLAIN
    async with api.maker() as db:
        record = await db.get(TrackedSurvey, "Coffee Machine Study")
        assert record is not None and record.uploads == 1 and record.signed


@pytest.mark.asyncio
async def test_upload_twice_gives_the_same_file_and_one_record(api):
    first = (await upload(api, PLAIN)).json()
    again = await upload(api, first["xml"], name="coffee_tracked.xml")
    body = again.json()
    assert body["replaced_existing_tracking"] is True and body["new_survey_record"] is False
    assert body["xml"] == first["xml"]
    assert body["filename"] == "coffee_tracked.xml"
    async with api.maker() as db:
        assert (await db.get(TrackedSurvey, "Coffee Machine Study")).uploads == 2


@pytest.mark.asyncio
async def test_upload_with_bot_termination_and_no_privacy_notice(api):
    response = await upload(
        api, LOOPS, name="espresso.xml", terminate=True, after_page=2,
        signals="automation,honeypot", privacy_notice=False,
    )
    body = response.json()
    assert response.status_code == 200, body
    assert body["early_check"]["page"] == 2
    assert body["survey"]["loops"] == 1 and body["survey"]["blocks"] == 2
    assert "QOS_privacy" not in body["xml"] and "QOS_bot_term" in body["xml"]
    assert body["options"]["signals"] == ["automation", "honeypot"]


@pytest.mark.asyncio
async def test_xml_format_downloads_the_file(api):
    response = await api.post(
        "/tracking/decipher?format=xml", files={"file": ("coffee.xml", PLAIN.encode(), "application/xml")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert 'filename="coffee_tracked.xml"' in response.headers["content-disposition"]
    assert 'label="QOS_SESSION"' in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body, name, status, message",
    [
        ("<notes><note>hi</note></notes>", "notes.xml", 422, "not a Decipher survey XML"),
        ("<survey><radio></survey>", "broken.xml", 422, "not well-formed"),
        (PLAIN, "coffee.docx", 400, ".xml"),
    ],
)
async def test_upload_refuses_anything_that_is_not_survey_xml(api, body, name, status, message):
    response = await upload(api, body, name=name)
    assert response.status_code == status
    assert message in response.json()["detail"]
    async with api.maker() as db:
        assert (await db.get(TrackedSurvey, "Coffee Machine Study")) is None


@pytest.mark.asyncio
async def test_unknown_signal_is_refused(api):
    response = await upload(api, PLAIN, terminate=True, signals="mind_reading")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_tracker_token_opens_a_session_under_the_uploaded_survey(api):
    body = (await upload(api, PLAIN, survey_id="Coffee Wave 2")).json()
    token = re.search(r'var TOKEN = "([0-9a-f]+)";', body["xml"]).group(1)
    created = await api.post(
        f"/detection/sessions?survey_id=Coffee Wave 2&platform_id=decipher&respondent_id=R-1&token={token}"
    )
    assert created.status_code == 200, created.text
    # Once protected, a session without the token is refused.
    refused = await api.post("/detection/sessions?survey_id=Coffee Wave 2&platform_id=decipher&respondent_id=R-2")
    assert refused.status_code == 403
    survey = await api.get("/surveys/Coffee Wave 2")
    assert survey.status_code == 200, survey.text
    again = (await upload(api, PLAIN, survey_id="Coffee Wave 2")).json()
    assert again["existing_sessions"] == 1


@pytest.mark.asyncio
async def test_options_endpoint_lists_signals_and_default_notice(api):
    body = (await api.get("/tracking/decipher/options")).json()
    assert {item["code"] for item in body["signals"]} >= {"automation", "honeypot"}
    assert body["signed"] is True and body["default_after_page"] == 2
