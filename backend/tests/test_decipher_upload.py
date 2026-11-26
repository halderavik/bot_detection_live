"""
Uploading a tracked survey XML to Decipher.

Decipher is replaced by an httpx mock transport, so no request leaves the test.
The survey is a made-up coffee machine study.
"""

import json

import httpx
import pytest

pytest.importorskip("aiosqlite")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.controllers import survey_tracking_controller  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.models import TrackedSurvey  # noqa: E402
from app.services.decipher_upload import (  # noqa: E402
    DecipherNotConfigured,
    DecipherUploader,
    DecipherUploadError,
    clean_path,
    public_url,
)
from app.utils import rate_limit  # noqa: E402
from main import create_app  # noqa: E402

from tests.test_decipher_tracking import PLAIN  # noqa: E402

KEY = "test-decipher-key-123456"
BASE = "https://selfserve.decipherinc.com/api/v1"


class FakeDecipher:
    """Records calls and answers like the Decipher REST API."""

    def __init__(self, reject_xml=None, unreachable=False, layouts=None, layouts_put_status=200):
        self.calls = []
        self.reject_xml = reject_xml
        self.unreachable = unreachable
        self.created = 0
        self.layouts = layouts  # saved data layouts (layouts.json); None means the survey has none
        self.layouts_put_status = layouts_put_status

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if self.unreachable:
            raise httpx.ConnectError("no route", request=request)
        if request.headers.get("x-apikey") != KEY:
            return httpx.Response(401, json={"$error": "bad key"})
        if request.method == "POST" and request.url.path.endswith("/rh/companies/self/surveys"):
            self.created += 1
            return httpx.Response(200, json={"path": f"selfserve/53b/24{self.created:04d}"})
        if request.method == "PUT" and request.url.path.endswith("/files/survey.xml"):
            if self.reject_xml:
                return httpx.Response(400, json={"extra": [{"type": "parse", "message": self.reject_xml}]})
            return httpx.Response(200, json={})
        if request.url.path.endswith("/files/layouts.json"):
            if request.method == "GET" and self.layouts is not None:
                return httpx.Response(200, content=json.dumps(self.layouts).encode())
            if request.method == "PUT":
                if self.layouts_put_status == 200:
                    body = request.content.decode("utf-8")
                    self.layouts = json.loads(body[body.index("{"): body.rindex("}") + 1])
                return httpx.Response(self.layouts_put_status, json={"filename": "layouts.json"})
        return httpx.Response(404, json={"$error": "not found"})

    def methods(self):
        return [(request.method, request.url.path) for request in self.calls]


def uploader(fake):
    return DecipherUploader(KEY, BASE, "self", transport=httpx.MockTransport(fake))


# --- the client ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_new_survey_is_created_then_its_xml_uploaded():
    fake = FakeDecipher()
    result = await uploader(fake).upload("<survey/>", "Coffee Machine Study")
    assert result.created and result.survey_path == "selfserve/53b/240001"
    assert result.survey_url == "https://selfserve.decipherinc.com/survey/selfserve/53b/240001"
    assert fake.methods() == [
        ("POST", "/api/v1/rh/companies/self/surveys"),
        ("PUT", "/api/v1/surveys/selfserve/53b/240001/files/survey.xml"),
    ]
    assert json.loads(fake.calls[0].content) == {"name": "Coffee Machine Study", "ptype": "beacon", "lang": "english"}
    body = fake.calls[1].content.decode("utf-8", "replace")
    # Validated before saving, and a live survey is never overwritten.
    assert 'name="validate"\r\n\r\ntrue' in body and 'name="overwriteLive"\r\n\r\nfalse' in body
    assert "<survey/>" in body


@pytest.mark.asyncio
async def test_existing_path_is_updated_without_creating_a_survey():
    fake = FakeDecipher()
    result = await uploader(fake).upload("<survey/>", "Coffee", "selfserve/53b/240777")
    assert not result.created and result.survey_path == "selfserve/53b/240777"
    assert [method for method, _ in fake.methods()] == ["PUT"]


@pytest.mark.asyncio
async def test_rejection_reports_decipher_errors_without_the_key():
    fake = FakeDecipher(reject_xml=f"Unknown attribute on line 3 ({KEY})")
    with pytest.raises(DecipherUploadError) as caught:
        await uploader(fake).upload("<survey/>", "Coffee")
    error = caught.value
    assert error.status == 400 and error.survey_path == "selfserve/53b/240001"
    assert "Unknown attribute on line 3" in error.message
    assert KEY not in error.message and KEY not in " ".join(error.errors)


@pytest.mark.asyncio
async def test_unreachable_decipher_gives_a_plain_message():
    with pytest.raises(DecipherUploadError, match="could not be reached"):
        await uploader(FakeDecipher(unreachable=True)).upload("<survey/>", "Coffee")


def test_missing_or_placeholder_key_is_not_configured():
    for key in (None, "", "   ", "your-decipher-key"):
        with pytest.raises(DecipherNotConfigured):
            DecipherUploader(key)
    with pytest.raises(DecipherNotConfigured, match="https"):
        DecipherUploader(KEY, "http://selfserve.decipherinc.com/api/v1")


