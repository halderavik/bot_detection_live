"""Live quality: dashboard rows, totals, rules, trend and CSV, from report data."""

from app.services import live_quality
from app.services.quality_rules import QualityRules, changed_fields, rules_state


def _respondent(**overrides):
    base = {
        "session_id": "s",
        "respondent_id": "R",
        "created_at": "2026-11-16T10:00:00+00:00",
        "is_bot": False,
        "confidence_score": 0.2,
        "risk_level": "LOW",
    }
    base.update(overrides)
    return base


def _row(item, extras=None, **rules):
    result = live_quality.summarize("S", {}, {"respondents": [item]}, extras, rules=QualityRules(**rules))
    return result["respondents"][0]


def test_summary_counts_match_rows():
    """Rows get a status, verdict, and flags; totals are counted from the rows."""
    detailed = {
        "respondents": [
            {
                "session_id": "s1",
                "respondent_id": "R-1",
                "created_at": "2026-11-16T10:00:00+00:00",
                "last_activity": "2026-11-16T10:03:00+00:00",
                "is_bot": True,
                "confidence_score": 0.9,
                "risk_level": "HIGH",
                "flagged_text_responses": 1,
                "timing_speeder": True,
                "text_responses_of_interest": [
                    {
                        "question_preview": "Why?",
                        "response_preview": "asdf",
                        "quality_score": 5,
                        "is_flagged": True,
                        "flag_reasons": {"gibberish": {"is_gibberish": True}},
                    }
                ],
            },
            {
                "session_id": "s2",
                "respondent_id": "R-2",
                "created_at": "2026-11-16T10:05:00+00:00",
                "last_activity": "2026-11-16T10:06:00+00:00",
                "is_bot": False,
                "confidence_score": 0.1,
                "risk_level": "LOW",
            },
            {
                "session_id": "s3",
                "respondent_id": "R-3",
                "created_at": "2020-01-01T00:00:00+00:00",
                "last_activity": "2020-01-01T00:01:00+00:00",
                "risk_level": "unknown",
            },
        ]
    }
    result = live_quality.summarize("QOS-X", {"text_quality_summary": {"total_responses": 3}}, detailed)
    assert result["totals"] == {
        "sessions": 3,
        "respondents": 3,
        "in_progress": 0,
        "checked": 2,
        "dropped": 1,
        "bots": 1,
        "flagged": 1,
        "duplicates": 0,
        "speeders": 0,
        "straight_liners": 0,
        "low_quality_text": 1,
    }
    assert result["text"]["responses"] == 3
    first = result["respondents"][0]
    assert first["session_id"] == "s2" and first["verdict"] == "human"
    bot = next(row for row in result["respondents"] if row["session_id"] == "s1")
    # The per-answer timing_speeder is ignored; speeders come from page times.
    assert bot["flags"] == ["Bot-like behaviour", "Low-quality open ends"]
    assert bot["text_details"][0]["reasons"] == ["gibberish"]
    assert next(row for row in result["respondents"] if row["session_id"] == "s3")["verdict"] == "pending"
    assert [item["count"] for item in result["flag_counts"]][:2] == [1, 1]


def test_page_times_and_grids_come_from_form_submit_ids():
    """Repeated sends count once; page times and grid answers are parsed."""
    events = [
        {"event_type": "form_submit", "timestamp": "t1", "element_id": "qos-page:8000"},
        {"event_type": "form_submit", "timestamp": "t1", "element_id": "qos-page:8000"},
        {"event_type": "form_submit", "timestamp": "t1", "element_id": "qos-grid:3,3,3,3"},
        {"event_type": "form_submit", "timestamp": "t2", "element_id": "qos-page:2000"},
        {"event_type": "focus", "timestamp": "t3", "element_id": "qos-page:9"},
    ]
    parsed = live_quality.parse_events(events)
    assert parsed["pages"] == [8000, 2000]
    assert parsed["grids"] == [["3", "3", "3", "3"]]


