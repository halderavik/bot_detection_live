"""
Explain Decipher's refusal messages in plain words.

Decipher validates every uploaded XML and answers with short technical messages
such as "survey: while using style 'lib/steam/atm1d/v9': Style requires AT MOST
compat level 149, but this survey is 155" or "Exec (page 58): File 'x.dat' does
not exist". Each message here gets an explanation, what to do, whether Fix with
AI can repair it on its own, and whether it needs the user's instruction (for
example removing quotas whose sheet the Decipher survey does not have).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class ExplainedError:
    """One Decipher message with its explanation."""

    message: str
    kind: str
    explanation: str
    fix: str
    page: Optional[int] = None
    ai_can_fix: bool = True
    needs_instruction: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _page(message: str) -> Optional[int]:
    found = re.search(r"\(page (\d+)\)", message)
    return int(found.group(1)) if found else None


def explain_one(message: str) -> ExplainedError:
    """Explain a single Decipher message."""
    text = message.strip()
    lower = text.lower()
    page = _page(text)

    style = re.search(r"style '([^']+)'.*?AT MOST compat level (\d+)", text, flags=re.I)
    if style:
        name = style.group(1).replace("lib/steam/", "")
        return ExplainedError(
            text, "style_compat",
            f'The question style "{name}" only works up to compat {style.group(2)}, and the survey is set higher.',
            f'Lower compat on the <survey> tag to {style.group(2)} (or update those questions to a newer style in Decipher).',
            page,
        )
    if "compat" in lower and ("retired" in lower or "lower than" in lower or "no longer" in lower):
        return ExplainedError(
            text, "compat", "The survey's compat level is too old for Decipher.",
            'Set compat="155" (with delphi="1") on the <survey> tag, or the highest compat its styles allow.', page,
        )
    if "delphi" in lower:
        return ExplainedError(
            text, "delphi", 'Surveys at compat 151 and above need delphi="1" on the <survey> tag.',
            'Add delphi="1" to the <survey> tag.', page,
        )
    missing_file = re.search(r"file '([^']+)' does not exist", text, flags=re.I)
    if missing_file:
        return ExplainedError(
            text, "missing_file",
            f'The survey reads the file "{missing_file.group(1)}", which this Decipher survey does not have. '
            "Data files live in the Decipher survey, not in the XML.",
            "Upload the file to the survey in Decipher, or upload over the original project that has it. Fix with AI can "
            "remove the code that reads it only if you tell it to.",
            page, ai_can_fix=False, needs_instruction=True,
        )
    if re.search(r"no \S*quota\.xls file", lower):
        return ExplainedError(
            text, "missing_quota",
            "The XML has <quota> tags, but this Decipher survey has no quota file (quota.xls) at all. "
            "Quota sheets live in the Decipher survey, not in the XML.",
            "Upload over the original project that has the quota file, or add a quota file with those sheets in Decipher. "
            "Fix with AI can remove the quotas only if you tell it to.",
            page, ai_can_fix=False, needs_instruction=True,
        )
    if "quota" in lower and ("sheet" in lower or "quota.xls" in lower or "does not exist" in lower or "not found" in lower):
        return ExplainedError(
            text, "missing_quota",
            "A <quota> tag reads a sheet that this Decipher survey's quota file does not have.",
            "Add the sheet to the survey's quota file in Decipher, or upload over the original project. Fix with AI can "
            "remove the quotas only if you tell it to.",
            page, ai_can_fix=False, needs_instruction=True,
        )
    missing_label = re.search(r"no object with label '([^']+)'", text, flags=re.I)
    if missing_label:
        return ExplainedError(
            text, "missing_label",
            f'Something in the survey refers to "{missing_label.group(1)}", but no question or element has that label. '
            "This often happens when logic is copied from another survey or a question was renamed.",
            f'Point the reference to the right label, add the missing element, or remove the reference to "{missing_label.group(1)}".',
            page,
        )
    if "duplicate" in lower or "already defined" in lower or "already exists" in lower:
        return ExplainedError(
            text, "duplicate", "Two elements use the same label.",
            "Give each element its own label.", page,
        )
    if re.match(r"exec\b", lower) or "traceback" in lower or "error in condition" in lower or "syntaxerror" in lower:
        return ExplainedError(
            text, "script",
            "Python code in the survey (an <exec> block, a condition or a validation) fails when Decipher runs it"
            + (f" on page {page}." if page else "."),
            "Correct the code at that point in the survey.", page,
        )
    if "not well-formed" in lower or "mismatched tag" in lower or "xml" in lower and "pars" in lower:
        return ExplainedError(
            text, "xml", "Decipher could not read the XML.",
            "Correct the XML at the place named in the message.", page,
        )
    return ExplainedError(
        text, "other", "Decipher refused the file with this message.",
        "Read Decipher's message and correct that part of the survey.", page,
    )


def explain(messages: List[str]) -> List[dict]:
    """Explain each Decipher message (duplicates once, in order)."""
    seen, out = set(), []
    for message in messages or []:
        text = str(message or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(explain_one(text).to_dict())
    return out


def lowest_style_compat(messages: List[str]) -> Optional[int]:
    """The highest compat every style named in Decipher's messages allows, if any."""
    limits = [int(found) for message in messages or [] for found in re.findall(r"AT MOST compat level (\d+)", message, flags=re.I)]
    return min(limits) if limits else None
