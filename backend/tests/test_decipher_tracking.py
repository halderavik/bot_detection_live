"""
Adding live tracking to an uploaded Decipher survey XML.

The surveys here are made up (a coffee machine study). Covers the injection
itself and the upload endpoint: a plain survey, an already-tracked survey, a
survey with loops and conditional blocks, and files that are not survey XML.
"""

import xml.etree.ElementTree as ET

import pytest

from app.services.decipher_tracking import (
    FIELD_LABELS,
    NotASurveyError,
    TrackingOptions,
    add_tracking,
    has_tracking,
    page_breaks,
    parse_survey,
    read_survey,
    remove_tracking,
    track_survey,
    tracked_survey_id,
    tracker_script,
)
from app.utils.survey_tokens import survey_token, token_valid

API = "https://bot.example/api/v1"
SECRET = "coffee-secret"

PLAIN = """<?xml version="1.0" encoding="UTF-8"?>
<survey alt="Coffee Machine Study" name="Survey" compat="155" delphi="1" state="testing">
<samplesources default="1">
  <samplesource list="1"><title>Open</title><exit cond="terminated">Bye</exit></samplesource>
</samplesources>
<radio label="S1"><title>Do you own a coffee machine?</title><row label="r1">Yes</row><row label="r2">No</row></radio>
<suspend/>
<text label="Q1"><title>Which brand is it?</title></text>
<suspend/>
<radio label="Q2"><title>Would you buy it again?</title><row label="r1">Yes</row><row label="r2">No</row></radio>
</survey>
"""

# Shaped like a programmer's file: undeclared ss: and builder: prefixes, the survey's
# own page script, a loop, and a block only some respondents see.
LOOPS = """<?xml version="1.0" encoding="UTF-8"?>
<survey alt="Espresso Machine Tracker" name="Survey" compat="155" delphi="1" builder:wizardCompleted="1" ss:disableBackButton="1" state="testing">
<samplesources default="1">
  <samplesource list="1"><title>Open</title><exit cond="terminated">Bye</exit></samplesource>
</samplesources>
<style mode="after" name="respview.client.js" wrap="ready"><![CDATA[
if (a < b) { console.log("house script"); }
]]></style>
<radio label="S1"><title>Do you make espresso at home?</title><row label="r1">Yes</row><row label="r2">No</row></radio>
<suspend/>
<block label="BLK_Fans" cond="S1.r1">
  <radio label="S2"><title>How often?</title><row label="r1">Daily</row><row label="r2">Weekly</row></radio>
  <suspend/>
</block>
<loop label="L1" vars="machine">
  <block label="B_L1">
    <radio label="Q1_[loopvar: label]"><title>Rate [loopvar: machine]</title><row label="r1">Good</row><row label="r2">Bad</row></radio>
    <suspend/>
  </block>
  <looprow label="1"><loopvar name="machine">Model A</loopvar></looprow>
  <looprow label="2"><loopvar name="machine">Model B</loopvar></looprow>
</loop>
<text label="Q2"><title>Anything else about your machine?</title></text>
<suspend/>
<radio label="Q3"><title>Would you recommend it?</title><row label="r1">Yes</row><row label="r2">No</row></radio>
<suspend/>
</survey>
"""


def _token(survey_id):
    return survey_token(survey_id, SECRET) or ""


def _track(xml, **kwargs):
    options = kwargs.pop("options", None)
    return track_survey(xml.encode("utf-8"), API, _token, options=options, **kwargs)


# --- plain survey ---------------------------------------------------------------------


def test_plain_survey_gets_script_hidden_fields_and_privacy_notice():
    result = _track(PLAIN, options=TrackingOptions(privacy_text="We check how answers are entered."))
    xml = result.xml
    assert result.survey_id == "Coffee Machine Study"
    assert not result.replaced
    assert result.questions == 3 and result.pages == 3
    # Script right after </samplesources>, adding to (not replacing) the survey's scripts.
    style_at = xml.index('<style mode="after" name="respview.client.js"><![CDATA[')
    assert xml.index("</samplesources>") < style_at < xml.index('label="S1"')
    assert '"Coffee Machine Study"' in xml and API in xml
    assert _token("Coffee Machine Study") in xml
    for label in FIELD_LABELS:
        assert xml.count(f'label="{label}"') == 1
    # Hidden results page is last, before </survey>.
    assert xml.index('label="QOS_RISK"') > xml.index('label="Q2"')
    assert '<html label="QOS_privacy" where="survey">We check how answers are entered.</html>' in xml
    # No in-survey termination unless asked for.
    assert "QOS_EARLY" not in xml and "QOS_bot_term" not in xml
    parse_survey(xml)
    assert remove_tracking(xml) == PLAIN


def test_token_in_the_script_is_accepted_by_the_service(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "TRACKING_TOKEN_SECRET", SECRET)
    result = _track(PLAIN)
    assert token_valid("Coffee Machine Study", _token("Coffee Machine Study"))
    assert f'var TOKEN = "{_token("Coffee Machine Study")}";' in result.xml


