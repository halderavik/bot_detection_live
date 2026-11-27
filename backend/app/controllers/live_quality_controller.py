"""
Live quality: per-survey quality rules, live bot and fraud results, exports, and
adding the results to a survey data file.

The survey id travels as a query parameter because survey ids are often titles
with spaces and punctuation.

GET    /quality/surveys                  every survey, tracked ones first
GET    /quality/results?survey_id=...    dashboard payload under the survey's rules
GET    /quality/export?survey_id=...     the same rows as CSV
GET    /quality/report?survey_id=...     report: results for a period, survey details, rules in force
GET    /quality/rules?survey_id=...      rules in force, defaults, and editor labels
PUT    /quality/rules?survey_id=...      save the survey's rules
DELETE /quality/rules?survey_id=...      back to the defaults
POST   /quality/merge?survey_id=...      data file in (sav, csv, xlsx), same file out with LQ_ variables
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import live_quality, quality_merge, quality_rules
from app.services.quality_rules import QualityRules
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

MAX_DATA_BYTES = 50 * 1024 * 1024
REPORT_HEADER = "X-Quality-Report"

router = APIRouter(prefix="/quality", tags=["live quality"])


def _survey(survey_id: str) -> str:
    survey_id = (survey_id or "").strip()
    if not survey_id or len(survey_id) > 255:
        raise HTTPException(status_code=422, detail="Choose a survey id (1 to 255 characters).")
    return survey_id


def _safe_name(survey_id: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in survey_id)[:80] or "survey"


async def _results(db: AsyncSession, survey_id: str) -> dict:
    rules = await quality_rules.get_rules(db, survey_id)
    try:
        return await live_quality.live_results(db, survey_id, rules)
    except Exception as exc:  # noqa: BLE001 - report failures are logged and shown as one message
        logger.error(f"Live quality results failed for {survey_id!r}: {exc}")
        raise HTTPException(status_code=500, detail="The live quality results could not be built for this survey.")


@router.get("/surveys")
async def list_quality_surveys(db: AsyncSession = Depends(get_db)):
    """Every survey with sessions, plus tracked surveys nobody has started yet."""
    try:
        return {"surveys": await live_quality.list_surveys(db)}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Listing live quality surveys failed: {exc}")
        raise HTTPException(status_code=500, detail="The survey list could not be loaded.")


@router.get("/results")
async def get_quality_results(survey_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Totals, charts, flag counts and one row per session, under the survey's rules."""
    return await _results(db, _survey(survey_id))


@router.get("/export")
async def export_quality_results(survey_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """One row per respondent as CSV, under the survey's rules."""
    survey_id = _survey(survey_id)
    result = await _results(db, survey_id)
    return Response(
        live_quality.results_csv(result),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="quality-{_safe_name(survey_id)}.csv"'},
    )


@router.get("/report")
async def get_quality_report(
    survey_id: str = Query(...),
    date_from: Optional[datetime] = Query(None, description="First start time to include (ISO 8601, UTC when no zone)"),
    date_to: Optional[datetime] = Query(None, description="Last start time to include (ISO 8601, UTC when no zone)"),
    db: AsyncSession = Depends(get_db),
):
    """Everything a report needs: live results for the period, the survey's details, and its rules."""
    survey_id = _survey(survey_id)
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="The start of the period is after its end.")
    rules = await quality_rules.get_rules(db, survey_id)
    result = live_quality.for_period(await _results(db, survey_id), date_from, date_to)
    return {
        **result,
        "survey": await live_quality.survey_details(db, survey_id),
        "rules_state": quality_rules.rules_state(rules),
    }


@router.get("/rules")
async def get_survey_rules(survey_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """The survey's rules (defaults until saved), the defaults, what changed, and labels."""
    return quality_rules.rules_state(await quality_rules.get_rules(db, _survey(survey_id)))


@router.put("/rules")
async def put_survey_rules(body: QualityRules, survey_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Save the survey's complete rules."""
    return quality_rules.rules_state(await quality_rules.save_rules(db, _survey(survey_id), body))


@router.delete("/rules")
async def reset_survey_rules(survey_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Restore the default rules for the survey."""
    return quality_rules.rules_state(await quality_rules.save_rules(db, _survey(survey_id), None))


@router.post("/merge")
async def merge_quality_into_file(
    survey_id: str = Query(...),
    file: UploadFile = File(..., description="Survey data: SPSS (.sav), CSV (.csv) or Excel (.xlsx)"),
    db: AsyncSession = Depends(get_db),
):
    """Return the uploaded data file with the LQ_ variables added.

    The merge report (matched, tracked, flagged, bots, message) is in the
    ``X-Quality-Report`` header as JSON.
    """
    survey_id = _survey(survey_id)
    try:
        quality_merge.file_format(file.filename or "")
    except quality_merge.MergeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    content = await file.read(MAX_DATA_BYTES + 1)
    if len(content) > MAX_DATA_BYTES:
        raise HTTPException(status_code=413, detail="The data file is over 50 MB.")
    if not content:
        raise HTTPException(status_code=422, detail="The data file is empty.")
    result = await _results(db, survey_id)
    if not result.get("respondents"):
        raise HTTPException(
            status_code=422,
            detail=f"There are no live quality results for '{survey_id}' yet, so there is nothing to add.",
        )
    try:
        payload, filename, media_type, report = quality_merge.merge_file(content, file.filename or "", result)
    except quality_merge.MergeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return Response(
        payload,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            REPORT_HEADER: json.dumps(report, ensure_ascii=True),
        },
    )
