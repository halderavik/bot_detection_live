"""
Manual installation: the Decipher XML blocks and the tracker file for other sites.

The Integrations page shows these for copy and paste, so pasting them by hand must
give exactly what the automatic upload produces.
"""

import pytest

from app.services.decipher_tracking import TrackingOptions, track_survey, tracker_script
from tests.test_tracking_upload_endpoint import api, upload  # noqa: F401 - fixture
from tests.test_decipher_tracking import PLAIN

API = "https://bot.example/api/v1"


def paste_by_hand(xml: str, style: str, results: str) -> str:
    """Do what the Integrations page tells a programmer to do."""
    anchor = xml.find("</samplesources>") + len("</samplesources>")
    xml = xml[:anchor] + "\n  " + style.lstrip() + xml[anchor:]
    closing = xml.rfind("</survey>")
    return xml[:closing] + results + xml[closing:]


@pytest.mark.asyncio
async def test_pasted_decipher_blocks_equal_the_automatic_upload(api):  # noqa: F811
    response = await api.get("/tracking/decipher/snippet", params={"survey_id": "Coffee Machine Study"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["signed"] is True
    assert body["fields"][0] == "QOS_RESPONDENT"
    assert body["style"].startswith("<!-- Bot detection live tracking: survey id Coffee Machine Study -->")
    assert 'var PLATFORM_RESPONDENT = "${uuid}";' in body["style"]

    automatic = await upload(api, PLAIN, privacy_notice=False, terminate=False)
    assert automatic.status_code == 200, automatic.text
    assert paste_by_hand(PLAIN, body["style"], body["results_page"]) == automatic.json()["xml"]


@pytest.mark.asyncio
async def test_snippet_can_point_at_another_service_unsigned(api):  # noqa: F811
    other = "https://prod.example/api/v1"
    response = await api.get("/tracking/decipher/snippet", params={"survey_id": "Coffee", "api_base": other})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["api_base"] == other
    assert body["signed"] is False
    assert f'var API = "{other}";' in body["style"]
    assert 'var TOKEN = "";' in body["style"]
    plain_http = await api.get("/tracking/decipher/snippet", params={"survey_id": "Coffee", "api_base": "http://prod.example/api/v1"})
    assert plain_http.status_code == 422


@pytest.mark.asyncio
async def test_snippet_refuses_unsafe_survey_ids(api):  # noqa: F811
    response = await api.get("/tracking/decipher/snippet", params={"survey_id": "bad <id>"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_tracker_file_for_other_websites(api):  # noqa: F811
    response = await api.get("/tracking/script.js", params={"survey_id": "Coffee web", "platform": "web"})
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/javascript")
    script = response.text
    assert "<script>" not in script and "</script>" not in script
    assert 'var PLATFORM = "web";' in script
    assert 'var API = "https://bot.example/api/v1";' in script
    assert 'var PLATFORM_RESPONDENT = String(window.QOS_RESPONDENT_ID || "");' in script
    assert "__QOS_" not in script
    assert "window.QOSTracker" in script


@pytest.mark.asyncio
async def test_tracker_file_for_qualtrics_and_bad_platforms(api):  # noqa: F811
    response = await api.get("/tracking/script.js", params={"survey_id": "Coffee Q", "platform": "qualtrics"})
    assert response.status_code == 200
    assert 'var PLATFORM = "qualtrics";' in response.text
    assert "setEmbeddedData(\"QOS_SESSION\"" in response.text
    bad = await api.get("/tracking/script.js", params={"survey_id": "Coffee Q", "platform": "decipher"})
    assert bad.status_code == 422


def test_unknown_platform_is_refused():
    with pytest.raises(ValueError):
        tracker_script("Coffee", API, "", None, "surveymonkey")


def test_automatic_tracking_is_unchanged_by_the_refactor():
    result = track_survey(PLAIN.encode("utf-8"), API, lambda sid: "", options=TrackingOptions())
    assert 'var PLATFORM = "decipher";' in result.xml
    assert result.xml.count('class="qos-bot-field"') == 21
