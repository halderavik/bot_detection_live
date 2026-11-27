"""
"Fix with AI" for Decipher survey XML.

The model never rewrites the whole file (real surveys are often 150-300 KB). It
returns exact edits: text to find (copied from the file, matching exactly one
place), its replacement, and text to add at the start or end. This module applies
only edits that match exactly once, then checks the result again with the same
rules as the upload check. If errors the model can fix are left, it gets one more
round with what is still wrong.

The user's own instructions (survey title, compat, "remove the quotas", ...) go to
the model with the problems. Without instructions it fixes the errors itself and
leaves things it cannot know (quota sheets, data files) alone.
"""

from __future__ import annotations

import asyncio
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from typing import List, Optional

from app.config import settings
from app.services.decipher_tracking import DELPHI_FROM_COMPAT, has_tracking, parse_survey, remove_tracking
from app.services.decipher_errors import explain_one, lowest_style_compat
from app.services.decipher_xml_check import (
    CheckReport,
    Issue,
    check_survey_xml,
    fill_empty_python_blocks,
    rename_duplicate_labels,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

MAX_INSTRUCTIONS = 2000
# Files up to this size go to the model whole; larger ones as excerpts around each problem.
FULL_FILE_CHARS = 80_000
MAX_ROUNDS = 2
TIMEOUT_SECONDS = 150
# Tested on real Decipher files: gpt-4o, gpt-4.1 and gpt-4.1-mini applied every fix and instruction;
# gpt-4o-mini sometimes ignored instructions. Settings can choose another model (OPENAI_FIX_MODEL).
DEFAULT_MODEL = "gpt-4o"

# The survey header Decipher accepted in this project's end-to-end test (tests/fixtures/coffee_demo_survey.xml).
SURVEY_HEADER = (
    '<survey alt="{title}" autosave="0" builderCompatible="1" compat="{compat}"{delphi} '
    'extraVariables="source,record,decLang,list,userAgent" lang="english" name="Survey" newStyle="1" '
    'secure="1" setup="term,quota,time,decLang" state="testing">\n'
    '  <samplesources default="0">\n'
    '    <samplesource list="0"><title>Open Survey</title>\n'
    '      <completed>It seems you have already completed this survey.</completed>\n'
    '      <invalid>You are missing information in the URL. Please verify the URL with the original invite.</invalid>\n'
    '      <exit cond="terminated">Thank you for taking our survey.</exit>\n'
    '      <exit cond="qualified">Thank you for taking our survey. Your efforts are greatly appreciated!</exit>\n'
    '      <exit cond="overquota">Thank you for taking our survey.</exit>\n'
    '    </samplesource>\n'
    '  </samplesources>\n'
)

SYSTEM_PROMPT = """You are an expert Decipher (Forsta Surveys) XML programmer. You repair survey XML so that
Decipher accepts it and live tracking can be added. You return exact text edits, never a whole file.

Rules:
- Fix every listed ERROR. Follow the user's instructions when given; they win over your own choices.
- Change as little as possible. Never change question wording, answer options, labels, logic, or styles unless
  an error or the user's instructions require it. Never add <script>, <style> or anything named QOS_ (the tracker adds those).
- Leave WARNINGS about quota sheets and data files (.dat) alone unless the user asks you to remove or change them.
  You cannot create those files.
- If something cannot be fixed without information you don't have, leave it and say so in "cannot_fix".
- Each edit's "find" must be copied character for character from the XML shown (same spaces and quotes) and must
  appear exactly once in the whole file. Use a whole line or more so it is unique. "replace" is the new text.
- Use "prepend" for text that must go before everything else, and "append" for text after everything else.
- A file that was only part of a survey has already been wrapped in a <survey> tag with standard settings
  before you see it. Never add another <survey> tag. If the user gives a title, compat or other setting, edit the
  attributes of the existing <survey ...> tag (find the whole opening tag). The survey title is the alt attribute;
  leave name="Survey" as it is.
- compat: Decipher refuses compat below 143. Compat 151 and above needs delphi="1". Some styles only work up to a
  compat (atm1d.9 up to 149; autosum.5, ranksort.7, cardsort.8 and atmtable.6 up to 154). Never raise compat
  unless the checker reports it as missing or too low; lowering it for a style is done before you see the file.
- Duplicate labels are renamed before you see the file; never rename a label unless the user asks.
- Every choice the user did not specify (a new label name, the compat value, a survey title, which element a
  reference meant) must also be listed in "assumptions" so the researcher can check it.

Reply with JSON only:
{"edits": [{"find": "...", "replace": "...", "reason": "..."}], "prepend": "", "append": "",
 "changes": ["plain sentence per change, for a researcher"], "assumptions": ["choices you made without being told"],
 "cannot_fix": ["what is left and why"]}"""


class FixUnavailable(RuntimeError):
    """Fix with AI cannot run (no OpenAI key on the service)."""


@dataclass
class FixResult:
    """What Fix with AI changed and what is still wrong."""

    xml: str
    changes: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    cannot_fix: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    applied: int = 0
    rounds: int = 0
    model: str = ""
    report: Optional[CheckReport] = None


def _header(title: str, compat: int) -> str:
    safe = re.sub(r'[<>&"]', "", title).strip() or "Survey"
    delphi = ' delphi="1"' if compat >= DELPHI_FROM_COMPAT else ""
    return SURVEY_HEADER.format(title=safe, compat=compat, delphi=delphi)


def _excerpt(xml: str, report: CheckReport, instructions: str, decipher_errors: Optional[List[str]] = None) -> str:
    """The file, or the parts of it the problems (and instructions, and Decipher's messages) are about."""
    if len(xml) <= FULL_FILE_CHARS:
        return xml
    lines = xml.splitlines()
    total = len(lines)
    wanted = set(range(1, min(total, 60) + 1)) | set(range(max(1, total - 30), total + 1))
    for issue in report.issues:
        if issue.line and (issue.severity == "error" or instructions):
            wanted |= set(range(max(1, issue.line - 25), min(total, issue.line + 25) + 1))
    if instructions:
        # Reason: instructions such as "remove the quotas" need every place those appear.
        for number, text in enumerate(lines, start=1):
            if re.search(r"<quota\b|\b(?:Database|File)\(|\.dat\b", text):
                wanted |= set(range(max(1, number - 2), min(total, number + 2) + 1))
    for message in decipher_errors or []:
        # Names Decipher quotes ('Q5', 'x.dat') are searched in the file.
        for name in re.findall(r"'([^']{2,80})'", message):
            needle = name.split("/")[-1]
            for number, text in enumerate(lines, start=1):
                if needle in text:
                    wanted |= set(range(max(1, number - 6), min(total, number + 6) + 1))
        # "(page N)": the page after the (N-1)th page break, roughly.
        page = re.search(r"\(page (\d+)\)", message)
        if page:
            breaks = [number for number, text in enumerate(lines, start=1) if "<suspend" in text]
            index = int(page.group(1)) - 2
            anchor = breaks[index] if 0 <= index < len(breaks) else None
            if anchor:
                wanted |= set(range(max(1, anchor - 5), min(total, anchor + 60) + 1))
    parts, start, previous = [], None, None
    for number in sorted(wanted):
        if previous is None or number != previous + 1:
            if start is not None:
                parts.append((start, previous))
            start = number
        previous = number
    if start is not None:
        parts.append((start, previous))
    chunks = [f"----- lines {a}-{b} of {total} -----\n" + "\n".join(lines[a - 1:b]) for a, b in parts]
    return "\n".join(chunks)


def _describe(report: CheckReport) -> str:
    rows = []
    for issue in report.issues:
        where = f" (line {issue.line})" if issue.line else ""
        items = f" Items: {', '.join(issue.items[:15])}." if issue.items else ""
        rows.append(f"- {issue.severity.upper()} [{issue.code}]{where}: {issue.title}. {issue.detail} Fix: {issue.fix}{items}")
    return "\n".join(rows) or "- none"


def _readable(xml: str) -> bool:
    try:
        parse_survey(xml)
        return True
    except ET.ParseError:
        return False


def _remove_whole_element(xml: str, find: str, replace: str) -> Optional[str]:
    """When an edit removes only the start of an element, remove the whole element.

    Models often "remove an <exec> block" by replacing its first lines, which
    leaves the closing tag behind. If ``find`` opens an element it doesn't close
    and ``replace`` opens no such element, the replacement runs to the closing tag.
    """
    # Reason: only code blocks, and only when the edit also takes code lines; a question
    # is never removed because an edit dropped its opening tag.
    opened = re.match(r"\s*<(exec|validate)\b[^>]*>(.*)", find, flags=re.S)
    if not opened or not opened.group(2).strip() or replace.strip() and not replace.strip().startswith("<!--"):
        return None
    tag = opened.group(1)
    if f"</{tag}>" in find or re.search(rf"<{re.escape(tag)}[\s>/]", replace):
        return None
    start = xml.find(find)
    after = start + len(find)
    close = xml.find(f"</{tag}>", after)
    if close < 0 or re.search(rf"<{re.escape(tag)}[\s>/]", xml[after:close]):
        return None  # Reason: nested elements of the same tag are not guessed at.
    return xml[:start] + replace + xml[close + len(f"</{tag}>"):]


def _apply(xml: str, plan: dict) -> tuple[str, int, List[str]]:
    applied, skipped = 0, []
    # Reason: when the file can be read, each edit must keep it readable; one bad edit is
    # dropped on its own instead of losing every other edit in the reply.
    guard = "<survey" in xml and _readable(xml)
    for edit in plan.get("edits") or []:
        if not isinstance(edit, dict):
            continue
        find, replace = str(edit.get("find") or ""), str(edit.get("replace") or "")
        if not find:
            continue
        count = xml.count(find)
        if count == 1:
            candidate = xml.replace(find, replace)
            if guard and not _readable(candidate):
                whole = _remove_whole_element(xml, find, replace)
                if whole is not None and _readable(whole):
                    xml = whole
                    applied += 1
                    continue
                skipped.append(f"Skipped an edit ({edit.get('reason') or 'no reason given'}): it would have broken the XML.")
                continue
            xml = candidate
            applied += 1
        else:
            reason = "was not found" if count == 0 else f"matched {count} places"
            skipped.append(f"Skipped an edit ({edit.get('reason') or 'no reason given'}): its text {reason}.")
    prepend, append = str(plan.get("prepend") or ""), str(plan.get("append") or "")
    if "<survey" in xml and ("<survey" in prepend or "</survey>" in append):
        # Reason: the file is already one <survey>; a second wrapper would nest surveys.
        skipped.append("Skipped adding a second <survey> tag; the file already has one.")
        prepend, append = "", ""
    if prepend.strip():
        declaration = re.match(r"\s*<\?xml[^>]*\?>\s*", xml)
        if declaration and not prepend.lstrip().startswith("<?xml"):
            xml = xml[: declaration.end()] + prepend + xml[declaration.end():]
        else:
            xml = prepend + xml
        applied += 1
    if append.strip():
        xml = xml.rstrip() + append
        applied += 1
    return xml, applied, skipped


def _strings(value) -> List[str]:
    return [str(item) for item in value or [] if str(item).strip()][:30]


async def _ask(
    client, model: str, xml: str, report: CheckReport, instructions: str, note: str,
    decipher_errors: Optional[List[str]] = None,
) -> dict:
    compat = report.recommended_compat or 155
    opening = re.search(r"<survey\b[^>]*>", xml)
    survey_tag = (
        "CURRENT OPENING <survey> TAG (to change the title or other settings, copy this whole tag into \"find\"):\n"
        f"{opening.group(0)}\n"
        if opening else ""
    )
    user = (
        f"PROBLEMS FOUND BY THE CHECKER:\n{_describe(report)}\n\n"
        f"RECOMMENDED compat: {compat}\n"
        f"{survey_tag}"
        f"USER INSTRUCTIONS: {instructions.strip() or '(none: fix the errors yourself)'}\n"
        + (f"\nNOTE FROM THE PREVIOUS ROUND:\n{note}\n" if note else "")
        + f"\nSURVEY XML{' (excerpts; only these parts are shown)' if len(xml) > FULL_FILE_CHARS else ''}:\n"
        f"{_excerpt(xml, report, instructions, decipher_errors)}"
    )
    params = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}],
        "temperature": 0,
        # Reason: newer models refuse max_tokens; max_completion_tokens works on old and new ones,
        # and leaves room for reasoning models to think before answering.
        "max_completion_tokens": 16000,
        "response_format": {"type": "json_object"},
    }
    try:
        response = await asyncio.wait_for(client.chat.completions.create(**params), timeout=TIMEOUT_SECONDS)
    except Exception as error:  # noqa: BLE001 - retried once without the setting the model refused
        if "temperature" not in str(error):
            raise
        params.pop("temperature")
        response = await asyncio.wait_for(client.chat.completions.create(**params), timeout=TIMEOUT_SECONDS)
    content = response.choices[0].message.content or "{}"
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("The AI reply was not valid JSON.") from error
    return plan if isinstance(plan, dict) else {}


