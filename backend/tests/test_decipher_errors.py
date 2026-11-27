"""
Decipher's refusal messages explained, and Fix with AI acting on them.

The messages are the real ones Decipher sent for files in this project
(style compat limits, a missing .dat file) plus the other shapes it uses.
"""

import pytest

from app.services.decipher_ai_fix import fix_with_ai
from app.services.decipher_errors import explain, explain_one, lowest_style_compat
from tests.test_decipher_xml_check import BODY, GOOD_HEAD, FakeClient
from tests.test_tracking_upload_endpoint import api  # noqa: F401 - fixture

STYLE = "survey: while using style 'lib/steam/atm1d/v9': Style requires AT MOST compat level 149, but this survey is 155"
STYLE_2 = "survey: while using style 'lib/steam/ranksort/v7': Style requires AT MOST compat level 154, but this survey is 155"
MISSING_FILE = "Exec (page 58): File '15955_Data_IP_AG.dat' does not exist"
MISSING_LABEL = "error: No object with label 'term'"


def test_style_limit_is_explained_with_the_compat_to_use():
    item = explain_one(STYLE)
    assert item.kind == "style_compat" and item.ai_can_fix
    assert '"atm1d/v9"' in item.explanation and "compat 149" in item.explanation
    assert "149" in item.fix
    assert lowest_style_compat([STYLE_2, STYLE]) == 149


def test_missing_file_needs_the_users_instruction():
    item = explain_one(MISSING_FILE)
    assert item.kind == "missing_file" and item.page == 58
    assert not item.ai_can_fix and item.needs_instruction
    assert "15955_Data_IP_AG.dat" in item.explanation


def test_missing_label_and_other_messages():
    assert explain_one(MISSING_LABEL).kind == "missing_label"
    assert "term" in explain_one(MISSING_LABEL).explanation
    assert explain_one("Exec (page 3): NameError: name 'x' is not defined").kind == "script"
    other = explain_one("Something new Decipher says")
    assert other.kind == "other" and other.ai_can_fix
    assert [e["message"] for e in explain([STYLE, STYLE, "", MISSING_FILE])] == [STYLE, MISSING_FILE]


@pytest.mark.asyncio
async def test_style_errors_from_decipher_set_compat_in_code_without_the_ai():
    xml = GOOD_HEAD + BODY.replace('<radio label="Q1">', '<radio label="Q1" uses="mystyle.3">') + "</survey>"
    client = FakeClient()
    result = await fix_with_ai(xml.encode("utf-8"), client=client, decipher_errors=[STYLE.replace("atm1d/v9", "mystyle/v3")])
    assert client.prompts == []
    assert 'compat="149"' in result.xml and result.report.ok
    assert result.changes == ["Set compat to 149 on the <survey> tag (Decipher said a question style only works up to this compat)."]


@pytest.mark.asyncio
async def test_other_decipher_errors_go_to_the_ai_with_the_right_part_of_the_file(monkeypatch):
    from app.services import decipher_ai_fix

    monkeypatch.setattr(decipher_ai_fix, "FULL_FILE_CHARS", 300)
    filler = "".join(f'  <html label="h{n}">Line {n}</html>\n' for n in range(300))
    xml = GOOD_HEAD + filler + '  <exec>go = "term"</exec>\n' + BODY + "</survey>"
    client = FakeClient({
        "edits": [{"find": '  <exec>go = "term"</exec>\n', "replace": "", "reason": "label does not exist"}],
        "changes": ["Removed the reference to the missing label term."],
    })
    result = await fix_with_ai(xml.encode("utf-8"), client=client, decipher_errors=[MISSING_LABEL])
    prompt = client.prompts[0]
    assert "Decipher refused the upload: error: No object with label 'term'" in prompt
    assert 'go = "term"' in prompt and "h150" not in prompt  # the line Decipher points at, not the whole file
    assert result.applied == 1 and "term" not in result.xml.split("</exec>")[0][-40:]