def test_script_has_nothing_decipher_templates_would_read():
    script = tracker_script("Coffee Machine Study", API, "ab12", {"terminate": True, "signals": ["honeypot"]})
    # The only Decipher expression is the respondent's uuid.
    assert script.count("$") == 1
    assert 'var PLATFORM_RESPONDENT = "${uuid}";' in script
    assert "`" not in script and "]]>" not in script
    assert not any(line.lstrip().startswith("@") for line in script.splitlines())
    assert '"signals": ["honeypot"]' in script


def test_survey_id_given_by_the_user_wins():
    result = _track(PLAIN, survey_id="Coffee Wave 2")
    assert result.survey_id == "Coffee Wave 2"
    assert tracked_survey_id(result.xml) == "Coffee Wave 2"


def test_survey_without_samplesources_gets_script_after_the_survey_tag():
    bare = '<survey name="Survey" alt="Grinder Check"><radio label="Q1"><title>Grind?</title><row label="r1">Yes</row></radio></survey>'
    result = _track(bare)
    assert result.xml.index("<survey ") < result.xml.index("respview.client.js") < result.xml.index('label="Q1"')
    assert remove_tracking(result.xml) == bare


# --- already-tracked survey -------------------------------------------------------------


def test_already_tracked_survey_is_not_doubled_and_keeps_its_survey_id():
    first = _track(PLAIN, survey_id="Coffee Machine Study W1").xml
    second = _track(first)
    assert second.replaced
    assert second.survey_id == "Coffee Machine Study W1"
    for label in FIELD_LABELS:
        assert second.xml.count(f'label="{label}"') == 1
    assert second.xml.count("respview.client.js") == 1
    # Same options give the same file: uploading again is idempotent.
    assert second.xml == first
    assert remove_tracking(second.xml) == PLAIN


def test_retracking_with_new_options_replaces_the_old_ones():
    first = _track(LOOPS, options=TrackingOptions(terminate=True, privacy_text="Old notice")).xml
    second = _track(first, options=TrackingOptions(terminate=False, privacy_text="")).xml
    assert "QOS_EARLY" not in second and "QOS_privacy" not in second
    assert second.count('label="QOS_SESSION"') == 1
    assert remove_tracking(second) == LOOPS


def test_tracking_from_quant_os_is_recognised_and_replaced():
    quant_os = add_tracking(PLAIN, "Coffee OS Id", API).replace(
        "Bot detection live tracking", "Quant OS live quality tracking"
    )
    assert has_tracking(quant_os)
    result = _track(quant_os)
    assert result.replaced and result.survey_id == "Coffee OS Id"
    assert "Quant OS live quality tracking" not in result.xml
    assert result.xml.count('label="QOS_SESSION"') == 1


def test_add_tracking_returns_tracked_xml_unchanged():
    tracked = add_tracking(PLAIN, "Coffee Machine Study", API)
    assert add_tracking(tracked, "Coffee Machine Study", API) == tracked


# --- loops and blocks -------------------------------------------------------------------


def test_programmer_xml_parses_with_undeclared_prefixes():
    assert parse_survey(LOOPS).tag == "survey"


def test_page_breaks_skip_loops_and_conditional_blocks():
    breaks = page_breaks(LOOPS)
    assert len(breaks) == 3  # after S1, after Q2, after Q3
    before = [LOOPS[: match.start()] for match in breaks]
    assert before[0].rstrip().endswith("</radio>") and "S2" not in before[0]
    assert "Q2" in before[1] and "Q3" not in before[1]


def test_loops_and_blocks_get_the_early_check_on_a_page_everyone_reaches():
    result = _track(LOOPS, options=TrackingOptions(terminate=True, after_page=2, signals=["automation", "honeypot"]))
    xml = result.xml
    assert result.loops == 1 and result.blocks == 2
    assert result.early_check_page == 2
    early = xml.index('label="QOS_EARLY"')
    assert xml.index('label="Q2"') < early < xml.index('label="Q3"')
    # Never inside the loop or the conditional block.
    assert not (xml.index('<loop label="L1"') < early < xml.index("</loop>"))
    assert "QOS_bot_term" in xml and "QOS_EARLY.val.strip() == 'bot'" in xml
    assert '"terminate": true' in xml and '"signals": ["automation", "honeypot"]' in xml
    assert "house script" in xml
    parse_survey(xml)
    assert remove_tracking(xml) == LOOPS


def test_early_check_is_skipped_when_the_page_does_not_exist():
    result = _track(LOOPS, options=TrackingOptions(terminate=True, after_page=9))
    assert result.early_check_page is None
    assert "QOS_EARLY" not in result.xml
    assert any("no page 9" in warning for warning in result.warnings)


