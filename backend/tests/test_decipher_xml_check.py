"""
The upload check that explains problems in a survey XML, and Fix with AI.

Fix with AI is tested with a stand-in client that returns a fixed reply, so the
edit rules (exact single matches, prepend/append, re-check, never keeping an
unreadable result) are tested without calling a paid model.
"""

import json
import re
from types import SimpleNamespace

import pytest

from app.services import decipher_ai_fix
from app.services.decipher_ai_fix import FixUnavailable, fix_with_ai
from app.services.decipher_xml_check import check_survey_xml
from tests.test_decipher_tracking import PLAIN
from tests.test_tracking_upload_endpoint import api  # noqa: F401 - fixture

GOOD_HEAD = '<survey alt="Coffee" compat="155" delphi="1" name="Survey">\n'
BODY = (
    '  <radio label="Q1">\n    <title>How often?</title>\n    <row label="r1">Daily</row>\n'
    '    <row label="r2">Weekly</row>\n  </radio>\n  <suspend/>\n'
    '  <text label="Q2" optional="1">\n    <title>Why?</title>\n  </text>\n'
)


def codes(xml: str):
    report = check_survey_xml(xml.encode("utf-8"))
    return report, [(issue.severity, issue.code) for issue in report.issues]


def test_good_survey_passes():
    report, found = codes(PLAIN)
    assert report.ok and found == []
    assert report.questions >= 1


def test_fragment_is_explained_and_fixable():
    report, found = codes(BODY)
    assert ("error", "fragment") in found
    issue = report.issues[0]
    assert "no <survey> tag" in issue.title and issue.ai_can_fix
    assert report.questions == 2  # still read, so the other checks run


def test_broken_xml_gives_line_and_hint():
    report, found = codes(GOOD_HEAD + BODY.replace("Daily", "Tea & coffee") + "</survey>")
    assert found == [("error", "not_well_formed")]
    issue = report.issues[0]
    assert issue.line == 4
    assert "&amp;" in issue.detail and "Tea & coffee" in issue.detail


def test_cut_off_file():
    _, found = codes(GOOD_HEAD + BODY)
    assert found == [("error", "not_well_formed")]


def test_compat_rules():
    _, found = codes('<survey name="S">\n' + BODY + "</survey>")
    assert ("error", "compat_missing") in found
    _, found = codes('<survey compat="120" name="S">\n' + BODY + "</survey>")
    assert ("error", "compat_too_low") in found
    _, found = codes('<survey compat="155" name="S">\n' + BODY + "</survey>")
    assert ("error", "delphi_missing") in found


def test_old_style_limits_compat_and_recommendation():
    xml = GOOD_HEAD + BODY.replace('<radio label="Q1">', '<radio label="Q1" uses="atm1d.9">') + "</survey>"
    report, found = codes(xml)
    assert ("error", "style_compat") in found
    assert report.recommended_compat == 149
    assert next(i for i in report.issues if i.code == "style_compat").line == 2


def test_duplicate_and_reserved_labels():
    xml = GOOD_HEAD + BODY + BODY.replace("Q2", "QOS_FLAG") + "</survey>"
    report, found = codes(xml)
    assert ("error", "duplicate_labels") in found
    assert ("error", "qos_labels") in found
    dup = next(i for i in report.issues if i.code == "duplicate_labels")
    assert dup.items[0].startswith("Q1 (lines 2, 11")


def test_tracked_file_is_not_reported_for_its_own_qos_questions():
    from app.services.decipher_tracking import add_tracking

    tracked = add_tracking(PLAIN, "Coffee", "https://bot.example/api/v1")
    report, found = codes(tracked)
    assert report.ok and report.already_tracked and found == []


def test_quota_sheets_and_data_files_are_warnings_ai_leaves_alone():
    extra = (
        '  <quota label="Q_age" overquota="noqual" sheet="Age_Quota"/>\n'
        '  <exec when="init">db = Database("12345_ids.dat")</exec>\n'
    )
    report, found = codes(GOOD_HEAD + extra + BODY + "</survey>")
    assert report.ok
    assert ("warning", "quota_sheets") in found and ("warning", "data_files") in found
    quota = next(i for i in report.issues if i.code == "quota_sheets")
    assert quota.items == ["Age_Quota"] and not quota.ai_can_fix
    files = next(i for i in report.issues if i.code == "data_files")
    assert files.items == ["12345_ids.dat"]