@pytest.mark.parametrize(
    "raw, path",
    [
        ("selfserve/53b/240101", "selfserve/53b/240101"),
        ("/selfserve/53b/240101/", "selfserve/53b/240101"),
        ("https://selfserve.decipherinc.com/survey/selfserve/53b/240101", "selfserve/53b/240101"),
        ("https://selfserve.decipherinc.com/rep/selfserve/53b/240101:dashboard", "selfserve/53b/240101"),
        ("selfserve/../../admin", None),
        ("https://example.com/nothing", None),
        ("selfserve/53b/240101?x=1", None),
        ("", None),
    ],
)
def test_survey_paths_and_links_are_read_safely(raw, path):
    assert clean_path(raw) == path


def test_public_url_is_the_survey_page_not_the_api():
    assert public_url(BASE, "selfserve/1/2") == "https://selfserve.decipherinc.com/survey/selfserve/1/2"


# --- the endpoint ---------------------------------------------------------------------


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'decipher.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def db():
        async with maker() as session:
            yield session

    fake = FakeDecipher()

    class MockedUploader(DecipherUploader):
        def __init__(self, key, base=None, company_id=None):
            super().__init__(key, base, company_id, transport=httpx.MockTransport(fake))

    monkeypatch.setattr(survey_tracking_controller, "DecipherUploader", MockedUploader)
    monkeypatch.setattr(rate_limit, "LIMITS", {"new_session": (100000, 60), "write": (100000, 60)})
    monkeypatch.setattr(settings, "TRACKING_TOKEN_SECRET", "coffee-secret")
    monkeypatch.setattr(settings, "TRACKER_API_BASE", "https://bot.example/api/v1")
    monkeypatch.setattr(settings, "DECIPHER_API_KEY", KEY)
    monkeypatch.setattr(settings, "DECIPHER_API_BASE", BASE)
    app = create_app()
    app.dependency_overrides[get_db] = db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as client:
        client.maker = maker
        client.fake = fake
        yield client
    await engine.dispose()


async def tracked(api, body=PLAIN):
    response = await api.post("/tracking/decipher", files={"file": ("coffee.xml", body.encode(), "application/xml")})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_first_upload_creates_a_survey_and_later_ones_update_it(api):
    survey = await tracked(api)
    assert survey["decipher_upload"] == {"configured": True, "last_path": None}
    first = await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"]})
    assert first.status_code == 200, first.text
    assert first.json()["created"] is True and first.json()["survey_path"] == "selfserve/53b/240001"
    async with api.maker() as db:
        assert (await db.get(TrackedSurvey, "Coffee Machine Study")).decipher_path == "selfserve/53b/240001"

    again = await tracked(api, survey["xml"])
    assert again["decipher_upload"]["last_path"] == "selfserve/53b/240001"
    second = (await api.post("/tracking/decipher/upload", json={"xml": again["xml"], "survey_id": again["survey_id"]})).json()
    assert second["created"] is False and second["survey_path"] == "selfserve/53b/240001"
    assert api.fake.created == 1

    fresh = (await api.post(
        "/tracking/decipher/upload", json={"xml": again["xml"], "survey_id": again["survey_id"], "create_new": True}
    )).json()
    assert fresh["created"] is True and fresh["survey_path"] == "selfserve/53b/240002"


@pytest.mark.asyncio
async def test_upload_to_a_path_the_user_gives(api):
    survey = await tracked(api)
    response = await api.post(
        "/tracking/decipher/upload",
        json={"xml": survey["xml"], "survey_id": survey["survey_id"],
              "survey_path": "https://selfserve.decipherinc.com/survey/selfserve/53b/249999"},
    )
    assert response.json()["survey_path"] == "selfserve/53b/249999"
    assert api.fake.created == 0
    bad = await api.post(
        "/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"], "survey_path": "../etc"}
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_only_tracked_survey_xml_is_uploaded(api):
    untracked = await api.post("/tracking/decipher/upload", json={"xml": PLAIN, "survey_id": "Coffee Machine Study"})
    assert untracked.status_code == 422 and "tracking" in untracked.json()["detail"]
    notes = await api.post("/tracking/decipher/upload", json={"xml": "<notes/>", "survey_id": "x"})
    assert notes.status_code == 422
    survey = await tracked(api)
    other = await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": "Another Survey"})
    assert other.status_code == 422
    assert api.fake.calls == []


