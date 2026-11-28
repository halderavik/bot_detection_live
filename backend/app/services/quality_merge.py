"""
Add live quality results to a survey data file as ``LQ_*`` variables.

A Decipher export of a tracked survey carries ``QOS_SESSION`` and ``QOS_RESPONDENT``
(written by the tracker on the final page) and Decipher's own ``uuid``, which the
tracker uses as the respondent id. Each record is joined to its row in the live
quality results, under the survey's quality rules, and the file comes back in the
same format (SPSS .sav, CSV, or Excel) with the LQ_ variables added at the end, so
flags can be used in tables, filters and cleaning like any other variable.
"""

import io
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.services.decipher_tracking import BOT_SIGNALS

PREFIX = "LQ_"
SESSION_COLUMN = "QOS_SESSION"
RESPONDENT_COLUMN = "QOS_RESPONDENT"
# Decipher's respondent id; the tracker reports respondents under the same value.
UUID_COLUMN = "uuid"
FORMATS = {".sav": "sav", ".csv": "csv", ".xlsx": "xlsx"}
MEDIA_TYPES = {
    "sav": "application/octet-stream",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# One 0/1 variable per dashboard flag, in the dashboard's order.
FLAG_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("LQ_F_BOT", "Bot-like behaviour"),
    ("LQ_F_TEXT", "Low-quality open ends"),
    ("LQ_F_PASTED", "Pasted answers"),
    ("LQ_F_STRAIGHT", "Straight-lining"),
    ("LQ_F_SPEEDER", "Speeder"),
    ("LQ_F_FLATLINE", "Flatliner"),
    ("LQ_F_DUPLICATE", "Duplicate"),
    ("LQ_F_FRAUD", "High fraud risk"),
    ("LQ_F_DATACENTRE", "Data-centre IP"),
)
_BANDS = {"1": "Low (under 0.5)", "2": "Medium (0.5 to 0.7)", "3": "High (0.7 and over)"}
_YES_NO = {"0": "No", "1": "Yes"}


class MergeError(ValueError):
    """The file could not be read, or has nothing to match on."""


def _variable(
    name: str, label: str, *, values: Optional[Dict[str, str]] = None, text: bool = False, scale: bool = False
) -> Dict[str, Any]:
    """One LQ_ variable: name, label, value labels, and measurement level."""
    return {
        "name": name,
        "label": label,
        "measurement": "nominal" if text or not scale else "scale",
        "value_labels": values or {},
        "is_text": text,
    }


def quality_variables() -> List[Dict[str, Any]]:
    """Every ``LQ_*`` variable, with labels and value labels."""
    entries = [
        _variable("LQ_MATCHED", "[Live quality] Record found in live quality results", values=_YES_NO),
        _variable(
            "LQ_STATUS",
            "[Live quality] Session status",
            values={"1": "Checked", "2": "In progress", "3": "Dropped or ended early"},
        ),
        _variable(
            "LQ_VERDICT",
            "[Live quality] Verdict under the survey's rules",
            values={"1": "Human", "2": "Bot", "3": "Not checked yet"},
        ),
        _variable("LQ_BOT_SCORE", "[Live quality] Behaviour bot score (0 human to 1 bot)", scale=True),
        _variable("LQ_BOT_RISK", "[Live quality] Behaviour risk band", values=_BANDS),
        _variable("LQ_BOT_SIGNALS", "[Live quality] Decisive bot signals that fired", text=True),
        _variable("LQ_SECONDS", "[Live quality] Seconds on tracked pages", scale=True),
        _variable("LQ_PAGES", "[Live quality] Tracked pages", scale=True),
        _variable("LQ_SEC_PER_PAGE", "[Live quality] Seconds per page", scale=True),
        _variable("LQ_TEXT_QUALITY", "[Live quality] Average open-end quality (0 poor to 100 good)", scale=True),
        _variable("LQ_FRAUD_SCORE", "[Live quality] Fraud score (0 genuine to 1 fraud)", scale=True),
        _variable("LQ_FRAUD_RISK", "[Live quality] Fraud risk band", values=_BANDS),
    ]
    entries += [_variable(name, f"[Live quality] Flag: {flag}", values=_YES_NO) for name, flag in FLAG_COLUMNS]
    entries += [
        _variable("LQ_NFLAGS", "[Live quality] Number of flags", scale=True),
        _variable("LQ_FLAGS", "[Live quality] All flags", text=True),
    ]
    return entries