# --- invalid files ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "body, message",
    [
        ("<notes><note>hi</note></notes>", "not a Decipher survey XML"),
        ("<survey name='Survey'><radio label='Q1'></survey>", "not well-formed"),
        ("just some text", "not well-formed"),
        ("", "empty"),
        ('<!DOCTYPE survey [<!ENTITY a "aaaa">]><survey name="Survey">&a;</survey>', "DOCTYPE"),
    ],
)
def test_files_that_are_not_survey_xml_are_refused(body, message):
    with pytest.raises(NotASurveyError, match=message):
        read_survey(body.encode("utf-8"))


def test_non_utf8_file_is_refused():
    with pytest.raises(NotASurveyError, match="UTF-8"):
        read_survey("<survey alt='Café'></survey>".encode("utf-16"))


def test_survey_with_its_own_qos_labels_is_refused():
    clash = PLAIN.replace('label="Q1"', 'label="QOS_note"')
    with pytest.raises(NotASurveyError, match="QOS_"):
        _track(clash)


@pytest.mark.parametrize("survey_id", ["bad$id", "a--b", "x" * 101, "<script>"])
def test_unsafe_survey_ids_are_refused(survey_id):
    with pytest.raises(ValueError):
        _track(PLAIN, survey_id=survey_id)


def test_http_api_is_refused_except_on_localhost():
    with pytest.raises(ValueError, match="https"):
        track_survey(PLAIN.encode(), "http://bot.example/api/v1", _token)
    result = track_survey(PLAIN.encode(), "http://localhost:8000/api/v1", _token)
    assert "http://localhost:8000/api/v1" in result.xml


def test_privacy_text_with_decipher_markup_is_refused():
    with pytest.raises(ValueError, match="privacy"):
        _track(PLAIN, options=TrackingOptions(privacy_text="Hello ${pipe}"))


def test_tracked_xml_stays_well_formed_for_a_strict_parser():
    """Decipher imports the result: it must still be one well-formed <survey>."""
    xml = _track(LOOPS, options=TrackingOptions(terminate=True, privacy_text="We check & verify.")).xml
    root = parse_survey(xml)
    assert root.tag == "survey"
    qos = [element.get("label") for element in root.iter() if str(element.get("label", "")).startswith("QOS_")]
    assert sorted(qos) == sorted([*FIELD_LABELS, "QOS_EARLY", "QOS_bot_term", "QOS_finish", "QOS_privacy"])
    assert "We check &amp; verify." in xml
    # Without Decipher's undeclared prefixes the file is plain well-formed XML.
    ET.fromstring(xml.split("?>", 1)[1].replace("builder:", "b_").replace("ss:", "s_"))


def test_tracker_uses_decipher_uuid_as_the_respondent_id():
    """Results share Decipher's uuid, so they line up with the SPSS export's uuid column."""
    xml = _track(PLAIN).xml
    assert 'var PLATFORM_RESPONDENT = "${uuid}";' in xml
    # The tracker only takes a plain id; an unrendered expression falls back to its own id.
    assert "!/[^A-Za-z0-9_-]/.test(PLATFORM_RESPONDENT)" in xml
    assert remove_tracking(xml) == PLAIN


def test_tracker_skips_personal_boxes_and_sends_addresses_without_query_strings():
    script = tracker_script("Coffee Machine Study", API, "ab12", None)
    assert "location.href" not in script
    assert "page_url: pageAddress()" in script
    assert "return !isPersonal(el);" in script
    assert "e-?mail address" in script and "date of birth" in script


# ------------------------------------------------------------------ settings Decipher refuses


@pytest.mark.parametrize(
    "attributes, expected",
    [
        ('compat="155" delphi="1"', []),
        ('compat="150"', []),
        ("", ["no compat setting"]),
        ('compat="120"', ["below 143"]),
        ('compat="153"', ['delphi="1"']),
        ('compat="12x"', ["not a number"]),
    ],
)
def test_settings_decipher_refuses_are_found(attributes, expected):
    from app.services.decipher_tracking import decipher_settings_problems, parse_survey

    root = parse_survey(f'<survey name="Survey" {attributes}><suspend/></survey>')
    problems = decipher_settings_problems(root)
    assert len(problems) == len(expected)
    for problem, text in zip(problems, expected):
        assert text in problem


def test_tracking_still_works_but_warns_when_decipher_would_refuse():
    old = PLAIN.replace(' compat="155" delphi="1"', "")
    result = _track(old)
    assert any(w.startswith("Decipher will refuse this file") and "compat" in w for w in result.warnings)
    assert remove_tracking(result.xml) == old
    assert not any("Decipher will refuse" in w for w in _track(PLAIN).warnings)


@pytest.mark.parametrize("name", ["espresso_machine_tracker.xml", "coffee_demo_survey.xml"])
def test_the_example_survey_files_pass_decipher_checks(name):
    from pathlib import Path

    from app.services.decipher_tracking import decipher_settings_problems, read_survey

    data = (Path(__file__).parent / "fixtures" / name).read_bytes()
    _, root = read_survey(data)
    assert decipher_settings_problems(root) == []
    result = _track(data.decode("utf-8"))
    assert not any("Decipher will refuse" in w for w in result.warnings)

