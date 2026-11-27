"""
Check a Decipher survey XML before tracking is added, and explain every problem.

Each issue says what is wrong, why it matters, how to fix it, where it is (line),
and whether "Fix with AI" can repair it. Errors stop tracking from being added;
warnings are things Decipher may refuse or that need files only the original
Decipher project has (quota sheets, .dat data files).

The rules come from what Decipher itself refuses:
- the file must be one ``<survey>`` element (a copied survey body is not enough);
- ``compat`` below 143 is retired, and compat 151+ needs ``delphi="1"``;
- some old question styles only run up to a given compat (``atm1d.9`` up to 149;
  ``autosum.5``, ``ranksort.7``, ``cardsort.8`` and ``atmtable.6`` up to 154);
- labels of questions and other top-level elements must be unique;
- ``quota sheet="..."`` needs that sheet in the survey's quota file, and
  ``Database("x.dat")`` / ``File("x.dat")`` need those files in the survey.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from app.services.decipher_tracking import (
    DELPHI_FROM_COMPAT,
    MIN_COMPAT,
    _QUESTION_TAGS,
    has_tracking,
    parse_survey,
    remove_tracking,
)

# Highest compat each old style runs on, from Decipher's own refusals
# ("Style requires AT MOST compat level 149, but this survey is 155").
STYLE_MAX_COMPAT = {"atm1d.9": 149, "autosum.5": 154, "ranksort.7": 154, "cardsort.8": 154, "atmtable.6": 154}
# Compat used when the survey has none and no style limits it (what Decipher exports today).
DEFAULT_COMPAT = 155

_LABELLED_TAGS = _QUESTION_TAGS | {"html", "block", "loop", "term", "image", "imageupload"}
_DATA_FILE = re.compile(r"""\b(?:Database|File)\(\s*["']([^"']+)["']""")
_USES = re.compile(r'\buses\s*=\s*"([^"]+)"')
_QOS_LABEL = re.compile(r"""\blabel\s*=\s*["'](QOS_[A-Za-z0-9_]*)["']""")


@dataclass
class Issue:
    """One problem found in the file."""

    code: str
    severity: str  # "error" stops tracking; "warning" does not
    title: str
    detail: str
    fix: str
    line: Optional[int] = None
    ai_can_fix: bool = True
    items: List[str] = field(default_factory=list)


@dataclass
class CheckReport:
    """Everything found in one file."""

    ok: bool
    issues: List[Issue]
    questions: int = 0
    pages: int = 0
    lines: int = 0
    size_kb: int = 0
    title: str = ""
    already_tracked: bool = False
    recommended_compat: Optional[int] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["errors"] = sum(1 for issue in self.issues if issue.severity == "error")
        data["warnings"] = sum(1 for issue in self.issues if issue.severity == "warning")
        data["ai_fixable"] = any(issue.ai_can_fix and issue.severity == "error" for issue in self.issues)
        return data


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, max(index, 0)) + 1


def _first_line(text: str, pattern: str) -> Optional[int]:
    found = re.search(pattern, text)
    return _line_of(text, found.start()) if found else None


def _decode(data: bytes) -> tuple[Optional[str], Optional[Issue]]:
    try:
        return data.decode("utf-8-sig"), None
    except UnicodeDecodeError as error:
        return None, Issue(
            code="not_utf8",
            severity="error",
            title="The file is not saved as UTF-8 text",
            detail=(
                f"Byte {error.start} cannot be read as UTF-8. Decipher survey XML is always UTF-8; this usually "
                "means the file was saved from Word or Excel, or in another encoding."
            ),
            fix="Export the XML from Decipher again, or open the file in a text editor and save it as UTF-8.",
            ai_can_fix=False,
        )


def _parse_problem(xml: str, error: ET.ParseError) -> Issue:
    line, column = getattr(error, "position", (None, None))
    message = str(error).split(":")[0]
    hints = {
        "not well-formed (invalid token)": (
            "Often a bare & or < inside text. In XML they must be written &amp; and &lt; "
            "(or the text wrapped in <![CDATA[ ... ]]>)."
        ),
        "mismatched tag": "A closing tag does not match the element that is open, for example </row> where </col> was expected.",
        "unclosed token": "The file ends in the middle of a tag or text. It may have been cut off when copied.",
        "no element found": "The file ends before the survey is closed. It may have been cut off when copied.",
        "junk after document element": "There is text after the closing </survey> tag.",
        "duplicate attribute": "A tag has the same attribute twice.",
    }
    hint = next((text for key, text in hints.items() if message.startswith(key)), "")
    excerpt = ""
    if line:
        lines = xml.splitlines()
        if 0 < line <= len(lines):
            excerpt = lines[line - 1].strip()[:200]
    detail = f"The XML cannot be read: {message}" + (f" at line {line}, column {column}." if line else ".")
    if hint:
        detail += f" {hint}"
    if excerpt:
        detail += f' Line {line}: "{excerpt}"'
    return Issue(
        code="not_well_formed",
        severity="error",
        title="The XML is broken and cannot be read",
        detail=detail,
        fix="Correct the XML at that line and upload it again, or use Fix with AI.",
        line=line,
    )


def check_survey_xml(data: bytes) -> CheckReport:
    """Check one uploaded file and explain what Decipher or the tracker would trip over.

    Args:
        data: File bytes as uploaded.

    Returns:
        The report; ``ok`` is True when there are no errors.
    """
    issues: List[Issue] = []
    xml, problem = _decode(data)
    size_kb = max(1, round(len(data) / 1024))
    if problem:
        return CheckReport(ok=False, issues=[problem], size_kb=size_kb)
    if not xml.strip():
        return CheckReport(
            ok=False,
            size_kb=size_kb,
            issues=[Issue("empty", "error", "The file is empty", "There is no XML in the file.",
                          "Export the survey XML from Decipher and upload that file.", ai_can_fix=False)],
        )
    lines = xml.count("\n") + 1
    if re.search(r"<!DOCTYPE|<!ENTITY", xml, flags=re.I):
        issues.append(Issue(
            "doctype", "error", "The file has a DOCTYPE declaration",
            "Decipher survey XML never has <!DOCTYPE> or <!ENTITY> lines, and this service does not read files that do.",
            "Delete the <!DOCTYPE ...> line (and any <!ENTITY> lines), then upload again.",
            line=_first_line(xml, r"<!DOCTYPE|<!ENTITY"),
        ))
        return CheckReport(ok=False, issues=issues, lines=lines, size_kb=size_kb)

    already_tracked = has_tracking(xml)
    body = remove_tracking(xml) if already_tracked else xml

    root: Optional[ET.Element] = None
    try:
        root = parse_survey(body)
    except ET.ParseError as error:
        has_survey_tag = re.search(r"<survey\b", body) is not None
        if not has_survey_tag:
            stripped = body.split("?>", 1)[1] if body.lstrip().startswith("<?xml") else body
            try:
                root = parse_survey(f"<survey>{stripped}</survey>")
            except ET.ParseError:
                root = None
        if root is None:
            issues.append(_parse_problem(body, error))
            return CheckReport(ok=False, issues=issues, lines=lines, size_kb=size_kb, already_tracked=already_tracked)
        first = re.search(r"<([A-Za-z][\w:-]*)", body)
        issues.append(Issue(
            "fragment", "error", "This is only part of a survey: there is no <survey> tag",
            (
                f"The file starts with <{first.group(1) if first else '?'}> instead of <survey ...>. A Decipher survey "
                "XML is one <survey> element holding the survey settings, sample sources and questions. This happens "
                "when only the questions are copied out of a Decipher project."
            ),
            (
                "Best: in Decipher open the survey, export the full XML, and upload that. Or use Fix with AI to wrap "
                "it in a <survey> tag with standard settings (you can give it the survey title and compat)."
            ),
            line=1,
        ))

    if root is not None and root.tag != "survey" and not any(i.code == "fragment" for i in issues):
        issues.append(Issue(
            "not_survey", "error", f"The top element is <{root.tag}>, not <survey>",
            "Decipher survey XML must start with a <survey ...> element that holds everything else.",
            "Export the full survey XML from Decipher, or use Fix with AI to wrap it in a <survey> tag.",
            line=1,
        ))

    is_fragment = any(i.code in ("fragment", "not_survey") for i in issues)
    title = "" if root is None or is_fragment else (root.get("alt") or root.get("name") or "")

    # Styles that only run up to a given compat decide the highest compat the survey can use.
    style_limits: Dict[str, int] = {}
    for match in _USES.finditer(body):
        for style in (part.strip() for part in match.group(1).split(",")):
            if style in STYLE_MAX_COMPAT:
                style_limits[style] = STYLE_MAX_COMPAT[style]
    highest_allowed = min(style_limits.values()) if style_limits else DEFAULT_COMPAT
    recommended = max(MIN_COMPAT, min(DEFAULT_COMPAT, highest_allowed))

    if root is not None and not is_fragment:
        issues.extend(_settings_issues(body, root, recommended, style_limits))

    issues.extend(_label_issues(body))
    issues.extend(_file_warnings(body))

    questions = 0
    if root is not None:
        questions = sum(1 for element in root.iter() if element.tag in _QUESTION_TAGS)
        if questions == 0:
            issues.append(Issue(
                "no_questions", "warning", "No questions found",
                "The file has no question elements (radio, checkbox, text, textarea, number, select, ...). The tracker "
                "still runs, but there is nothing for it to check.",
                "Check that you uploaded the right file.",
                ai_can_fix=False,
            ))

    issues.sort(key=lambda issue: (issue.severity != "error", issue.line or 0))
    return CheckReport(
        ok=not any(issue.severity == "error" for issue in issues),
        issues=issues,
        questions=questions,
        pages=len(re.findall(r"<suspend\b", body)) + 1,
        lines=lines,
        size_kb=size_kb,
        title=title,
        already_tracked=already_tracked,
        recommended_compat=recommended,
    )


def _settings_issues(xml: str, root: ET.Element, recommended: int, style_limits: Dict[str, int]) -> List[Issue]:
    issues: List[Issue] = []
    survey_line = _first_line(xml, r"<survey\b")
    raw = (root.get("compat") or "").strip()
    if not raw:
        issues.append(Issue(
            "compat_missing", "error", "The survey has no compat setting",
            "Decipher reads a missing compat as 0, and compat below 143 is no longer accepted.",
            f'Add compat="{recommended}" to the <survey> tag (Decipher\'s own export always includes it).'
            + (' Also add delphi="1".' if recommended >= DELPHI_FROM_COMPAT else ""),
            line=survey_line,
        ))
        return issues
    try:
        compat = int(raw)
    except ValueError:
        issues.append(Issue(
            "compat_invalid", "error", f'The compat setting "{raw}" is not a number',
            "Decipher expects a whole number such as 155.",
            f'Set compat="{recommended}" on the <survey> tag.',
            line=survey_line,
        ))
        return issues
    if compat < MIN_COMPAT:
        issues.append(Issue(
            "compat_too_low", "error", f"compat {compat} is no longer accepted by Decipher",
            f"Decipher has retired every compat below {MIN_COMPAT}.",
            f'Raise it to compat="{recommended}" on the <survey> tag, then test the survey: a newer compat can change how old questions look.',
            line=survey_line,
        ))
    for style, limit in sorted(style_limits.items()):
        if compat > limit:
            issues.append(Issue(
                "style_compat", "error", f'The question style "{style}" only works up to compat {limit}',
                f"The survey is at compat {compat}, so Decipher refuses the file "
                f'("Style requires AT MOST compat level {limit}").',
                f'Lower the survey to compat="{recommended}", or switch those questions to a newer version of the style in Decipher.',
                line=_first_line(xml, rf'uses\s*=\s*"[^"]*{re.escape(style)}'),
            ))
    if compat >= DELPHI_FROM_COMPAT and (root.get("delphi") or "").strip() != "1":
        issues.append(Issue(
            "delphi_missing", "error", f'compat {compat} needs delphi="1"',
            f'Decipher requires delphi="1" on the <survey> tag for compat {DELPHI_FROM_COMPAT} and above.',
            'Add delphi="1" to the <survey> tag.',
            line=survey_line,
        ))
    return issues


def _label_issues(xml: str) -> List[Issue]:
    issues: List[Issue] = []
    own = [match for match in _QOS_LABEL.finditer(xml)]
    if own:
        names = sorted({match.group(1) for match in own})
        issues.append(Issue(
            "qos_labels", "error", "The survey already uses QOS_ labels",
            "Labels starting with QOS_ are reserved for the hidden results questions the tracker adds, so these would clash.",
            "Rename these questions (and every place that refers to them), then upload again. Fix with AI can rename them.",
            line=_line_of(xml, own[0].start()),
            items=names[:20],
        ))

    seen: Dict[str, List[int]] = defaultdict(list)
    for label, start, _ in label_positions(xml):
        seen[label].append(_line_of(xml, start))
    duplicates = {label: found for label, found in seen.items() if len(found) > 1}
    if duplicates:
        listed = [f"{label} (lines {', '.join(map(str, found[:4]))})" for label, found in sorted(duplicates.items())]
        issues.append(Issue(
            "duplicate_labels", "error", "Some labels are used more than once",
            "Every question, page element, block and loop needs its own label. Decipher refuses the file otherwise.",
            "Give each one a different label (and update any logic that refers to it), or use Fix with AI.",
            line=min(found[1] for found in duplicates.values()),
            items=listed[:20],
        ))
    return issues


_LABEL_TAG = re.compile(
    rf"<({'|'.join(sorted(_LABELLED_TAGS))})\b[^>]*?\blabel\s*=\s*[\"']([^\"']+)[\"']"
)


def label_positions(xml: str) -> List[tuple]:
    """(label, tag start, label value start) for every labelled element, outside CDATA and comments."""
    # Reason: blank out scripts and comments but keep every character's position.
    masked = re.sub(r"<!\[CDATA\[.*?\]\]>|<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), xml, flags=re.S)
    return [(m.group(2), m.start(), m.start(2)) for m in _LABEL_TAG.finditer(masked)]


def rename_duplicate_labels(xml: str) -> tuple[str, List[str], List[str]]:
    """Keep the first element with each label; rename later ones to LABEL_2, LABEL_3, ...

    Returns:
        The XML, one change line per rename, and what the researcher should check.
    """
    found = label_positions(xml)
    taken = {label for label, _, _ in found}
    count: Dict[str, int] = defaultdict(int)
    renames = []
    for label, start, value_at in found:
        count[label] += 1
        if count[label] == 1:
            continue
        suffix = count[label]
        while f"{label}_{suffix}" in taken:
            suffix += 1
        new = f"{label}_{suffix}"
        taken.add(new)
        renames.append((value_at, label, new, _line_of(xml, start)))
    for value_at, label, new, _ in sorted(renames, reverse=True):
        xml = xml[:value_at] + new + xml[value_at + len(label):]
    changes, checks = [], []
    for _, label, new, line in sorted(renames, key=lambda item: item[3]):
        changes.append(f"Renamed the later {label} (line {line}) to {new}; the first {label} keeps its label.")
        checks.append(
            f"Conditions and logic that mention {label} still point to the first {label}. "
            f"If one of them meant the element on line {line}, change it to {new}."
        )
    return xml, changes, checks


def _file_warnings(xml: str) -> List[Issue]:
    issues: List[Issue] = []
    sheets = sorted({m.group(1) for m in re.finditer(r"<quota\b[^>]*\bsheet\s*=\s*[\"']([^\"']+)[\"']", xml)})
    if sheets:
        issues.append(Issue(
            "quota_sheets", "warning", "Quotas need a quota sheet in Decipher",
            (
                "These <quota> tags read sheets from the survey's quota file (quota.xls), which is not part of the XML. "
                "Replacing the XML of the original Decipher survey keeps its quota file. A new Decipher survey has none, "
                "so Decipher refuses the file there."
            ),
            "Upload over the original survey in Decipher, or add the sheets to the new survey's quota file. "
            "If you don't need the quotas, ask Fix with AI to remove them.",
            line=_first_line(xml, r"<quota\b"),
            ai_can_fix=False,
            items=sheets[:30],
        ))
    files = sorted({m.group(1) for m in _DATA_FILE.finditer(xml)})
    if files:
        issues.append(Issue(
            "data_files", "warning", "The survey reads data files that are not in the XML",
            (
                "Database(...) or File(...) calls load these files from the Decipher survey's files. The original survey "
                "has them; a new Decipher survey does not, and the survey fails where it reads them."
            ),
            "Upload over the original survey, or upload these files to the new survey in Decipher. If you don't need "
            "those checks, tell Fix with AI which ones to remove.",
            line=_first_line(xml, r"\b(?:Database|File)\("),
            ai_can_fix=False,
            items=files[:30],
        ))
    return issues
