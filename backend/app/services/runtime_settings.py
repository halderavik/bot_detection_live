"""
Settings that can be changed from the dashboard's Settings page while the service runs.

Each editable setting has an environment variable of the same name. A value saved on
the page is stored in ``app_settings`` and overrides the environment; clearing it goes
back to the environment value. Saved values are applied to the shared ``settings``
object, so code that reads ``settings.X`` at the time of use sees them at once, and
every instance re-reads the table every ``REFRESH_SECONDS`` so all instances agree.

Secrets (API keys, the tracking secret) are encrypted at rest with a key derived from
SECRET_KEY and are never sent back to the browser: the page only learns whether they
are set and where the value comes from.
"""

import asyncio
import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.app_setting import AppSetting
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

REFRESH_SECONDS = 30


class SettingsError(ValueError):
    """A value was refused; the message says why."""


@dataclass(frozen=True)
class Spec:
    key: str
    label: str
    group: str
    kind: str  # "secret", "text", "url", "number"
    help: str
    placeholder: str = ""
    minimum: Optional[float] = None
    maximum: Optional[float] = None


def _https_api_url(value: str, allow_empty: bool = True) -> str:
    if not value:
        return value
    if not re.match(r"^https://[^\s/]+(/[^\s]*)?$", value) and not re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?(/[^\s]*)?$", value):
        raise SettingsError("Use an https:// address (http:// only for localhost).")
    return value.rstrip("/")


SPECS: List[Spec] = [
    Spec(
        "DECIPHER_API_KEY", "Decipher API key", "Decipher", "secret",
        "REST API key used for Upload to Decipher. Sent only to Decipher.",
    ),
    Spec(
        "DECIPHER_API_BASE", "Decipher API address", "Decipher", "url",
        "Your Decipher server's API, ending in /api/v1.", "https://selfserve.decipherinc.com/api/v1",
    ),
    Spec(
        "DECIPHER_COMPANY", "Decipher company", "Decipher", "text",
        "Research Hub company id new surveys are created under.", "self",
    ),
    Spec(
        "QUALTRICS_API_TOKEN", "Qualtrics API token", "Qualtrics", "secret",
        "Used to read Qualtrics responses and check webhook signatures.",
    ),
    Spec(
        "OPENAI_API_KEY", "OpenAI API key", "Open-end scoring", "secret",
        "Scores open-ended answers. Without it, open-ended answers are stored as not checked "
        "(no quality score, never counted as acceptable).",
    ),
    Spec(
        "OPENAI_MODEL", "OpenAI model", "Open-end scoring", "text",
        "Model used to score open-ended answers.", "gpt-4o-mini",
    ),
    Spec(
        "OPENAI_FIX_MODEL", "Fix with AI model", "Open-end scoring", "text",
        "Model that repairs survey XML on Add tracking (Fix with AI). Empty uses gpt-4o, which applied every "
        "fix and instruction in testing; smaller models such as gpt-4o-mini sometimes ignore instructions.",
        "gpt-4o",
    ),
    Spec(
        "TRACKER_API_BASE", "Tracker API address", "Survey tracking", "url",
        "Public address of this service the survey tracker calls, ending in /api/v1. "
        "Empty means the address the upload came in on.",
        "https://bot-backend-....run.app/api/v1",
    ),
    Spec(
        "TRACKING_TOKEN_SECRET", "Tracking signing secret", "Survey tracking", "secret",
        "Signs trackers so outsiders who have never seen a survey cannot send fake sessions under its name "
        "(anyone who opens the survey page can read its token). Set it once: changing it later makes the "
        "tokens in surveys already live invalid, and their respondents are refused until each survey is "
        "tracked and uploaded again.",
    ),
    Spec(
        "DETECTION_THRESHOLD", "Bot threshold", "Detection", "number",
        "Bot probability (0 to 1) at or above which a session is a bot. Applies to new analyses; "
        "per-survey dashboard rules are set on Live Quality.",
        "0.7", 0.3, 0.99,
    ),
]
SPEC_BY_KEY: Dict[str, Spec] = {spec.key: spec for spec in SPECS}

# Environment values, captured before any override is applied.
_ENV: Dict[str, Any] = {spec.key: getattr(settings, spec.key) for spec in SPECS}
# Called after values change (for example, the OpenAI client is rebuilt with a new key).
_HOOKS: List[Callable[[], None]] = []
# Keys currently overridden from the database.
_ACTIVE: Dict[str, bool] = {}


def on_change(hook: Callable[[], None]) -> None:
    """Register a function to call after settings change."""
    _HOOKS.append(hook)