def test_fast_pages_and_straight_lines_are_flagged():
    """Under 3.5 seconds a page is a speeder; one answer across a grid is straight-lining."""
    detailed = {
        "respondents": [
            {"session_id": "fast", "created_at": "2026-11-16T10:00:00+00:00", "risk_level": "LOW"},
            {"session_id": "slow", "created_at": "2026-11-16T10:01:00+00:00", "risk_level": "LOW"},
        ]
    }
    extras = {
        "fast": {"pages": [1000, 1500, 900], "grids": [["2", "2", "2", "2", "2"]]},
        "slow": {"pages": [20000, 15000, 9000], "grids": [["1", "4", "2", "5", "3"]]},
    }
    result = live_quality.summarize("QOS-Z", {}, detailed, extras)
    fast = next(row for row in result["respondents"] if row["session_id"] == "fast")
    slow = next(row for row in result["respondents"] if row["session_id"] == "slow")
    assert fast["flags"] == ["Straight-lining", "Speeder"]
    assert fast["timing_explanation"] == "Answered 3 pages in 3 seconds."
    assert slow["flags"] == [] and slow["seconds"] == 44.0
    assert result["totals"]["speeders"] == 1 and result["totals"]["straight_liners"] == 1


def test_trend_buckets_by_hour_and_counts_flags():
    """Starts are bucketed by hour with empty hours filled."""
    rows = [
        {"started": "2026-11-16T10:05:00+00:00", "flags": ["Speeder"]},
        {"started": "2026-11-16T10:40:00+00:00", "flags": []},
        {"started": "2026-11-16T12:10:00+00:00", "flags": []},
    ]
    result = live_quality.trend(rows)
    assert result["unit"] == "hour"
    assert [(b["started"], b["flagged"]) for b in result["buckets"]] == [(2, 1), (0, 0), (1, 0)]


def test_trend_switches_to_days_and_reads_naive_times():
    rows = [{"started": "2026-11-10T10:00:00", "flags": []}, {"started": "2026-11-16T10:00:00", "flags": ["Duplicate"]}]
    result = live_quality.trend(rows)
    assert result["unit"] == "day" and len(result["buckets"]) == 7
    assert result["buckets"][-1]["flagged"] == 1


def test_csv_has_one_row_per_respondent():
    """The export lists flags and the flagged answers."""
    detailed = {
        "respondents": [
            {
                "session_id": "s1",
                "respondent_id": "R-1",
                "created_at": "2026-11-16T10:00:00+00:00",
                "risk_level": "LOW",
                "flagged_text_responses": 1,
                "text_responses_of_interest": [
                    {"question_preview": "Why?", "response_preview": "xx", "quality_score": 0, "is_flagged": True}
                ],
            }
        ]
    }
    text = live_quality.results_csv(live_quality.summarize("S", {}, detailed))
    lines = text.strip().splitlines()
    assert lines[0].startswith("respondent_id,session_id")
    assert "R-1" in lines[1] and "Low-quality open ends" in lines[1] and lines[1].endswith("xx")


def test_behaviour_risk_follows_the_score():
    """A low bot score is low risk, whatever label was stored."""
    row = live_quality.summarize(
        "S", {}, {"respondents": [{"session_id": "a", "risk_level": "high", "confidence_score": 0.12}]}
    )["respondents"][0]
    assert row["risk"] == "low" and row["service_risk"] == "high"
    assert live_quality.behaviour_risk(0.75) == "high"
    assert live_quality.behaviour_risk(0.55) == "medium"


def test_pasted_answers_get_their_own_flag():
    """A pasted but sensible answer is flagged as pasted, not as low quality."""

    def item(reasons):
        return _respondent(
            flagged_text_responses=1,
            text_responses_of_interest=[
                {
                    "question_preview": "Why?",
                    "response_preview": "A long pasted answer.",
                    "quality_score": 80,
                    "is_flagged": True,
                    "flag_reasons": reasons,
                }
            ],
        )

    assert _row(item({"pasted": {"pasted_chars": 90}}))["flags"] == ["Pasted answers"]
    assert _row(item({"pasted": {}, "generic": {}}))["flags"] == ["Low-quality open ends", "Pasted answers"]
    assert _row(item({"pasted": {}}), flag_pasted=False)["flags"] == []


# ------------------------------------------------------------------ rules