def _band(score: Any) -> float:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return np.nan
    return 3.0 if value >= 0.7 else 2.0 if value >= 0.5 else 1.0


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _key(value: Any) -> str:
    """A cell as a match key: text, with blanks, NaN and a trailing ``.0`` from numeric reads removed."""
    if value is None:
        return ""
    if isinstance(value, float):
        if np.isnan(value):
            return ""
        if value.is_integer():
            return str(int(value))
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _values(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The ``LQ_*`` values for one dashboard row, or the unmatched defaults."""
    if row is None:
        blank: Dict[str, Any] = {entry["name"]: ("" if entry["is_text"] else np.nan) for entry in quality_variables()}
        blank["LQ_MATCHED"] = 0.0
        return blank
    flags = list(row.get("flags") or [])
    seconds, pages = _number(row.get("seconds")), _number(row.get("pages")) or np.nan
    verdict = {"human": 1.0, "bot": 2.0}.get(str(row.get("verdict")), 3.0)
    status = {"checked": 1.0, "in_progress": 2.0}.get(str(row.get("status")), 3.0)
    fraud = _number(row.get("fraud_score"))
    fraud_band = _band(fraud)
    if np.isnan(fraud_band):
        fraud_band = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 3.0}.get(
            str(row.get("fraud_risk") or "").upper(), np.nan
        )
    values: Dict[str, Any] = {
        "LQ_MATCHED": 1.0,
        "LQ_STATUS": status,
        "LQ_VERDICT": verdict,
        "LQ_BOT_SCORE": _number(row.get("confidence")),
        "LQ_BOT_RISK": {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 3.0}.get(str(row.get("risk")), np.nan),
        "LQ_BOT_SIGNALS": "; ".join(BOT_SIGNALS.get(code, code) for code in row.get("bot_signals") or []),
        "LQ_SECONDS": seconds,
        "LQ_PAGES": pages,
        "LQ_SEC_PER_PAGE": round(seconds / pages, 1) if pages and not np.isnan(seconds) else np.nan,
        "LQ_TEXT_QUALITY": _number(row.get("text_quality")),
        "LQ_FRAUD_SCORE": fraud,
        "LQ_FRAUD_RISK": fraud_band,
        "LQ_NFLAGS": float(len(flags)),
        "LQ_FLAGS": "; ".join(flags),
    }
    for name, flag in FLAG_COLUMNS:
        values[name] = 1.0 if flag in flags else 0.0
    return values


def _column(frame: pd.DataFrame, name: str) -> pd.Series:
    """A column by name, ignoring case, or an empty column when the data has none."""
    for column in frame.columns:
        if str(column).lower() == name.lower():
            return frame[column]
    return pd.Series([""] * len(frame), index=frame.index)


_STATUS_ORDER = {"checked": 2, "in_progress": 1}


def _preference(row: Dict[str, Any]) -> tuple:
    """Which of a respondent's sessions speaks for them: checked first, then the latest."""
    return (_STATUS_ORDER.get(row.get("status"), 0), str(row.get("started") or ""))


def match_columns(frame: pd.DataFrame) -> List[str]:
    """The id columns present with any values, in match order."""
    found = []
    for name in (SESSION_COLUMN, RESPONDENT_COLUMN, UUID_COLUMN):
        if any(_key(value) for value in _column(frame, name)):
            found.append(name)
    return found


def add_quality_columns(frame: pd.DataFrame, result: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Join live quality rows to survey records and add the ``LQ_*`` variables.

    Records match on ``QOS_SESSION``, then ``QOS_RESPONDENT``, then Decipher's ``uuid``.
    Existing ``LQ_*`` columns are replaced, so running it again refreshes the flags.

    Args:
        frame: Survey data.
        result: Payload from :func:`app.services.live_quality.live_results`.

    Returns:
        The new frame and counts of what matched.
    """
    by_session: Dict[str, Dict[str, Any]] = {}
    by_respondent: Dict[str, Dict[str, Any]] = {}
    for row in result.get("respondents") or []:
        if _key(row.get("session_id")):
            by_session[_key(row.get("session_id"))] = row
        key = _key(row.get("respondent_id"))
        # A respondent who reopened the survey has several sessions: use the one that
        # was checked, then the latest, never an abandoned earlier one.
        if key and (key not in by_respondent or _preference(row) > _preference(by_respondent[key])):
            by_respondent[key] = row
    sessions = _column(frame, SESSION_COLUMN)
    respondents = _column(frame, RESPONDENT_COLUMN)
    uuids = _column(frame, UUID_COLUMN)
    records = []
    tracked = 0
    for session, respondent, uuid in zip(sessions, respondents, uuids):
        session, respondent, uuid = _key(session), _key(respondent), _key(uuid)
        tracked += bool(session or respondent or uuid)
        records.append(_values(by_session.get(session) or by_respondent.get(respondent) or by_respondent.get(uuid)))
    added = pd.DataFrame(records, index=frame.index, columns=[entry["name"] for entry in quality_variables()])
    kept = frame[[name for name in frame.columns if not str(name).upper().startswith(PREFIX)]]
    merged = pd.concat([kept, added], axis=1)
    for entry in quality_variables():
        if entry["is_text"]:
            merged[entry["name"]] = merged[entry["name"]].fillna("").astype(str)
    matched = int(added["LQ_MATCHED"].sum())
    report = {
        "survey_id": result.get("survey_id"),
        "records": int(len(frame)),
        "tracked": tracked,
        "matched": matched,
        "unmatched": tracked - matched,
        "flagged": int((added["LQ_NFLAGS"].fillna(0) > 0).sum()),
        "bots": int((added["LQ_VERDICT"] == 2).sum()),
        "match_columns": match_columns(frame),
        "variables": [entry["name"] for entry in quality_variables()],
    }
    return merged, report


def file_format(filename: str) -> str:
    """``sav``, ``csv`` or ``xlsx`` from the file name.

    Raises:
        MergeError: Any other kind of file.
    """
    suffix = Path(filename or "").suffix.lower()
    if suffix not in FORMATS:
        raise MergeError("Upload the survey data as an SPSS (.sav), CSV (.csv) or Excel (.xlsx) file.")
    return FORMATS[suffix]


def read_data(content: bytes, kind: str) -> Tuple[pd.DataFrame, Any]:
    """Read a data file into a frame, keeping SPSS metadata to write back.

    CSV and Excel cells are read as text so ids and codes come back exactly as written.

    Raises:
        MergeError: The file could not be read.
    """
    try:
        if kind == "csv":
            return pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding="utf-8-sig"), None
        if kind == "xlsx":
            return pd.read_excel(io.BytesIO(content), dtype=str, keep_default_na=False, engine="openpyxl"), None
        import pyreadstat

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.sav")
            with open(path, "wb") as handle:
                handle.write(content)
            frame, meta = pyreadstat.read_sav(path, apply_value_formats=False)
        return frame, meta
    except Exception as exc:  # noqa: BLE001 - any reader error means an unreadable file
        raise MergeError(f"The file could not be read as {kind.upper()} ({exc.__class__.__name__}).") from None


def write_data(frame: pd.DataFrame, kind: str, meta: Any = None) -> bytes:
    """Write the merged frame back in the uploaded format, with labels for the LQ_ variables in SPSS."""
    if kind == "csv":
        return frame.to_csv(index=False).encode("utf-8-sig")
    if kind == "xlsx":
        buffer = io.BytesIO()
        frame.to_excel(buffer, index=False, engine="openpyxl")
        return buffer.getvalue()
    import pyreadstat

    entries = {entry["name"]: entry for entry in quality_variables()}
    column_names = [str(name) for name in frame.columns]
    original_labels = dict(zip(meta.column_names, meta.column_labels)) if meta is not None else {}
    labels = [
        entries[name]["label"] if name in entries else (original_labels.get(name) or "")
        for name in column_names
    ]
    value_labels = {
        name: labels_
        for name, labels_ in (getattr(meta, "variable_value_labels", None) or {}).items()
        if name in column_names
    }
    measures = {
        name: level
        for name, level in (getattr(meta, "variable_measure", None) or {}).items()
        if name in column_names and level in {"nominal", "ordinal", "scale"}
    }
    widths = {
        name: width
        for name, width in (getattr(meta, "variable_display_width", None) or {}).items()
        if name in column_names
    }
    for name, entry in entries.items():
        if entry["value_labels"]:
            value_labels[name] = {float(code): text for code, text in entry["value_labels"].items()}
        measures[name] = entry["measurement"]
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "merged.sav")
        pyreadstat.write_sav(
            frame,
            path,
            column_labels=labels,
            variable_value_labels=value_labels,
            variable_measure=measures,
            variable_display_width=widths or None,
        )
        with open(path, "rb") as handle:
            return handle.read()


def merged_filename(filename: str) -> str:
    """``<name>_quality.<ext>`` for the download."""
    path = Path(filename or "data.csv")
    stem = path.stem.removesuffix("_quality") or "data"
    safe = "".join(char if char.isalnum() or char in "-_." else "_" for char in stem)[:100] or "data"
    return f"{safe}_quality{path.suffix.lower()}"


def merge_file(content: bytes, filename: str, result: Dict[str, Any]) -> Tuple[bytes, str, str, Dict[str, Any]]:
    """Add the LQ_ variables to an uploaded data file.

    Args:
        content: File bytes.
        filename: Uploaded file name (decides the format).
        result: Live quality payload for the survey.

    Returns:
        The new file bytes, its download name, its media type, and the merge report.

    Raises:
        MergeError: Unsupported or unreadable file, or no id column to match on.
    """
    kind = file_format(filename)
    frame, meta = read_data(content, kind)
    if not match_columns(frame):
        raise MergeError(
            "The file has no QOS_SESSION, QOS_RESPONDENT or uuid values, so there is nothing to match. "
            "Export the Decipher data of a tracked survey with those variables included."
        )
    merged, report = add_quality_columns(frame, result)
    payload = write_data(merged, kind, meta)
    report.update(
        merged_at=datetime.now(timezone.utc).isoformat(),
        message=(
            f"Added live quality flags for {report['matched']} of {report['tracked']} tracked records "
            f"({report['flagged']} flagged, {report['bots']} bots) as LQ_ variables."
            + (
                f" {report['unmatched']} tracked records were not found in the live quality results."
                if report["unmatched"]
                else ""
            )
        ),
    )
    return payload, merged_filename(filename), MEDIA_TYPES[kind], report
