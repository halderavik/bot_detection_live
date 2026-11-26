"""
Settings page API.

GET  /settings          every editable setting (secret values are never returned)
POST /settings/check    check an admin token without changing anything
PUT  /settings          save changes; needs the X-Admin-Token header to match ADMIN_TOKEN

Body of PUT: ``{"changes": {"DECIPHER_API_KEY": "...", "TRACKER_API_BASE": null}}``.
A value overrides the environment variable; ``null`` goes back to the environment value.
"""

import hmac
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services import runtime_settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsChanges(BaseModel):
    changes: Dict[str, Optional[Any]]


def require_admin(x_admin_token: Optional[str] = Header(None)) -> None:
    """Refuse unless ADMIN_TOKEN is set and the request carries it."""
    expected = settings.ADMIN_TOKEN
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="Settings are read-only: set ADMIN_TOKEN on the service to change them here.",
        )
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="The admin token is not correct.")


@router.get("")
async def get_settings():
    """Every editable setting with its source; secrets only say whether they are set."""
    return runtime_settings.state()


@router.post("/check", dependencies=[Depends(require_admin)])
async def check_admin_token():
    """200 when the admin token is correct."""
    return {"ok": True}


@router.put("", dependencies=[Depends(require_admin)])
async def save_settings(body: SettingsChanges, db: AsyncSession = Depends(get_db)):
    """Save changes and apply them at once on this instance (others within 30 seconds)."""
    try:
        await runtime_settings.save(db, body.changes)
    except runtime_settings.SettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    logger.info(f"Settings changed from the dashboard: {', '.join(sorted(body.changes))}")
    return runtime_settings.state()