@pytest.mark.asyncio
async def test_upload_refused_before_sending_is_explained(api):  # noqa: F811
    from app.services.decipher_tracking import add_tracking

    tracked = add_tracking('<survey name="S">\n' + BODY + "</survey>", "Coffee", "https://bot.example/api/v1")
    from app.config import settings

    settings.DECIPHER_API_KEY, saved = "k" * 64, settings.DECIPHER_API_KEY
    try:
        response = await api.post("/tracking/decipher/upload", json={"xml": tracked, "survey_id": "Coffee"})
    finally:
        settings.DECIPHER_API_KEY = saved
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["file_problem"] is True
    assert detail["explained"] and detail["explained"][0]["message"] == detail["errors"][0]


def test_missing_quota_file_is_explained():
    item = explain_one("survey: No selfserve/563/261185/temp-api/quota.xls file")
    assert item.kind == "missing_quota" and item.needs_instruction and not item.ai_can_fix
    assert "no quota file" in item.explanation


def test_cardsort_and_atmtable_limits_are_known_before_upload():
    from app.services.decipher_xml_check import check_survey_xml

    xml = GOOD_HEAD + BODY.replace('<radio label="Q1">', '<radio label="Q1" uses="cardsort.8">') + "</survey>"
    report = check_survey_xml(xml.encode("utf-8"))
    assert report.recommended_compat == 154
    assert [i.code for i in report.issues] == ["style_compat"]


@pytest.mark.asyncio
async def test_ai_cannot_raise_compat_without_being_asked():
    xml = '<survey alt="S" compat="154" delphi="1" name="Survey">\n' + BODY + "</survey>"
    client = FakeClient({
        "edits": [{"find": 'compat="154"', "replace": 'compat="155"', "reason": "recommended"},
                  {"find": "<title>Why?</title>", "replace": "<title>Why do you drink it?</title>", "reason": "asked"}],
        "changes": ["Updated compat to 155."],
    })
    result = await fix_with_ai(xml.encode("utf-8"), "Make Q2's title clearer", client=client)
    assert 'compat="154"' in result.xml and "Why do you drink it?" in result.xml
    assert "kept at 154" in result.skipped[-1]


@pytest.mark.asyncio
async def test_windows_line_breaks_and_one_bad_edit_do_not_block_the_rest():
    xml = (GOOD_HEAD + '  <exec when="init">\nData = File("zip.dat", "Zip")\n</exec>\n' + BODY + "</survey>").replace("\n", "\r\n")
    client = FakeClient({"edits": [
        # Multi-line edit written with plain line breaks, as models do.
        {"find": '  <exec when="init">\nData = File("zip.dat", "Zip")\n</exec>\n', "replace": "", "reason": "remove data file"},
        # This one would leave a closing tag without its opening tag.
        {"find": '  <radio label="Q1">', "replace": "", "reason": "bad"},
    ]})
    result = await fix_with_ai(xml.encode("utf-8"), "Remove the code that reads .dat files", client=client)
    assert "zip.dat" not in result.xml and '<radio label="Q1">' in result.xml
    assert result.applied == 1 and "would have broken the XML" in result.skipped[0]
    assert result.report.ok


def test_bare_exec_error_points_at_data_files_the_survey_still_reads():
    xml = GOOD_HEAD + '  <exec when="init">\nCBC = setupDCMFile("15955_DCM_v4.dat")\n</exec>\n' + BODY + "</survey>"
    [item] = explain(["Exec (page 79): exec"], xml)
    assert item["kind"] == "script" and item["needs_instruction"]
    assert "15955_DCM_v4.dat" in item["explanation"]
    # Without data files the same message stays a plain script error.
    assert not explain(["Exec (page 79): exec"], GOOD_HEAD + BODY + "</survey>")[0]["needs_instruction"]


