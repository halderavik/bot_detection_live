"""
Live quality: one survey's bot and fraud results, judged under that survey's quality rules.

Reads the summary and detailed reports this service already builds, plus the page
times and grid answers the tracker stores in form_submit events, and turns them
into a dashboard payload: totals, per-check summaries, a starts-over-time trend,
flag counts, and one row per session. Rules are applied on every read, so edits to
a survey's rules show at once.
"""

import csv
import io
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BehaviorData, SurveyQualityRules, TrackedSurvey
from app.services.quality_rules import QualityRules
from app.services.report_service import ReportService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_CACHE_SECONDS = 4.0
_IN_PROGRESS = timedelta(minutes=20)
# Raw reports per survey id; rules are applied on every read. Reason: the dashboard
# polls every few seconds, possibly from several tabs.
_CACHE: Dict[str, Tuple[float, Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Dict[str, Any]]]]] = {}
_CHUNK = 500

_report_service = ReportService()


async def live_results(db: AsyncSession, survey_id: str, rules: Optional[QualityRules] = None) -> Dict[str, Any]:
    """Build live results for one survey id.

    Args:
        db: Database session.
        survey_id: Tracking survey id.
        rules: Quality rules to apply; defaults when None.

    Returns:
        Totals, per-check summaries, and one row per session, newest first.
    """
    cached = _CACHE.get(survey_id)
    if cached and time.monotonic() - cached[0] < _CACHE_SECONDS:
        return summarize(survey_id, *cached[1], rules=rules)
    summary = await _report_service.generate_summary_report(survey_id=survey_id, db=db, include_inactive=True)
    detailed = await _report_service.generate_detailed_report(survey_id=survey_id, db=db, include_inactive=True)
    summary_json = jsonable_encoder(summary)
    detailed_json = jsonable_encoder(detailed)
    session_ids = [str(item.get("session_id")) for item in detailed_json.get("respondents") or [] if item.get("session_id")]
    extras = await session_extras(db, session_ids)
    raw = (summary_json, detailed_json, extras)
    _CACHE[survey_id] = (time.monotonic(), raw)
    return summarize(survey_id, *raw, rules=rules)


