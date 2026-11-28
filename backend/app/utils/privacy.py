"""
Keep personal details out of what the service stores and sends to OpenAI.

Applied on arrival, so it also covers trackers already embedded in live surveys:
- page addresses and referrers lose their query string and fragment (panel ids,
  respondent ids, and tokens often travel there);
- text boxes that ask for contact or identity details (email, phone, name, address,
  postcode, date of birth) are registered as ``personal``: their answers are never
  stored or text-scored;
- email addresses and phone numbers inside other answers are masked.
"""
import re
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

PERSONAL_QUESTION_TYPE = "personal"
MASKED_EMAIL = "[email]"
MASKED_PHONE = "[phone]"

# Question wording that asks for contact or identity details. Kept specific so real
# open ends still get checked: a bare "name", "phone", or "email" would also match
# "Name three brands", "What do you like about your phone?", or "email marketing".
_PERSONAL_WORDING = re.compile(
    r"e-?mail address|your e-?mail\b|phone number|telephone|mobile number|cell number|contact number"
    r"|\b(?:first|last|full|given|family|sur|middle|maiden)\s?name\b|\byour name\b"
    r"|street address|mailing address|home address|postal address|your address|delivery address"
    r"|post\s?code|postal code|zip\s?code"
    r"|date of birth|birth\s?date|\bdob\b"
    r"|social security|\bssn\b|social insurance|passport number|driver'?s licen[cs]e",
    re.IGNORECASE,
)

# A whole email address.
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# A phone-like run: digits with spaces, dots, dashes, or brackets, optionally led by +.
_PHONE_RUN = re.compile(r"\+?\(?\d[\d\s().-]{6,}\d")
_PHONE_DIGITS = (9, 15)


def strip_url(url: Optional[str], limit: int = 2000) -> Optional[str]:
    """
    The address without its query string and fragment.

    Args:
        url: A page address or referrer, or None.
        limit: Longest result kept.

    Returns:
        str | None: scheme, host, and path only; None or "" unchanged. Anything that
        does not parse as an address is cut at the first ? or #.
    """
    if not url:
        return url
    try:
        parts = urlsplit(url)
        if parts.scheme and parts.netloc:
            return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))[:limit]
    except ValueError:
        pass
    return re.split(r"[?#]", url, maxsplit=1)[0][:limit]


def is_personal_question(question_text: Optional[str], element_id: Optional[str] = None) -> bool:
    """
    Whether a text box asks for contact or identity details.

    Args:
        question_text: The wording the tracker read next to the box.
        element_id: The box's id or name (for example "email" or "Q5").

    Returns:
        bool: True for email, phone, name, address, postcode, date of birth, or
        government id questions.
    """
    if question_text and _PERSONAL_WORDING.search(question_text):
        return True
    return bool(element_id and re.search(r"e-?mail|phone|\btel\b|postcode|postal|zip", element_id, re.IGNORECASE))


def _mask_phone(match: "re.Match[str]") -> str:
    digits = sum(ch.isdigit() for ch in match.group(0))
    low, high = _PHONE_DIGITS
    return MASKED_PHONE if low <= digits <= high else match.group(0)


def mask_personal(text: Optional[str]) -> Optional[str]:
    """
    The answer with email addresses and phone numbers replaced.

    Args:
        text: An open-ended answer, or None.

    Returns:
        str | None: The same text with each email as "[email]" and each run of 9-15
        digits (spaces, dots, dashes, brackets allowed between them) as "[phone]".
    """
    if not text:
        return text
    return _PHONE_RUN.sub(_mask_phone, _EMAIL.sub(MASKED_EMAIL, text))
