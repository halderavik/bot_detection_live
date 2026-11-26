"""
Survey data variables (QOS_STATUS, QOS_FRAUD, ...) built from a composite result.

The respondents here are made up; the dicts mirror what the composite analysis
returns for a coffee machine study.
"""

import re

from app.services.decipher_tracking import FIELD_LABELS, add_tracking, parse_survey, remove_tracking
from app.services.quality_variables import REASON_CODES, survey_variables

NUMBER_LABELS = [label for label in FIELD_LABELS if label not in (
    "QOS_RESPONDENT", "QOS_SESSION", "QOS_FLAG", "QOS_SCORE", "QOS_RISK", "QOS_REASONS")]


def _human():
    return {
        "is_bot": False,
        "risk_level": "LOW",
        "behavioral_details": {"confidence_score": 0.12, "is_bot": False, "flagged_patterns": {"base_score": 0.12}},
        "text_quality_details": {"avg_quality_score": 82.4, "flagged_count": 0},
        "fraud_details": {
            "fraud_score": 0.05, "ip_risk_score": 0.0, "fingerprint_risk_score": 0.0,
            "duplicate_risk_score": 0.1, "geolocation_risk_score": 0.0, "velocity_risk_score": 0.0,
            "flag_reasons": None,
        },
        "grid_details": {"straight_lined_questions": 0},
        "timing_details": {"speeders": 0},
    }


def test_clean_respondent_is_human_with_no_reasons():
    values = survey_variables(_human())
    assert values["QOS_STATUS"] == 1
    assert values["QOS_BEHAV"] == 12 and values["QOS_OES"] == 82 and values["QOS_FRAUD"] == 5
    assert values["QOS_DUP"] == 0 and values["QOS_DUP_SCORE"] == 10 and values["QOS_DATACENTER"] == 0
    assert values["QOS_SPEEDER"] == 0 and values["QOS_STRAIGHTLINE"] == 0
    assert values["QOS_REASON"] == 0 and values["QOS_REASONS"] == "" and values["QOS_FLAGCOUNT"] == 0


def test_bot_gets_status_3_and_the_behavioural_reason_first():
    composite = _human()
    composite["is_bot"] = True
    composite["behavioral_details"] = {
        "confidence_score": 0.95, "is_bot": True,
        "flagged_patterns": {"decisive_codes": ["honeypot", "automation"]},
    }
    composite["fraud_details"]["flag_reasons"] = {"datacenter_ip": {"severity": "high"}, "device_reuse": {}}
    values = survey_variables(composite)
    assert values["QOS_STATUS"] == 3
    assert values["QOS_REASON"] == 1  # automation, the most severe
    assert values["QOS_REASONS"] == "1,4,10,11"
    assert values["QOS_FLAGCOUNT"] == 4
    assert values["QOS_DUP"] == 1 and values["QOS_DATACENTER"] == 1


def test_quality_problems_alone_make_a_suspect():
    composite = _human()
    composite["text_quality_details"]["flagged_count"] = 2
    composite["grid_details"]["straight_lined_questions"] = 3
    composite["timing_details"]["speeders"] = 5
    values = survey_variables(composite)
    assert values["QOS_STATUS"] == 2
    assert values["QOS_REASONS"] == "20,21,22"
    assert values["QOS_STRAIGHTLINE"] == 3 and values["QOS_SPEEDER"] == 5


def test_bot_by_score_without_decisive_signals_has_the_behaviour_code():
    composite = _human()
    composite["behavioral_details"] = {"confidence_score": 0.74, "is_bot": True}
    assert survey_variables(composite)["QOS_REASON"] == 6


def test_checks_that_did_not_run_are_left_blank():
    values = survey_variables({"behavioral_details": {"confidence_score": 0.3}})
    assert values["QOS_STATUS"] == 1 and values["QOS_BEHAV"] == 30
    for label in ("QOS_OES", "QOS_FRAUD", "QOS_DUP", "QOS_DUP_SCORE", "QOS_IP_RISK",
                  "QOS_DEVICE_RISK", "QOS_GEO_RISK", "QOS_VELOCITY", "QOS_DATACENTER",
                  "QOS_SPEEDER", "QOS_STRAIGHTLINE"):
        assert values[label] is None, label


def test_every_variable_has_a_hidden_question_and_fits_its_range():
    composite = _human()
    composite["fraud_details"]["fraud_score"] = 7.5  # out of range input is clipped
    values = survey_variables(composite)
    assert set(values) == set(FIELD_LABELS) - {"QOS_RESPONDENT", "QOS_SESSION", "QOS_FLAG", "QOS_SCORE", "QOS_RISK"}
    assert values["QOS_FRAUD"] == 100
    xml = add_tracking('<survey alt="Espresso Study" name="Survey"><text label="Q1"><title>Why?</title></text></survey>',
                       "Espresso Study", "https://bot.example/api/v1")
    root = parse_survey(xml)
    for label in NUMBER_LABELS:
        element = next(e for e in root.iter() if e.get("label") == label)
        assert element.tag == "number", label
        top = int(re.search(r"range\(0,(\d+)\)", element.get("verify")).group(1))
        assert 0 <= values[label] <= top, label
    assert next(e for e in root.iter() if e.get("label") == "QOS_REASONS").tag == "text"


def test_reason_codes_are_unique():
    numbers = [number for number, _, _ in REASON_CODES]
    names = [name for _, name, _ in REASON_CODES]
    assert len(set(numbers)) == len(numbers) and len(set(names)) == len(names)


def test_survey_tracked_with_the_older_five_fields_is_upgraded():
    plain = '<survey alt="Espresso Study" name="Survey"><text label="Q1"><title>Why?</title></text></survey>'
    new = add_tracking(plain, "Espresso Study", "https://bot.example/api/v1")
    # The earlier layout: only the five text fields.
    old = re.sub(r'  <number label="QOS_[A-Z_]+"[^>]*>\n.*?\n  </number>\n', "", new, flags=re.S)
    old = re.sub(r'  <text label="QOS_REASONS"[^>]*>\n.*?\n  </text>\n', "", old, flags=re.S)
    assert "<number" not in old and 'label="QOS_RISK"' in old
    assert remove_tracking(old) == plain
    assert remove_tracking(new) == plain