def _wrap_fragment(xml: str, title: str, compat: int) -> str:
    declaration = re.match(r"\s*<\?xml[^>]*\?>\s*", xml)
    body = xml[declaration.end():] if declaration else xml
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + _header(title, compat) + "\n" + body.rstrip() + "\n</survey>\n"


def _exact_fixes(result: FixResult, report: CheckReport, title: str = "") -> CheckReport:
    """Fixes done in code rather than by the model, because they must be exact."""
    if any(issue.code == "fragment" for issue in report.issues):
        compat = report.recommended_compat or 155
        name = title or "Survey"
        wrapped = _wrap_fragment(result.xml, name, compat)
        new_report = check_survey_xml(wrapped.encode("utf-8"))
        if not any(issue.code in ("fragment", "not_well_formed") for issue in new_report.issues):
            result.xml, report = wrapped, new_report
            result.applied += 1
            result.changes.append(
                f'Wrapped the questions in a <survey> tag with standard Decipher settings: title "{name}", '
                f"compat {compat}{', delphi=1' if compat >= DELPHI_FROM_COMPAT else ''}, English, one open sample source."
            )
            result.assumptions.append(
                f'The survey settings were not in the file, so standard ones were used (title "{name}", compat {compat}'
                + (", the highest the survey's question styles allow" if compat < 155 else "")
                + "). If the original Decipher project used other settings (language, sample sources, extra variables), "
                "upload over that project or tell Fix with AI which settings to use."
            )
    # Reason: removing quota or data-file code often leaves an if/else with nothing under it,
    # which Decipher refuses; "pass" keeps the logic as it was and the model often misses it.
    if any(issue.code == "empty_code_block" for issue in report.issues):
        filled, count = fill_empty_python_blocks(result.xml)
        if count:
            result.xml = filled
            result.applied += count
            result.changes.append(
                f"Added pass under {count} Python if/else or loop statement(s) that had nothing under them "
                "(usually left after code was removed), so the code compiles."
            )
            report = check_survey_xml(result.xml.encode("utf-8"))
    # Reason: renaming the later copies of a duplicate label is position work; language models
    # tend to rename the wrong copy, which would change the data's variable names.
    if any(issue.code == "duplicate_labels" for issue in report.issues):
        renamed, changes, checks = rename_duplicate_labels(result.xml)
        if changes:
            result.xml = renamed
            result.applied += len(changes)
            result.changes.extend(changes)
            result.assumptions.extend(checks)
            return check_survey_xml(result.xml.encode("utf-8"))
    return report


