"""
Add live tracking to an uploaded Decipher survey XML.

POST /api/v1/tracking/decipher takes the survey XML (multipart field ``file``),
checks that it is a Decipher survey, creates or updates the survey's record,
signs the survey id, and returns the same survey with the tracker script, the
hidden ``QOS_*`` results page, and the chosen options added, ready to import
into Decipher.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ProtectedSurvey, Session, TrackedSurvey
from app.services.decipher_tracking import (
    BOT_SIGNALS,
    DEFAULT_PRIVACY_TEXT,
    FIELD_LABELS,
    NotASurveyError,
    TrackingOptions,
    decipher_settings_problems,
    check_api_base,
    check_survey_id,
    has_tracking,
    read_survey,
    results_page,
    style_block,
    track_survey,
    tracked_survey_id,
    tracker_javascript,
    tracker_script,
)
from app.services.decipher_ai_fix import FixUnavailable, fix_with_ai
from app.services.decipher_errors import explain as explain_decipher_errors
from app.services.decipher_xml_check import check_survey_xml
from app.services.decipher_upload import (
    DecipherNotConfigured,
    DecipherUploader,
    DecipherUploadError,
    clean_path,
    is_configured,
)
from app.utils.logger import setup_logger
from app.utils.survey_tokens import survey_token

logger = setup_logger(__name__)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/tracking", tags=["survey tracking"])


def tracker_api_base(request: Request) -> str:
    """The API base URL respondents' browsers will call.

    ``TRACKER_API_BASE`` when set; otherwise this request's own origin (honouring
    the proxy's forwarded scheme and host) plus ``/api/v1``.
    """
    if settings.TRACKER_API_BASE:
        return settings.TRACKER_API_BASE.rstrip("/")
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host.split(',')[0].strip()}{settings.API_V1_STR}"


def _tracked_filename(filename: str) -> str:
    stem = Path(filename or "survey.xml").stem or "survey"
    stem = re.sub(r"_tracked$", "", stem)
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_") or "survey"
    return f"{stem}_tracked.xml"


@router.get("/decipher/options")
async def tracking_options():
    """Defaults the upload screen shows: bot signals and the privacy notice."""
    return {
        "signals": [{"code": code, "label": label} for code, label in BOT_SIGNALS.items()],
        "default_privacy_text": DEFAULT_PRIVACY_TEXT,
        "default_after_page": 2,
        "signed": bool(settings.TRACKING_TOKEN_SECRET),
        "decipher_upload": is_configured(settings.DECIPHER_API_KEY),
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
    }


def _script_for(
    request: Request, survey_id: str, platform: str, target: Optional[str] = None
) -> tuple[str, str, str, bool]:
    """Tracker script, checked survey id, API base, and whether it is signed.

    ``target`` is the API the code should call when it is not this service (for
    example the production service while the dashboard runs locally). Only this
    service's own secret can sign, so code for another service is unsigned.
    """
    try:
        clean_id = check_survey_id(survey_id)
        own_base = check_api_base(tracker_api_base(request))
        api_base = check_api_base(target) if target else own_base
        token = (survey_token(clean_id) or "") if api_base == own_base else ""
        # Same rules as an upload without the in-survey check, so pasted XML matches it.
        rules = {"terminate": False, "signals": list(BOT_SIGNALS)}
        script = tracker_script(clean_id, api_base, token, rules, platform)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return script, clean_id, api_base, bool(token)


@router.get("/decipher/snippet")
async def decipher_snippet(request: Request, survey_id: str, api_base: Optional[str] = None):
    """The two XML blocks to paste into a Decipher survey by hand.

    ``style`` goes right after ``</samplesources>`` (or right after the opening
    ``<survey ...>`` tag); ``results_page`` goes right before ``</survey>``. They are
    exactly what the automatic upload adds without the privacy notice and the
    in-survey bot check. ``api_base`` (https, ending in /api/v1) makes the tracker
    call another service, such as production, instead of this one.
    """
    script, clean_id, api_base, signed = _script_for(request, survey_id, "decipher", api_base)
    return {
        "survey_id": clean_id,
        "api_base": api_base,
        "signed": signed,
        "style": style_block(script, clean_id).lstrip(),
        "results_page": results_page(),
        "fields": list(FIELD_LABELS),
    }


@router.get("/script.js")
async def tracker_file(request: Request, survey_id: str, platform: str = "web"):
    """The tracker as a JavaScript file for Qualtrics or any other website.

    Load it with ``<script src=".../tracking/script.js?survey_id=...&platform=web">``.
    """
    if platform not in ("qualtrics", "web"):
        raise HTTPException(status_code=422, detail="platform must be qualtrics or web.")
    script, _, _, _ = _script_for(request, survey_id, platform)
    return Response(
        tracker_javascript(script),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/decipher")
async def add_decipher_tracking(
    request: Request,
    file: UploadFile = File(..., description="Decipher survey XML (.xml or .txt)"),
    survey_id: Optional[str] = Form(None, description="Tracking survey id; default from the survey title"),
    terminate: bool = Form(False, description="End the survey on a clear bot signal"),
    after_page: int = Form(2, description="Page whose submit runs the in-survey check"),
    signals: Optional[str] = Form(None, description="Comma-separated bot signals that end the survey"),
    privacy_notice: bool = Form(True, description="Show a short privacy notice on the first page"),
    privacy_text: Optional[str] = Form(None, description="Privacy notice text; default wording when empty"),
    format: str = "json",
    db: AsyncSession = Depends(get_db),
):
    """Return the uploaded Decipher survey with live tracking added once.

    ``format=xml`` returns the tracked file itself; the default JSON also says what
    was added and where the survey's dashboard is.
    """
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 5 MB.")
    if file.filename and Path(file.filename).suffix.lower() not in {".xml", ".txt", ""}:
        raise HTTPException(status_code=400, detail="Upload the survey as an .xml file (or .txt holding the XML).")

    try:
        api_base = check_api_base(tracker_api_base(request))
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=f"{error} Set TRACKER_API_BASE to the service's public https URL ending in /api/v1.",
        ) from error

    codes = [code.strip() for code in (signals or "").split(",") if code.strip()] or list(BOT_SIGNALS)
    unknown = [code for code in codes if code not in BOT_SIGNALS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown bot signal(s): {', '.join(unknown)}")
    options = TrackingOptions(
        terminate=terminate,
        after_page=after_page,
        signals=codes,
        privacy_text=(privacy_text or DEFAULT_PRIVACY_TEXT) if privacy_notice else "",
    )
    try:
        result = track_survey(
            data,
            api_base,
            lambda sid: survey_token(sid) or "",
            survey_id=survey_id,
            filename=file.filename or "",
            options=options,
        )
    except NotASurveyError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    signed = bool(settings.TRACKING_TOKEN_SECRET)
    warnings = list(result.warnings)
    if api_base.startswith("http://"):
        warnings.append(
            f"The tracker calls {api_base}, which only works on this computer. Set TRACKER_API_BASE "
            "to the service's public https URL before importing the survey into Decipher."
        )

    existing_sessions = 0
    new_record = True
    decipher_path = None
    try:
        record = await db.get(TrackedSurvey, result.survey_id)
        new_record = record is None
        if record is None:
            record = TrackedSurvey(survey_id=result.survey_id, uploads=0)
            db.add(record)
        record.title = result.survey_id
        record.source_filename = (file.filename or "")[:255]
        record.platform_id = "decipher"
        record.signed = signed
        record.terminate = terminate
        record.privacy_notice = result.privacy_notice
        record.uploads = (record.uploads or 0) + 1
        decipher_path = record.decipher_path
        await db.commit()
        existing_sessions = (
            await db.execute(select(func.count()).select_from(Session).where(Session.survey_id == result.survey_id))
        ).scalar() or 0
    except Exception as error:  # noqa: BLE001 - the tracked file does not depend on the record
        await db.rollback()
        logger.error(f"Could not save the tracked survey record for {result.survey_id}: {error}")
        warnings.append("The survey record could not be saved; the tracked file is still complete.")

    filename = _tracked_filename(file.filename or "")
    if format == "xml":
        return Response(
            content=result.xml.encode("utf-8"),
            media_type="application/xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    added = [
        "Tracker script, as a respview.client.js style with mode=\"after\" (runs on every page, "
        "alongside the survey's own scripts)",
        f"Hidden results page with {len(FIELD_LABELS)} quality variables for the data export "
        f"({', '.join(FIELD_LABELS)})",
        "Respondent id: Decipher's uuid, so results match the uuid column in Decipher's data exports (SPSS, Excel, CSV)",
    ]
    if result.privacy_notice:
        added.append("Privacy notice at the top of the first page (QOS_privacy)")
    if result.early_check_page:
        added.append(result.early_check_note)

    return {
        "survey_id": result.survey_id,
        "filename": filename,
        "xml": result.xml,
        "replaced_existing_tracking": result.replaced,
        "new_survey_record": new_record,
        "existing_sessions": existing_sessions,
        "signed": signed,
        "api_base": api_base,
        "added": added,
        "survey": {
            "questions": result.questions,
            "pages": result.pages,
            "loops": result.loops,
            "blocks": result.blocks,
        },
        "options": {
            "terminate": terminate,
            "after_page": after_page if terminate else None,
            "signals": codes if terminate else [],
            "privacy_notice": result.privacy_notice,
        },
        "early_check": {
            "requested": terminate,
            "page": result.early_check_page,
            "note": result.early_check_note,
        },
        "hidden_fields": list(FIELD_LABELS),
        "warnings": warnings,
        "dashboard_path": f"/surveys/{result.survey_id}",
        "decipher_upload": {
            "configured": is_configured(settings.DECIPHER_API_KEY),
            "last_path": decipher_path,
        },
    }


class DecipherUploadRequest(BaseModel):
    """A tracked survey XML to send to Decipher."""

    xml: str = Field(..., max_length=MAX_UPLOAD_BYTES)
    survey_id: str = Field(..., max_length=255)
    survey_path: Optional[str] = Field(None, max_length=255, description="Existing Decipher survey path to update")
    create_new: bool = Field(False, description="Create a new Decipher survey even if one was used before")


@router.post("/decipher/upload")
async def upload_to_decipher(body: DecipherUploadRequest, db: AsyncSession = Depends(get_db)):
    """Send tracked survey XML to Decipher.

    The target is, in order: a new survey when ``create_new``; ``survey_path``
    when given; the survey this id was last uploaded to; otherwise a new survey.
    Decipher validates the file before saving it and never overwrites a live survey.
    """
    try:
        uploader = DecipherUploader(
            settings.DECIPHER_API_KEY, settings.DECIPHER_API_BASE, settings.DECIPHER_COMPANY
        )
    except DecipherNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    try:
        xml, root = read_survey(body.xml.encode("utf-8"))
    except NotASurveyError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Reason: checked before anything is sent, so a file Decipher would refuse never
    # leaves an empty new survey behind in the Decipher account.
    problems = decipher_settings_problems(root)
    if problems:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Decipher would refuse this file, so nothing was sent to Decipher. " + problems[0],
                "errors": problems,
                "explained": explain_decipher_errors(problems),
                "file_problem": True,
                "survey_path": None,
                "survey_url": None,
            },
        )
    if not has_tracking(xml):
        raise HTTPException(status_code=422, detail="This survey has no tracking yet. Add tracking first, then upload.")
    if tracked_survey_id(xml) != body.survey_id:
        raise HTTPException(
            status_code=422,
            detail=f"The XML is tracked as \"{tracked_survey_id(xml)}\", not \"{body.survey_id}\". Add tracking again.",
        )

    record = await db.get(TrackedSurvey, body.survey_id)
    if body.create_new:
        target = None
    elif body.survey_path and body.survey_path.strip():
        target = clean_path(body.survey_path)
        if target is None:
            raise HTTPException(
                status_code=400,
                detail="That is not a Decipher survey path. Use the form selfserve/123/456789, or paste the survey link.",
            )
    else:
        target = record.decipher_path if record else None

    async def remember(path: Optional[str]) -> None:
        if not path:
            return
        try:
            row = record or TrackedSurvey(survey_id=body.survey_id, title=body.survey_id, uploads=0)
            row.decipher_path = path
            db.add(row)
            await db.commit()
        except Exception as error:  # noqa: BLE001 - the upload itself already happened
            await db.rollback()
            logger.error(f"Could not save the Decipher path for {body.survey_id}: {error}")

    try:
        result = await uploader.upload(xml, (record.title if record else None) or body.survey_id, target)
    except DecipherUploadError as error:
        # A survey created before the XML was refused is kept, so a retry updates it.
        await remember(error.survey_path)
        raise HTTPException(
            # Reason: 400/404 are about this file or path; anything else is Decipher or the key.
            status_code=400 if error.status in (400, 404) else 502,
            detail={
                "message": error.message,
                "errors": error.errors,
                # Plain-words explanation of each Decipher message, and whether the file itself is the problem
                # (Decipher refused it) rather than the key, the path or Decipher being unreachable.
                "explained": explain_decipher_errors(error.errors or ([error.message] if error.status == 400 else []), xml),
                "file_problem": error.status == 400,
                "survey_path": error.survey_path,
                "survey_url": error.survey_url,
            },
        ) from error
    await remember(result.survey_path)
    await _protect_if_signed(db, body.survey_id, xml)
    logger.info(f"Uploaded tracked survey {body.survey_id} to Decipher at {result.survey_path}")
    return {
        "survey_id": body.survey_id,
        "survey_path": result.survey_path,
        "survey_url": result.survey_url,
        "created": result.created,
        "message": result.message,
        "layouts_updated": result.layouts_updated,
        "warnings": result.warnings,
    }


async def _protect_if_signed(db: AsyncSession, survey_id: str, xml: str) -> None:
    """Require signed sessions for this survey once a signed tracker is live in Decipher.

    Before this, a survey became protected only when its first signed respondent
    arrived, so fake unsigned sessions were accepted until then. Protecting when the
    tracked file is created would refuse real respondents of a survey still running
    an older, unsigned tracker; a successful upload is when the signed one goes live.
    """
    token = survey_token(survey_id)
    if not token or token not in xml:
        return
    try:
        if await db.get(ProtectedSurvey, survey_id) is None:
            db.add(ProtectedSurvey(survey_id=survey_id))
            await db.commit()
    except Exception as error:  # noqa: BLE001 - the upload itself already happened
        await db.rollback()
        logger.warning(f"Could not mark {survey_id} as requiring signed sessions: {error}")


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The file is larger than 5 MB.")
    if file.filename and Path(file.filename).suffix.lower() not in {".xml", ".txt", ""}:
        raise HTTPException(status_code=400, detail="Upload the survey as an .xml file (or .txt holding the XML).")
    return data


@router.post("/decipher/check")
async def check_decipher_xml(file: UploadFile = File(..., description="Decipher survey XML (.xml or .txt)")):
    """Check a survey XML before tracking is added and explain each problem.

    Errors (``severity: "error"``) must be fixed before tracking is added; warnings
    are things Decipher may refuse in some setups. Each issue says what is wrong,
    how to fix it, the line, and whether Fix with AI can repair it.
    """
    data = await _read_upload(file)
    report = check_survey_xml(data).to_dict()
    report["filename"] = file.filename or "survey.xml"
    report["ai_available"] = bool(settings.OPENAI_API_KEY)
    return report


def _fixed_filename(filename: str) -> str:
    stem = Path(filename or "survey.xml").stem or "survey"
    stem = re.sub(r"_(tracked|fixed)$", "", stem)
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_") or "survey"
    return f"{stem}_fixed.xml"


@router.post("/decipher/fix")
async def fix_decipher_xml(
    file: UploadFile = File(..., description="Decipher survey XML (.xml or .txt)"),
    instructions: Optional[str] = Form(None, description="How to fix it, or missing information (optional)"),
    decipher_errors: Optional[str] = Form(
        None, description="JSON list of Decipher's refusal messages from an upload, so the fix addresses them"
    ),
):
    """Repair a survey XML with AI ("Fix with AI") and check the result again.

    The model returns exact edits that are applied only where they match one place
    in the file. The response has the fixed XML (without tracking), what changed,
    the assumptions made, what could not be fixed, and the new check report.
    """
    data = await _read_upload(file)
    errors: list = []
    if decipher_errors:
        try:
            parsed = json.loads(decipher_errors)
        except ValueError:
            parsed = [line for line in decipher_errors.splitlines()]
        errors = [str(item).strip()[:1000] for item in (parsed if isinstance(parsed, list) else [parsed]) if str(item).strip()][:30]
    try:
        result = await fix_with_ai(data, instructions or "", filename=file.filename or "", decipher_errors=errors)
    except FixUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except asyncio.TimeoutError as error:
        raise HTTPException(status_code=504, detail="The AI took too long to answer. Try again in a moment.") from error
    except Exception as error:  # noqa: BLE001 - provider errors (quota, network) reach the user as one message
        logger.error(f"Fix with AI failed: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not be reached or refused the request. Try again later, or fix the file by hand.",
        ) from error
    report = result.report.to_dict() if result.report else None
    return {
        "xml": result.xml,
        "filename": _fixed_filename(file.filename or "survey.xml"),
        "changed": result.applied > 0,
        "applied": result.applied,
        "changes": result.changes,
        "assumptions": result.assumptions,
        "cannot_fix": result.cannot_fix,
        "skipped": result.skipped,
        "rounds": result.rounds,
        "model": result.model,
        "report": report,
    }
