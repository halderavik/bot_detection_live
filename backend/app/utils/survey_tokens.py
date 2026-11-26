"""
Signed survey tokens.

The token is an HMAC of the survey id with TRACKING_TOKEN_SECRET. This service
writes it into the tracker when it adds tracking to a survey XML; another survey
builder given the same secret can issue matching tokens. It proves the
tracker was issued for that survey; it is not a secret from respondents.
"""

import hashlib
import hmac
from typing import Optional

from app.config import settings


def survey_token(survey_id: str, secret: Optional[str] = None) -> Optional[str]:
    """Token for a survey id, or None when tokens are not configured."""
    key = secret if secret is not None else settings.TRACKING_TOKEN_SECRET
    if not key:
        return None
    digest = hmac.new(key.encode("utf-8"), survey_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:32]


def token_valid(survey_id: str, token: Optional[str]) -> bool:
    """True when ``token`` was issued for ``survey_id``."""
    expected = survey_token(survey_id)
    return bool(expected and token and hmac.compare_digest(expected, token))