@pytest.mark.asyncio
async def test_rejected_xml_keeps_the_created_survey_for_a_retry(api):
    survey = await tracked(api)
    api.fake.reject_xml = "Tag <bogus> is not allowed here"
    rejected = await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"]})
    assert rejected.status_code == 400
    detail = rejected.json()["detail"]
    assert "not allowed here" in detail["message"] and detail["survey_path"] == "selfserve/53b/240001"
    api.fake.reject_xml = None
    retry = (await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"]})).json()
    assert retry["survey_path"] == "selfserve/53b/240001" and retry["created"] is False
    assert api.fake.created == 1


@pytest.mark.asyncio
async def test_upload_is_refused_when_no_key_is_set(api, monkeypatch):
    monkeypatch.setattr(settings, "DECIPHER_API_KEY", None)
    survey = await tracked(api)
    assert survey["decipher_upload"]["configured"] is False
    response = await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"]})
    assert response.status_code == 503 and "DECIPHER_API_KEY" in response.json()["detail"]
    assert (await api.get("/tracking/decipher/options")).json()["decipher_upload"] is False


# --- saved data layouts ---------------------------------------------------------------


def _layouts():
    return {"layouts": [
        {"id": 1, "description": "Standard", "variableData": [
            {"minStart": 0, "altlabel": "record", "shown": 1, "fwidth": 7, "label": "record"},
            {"minStart": 0, "altlabel": "uuid", "shown": 1, "fwidth": 16, "label": "uuid"},
        ]},
        {"id": 2, "description": "Coffee tables", "variableData": [
            {"minStart": 0, "altlabel": "uuid", "shown": 1, "fwidth": 16, "label": "uuid"},
            {"minStart": 0, "altlabel": "QOS_SESSION", "shown": 1, "fwidth": 40, "label": "QOS_SESSION"},
        ]},
    ]}


def _tracked():
    from app.services.decipher_tracking import add_tracking

    return add_tracking(PLAIN, "Coffee Machine Study", "https://bot.example/api/v1")


@pytest.mark.asyncio
async def test_quality_variables_are_added_to_saved_layouts():
    from app.services.decipher_tracking import FIELD_LABELS

    fake = FakeDecipher(layouts=_layouts())
    result = await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    assert result.layouts_updated == 2 and not result.warnings
    assert "2 saved data layouts" in result.message
    assert fake.methods()[-2:] == [
        ("GET", "/api/v1/surveys/selfserve/53b/240777/files/layouts.json"),
        ("PUT", "/api/v1/surveys/selfserve/53b/240777/files/layouts.json"),
    ]
    for layout in fake.layouts["layouts"]:
        labels = [column["label"] for column in layout["variableData"]]
        assert all(labels.count(label) == 1 for label in FIELD_LABELS)
        assert labels[:1] in (["record"], ["uuid"])  # existing columns keep their place
    columns = {c["label"]: c for c in fake.layouts["layouts"][0]["variableData"]}
    assert columns["QOS_STATUS"]["fwidth"] == 1 and columns["QOS_RESPONDENT"]["fwidth"] == 40
    assert fake.layouts["layouts"][1]["description"] == "Coffee tables"


@pytest.mark.asyncio
async def test_layouts_that_already_have_the_variables_are_not_rewritten():
    fake = FakeDecipher(layouts=_layouts())
    await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    fake.calls.clear()
    result = await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    assert result.layouts_updated == 0 and not result.warnings
    assert [method for method, _ in fake.methods()] == ["PUT", "GET"]


@pytest.mark.asyncio
async def test_survey_without_saved_layouts_is_left_alone():
    fake = FakeDecipher()
    result = await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    assert result.layouts_updated == 0 and not result.warnings
    assert [method for method, _ in fake.methods()] == ["PUT", "GET"]


@pytest.mark.asyncio
async def test_layout_failure_is_a_warning_not_a_failed_upload():
    fake = FakeDecipher(layouts=_layouts(), layouts_put_status=500)
    result = await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    assert result.survey_path == "selfserve/53b/240777" and result.layouts_updated == 0
    assert len(result.warnings) == 1 and "saved data layouts" in result.warnings[0]
    assert KEY not in result.warnings[0]


@pytest.mark.asyncio
async def test_unreadable_layouts_file_is_a_warning():
    fake = FakeDecipher(layouts=["not", "a", "layouts", "file"])
    result = await uploader(fake).upload(_tracked(), "Coffee", "selfserve/53b/240777")
    assert result.layouts_updated == 0 and len(result.warnings) == 1


@pytest.mark.asyncio
async def test_xml_decipher_would_refuse_is_stopped_before_any_survey_is_created(api):
    old = PLAIN.replace(' compat="155" delphi="1"', "")
    survey = await tracked(api, old)
    assert any("Decipher will refuse" in w for w in survey["warnings"])
    refused = await api.post("/tracking/decipher/upload", json={"xml": survey["xml"], "survey_id": survey["survey_id"]})
    assert refused.status_code == 422
    detail = refused.json()["detail"]
    assert "nothing was sent to Decipher" in detail["message"] and detail["survey_path"] is None
    assert api.fake.calls == [] and api.fake.created == 0  # no empty survey left in Decipher


def test_script_errors_from_decipher_are_shown_in_full():
    from app.services.decipher_upload import _messages

    body = {
        "$error": "Bad content. Additional error in body.",
        "extra": {"label": "exec", "type": "Exec", "msg": "File 'USA_Zip_Code.dat' does not exist", "page": 58},
    }
    assert _messages(body) == ["Exec (page 58): File 'USA_Zip_Code.dat' does not exist"]
    assert _messages({"$error": "Bad content."}) == ["Bad content."]

