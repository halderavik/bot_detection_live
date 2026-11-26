"""Settings page API: admin token, encrypted secrets, live apply, and going back to the environment."""

import pytest

pytest.importorskip("aiosqlite")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.models import AppSetting  # noqa: E402
from app.services import runtime_settings  # noqa: E402
from app.services.bot_detection_engine import BotDetectionEngine  # noqa: E402
from main import create_app  # noqa: E402

KEYS = [spec.key for spec in runtime_settings.SPECS]


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    before = {key: getattr(settings, key) for key in KEYS}
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'settings.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def db():
        async with maker() as session:
            yield session

    monkeypatch.setattr(settings, "ADMIN_TOKEN", "admin-secret")
    monkeypatch.setitem(runtime_settings._ENV, "DECIPHER_API_KEY", None)
    monkeypatch.setitem(runtime_settings._ENV, "DETECTION_THRESHOLD", 0.7)
    app = create_app()
    app.dependency_overrides[get_db] = db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        client.maker = maker
        yield client
    await engine.dispose()
    for key, value in before.items():
        setattr(settings, key, value)
    runtime_settings._ACTIVE.clear()


ADMIN = {"X-Admin-Token": "admin-secret"}


@pytest.mark.asyncio
async def test_reading_never_returns_secret_values(api):
    settings.DECIPHER_API_KEY = None
    body = (await api.get("/settings")).json()
    assert body["editable"] is True
    items = {item["key"]: item for item in body["settings"]}
    assert set(items) == set(KEYS)
    assert items["DECIPHER_API_KEY"]["value"] is None and items["DECIPHER_API_KEY"]["is_set"] is False
    assert items["DETECTION_THRESHOLD"]["value"] == 0.7 and items["DETECTION_THRESHOLD"]["source"] == "environment"


@pytest.mark.asyncio
async def test_saving_needs_the_admin_token(api, monkeypatch):
    body = {"changes": {"DECIPHER_COMPANY": "acme"}}
    assert (await api.put("/settings", json=body)).status_code == 401
    assert (await api.put("/settings", json=body, headers={"X-Admin-Token": "wrong"})).status_code == 401
    assert (await api.post("/settings/check", headers=ADMIN)).status_code == 200
    monkeypatch.setattr(settings, "ADMIN_TOKEN", None)
    refused = await api.put("/settings", json=body, headers=ADMIN)
    assert refused.status_code == 403 and "ADMIN_TOKEN" in refused.json()["detail"]
    assert (await api.get("/settings")).json()["editable"] is False


@pytest.mark.asyncio
async def test_saved_secret_is_encrypted_applied_and_can_be_cleared(api):
    key = "decipher-key-1234567890"
    saved = await api.put("/settings", json={"changes": {"DECIPHER_API_KEY": key}}, headers=ADMIN)
    assert saved.status_code == 200, saved.text
    item = next(i for i in saved.json()["settings"] if i["key"] == "DECIPHER_API_KEY")
    assert item == {**item, "is_set": True, "source": "saved", "value": None}
    assert key not in saved.text
    assert settings.DECIPHER_API_KEY == key
    async with api.maker() as db:
        row = await db.get(AppSetting, "DECIPHER_API_KEY")
        assert row.is_secret and key not in row.value
    # The upload screen sees the key at once.
    assert (await api.get("/tracking/decipher/options")).json()["decipher_upload"] is True

    cleared = await api.put("/settings", json={"changes": {"DECIPHER_API_KEY": None}}, headers=ADMIN)
    item = next(i for i in cleared.json()["settings"] if i["key"] == "DECIPHER_API_KEY")
    assert item["source"] == "not set" and settings.DECIPHER_API_KEY is None


@pytest.mark.asyncio
async def test_bot_threshold_reaches_the_engine_and_bad_values_are_refused(api):
    saved = await api.put("/settings", json={"changes": {"DETECTION_THRESHOLD": "0.85"}}, headers=ADMIN)
    assert saved.status_code == 200
    assert settings.DETECTION_THRESHOLD == 0.85 and BotDetectionEngine().BOT_THRESHOLD == 0.85
    for bad in ({"DETECTION_THRESHOLD": 1.5}, {"TRACKER_API_BASE": "http://example.com/api/v1"},
                {"DECIPHER_COMPANY": "a b"}, {"SECRET_KEY": "x"}, {"OPENAI_API_KEY": "short"}):
        response = await api.put("/settings", json={"changes": bad}, headers=ADMIN)
        assert response.status_code == 422, bad
    assert settings.DETECTION_THRESHOLD == 0.85  # a refused save changes nothing
    await api.put("/settings", json={"changes": {"DETECTION_THRESHOLD": None}}, headers=ADMIN)
    assert settings.DETECTION_THRESHOLD == 0.7


@pytest.mark.asyncio
async def test_another_instance_picks_up_saved_values(api):
    await api.put("/settings", json={"changes": {"TRACKER_API_BASE": "https://bot.example/api/v1/"}}, headers=ADMIN)
    settings.TRACKER_API_BASE = None  # as if this were a different instance
    async with api.maker() as db:
        await runtime_settings.load(db)
    assert settings.TRACKER_API_BASE == "https://bot.example/api/v1"