def _compat_of(xml: str) -> Optional[int]:
    opening = re.search(r"<survey\b[^>]*>", xml)
    found = re.search(r'\bcompat="(\d+)"', opening.group(0)) if opening else None
    return int(found.group(1)) if found else None


def _keep_compat(old_xml: str, new_xml: str, new_report: CheckReport, old_report: CheckReport, instructions: str):
    """Undo a compat increase the model made without being asked (it would break old styles again)."""
    before, after = _compat_of(old_xml), _compat_of(new_xml)
    asked = re.search(r"compat", instructions or "", flags=re.I)
    too_low = any(i.code in ("compat_missing", "compat_invalid", "compat_too_low") for i in old_report.issues)
    if before is None or after is None or after <= before or asked or too_low:
        return new_xml, new_report, ""
    opening = re.search(r"<survey\b[^>]*>", new_xml).group(0)
    restored = new_xml.replace(opening, re.sub(r'\bcompat="\d+"', f'compat="{before}"', opening), 1)
    note = f"The AI raised compat to {after} without being asked; it was kept at {before}, the highest this survey's styles allow."
    return restored, check_survey_xml(restored.encode("utf-8")), note


def _set_compat(result: FixResult, compat: int, reason: str) -> None:
    opening = re.search(r"<survey\b[^>]*>", result.xml)
    if not opening:
        return
    tag = opening.group(0)
    current = re.search(r'\bcompat="(\d+)"', tag)
    if current and int(current.group(1)) <= compat:
        return
    new_tag = re.sub(r'\bcompat="[^"]*"', f'compat="{compat}"', tag) if current else tag.replace("<survey", f'<survey compat="{compat}"', 1)
    result.xml = result.xml.replace(tag, new_tag, 1)
    result.applied += 1
    result.changes.append(f"Set compat to {compat} on the <survey> tag ({reason}).")
    result.assumptions.append(
        f"compat {compat} can change how some questions look or behave compared with a newer compat; test the survey in Decipher."
    )