def test_custom_dat_readers_are_found_before_upload():
    from app.services.decipher_xml_check import check_survey_xml

    xml = GOOD_HEAD + '  <exec when="init">\nd = setupDCMFile("card1left_v3.dat")\n</exec>\n' + BODY + "</survey>"
    issue = next(i for i in check_survey_xml(xml.encode("utf-8")).issues if i.code == "data_files")
    assert issue.items == ["card1left_v3.dat"]


@pytest.mark.asyncio
async def test_removing_the_start_of_an_exec_block_removes_the_whole_block():
    xml = GOOD_HEAD + '  <exec when="init">\nCBC = setupDCMFile("x.dat")\nmore = 1\n</exec>\n' + BODY + "</survey>"
    client = FakeClient({"edits": [
        {"find": '<exec when="init">\nCBC = setupDCMFile("x.dat")', "replace": "<!-- removed -->", "reason": "remove .dat code"},
    ]})
    result = await fix_with_ai(xml.encode("utf-8"), "Remove the code that reads .dat files", client=client)
    assert result.applied == 1 and result.skipped == []
    assert "x.dat" not in result.xml and "more = 1" not in result.xml and "<!-- removed -->" in result.xml
    assert result.report.ok


EMPTY_ELSE = '  <exec>\nif CodeIP != None:\n\t# removed: db = Database("a.dat")\nelse:\n\tpass\nx = 1\n</exec>\n'


def test_empty_python_blocks_are_found_before_upload_and_filled_in_code():
    from app.services.decipher_xml_check import check_survey_xml, fill_empty_python_blocks

    xml = GOOD_HEAD + EMPTY_ELSE + BODY + "</survey>"
    report = check_survey_xml(xml.encode("utf-8"))
    issue = next(i for i in report.issues if i.code == "empty_code_block")
    assert issue.severity == "error" and "if CodeIP != None:" in issue.items[0]
    filled, count = fill_empty_python_blocks(xml)
    assert count == 1 and "if CodeIP != None:\n\tpass\n" in filled and check_survey_xml(filled.encode()).ok
    # Blocks with code under them, comments-only lines inside other code, and one-line ifs are left alone.
    fine = GOOD_HEAD + '  <exec>\nif a:\n    b = 1\nelif c: d = 2\nfor i in x:\n    # note\n    go(i)\n</exec>\n' + BODY + "</survey>"
    assert fill_empty_python_blocks(fine)[1] == 0


@pytest.mark.asyncio
async def test_fix_with_ai_puts_pass_under_blocks_left_empty():
    xml = GOOD_HEAD + EMPTY_ELSE + BODY + "</survey>"
    client = FakeClient()
    result = await fix_with_ai(xml.encode("utf-8"), client=client)
    assert client.prompts == [] and "if CodeIP != None:\n\tpass\n" in result.xml and result.report.ok
    assert "Added pass under 1" in result.changes[0]


def test_compile_and_unknown_attribute_messages_are_explained():
    compile_error = explain_one("""survey: Could not compile code: ("Line 59: IndentationError: expected an indented block at statement: 'else:'",)""")
    assert compile_error.kind == "script" and "nothing under it" in compile_error.explanation
    assert "line 59 of that code block" in compile_error.explanation and "pass" in compile_error.fix
    attribute = explain_one("survey: Extra unrecognized argument given: unicode")
    assert attribute.kind == "attribute" and 'Remove unicode="..."' in attribute.fix
    # A compile error is about the code, not missing data files, even if the survey reads some.
    xml = GOOD_HEAD + '  <exec>\nd = Database("x.dat")\n</exec>\n' + BODY + "</survey>"
    assert not explain(["survey: Could not compile code: ('Line 3: SyntaxError',)"], xml)[0]["needs_instruction"]


def test_newer_style_limits_are_known():
    from app.services.decipher_xml_check import check_survey_xml

    xml = GOOD_HEAD + BODY.replace('<radio label="Q1">', '<radio label="Q1" uses="atm1d.10">') + "</survey>"
    assert check_survey_xml(xml.encode("utf-8")).recommended_compat == 151
