"""Live quality flags joined to a survey data file as LQ_ variables."""

import io
import os

import numpy as np
import pandas as pd
import pytest

pyreadstat = pytest.importorskip("pyreadstat")

from app.services import live_quality, quality_merge  # noqa: E402

DETAILED = {
    "respondents": [
        {
            "session_id": "s-bot",
            "respondent_id": "R-1",
            "created_at": "2026-11-16T10:00:00+00:00",
            "is_bot": True,
            "confidence_score": 0.92,
            "risk_level": "HIGH",
            "fraud_score": 0.4,
            "flagged_patterns": {"base_score": 0.92, "decisive_codes": ["honeypot"]},
        },
        {
            "session_id": "s-fraud",
            "respondent_id": "R-2",
            "created_at": "2026-11-16T10:05:00+00:00",
            "confidence_score": 0.2,
            "risk_level": "LOW",
            "fraud_score": 0.85,
            "is_duplicate": True,
        },
        {
            "session_id": "s-human",
            "respondent_id": "abc123uuid",
            "created_at": "2026-11-16T10:07:00+00:00",
            "confidence_score": 0.1,
            "risk_level": "LOW",
            "fraud_score": 0.05,
        },
    ]
}


def _result() -> dict:
    return live_quality.summarize("BrewCo", {}, DETAILED)


def test_records_get_flags_matched_by_session_then_respondent_then_uuid():
    """Each record gets its own row's flags; untracked or unknown records are marked unmatched."""
    frame = pd.DataFrame(
        {
            "record": [1, 2, 3, 4, 5],
            "uuid": ["", "", "abc123uuid", "", ""],
            "QOS_SESSION": ["s-bot", "", "", "s-missing", ""],
            "QOS_RESPONDENT": ["", "R-2", "", "", ""],
        }
    )
    merged, report = quality_merge.add_quality_columns(frame, _result())
    assert list(merged["LQ_MATCHED"]) == [1, 1, 1, 0, 0]
    assert list(merged["LQ_VERDICT"][:3]) == [2, 1, 1]
    assert list(merged["LQ_F_BOT"][:3]) == [1, 0, 0]
    assert list(merged["LQ_F_FRAUD"][:3]) == [0, 1, 0]
    assert list(merged["LQ_F_DUPLICATE"][:3]) == [0, 1, 0]
    assert merged.loc[0, "LQ_BOT_SIGNALS"] == "Hidden honeypot field filled in"
    assert merged.loc[1, "LQ_FRAUD_RISK"] == 3 and merged.loc[2, "LQ_FRAUD_RISK"] == 1
    assert np.isnan(merged.loc[3, "LQ_BOT_SCORE"]) and merged.loc[3, "LQ_FLAGS"] == ""
    assert report["tracked"] == 4 and report["matched"] == 3 and report["unmatched"] == 1
    assert report["bots"] == 1 and report["flagged"] == 2
    assert report["match_columns"] == ["QOS_SESSION", "QOS_RESPONDENT", "uuid"]

    # Running it again replaces the LQ_ columns rather than adding a second set.
    again, _ = quality_merge.add_quality_columns(merged, _result())
    assert list(again.columns) == list(merged.columns)


def test_csv_comes_back_as_csv_with_ids_unchanged():
    source = "record,QOS_SESSION,zip\n1,s-bot,00501\n2,s-human,02134\n"
    payload, name, media, report = quality_merge.merge_file(source.encode(), "wave1.csv", _result())
    assert name == "wave1_quality.csv" and media == "text/csv"
    back = pd.read_csv(io.BytesIO(payload), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert list(back["zip"]) == ["00501", "02134"]  # leading zeros kept
    assert list(back["LQ_VERDICT"]) == ["2.0", "1.0"]
    assert report["matched"] == 2 and "LQ_ variables" in report["message"]


def test_excel_comes_back_as_excel():
    buffer = io.BytesIO()
    pd.DataFrame({"record": [1], "QOS_SESSION": ["s-fraud"]}).to_excel(buffer, index=False)
    payload, name, media, _ = quality_merge.merge_file(buffer.getvalue(), "data.xlsx", _result())
    assert name == "data_quality.xlsx" and media.endswith("spreadsheetml.sheet")
    back = pd.read_excel(io.BytesIO(payload))
    assert back.loc[0, "LQ_F_DUPLICATE"] == 1


def test_spss_keeps_labels_and_labels_the_new_variables(tmp_path):
    source = tmp_path / "decipher.sav"
    frame = pd.DataFrame({"record": [1.0, 2.0], "Q1": [1.0, 2.0], "QOS_SESSION": ["s-bot", "s-human"]})
    pyreadstat.write_sav(
        frame,
        str(source),
        column_labels=["Record", "How often?", "Session"],
        variable_value_labels={"Q1": {1.0: "Daily", 2.0: "Weekly"}},
    )
    payload, name, _, report = quality_merge.merge_file(source.read_bytes(), "decipher.sav", _result())
    assert name == "decipher_quality.sav" and report["matched"] == 2
    out = tmp_path / name
    out.write_bytes(payload)
    back, meta = pyreadstat.read_sav(str(out))
    labels = dict(zip(meta.column_names, meta.column_labels))
    assert labels["Q1"] == "How often?"
    assert labels["LQ_VERDICT"] == "[Live quality] Verdict under the survey's rules"
    assert meta.variable_value_labels["Q1"] == {1.0: "Daily", 2.0: "Weekly"}
    assert meta.variable_value_labels["LQ_F_BOT"] == {0.0: "No", 1.0: "Yes"}
    assert list(back["LQ_F_BOT"]) == [1.0, 0.0]
    assert back.loc[0, "LQ_FLAGS"] == "Bot-like behaviour"


def test_files_without_ids_or_of_other_kinds_are_refused():
    with pytest.raises(quality_merge.MergeError, match="nothing to match"):
        quality_merge.merge_file(b"record,Q1\n1,2\n", "plain.csv", _result())
    with pytest.raises(quality_merge.MergeError, match="SPSS"):
        quality_merge.merge_file(b"x", "data.json", _result())
    with pytest.raises(quality_merge.MergeError, match="could not be read"):
        quality_merge.merge_file(os.urandom(64), "broken.sav", _result())