def test_bot_rules_use_base_score_and_enabled_signals():
    """Enabled decisive signals make a bot; the threshold applies to the score before them."""
    item = _respondent(
        is_bot=True,
        confidence_score=0.85,
        flagged_patterns={"base_score": 0.45, "decisive_codes": ["honeypot"]},
    )
    assert _row(item)["verdict"] == "bot" and _row(item)["bot_signals"] == ["honeypot"]
    off = _row(item, bot_signals=["automation"])
    assert off["verdict"] == "human" and "Bot-like behaviour" not in off["flags"]
    assert _row(item, bot_signals=[], bot_threshold=0.4)["verdict"] == "bot"
    legacy = _respondent(is_bot=True, confidence_score=0.75)  # results stored before decisive codes existed
    assert _row(legacy)["verdict"] == "bot" and _row(legacy, bot_threshold=0.8)["verdict"] == "human"


def test_speed_text_and_fraud_rules():
    """Speeder, straight-lining, open-end, fraud, duplicate and data-centre flags follow the rules."""
    timed = _respondent(confidence_score=0.1)
    extras = {"s": {"pages": [5000, 5000, 5000, 5000], "grids": [["3", "3", "3"]]}}
    row = _row(timed, extras)
    assert "Speeder" not in row["flags"] and "Straight-lining" in row["flags"]
    row = _row(timed, extras, speeder_page_seconds=6, straightline_min_rows=4)
    assert "Speeder" in row["flags"] and "Straight-lining" not in row["flags"]

    generic = _respondent(
        flagged_text_responses=1,
        text_responses_of_interest=[
            {
                "question_preview": "Why?",
                "response_preview": "good",
                "quality_score": 10,
                "is_flagged": True,
                "flag_reasons": {"generic": {}},
            }
        ],
    )
    assert "Low-quality open ends" in _row(generic)["flags"]
    assert "Low-quality open ends" not in _row(generic, text_reasons=["gibberish"])["flags"]

    risky = _respondent(fraud_score=0.6, is_duplicate=True, fraud_flag_reasons={"datacenter_ip": {"provider": "AWS"}})
    assert "High fraud risk" not in _row(risky)["flags"] and "Data-centre IP" in _row(risky)["flags"]
    assert "High fraud risk" in _row(risky, fraud_threshold=0.5)["flags"]
    assert "Data-centre IP" not in _row(risky, flag_datacenter=False)["flags"]
    assert "Duplicate" in _row(risky)["flags"] and "Duplicate" not in _row(risky, flag_duplicates=False)["flags"]


def test_median_speeder_needs_five_timed_respondents():
    """Under half the median total time is a speeder once five checked respondents have timings."""
    items = [_respondent(session_id=f"s{i}", created_at=f"2026-11-16T10:0{i}:00+00:00") for i in range(5)]
    extras = {f"s{i}": {"pages": [60000, 60000]} for i in range(4)}
    extras["s4"] = {"pages": [20000, 20000]}  # 20 s a page: over 3.5 s, but a third of the median
    result = live_quality.summarize("S", {}, {"respondents": items}, extras)
    assert [row["session_id"] for row in result["respondents"] if row["speeder"]] == ["s4"]
    off = live_quality.summarize("S", {}, {"respondents": items}, extras, rules=QualityRules(speeder_median_share=0))
    assert not any(row["speeder"] for row in off["respondents"])


def test_rules_validate_and_list_changes():
    state = rules_state(QualityRules())
    assert state["rules"] == state["defaults"] and state["changed"] == []
    assert "honeypot" in state["bot_signals"] and "generic" in state["text_reasons"]
    edited = QualityRules(bot_threshold=0.8, bot_signals=["honeypot", "automation"])
    assert edited.bot_signals == ["automation", "honeypot"]  # kept in the standard order
    assert sorted(changed_fields(edited)) == ["bot_signals", "bot_threshold"]
    for bad in ({"bot_signals": ["telepathy"]}, {"bot_threshold": 1.5}, {"text_reasons": ["rude"]}):
        try:
            QualityRules(**bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} was accepted")