def test_not_utf8_and_doctype():
    report = check_survey_xml("<survey>caf\xe9</survey>".encode("latin-1"))
    assert report.issues[0].code == "not_utf8" and not report.issues[0].ai_can_fix
    _, found = codes("<!DOCTYPE x>\n" + GOOD_HEAD + BODY + "</survey>")
    assert found == [("error", "doctype")]


# ---------- Fix with AI ----------


class FakeClient:
    """Stands in for AsyncOpenAI: returns the queued JSON replies in order and keeps the prompts."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        self.prompts.append(kwargs["messages"][1]["content"])
        reply = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(reply)))])


@pytest.mark.asyncio
async def test_fix_wraps_a_fragment_in_code_and_ai_applies_the_title():
    client = FakeClient({
        "edits": [{"find": '<survey alt="15955" ', "replace": '<survey alt="Coffee study" ', "reason": "title"}],
        # A second wrapper from the model is refused: the file is already one survey.
        "prepend": "<survey>", "append": "</survey>",
        "changes": ["Set the survey title to Coffee study."], "assumptions": [],
    })
    result = await fix_with_ai(BODY.encode("utf-8"), "The survey title is Coffee study", client=client, filename="15955.txt")
    assert result.report.ok, [i.code for i in result.report.issues]
    assert result.xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<survey alt="Coffee study"')
    assert result.xml.count("<survey") == 1 and result.xml.rstrip().endswith("</survey>")
    assert BODY.rstrip() in result.xml  # the questions are untouched
    assert result.changes[0].startswith("Wrapped the questions in a <survey> tag")
    assert "standard ones were used" in result.assumptions[0]
    assert "second <survey>" in result.skipped[0]
    assert "The survey title is Coffee study" in client.prompts[0]


@pytest.mark.asyncio
async def test_fragment_without_instructions_needs_no_ai_and_respects_style_limits():
    body = BODY.replace('<radio label="Q1">', '<radio label="Q1" uses="atm1d.9">')
    client = FakeClient()
    result = await fix_with_ai(body.encode("utf-8"), client=client, filename="15880.txt")
    assert client.prompts == [] and result.report.ok
    assert 'alt="15880"' in result.xml and 'compat="149"' in result.xml and "delphi" not in result.xml


@pytest.mark.asyncio
async def test_fix_applies_only_exact_single_matches_and_retries():
    xml = '<survey compat="155" name="S">\n' + BODY + "</survey>"
    client = FakeClient(
        # Round 1: one edit matches two places, one does not exist, one is right but leaves delphi wrong.
        {"edits": [{"find": "<row label=", "replace": "x", "reason": "ambiguous"},
                   {"find": "not in the file", "replace": "y", "reason": "missing"},
                   {"find": "<title>Why?</title>", "replace": "<title>Why do you drink it?</title>", "reason": "asked"}]},
        # Round 2: told what is left, it adds delphi.
        {"edits": [{"find": '<survey compat="155" name="S">', "replace": '<survey compat="155" delphi="1" name="S">', "reason": "delphi"}]},
    )
    result = await fix_with_ai(xml.encode("utf-8"), client=client)
    assert len(result.skipped) == 2
    assert "matched 2 places" in result.skipped[0] and "was not found" in result.skipped[1]
    assert result.applied == 2 and result.rounds == 2 and result.report.ok
    assert "still there" in client.prompts[1]


def test_duplicate_labels_keep_the_first_and_rename_later_ones():
    from app.services.decipher_xml_check import rename_duplicate_labels

    xml = GOOD_HEAD + BODY + BODY.replace('label="Q2"', 'label="Q2_2"') + BODY + "</survey>"
    fixed, changes, checks = rename_duplicate_labels(xml)
    labels = re.findall(r'<(?:radio|text) label="([^"]+)"', fixed)
    assert labels == ["Q1", "Q2", "Q1_2", "Q2_2", "Q1_3", "Q2_3"]
    assert changes[0].startswith("Renamed the later Q1 (line 11) to Q1_2")
    assert "still point to the first Q1" in checks[0]
    assert check_survey_xml(fixed.encode("utf-8")).ok


@pytest.mark.asyncio
async def test_fix_renames_duplicates_in_code_not_by_the_ai():
    xml = GOOD_HEAD + BODY + BODY + "</survey>"
    client = FakeClient()
    result = await fix_with_ai(xml.encode("utf-8"), client=client)
    assert client.prompts == [] and result.report.ok
    assert result.xml.count('label="Q1"') == 1 and 'label="Q1_2"' in result.xml


@pytest.mark.asyncio
async def test_fix_never_keeps_an_unreadable_result():
    xml = '<survey compat="155" name="S">\n' + BODY + "</survey>"
    client = FakeClient({"edits": [{"find": "</survey>", "replace": "</surv", "reason": "bad"}]})
    result = await fix_with_ai(xml.encode("utf-8"), client=client)
    assert result.xml == xml and result.applied == 0
    assert "would have broken the XML" in result.skipped[-1]


@pytest.mark.asyncio
async def test_fix_without_problems_or_instructions_does_not_call_the_ai():
    client = FakeClient()
    result = await fix_with_ai(PLAIN.encode("utf-8"), client=client)
    assert result.rounds == 0 and client.prompts == [] and result.report.ok


@pytest.mark.asyncio
async def test_fix_sends_excerpts_of_large_files(monkeypatch):
    monkeypatch.setattr(decipher_ai_fix, "FULL_FILE_CHARS", 500)
    filler = "".join(f'  <html label="h{n}">Line {n}</html>\n' for n in range(400))
    xml = BODY + filler
    client = FakeClient({"edits": []})
    result = await fix_with_ai(xml.encode("utf-8"), "Keep everything else as it is", client=client)
    assert result.report.ok
    assert "----- lines 1-" in client.prompts[0] and "h200" not in client.prompts[0]


@pytest.mark.asyncio
async def test_fix_needs_an_openai_key(monkeypatch):
    from app.services.openai_service import openai_service

    monkeypatch.setattr(openai_service, "reload", lambda: None)
    monkeypatch.setattr(openai_service, "client", None)
    with pytest.raises(FixUnavailable):
        await fix_with_ai(BODY.encode("utf-8"))


# ---------- endpoints ----------


@pytest.mark.asyncio
async def test_check_endpoint_reports_issues(api):  # noqa: F811
    response = await api.post("/tracking/decipher/check", files={"file": ("15955.txt", BODY.encode("utf-8"), "text/plain")})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is False and body["errors"] == 1 and body["ai_fixable"] is True
    assert body["issues"][0]["code"] == "fragment" and body["filename"] == "15955.txt"


@pytest.mark.asyncio
async def test_fix_endpoint_returns_fixed_xml(api, monkeypatch):  # noqa: F811
    fake = FakeClient({"edits": [{"find": '<survey alt="15955" ', "replace": '<survey alt="Coffee" ', "reason": "title"}],
                       "changes": ["Set the title."]})
    real = decipher_ai_fix.fix_with_ai

    async def with_fake(data, instructions="", filename="", decipher_errors=None):
        return await real(data, instructions, client=fake, filename=filename, decipher_errors=decipher_errors)

    monkeypatch.setattr("app.controllers.survey_tracking_controller.fix_with_ai", with_fake)
    response = await api.post(
        "/tracking/decipher/fix",
        files={"file": ("15955.txt", BODY.encode("utf-8"), "text/plain")},
        data={"instructions": "Title is Coffee"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["filename"] == "15955_fixed.xml" and body["changed"] is True
    assert body["report"]["ok"] is True and body["changes"][-1] == "Set the title."
    assert '<survey alt="Coffee"' in body["xml"]


@pytest.mark.asyncio
async def test_fix_endpoint_without_key_says_so(api, monkeypatch):  # noqa: F811
    async def unavailable(data, instructions="", filename="", decipher_errors=None):
        raise FixUnavailable("Fix with AI needs an OpenAI API key. Add it on the Settings page.")

    monkeypatch.setattr("app.controllers.survey_tracking_controller.fix_with_ai", unavailable)
    response = await api.post("/tracking/decipher/fix", files={"file": ("a.xml", BODY.encode("utf-8"), "text/xml")})
    assert response.status_code == 503 and "OpenAI API key" in response.json()["detail"]