def _fernet() -> Fernet:
    digest = hashlib.sha256(f"app-settings:{settings.SECRET_KEY}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> Optional[str]:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def clean(key: str, value: Any) -> Any:
    """Validate one value for ``key`` and return it in the type the service uses.

    Raises:
        SettingsError: Unknown key or a value that is not allowed.
    """
    spec = SPEC_BY_KEY.get(key)
    if spec is None:
        raise SettingsError(f"{key} can't be changed here.")
    if spec.kind == "number":
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise SettingsError(f"{spec.label} must be a number.") from None
        if (spec.minimum is not None and number < spec.minimum) or (spec.maximum is not None and number > spec.maximum):
            raise SettingsError(f"{spec.label} must be between {spec.minimum} and {spec.maximum}.")
        return round(number, 4)
    text = "" if value is None else str(value).strip().replace("\r", "").replace("\n", "")
    if len(text) > 2000:
        raise SettingsError(f"{spec.label} is too long.")
    if spec.kind == "url":
        try:
            return _https_api_url(text)
        except SettingsError as exc:
            raise SettingsError(f"{spec.label}: {exc}") from None
    if spec.key == "DECIPHER_COMPANY" and text and not re.match(r"^[A-Za-z0-9._-]+$", text):
        raise SettingsError("Decipher company may contain only letters, numbers, dots, hyphens and underscores.")
    if spec.kind == "secret" and text and len(text) < 8:
        raise SettingsError(f"{spec.label} looks too short.")
    return text or None


def _apply(values: Dict[str, Any]) -> None:
    """Set overrides on ``settings``; keys without an override go back to the environment."""
    changed = False
    for spec in SPECS:
        new = values[spec.key] if spec.key in values else _ENV[spec.key]
        if getattr(settings, spec.key) != new:
            setattr(settings, spec.key, new)
            changed = True
        _ACTIVE[spec.key] = spec.key in values
    if changed:
        for hook in _HOOKS:
            try:
                hook()
            except Exception as exc:  # noqa: BLE001 - one failing hook must not stop the rest
                logger.error(f"Settings change hook failed: {exc}")


async def load(db: AsyncSession) -> None:
    """Read saved overrides and apply them."""
    rows = (await db.execute(select(AppSetting))).scalars().all()
    values: Dict[str, Any] = {}
    for row in rows:
        if row.key not in SPEC_BY_KEY:
            continue
        raw = _decrypt(row.value) if row.is_secret else row.value
        if raw is None:
            logger.warning(f"Saved {row.key} could not be decrypted (SECRET_KEY changed?); using the environment value.")
            continue
        try:
            values[row.key] = clean(row.key, raw)
        except SettingsError as exc:
            logger.warning(f"Saved {row.key} ignored: {exc}")
    _apply(values)


async def save(db: AsyncSession, changes: Dict[str, Any]) -> None:
    """Save changes: a value overrides the environment, ``None`` clears the override.

    Raises:
        SettingsError: Any value is refused (nothing is saved then).
    """
    cleaned: Dict[str, Any] = {}
    for key, value in changes.items():
        cleaned[key] = None if value is None else clean(key, value)
    for key, value in cleaned.items():
        row = await db.get(AppSetting, key)
        if value is None:
            if row is not None:
                await db.delete(row)
            continue
        spec = SPEC_BY_KEY[key]
        stored = _encrypt(str(value)) if spec.kind == "secret" else str(value)
        if row is None:
            db.add(AppSetting(key=key, value=stored, is_secret=spec.kind == "secret"))
        else:
            row.value, row.is_secret = stored, spec.kind == "secret"
    await db.commit()
    await load(db)


def state() -> Dict[str, Any]:
    """Every editable setting: label, group, help, where its value comes from, and the value
    itself for settings that are not secret."""
    items = []
    for spec in SPECS:
        current = getattr(settings, spec.key)
        source = "saved" if _ACTIVE.get(spec.key) else ("environment" if _ENV[spec.key] not in (None, "") else "not set")
        items.append({
            "key": spec.key,
            "label": spec.label,
            "group": spec.group,
            "kind": spec.kind,
            "help": spec.help,
            "placeholder": spec.placeholder,
            "minimum": spec.minimum,
            "maximum": spec.maximum,
            "is_set": current not in (None, ""),
            "source": source,
            "value": None if spec.kind == "secret" else current,
            "environment_value": None if spec.kind == "secret" else _ENV[spec.key],
        })
    return {"settings": items, "editable": bool(settings.ADMIN_TOKEN), "refresh_seconds": REFRESH_SECONDS}


async def keep_fresh(session_factory) -> None:
    """Re-read saved settings every REFRESH_SECONDS, so every instance sees changes."""
    while True:
        try:
            async with session_factory() as db:
                await load(db)
        except Exception as exc:  # noqa: BLE001 - keep trying; a missing table just means no overrides yet
            logger.debug(f"Settings refresh skipped: {exc}")
        await asyncio.sleep(REFRESH_SECONDS)