async def session_extras(db: AsyncSession, session_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Read page timing and grid answers the tracker stored in each session's events.

    The tracker writes ``qos-page:<ms>`` and ``qos-grid:<v1,v2,...>`` into the element id of
    form_submit events, because the API keeps only a fixed set of event fields.

    Args:
        db: Database session.
        session_ids: Sessions to read.

    Returns:
        Session id to ``{"pages": [ms, ...], "grids": [[values], ...], "events": n}``.
    """
    events: Dict[str, List[Dict[str, Any]]] = {}
    for start in range(0, len(session_ids), _CHUNK):
        chunk = session_ids[start:start + _CHUNK]
        result = await db.execute(
            select(BehaviorData.session_id, BehaviorData.timestamp, BehaviorData.element_id)
            .where(
                and_(
                    BehaviorData.session_id.in_(chunk),
                    BehaviorData.event_type == "form_submit",
                    BehaviorData.element_id.like("qos-%"),
                )
            )
            .order_by(BehaviorData.timestamp)
        )
        for session_id, timestamp, element_id in result.all():
            events.setdefault(str(session_id), []).append(
                {"event_type": "form_submit", "timestamp": str(timestamp), "element_id": element_id}
            )
    return {session_id: parse_events(items) for session_id, items in events.items()}


def parse_events(events: List[Any]) -> Dict[str, Any]:
    """Pull page times and grid answers out of stored events.

    Args:
        events: Behaviour events with ``event_type``, ``timestamp`` and ``element_id``.

    Returns:
        ``{"pages": [ms, ...], "grids": [[values], ...], "events": n}``. Repeated sends count once.
    """
    pages: List[int] = []
    grids: List[List[str]] = []
    seen: set = set()
    for event in events:
        if not isinstance(event, dict) or event.get("event_type") != "form_submit":
            continue
        element = str(event.get("element_id") or "")
        key = (str(event.get("timestamp") or ""), element)
        if key in seen:
            continue
        seen.add(key)
        if element.startswith("qos-page:"):
            try:
                pages.append(int(element.split(":", 1)[1]))
            except ValueError:
                continue
        elif element.startswith("qos-grid:"):
            values = [value for value in element.split(":", 1)[1].split(",") if value]
            if values:
                grids.append(values)
    return {"pages": pages, "grids": grids, "events": len(events)}


def _when(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp; naive times are taken as UTC."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _mark_speeders(rows: List[Dict[str, Any]], rules: QualityRules) -> None:
    """Flag speeders from page times.

    A respondent is a speeder when pages average under ``speeder_page_seconds``, or,
    once five or more checked respondents have timings, when their total time is
    under ``speeder_median_share`` of the median (0 turns that check off).

    Args:
        rows: Dashboard rows. Changed in place.
        rules: Quality rules.
    """
    timed = sorted(row["seconds"] for row in rows if row["status"] == "checked" and row.get("seconds"))
    median = timed[len(timed) // 2] if len(timed) >= 5 else None
    for row in rows:
        seconds, pages = row.get("seconds"), row.get("pages") or 0
        if not seconds or not pages:
            continue
        fast = seconds / pages < rules.speeder_page_seconds
        share = rules.speeder_median_share
        if median and share and row["status"] == "checked" and seconds < share * median:
            fast = True
        if fast and not row["speeder"]:
            row["speeder"] = True
            row["flags"].append("Speeder")
            row["timing_explanation"] = row.get("timing_explanation") or (
                f"Answered {pages} pages in {seconds:.0f} seconds."
            )


# Text reasons the rules can switch off; others the text check reports always count.
TEXT_REASON_CODES = ("gibberish", "generic", "irrelevant", "copy_paste", "low_quality")
# Text flags about how an answer was entered rather than what it says.
_ENTRY_REASONS = {"pasted", "no_typing"}


def _bot_verdict(item: Dict[str, Any], rules: QualityRules) -> Tuple[bool, List[str]]:
    """Decide bot or human under the survey's rules.

    The detection engine reports the behaviour score before decisive signals raised it
    (``base_score``) and which signals fired (``decisive_codes``). A respondent is a
    bot when the base score reaches the threshold or an enabled signal fired. Results
    stored before those fields existed fall back to the reported score.

    Args:
        item: Detailed-report respondent.
        rules: Quality rules.

    Returns:
        Whether the respondent is a bot, and the enabled signals that fired.
    """
    patterns = item.get("flagged_patterns") or {}
    codes = [code for code in patterns.get("decisive_codes") or [] if code in rules.bot_signals]
    base = patterns.get("base_score")
    if base is None:
        base = item.get("confidence_score")
    try:
        score = float(base)
    except (TypeError, ValueError):
        return bool(item.get("is_bot")), codes
    return score >= rules.bot_threshold or bool(codes), codes


def behaviour_risk(confidence: Any) -> str:
    """Map the behavioural bot score to a risk level: ``high`` from 0.7, ``medium`` from 0.5, else ``low``."""
    try:
        score = float(confidence)
    except (TypeError, ValueError):
        return "unknown"
    if score >= 0.7:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _bot_risk(confidence: Any, is_bot: bool) -> str:
    """Behaviour risk, at least ``high`` for a respondent judged a bot."""
    risk = behaviour_risk(confidence)
    return "high" if is_bot and risk in {"low", "medium", "unknown"} else risk


def _row(
    item: Dict[str, Any],
    now: datetime,
    extra: Optional[Dict[str, Any]] = None,
    rules: Optional[QualityRules] = None,
) -> Dict[str, Any]:
    """Turn one detailed-report respondent into a dashboard row.

    Args:
        item: Detailed-report respondent (JSON form).
        now: Current time.
        extra: Page times and grid answers read from the session's events.
        rules: Quality rules; defaults when None.

    Returns:
        Row with status, verdict, scores, flags, and explanations.
    """
    extra = extra or {}
    rules = rules or QualityRules()
    pages = [int(ms) for ms in extra.get("pages") or []]
    grids = extra.get("grids") or []
    straight = [values for values in grids if len(values) >= rules.straightline_min_rows and len(set(values)) == 1]
    risk = str(item.get("risk_level") or "unknown")
    checked = risk.lower() != "unknown"
    last = _when(item.get("last_activity")) or _when(item.get("created_at"))
    if checked:
        status = "checked"
    elif last and now - last < _IN_PROGRESS:
        status = "in_progress"
    else:
        status = "dropped"
    flags: List[str] = []
    is_bot, signals = _bot_verdict(item, rules)
    if is_bot:
        flags.append("Bot-like behaviour")
    entries = item.get("text_responses_of_interest") or []
    entry_reasons = [set((entry.get("flag_reasons") or {}).keys()) for entry in entries if entry.get("is_flagged")]
    counted = set(rules.text_reasons)
    if entries:
        low_quality = any(
            (not reasons) or (reasons & counted) or (reasons - _ENTRY_REASONS - set(TEXT_REASON_CODES))
            for reasons in entry_reasons
        )
    else:
        low_quality = (item.get("flagged_text_responses") or 0) > 0
    if low_quality:
        flags.append("Low-quality open ends")
    if rules.flag_pasted and any(reasons & _ENTRY_REASONS for reasons in entry_reasons):
        flags.append("Pasted answers")
    if rules.flag_duplicates and item.get("is_duplicate"):
        flags.append("Duplicate")
    fraud_score = item.get("fraud_score")
    if fraud_score is not None:
        high_fraud = float(fraud_score) >= rules.fraud_threshold
    else:
        high_fraud = str(item.get("fraud_risk_level") or "").upper() in {"HIGH", "CRITICAL"}
    if high_fraud:
        flags.append("High fraud risk")
    datacenter = (item.get("fraud_flag_reasons") or {}).get("datacenter_ip")
    if rules.flag_datacenter and datacenter:
        flags.append("Data-centre IP")
    if item.get("timing_flatliner"):
        flags.append("Flatliner")
    straight_lining = bool(item.get("grid_straight_lining")) or bool(straight)
    if straight_lining:
        flags.append("Straight-lining")
    return {
        "session_id": item.get("session_id"),
        "respondent_id": item.get("respondent_id"),
        "started": item.get("created_at"),
        "last_activity": item.get("last_activity"),
        "minutes": item.get("session_duration_minutes"),
        "events": item.get("total_events") or 0,
        "status": status,
        "verdict": ("bot" if is_bot else "human") if checked else "pending",
        "bot_signals": signals,
        "confidence": item.get("confidence_score"),
        # Reason: a stored risk label can disagree with a low score, so derive it from the score.
        "risk": _bot_risk(item.get("confidence_score"), is_bot) if checked else "unknown",
        "service_risk": risk,
        "text_responses": item.get("text_response_count") or 0,
        "text_quality": item.get("avg_text_quality_score"),
        "text_flagged": item.get("flagged_text_responses") or 0,
        "low_quality_text": low_quality,
        "fraud_score": item.get("fraud_score"),
        "duplicate": bool(item.get("is_duplicate")),
        "fraud_risk": item.get("fraud_risk_level"),
        "straight_lining": straight_lining,
        "grid_variance": item.get("grid_variance_score"),
        "grids": grids,
        "pages": len(pages),
        "seconds": round(sum(pages) / 1000, 1) if pages else None,
        # Set from page times by _mark_speeders; per-answer timing counts a quick
        # short open end as a speeder.
        "speeder": False,
        "flatliner": bool(item.get("timing_flatliner")),
        "flags": flags,
        "explanation": item.get("bot_explanation") or item.get("analysis_summary"),
        "text_details": [
            {
                "question": entry.get("question_preview"),
                "answer": entry.get("response_preview"),
                "quality": entry.get("quality_score"),
                "flagged": bool(entry.get("is_flagged")),
                "reasons": [
                    key
                    for key, value in (entry.get("flag_reasons") or {}).items()
                    if not isinstance(value, dict) or value.get("is_relevant") is not True
                ],
            }
            for entry in entries
        ],
        "fraud_reasons": item.get("fraud_flag_reasons"),
        "grid_explanation": item.get("grid_explanation")
        or (f"Gave the same answer to all {len(straight[0])} rows of a grid." if straight else None),
        "timing_explanation": item.get("timing_explanation"),
    }


def summarize(
    survey_id: str,
    summary: Dict[str, Any],
    detailed: Dict[str, Any],
    extras: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[QualityRules] = None,
) -> Dict[str, Any]:
    """Combine the summary and detailed reports into the dashboard payload.

    Args:
        survey_id: Tracking survey id.
        summary: Summary report (JSON form).
        detailed: Detailed report (JSON form).
        extras: Page times and grid answers per session id.
        rules: Quality rules; defaults when None.

    Returns:
        Dashboard payload. Counts come from the rows so they always match the table.
    """
    now = datetime.now(timezone.utc)
    extras = extras or {}
    rules = rules or QualityRules()
    rows = [
        _row(item, now, extras.get(str(item.get("session_id"))), rules)
        for item in detailed.get("respondents") or []
        if isinstance(item, dict)
    ]
    _mark_speeders(rows, rules)
    rows.sort(key=lambda row: row.get("started") or "", reverse=True)
    checked = [row for row in rows if row["status"] == "checked"]
    flagged = [row for row in rows if row["flags"]]
    text = summary.get("text_quality_summary") or {}
    fraud = summary.get("fraud_summary") or {}
    grid = summary.get("grid_analysis_summary") or {}
    timing = summary.get("timing_analysis_summary") or {}
    return {
        "survey_id": survey_id,
        "updated_at": now.isoformat(),
        "rules": rules.model_dump(),
        "totals": {
            "sessions": len(rows),
            "in_progress": sum(1 for row in rows if row["status"] == "in_progress"),
            "checked": len(checked),
            "dropped": sum(1 for row in rows if row["status"] == "dropped"),
            "bots": sum(1 for row in checked if row["verdict"] == "bot"),
            "flagged": len(flagged),
            "duplicates": sum(1 for row in rows if row["duplicate"]),
            "speeders": sum(1 for row in rows if row["speeder"]),
            "straight_liners": sum(1 for row in rows if row["straight_lining"]),
            "low_quality_text": sum(1 for row in rows if row["low_quality_text"]),
        },
        "text": {
            "responses": text.get("total_responses") or 0,
            "avg_quality": text.get("avg_quality_score"),
            "flagged": text.get("flagged_count") or 0,
            "flagged_pct": text.get("flagged_percentage") or 0,
        },
        "fraud": {
            "analyzed": fraud.get("total_sessions_analyzed") or 0,
            "avg_score": fraud.get("average_fraud_score"),
            "high_risk": fraud.get("high_risk_sessions") or 0,
            "duplicates": fraud.get("duplicate_sessions") or 0,
            "methods": fraud.get("fraud_methods") or {},
        },
        "grid": {
            "responses": grid.get("total_responses") or 0,
            "straight_lined_pct": grid.get("straight_lined_percentage") or 0,
        },
        "timing": {
            "analyses": timing.get("total_analyses") or 0,
            "speeders_pct": timing.get("speeders_percentage") or 0,
            "flatliners_pct": timing.get("flatliners_percentage") or 0,
        },
        "flag_counts": _flag_counts(rows),
        "quality_distribution": text.get("quality_distribution") or {},
        "trend": trend(rows),
        "respondents": rows,
    }


FLAG_ORDER = (
    "Bot-like behaviour",
    "Low-quality open ends",
    "Pasted answers",
    "Straight-lining",
    "Speeder",
    "Flatliner",
    "Duplicate",
    "High fraud risk",
    "Data-centre IP",
)


def _flag_counts(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Count respondents per flag in a fixed order, zeros included."""
    return [{"flag": flag, "count": sum(1 for row in rows if flag in row["flags"])} for flag in FLAG_ORDER]


def trend(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Bucket starts and flagged respondents by hour, or by day for longer fieldwork.

    Args:
        rows: Dashboard rows.

    Returns:
        ``{"unit": "hour" | "day", "buckets": [{"start": iso, "started": n, "flagged": n}]}``
        with empty buckets filled, at most 120 buckets ending at the latest start.
    """
    times = [(when, bool(row["flags"])) for row in rows if (when := _when(row.get("started")))]
    if not times:
        return {"unit": "hour", "buckets": []}
    first = min(when for when, _ in times)
    last = max(when for when, _ in times)
    unit = "hour" if last - first <= timedelta(hours=48) else "day"
    step = timedelta(hours=1) if unit == "hour" else timedelta(days=1)

    def floor(when: datetime) -> datetime:
        if unit == "hour":
            return when.replace(minute=0, second=0, microsecond=0)
        return when.replace(hour=0, minute=0, second=0, microsecond=0)

    end = floor(last)
    start = max(floor(first), end - step * 119)
    counts: Dict[datetime, List[int]] = {}
    cursor = start
    while cursor <= end:
        counts[cursor] = [0, 0]
        cursor += step
    for when, is_flagged in times:
        key = floor(when)
        if key in counts:
            counts[key][0] += 1
            counts[key][1] += int(is_flagged)
    return {
        "unit": unit,
        "buckets": [{"start": key.isoformat(), "started": value[0], "flagged": value[1]} for key, value in counts.items()],
    }


async def list_surveys(db: AsyncSession) -> List[Dict[str, Any]]:
    """List every survey with sessions, plus tracked surveys nobody has started yet.

    Args:
        db: Database session.

    Returns:
        One entry per survey id with counts, last activity, the title from its tracked
        XML, and whether it has its own rules. Tracked surveys come first, then by
        latest activity.
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    for item in await _report_service.get_available_surveys(db):
        survey_id = str(item.get("survey_id") or "")
        if not survey_id:
            continue
        entry = by_id.setdefault(
            survey_id,
            {"survey_id": survey_id, "title": None, "sessions": 0, "bots": 0, "last_session": None, "tracked": False},
        )
        entry["sessions"] += int(item.get("session_count") or 0)
        entry["bots"] += int(item.get("bot_count") or 0)
        last = item.get("last_session")
        if last and (entry["last_session"] is None or str(last) > str(entry["last_session"])):
            entry["last_session"] = last
    tracked = (await db.execute(select(TrackedSurvey.survey_id, TrackedSurvey.title))).all()
    for survey_id, title in tracked:
        entry = by_id.setdefault(
            survey_id,
            {"survey_id": survey_id, "title": None, "sessions": 0, "bots": 0, "last_session": None, "tracked": False},
        )
        entry["tracked"] = True
        entry["title"] = title
    custom = {row[0] for row in (await db.execute(select(SurveyQualityRules.survey_id))).all()}
    surveys = list(by_id.values())
    for entry in surveys:
        entry["custom_rules"] = entry["survey_id"] in custom
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    surveys.sort(key=lambda row: (not row["tracked"], -(_when(row["last_session"]) or epoch).timestamp()))
    return surveys


_CSV_COLUMNS = (
    "respondent_id",
    "session_id",
    "started",
    "status",
    "verdict",
    "risk",
    "confidence",
    "seconds",
    "pages",
    "text_responses",
    "text_quality",
    "text_flagged",
    "fraud_score",
    "fraud_risk",
    "duplicate",
    "straight_lining",
    "speeder",
    "flags",
    "flagged_answers",
)


def results_csv(result: Dict[str, Any]) -> str:
    """Write one row per respondent as CSV, with a header row."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_COLUMNS)
    for row in result.get("respondents") or []:
        values = []
        for column in _CSV_COLUMNS:
            if column == "flags":
                values.append("; ".join(row.get("flags") or []))
            elif column == "flagged_answers":
                values.append(
                    " | ".join(
                        str(detail.get("answer") or "") for detail in row.get("text_details") or [] if detail.get("flagged")
                    )
                )
            else:
                value = row.get(column)
                values.append("" if value is None else value)
        writer.writerow(values)
    return buffer.getvalue()