def _decipher_issues(messages: List[str]) -> List[Issue]:
    issues = []
    for message in messages:
        explained = explain_one(message)
        issues.append(Issue(
            code=f"decipher_{explained.kind}", severity="error",
            title=f"Decipher refused the upload: {message}",
            detail=explained.explanation + (f" (Decipher page {explained.page})" if explained.page else ""),
            fix=explained.fix, ai_can_fix=explained.ai_can_fix,
        ))
    return issues


async def fix_with_ai(
    data: bytes,
    instructions: str = "",
    client=None,
    filename: str = "",
    decipher_errors: Optional[List[str]] = None,
) -> FixResult:
    """Repair a survey XML with the OpenAI model and check the result again.

    Args:
        data: The uploaded file.
        instructions: The user's instructions or missing information (may be empty).
        client: An AsyncOpenAI-compatible client; the service's own client when omitted.
        filename: Upload name; its stem is the title when a survey body has to be wrapped.
        decipher_errors: Decipher's messages from a refused upload; the fix addresses them too.

    Raises:
        FixUnavailable: No OpenAI key is configured.
        ValueError: The instructions are too long, or the file cannot be read at all.
    """
    instructions = (instructions or "").strip()
    if len(instructions) > MAX_INSTRUCTIONS:
        raise ValueError(f"Instructions can be at most {MAX_INSTRUCTIONS} characters.")
    if client is None:
        from app.services.openai_service import openai_service

        openai_service.reload()
        client = openai_service.client
    if client is None:
        raise FixUnavailable("Fix with AI needs an OpenAI API key. Add it on the Settings page.")
    model = (settings.OPENAI_FIX_MODEL or "").strip() or DEFAULT_MODEL

    report = check_survey_xml(data)
    if any(issue.code in ("not_utf8", "empty") for issue in report.issues):
        raise ValueError(report.issues[0].fix)
    # Reason: the model writes plain line breaks; Windows line breaks in the file would stop its
    # multi-line edits from matching. Decipher reads either.
    xml = data.decode("utf-8-sig").replace("\r\n", "\n")
    # Reason: tracking is added again after the fix; the model never sees or edits the tracker.
    if has_tracking(xml):
        xml = remove_tracking(xml)

    result = FixResult(xml=xml, model=model)
    stem = re.sub(r"_(tracked|fixed)$", "", re.sub(r"\.[^.]*$", "", filename or "")).strip()
    default_title = re.sub(r"[^\w .()&',+:-]", " ", stem).strip()[:100] or "Survey"
    report = _exact_fixes(result, report, default_title)
    decipher_errors = [str(m).strip() for m in decipher_errors or [] if str(m).strip()]
    limit = lowest_style_compat(decipher_errors)
    if limit:
        _set_compat(result, limit, "Decipher said a question style only works up to this compat")
        report = check_survey_xml(result.xml.encode("utf-8"))
    # Messages a compat change already answers are not sent to the model again.
    pending = [m for m in decipher_errors if not (limit and "AT MOST compat level" in m)]
    note = ""
    for round_number in range(1, MAX_ROUNDS + 1):
        decipher_now = pending if round_number == 1 else []
        needs_work = any(i.severity == "error" and i.ai_can_fix for i in report.issues)
        if not needs_work and not ((instructions or decipher_now) and round_number == 1):
            break
        shown = replace(report, issues=report.issues + _decipher_issues(decipher_now)) if decipher_now else report
        plan = await _ask(client, model, result.xml, shown, instructions, note, decipher_now)
        result.rounds = round_number
        new_xml, applied, skipped = _apply(result.xml, plan)
        result.skipped.extend(skipped)
        result.cannot_fix = _strings(plan.get("cannot_fix"))
        if not applied:
            break
        new_report = check_survey_xml(new_xml.encode("utf-8"))
        was_readable = not any(i.code == "not_well_formed" for i in report.issues)
        if was_readable and any(i.code == "not_well_formed" for i in new_report.issues):
            # Reason: never hand back a file the AI made unreadable; keep the last good version.
            result.skipped.append("The AI's edits made the XML unreadable, so they were not kept.")
            break
        new_xml, new_report, kept = _keep_compat(result.xml, new_xml, new_report, report, instructions)
        if kept:
            result.skipped.append(kept)
        result.xml, report = new_xml, new_report
        result.applied += applied
        result.changes.extend(_strings(plan.get("changes")))
        result.assumptions.extend(_strings(plan.get("assumptions")))
        # Problems hidden while the XML was unreadable (such as duplicate labels) show up now.
        report = _exact_fixes(result, report, default_title)
        if report.ok:
            break
        note = "Some problems are still there after your edits. " + " ".join(skipped)
    result.report = report
    logger.info(f"Fix with AI: {result.applied} edits in {result.rounds} round(s), ok={report.ok}, model={model}")
    return result