def test_period_keeps_only_starts_inside_it_and_recounts():
    detailed = {"respondents": [
        _respondent(session_id="early", created_at="2026-11-10T10:00:00+00:00", is_bot=True, confidence_score=0.95, risk_level="HIGH"),
        _respondent(session_id="mid", created_at="2026-11-16T10:00:00+00:00", fraud_score=0.9, is_duplicate=True),
        _respondent(session_id="late", created_at="2026-11-20T10:00:00", text_response_count=2, flagged_text_responses=1,
                    avg_text_quality_score=35.0),
    ]}
    full = live_quality.summarize("S", {"fraud_summary": {"fraud_methods": {"ip": 1}}}, detailed)
    from datetime import datetime

    period = live_quality.for_period(full, datetime(2026, 11, 15), datetime(2026, 11, 30))
    assert [row["session_id"] for row in period["respondents"]] == ["late", "mid"]
    assert period["totals"]["sessions"] == 2 and period["totals"]["bots"] == 0
    assert period["totals"]["duplicates"] == 1 and period["fraud"]["high_risk"] == 1
    assert period["fraud"]["methods"] == {"ip": 1}
    assert period["text"] == {"responses": 2, "avg_quality": 35.0, "flagged": 1, "flagged_pct": 50.0, "unchecked": 0}
    assert period["quality_distribution"] == {"30-40": 1}
    assert sum(item["count"] for item in period["flag_counts"]) >= 2
    assert period["period"]["from"].startswith("2026-11-15")
    # No period: the results as they are.
    assert live_quality.for_period(full)["totals"] == full["totals"]


def test_straight_lining_follows_the_rule_not_the_stored_80_percent_check():
    """Only every row the same counts, with at least the rule's minimum rows."""
    stored_says_yes = _respondent(grid_straight_lining=True, grid_explanation="Straight-lined on 1 grid question(s); variance 0.21")
    five_of_six = {"s": {"pages": [30000], "grids": [["3", "3", "4", "3", "3", "3"]]}}
    row = _row(stored_says_yes, five_of_six)
    assert not row["straight_lining"] and "Straight-lining" not in row["flags"] and row["grid_explanation"] is None
    all_six = {"s": {"pages": [30000], "grids": [["3"] * 6]}}
    row = _row(_respondent(), all_six)
    assert row["straight_lining"] and row["grid_explanation"] == "Gave the same answer to all 6 rows of a grid."
    assert not _row(_respondent(), all_six, straightline_min_rows=7)["straight_lining"]
    # Without grid answers from the tracker, the stored check decides.
    assert _row(stored_says_yes)["straight_lining"]


def test_unchecked_open_ends_are_counted_and_exported():
    result = live_quality.summarize("S", {}, {"respondents": [_respondent(text_unchecked=2)]}, None, rules=QualityRules())
    assert result["respondents"][0]["text_unchecked"] == 2 and result["text"]["unchecked"] == 2
    header, line = live_quality.results_csv(result).splitlines()[:2]
    assert "text_unchecked" in header.split(",")
    assert line.split(",")[header.split(",").index("text_unchecked")] == "2"


def test_a_reopened_survey_counts_one_respondent_and_merges_the_checked_session():
    import pandas as pd

    from app.services import quality_merge

    old = _respondent(session_id="old", respondent_id="U1", created_at="2026-11-27T10:00:00+00:00",
                      last_activity="2026-11-27T10:01:00+00:00", risk_level="unknown", confidence_score=0.0)
    new = _respondent(session_id="new", respondent_id="U1", created_at="2026-11-27T10:30:00+00:00", risk_level="HIGH",
                      is_bot=True, confidence_score=0.95, flagged_patterns={"base_score": 0.2, "decisive_codes": ["honeypot"]})
    result = live_quality.summarize("S", {}, {"respondents": [old, new]}, None, rules=QualityRules())
    assert result["totals"]["sessions"] == 2 and result["totals"]["respondents"] == 1
    assert {row["session_id"]: row["other_sessions"] for row in result["respondents"]} == {"old": 1, "new": 1}
    merged, _ = quality_merge.add_quality_columns(pd.DataFrame({"uuid": ["U1"]}), result)
    assert merged.loc[0, "LQ_F_BOT"] == 1  # the checked bot session, not the abandoned one


def test_signals_added_after_rules_were_saved_start_switched_on():
    from app.services.quality_rules import _parse, _stored

    # Saved before signals were recorded: honeypot turned off, nothing about newer signals.
    old = {"bot_signals": ["automation", "scripted_input", "no_input", "untyped_answers"]}
    signals = _parse(old).bot_signals
    assert "honeypot" not in signals and {"robotic_timing", "timeline_mismatch"} <= set(signals)
    # Saved now with robotic_timing off: it stays off.
    saved = _stored(QualityRules(bot_signals=["automation", "honeypot", "timeline_mismatch"]))
    assert "robotic_timing" not in _parse(saved).bot_signals
