"""
Upload a tracked survey XML to Forsta Decipher.

A new survey is created through Research Hub (``POST /rh/companies/{company}/surveys``) unless a
survey path is given; then ``survey.xml`` is replaced with
``PUT /surveys/{path}/files/survey.xml`` and Decipher validates it before saving.
Live surveys are never overwritten (``overwriteLive=false``).

A survey's saved data layouts (``layouts.json``) list their export columns one by
one, so questions added later are missing from exports that use them. After the
upload, the tracking's ``QOS_*`` questions are added to every saved layout that
lacks them; a survey without saved layouts is left as it is.

The API key is sent only as the ``x-apikey`` header and never leaves the server;
it is removed from any error text Decipher echoes back.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import quote

import httpx

DEFAULT_API_BASE = "https://selfserve.decipherinc.com/api/v1"
_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")
_COMPANY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_PLACEHOLDERS = {"your-decipher-key", "your-decipher-api-key"}
# Hidden tracking questions and their width, read from the uploaded XML.
_QOS_QUESTION = re.compile(r'<(?:text|number) label="(QOS_[A-Za-z_]+)" optional="1" size="(\d+)"')


class DecipherNotConfigured(Exception):
    """No usable Decipher API key or base URL is configured."""


class DecipherUploadError(Exception):
    """Decipher refused the upload or could not be reached.

    Attributes:
        message: Explanation safe to show in the UI.
        status: HTTP status Decipher returned; 0 when it was not reached.
        errors: Validation messages from Decipher.
        survey_path: Path already created, so a retry updates the same survey.
        survey_url: Respondent link for that path.
    """

    def __init__(
        self,
        message: str,
        status: int = 0,
        errors: Optional[List[str]] = None,
        survey_path: Optional[str] = None,
        survey_url: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors or []
        self.survey_path = survey_path
        self.survey_url = survey_url


@dataclass
class UploadResult:
    """Where the survey went in Decipher."""

    survey_path: str
    survey_url: str
    created: bool
    message: str
    warnings: List[str] = field(default_factory=list)
    layouts_updated: int = 0


def is_configured(api_key: Optional[str]) -> bool:
    """True when a real Decipher API key is set."""
    key = (api_key or "").strip()
    return bool(key) and key not in _PLACEHOLDERS


def api_base(raw: Optional[str]) -> str:
    """The API root: https, ending in /api/v1, Selfserve when blank.

    Raises:
        DecipherNotConfigured: The URL is not https or does not end in /api/v1.
    """
    base = (raw or "").strip().rstrip("/") or DEFAULT_API_BASE
    if not base.startswith("https://") or not base.endswith("/api/v1"):
        raise DecipherNotConfigured("DECIPHER_API_BASE must be an https URL ending in /api/v1.")
    return base


def company(raw: Optional[str]) -> str:
    """The company segment of the create URL; ``self`` when blank.

    Raises:
        DecipherNotConfigured: The value cannot go in a URL path.
    """
    value = (raw or "").strip() or "self"
    if not _COMPANY.fullmatch(value):
        raise DecipherNotConfigured(
            "DECIPHER_COMPANY may contain only letters, numbers, dots, hyphens, and underscores."
        )
    return value


def clean_path(value: Optional[str]) -> Optional[str]:
    """A survey path safe to put in the API URL, or None.

    Accepts ``selfserve/123/456789`` and the same with a leading slash, or a
    Decipher link that contains it (``.../survey/selfserve/123/456789``,
    ``.../rep/selfserve/123/456789:dashboard``).
    """
    if not value or not value.strip():
        return None
    text = value.strip()
    found = re.search(r"(?:^|/)(selfserve/[0-9a-z]+/[0-9a-z]+)(?:[:/?#]|$)", text, flags=re.I)
    if "://" in text:
        if not found:
            return None
        text = found.group(1)
    path = text.strip("/")
    parts = path.split("/")
    # Reason: the path goes into the request URL, so parent segments are refused.
    if not path or ".." in parts or not _PATH.fullmatch(path):
        return None
    return path


def public_url(base: str, path: str) -> str:
    """The respondent link: Decipher serves the survey at ``/survey/{path}``."""
    host = base[: -len("/api/v1")] if base.endswith("/api/v1") else base
    return f"{host}/survey/{path}"


def _scrub(text: str, key: str) -> str:
    return text.replace(key, "[REDACTED]") if key and key in text else text


def _messages(body: dict) -> List[str]:
    """Validation messages from a Decipher error body (``extra`` or ``$error``)."""
    out: List[str] = []
    extra = body.get("extra")
    # Reason: Decipher sends a list of problems, or (for script errors) one object such as
    # {"type": "Exec", "msg": "File 'x.dat' does not exist", "page": 58}.
    items = extra if isinstance(extra, list) else [extra] if isinstance(extra, dict) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = next(
            (
                item[name].strip()
                for name in ("message", "msg", "error", "text", "detail", "description")
                if isinstance(item.get(name), str) and item[name].strip()
            ),
            "",
        )
        kind = str(item.get("type") or "error")
        where = f" (page {item['page']})" if isinstance(item.get("page"), int) else ""
        out.append(f"{kind}{where}: {text}" if text else kind)
    if not out and isinstance(body.get("$error"), str) and body["$error"].strip():
        out.append(body["$error"].strip())
    return out


def _json(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _raise_for_status(response: httpx.Response, key: str, path: Optional[str], url: Optional[str]) -> dict:
    body = _json(response)
    if response.is_success:
        return body
    status = response.status_code
    if status == 401:
        message = "Decipher rejected the API key. Check DECIPHER_API_KEY."
    elif status == 403:
        message = "Decipher refused this API key for that survey."
    elif status == 404:
        message = "Decipher could not find that survey path."
    elif status == 400:
        message = "Decipher rejected survey.xml."
    else:
        message = f"Decipher returned HTTP {status}."
    errors = [_scrub(item, key) for item in _messages(body)]
    if errors:
        message = f"{message} {' '.join(errors)}"
    raise DecipherUploadError(_scrub(message, key), status, errors, path, url)


class DecipherUploader:
    """Creates a Decipher survey when needed and uploads its survey.xml."""

    def __init__(
        self,
        api_key: Optional[str],
        base: Optional[str] = None,
        company_id: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        if not is_configured(api_key):
            raise DecipherNotConfigured(
                "Uploading to Decipher is not set up: DECIPHER_API_KEY is not set. Download the XML and import it in Decipher."
            )
        self.key = (api_key or "").strip()
        self.base = api_base(base)
        self.company = company(company_id)
        self.transport = transport

    async def upload(self, xml: str, name: str, survey_path: Optional[str] = None) -> UploadResult:
        """Upload ``xml`` to ``survey_path``, or to a new survey named ``name``.

        Raises:
            DecipherUploadError: Decipher rejected a call or could not be reached.
        """
        path = clean_path(survey_path) if survey_path else None
        if survey_path and path is None:
            raise DecipherUploadError(
                "That is not a Decipher survey path. Use the form selfserve/123/456789."
            )
        created = False
        headers = {"x-apikey": self.key, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                transport=self.transport, timeout=60.0, follow_redirects=False, headers=headers
            ) as client:
                if path is None:
                    path = await self._create(client, name)
                    created = True
                url = public_url(self.base, path)
                response = await client.put(
                    f"{self.base}/surveys/{path}/files/survey.xml",
                    files={"contents": ("survey.xml", xml.encode("utf-8"), "application/xml")},
                    data={"validate": "true", "overwriteLive": "false", "location": "root"},
                )
                _raise_for_status(response, self.key, path, url)
                layouts, warnings = await self._add_to_layouts(client, path, xml)
        except httpx.HTTPError as error:
            raise DecipherUploadError(
                "Decipher could not be reached. Try again, or download the XML and import it in Decipher.",
                survey_path=path,
                survey_url=public_url(self.base, path) if path else None,
            ) from error
        action = "Created a new Decipher survey" if created else "Updated the Decipher survey"
        message = f"{action} at {path}."
        if layouts:
            plural = "layout" if layouts == 1 else "layouts"
            message += f" Added the quality variables to {layouts} saved data {plural}."
        return UploadResult(
            survey_path=path,
            survey_url=url,
            created=created,
            message=message,
            warnings=warnings,
            layouts_updated=layouts,
        )

    async def _add_to_layouts(self, client: httpx.AsyncClient, path: str, xml: str) -> tuple[int, List[str]]:
        """Add the XML's QOS_* questions to each saved data layout that lacks them.

        The survey is already saved, so problems here become warnings, not errors.

        Returns:
            tuple: Number of layouts changed, and warnings.
        """
        widths = {label: int(size) for label, size in _QOS_QUESTION.findall(xml)}
        if not widths:
            return 0, []
        trouble = [
            "The quality variables could not be added to this survey's saved data layouts. "
            "In Decipher, add the QOS_ variables to the layout you export with, or export with all variables."
        ]
        url = f"{self.base}/surveys/{path}/files/layouts.json"
        try:
            response = await client.get(url)
            if response.status_code == 404:
                return 0, []
            if not response.is_success:
                return 0, trouble
            document = json.loads(response.content)
            layouts = document.get("layouts") if isinstance(document, dict) else None
            if not isinstance(layouts, list):
                return 0, trouble
            changed = 0
            for layout in layouts:
                columns = layout.get("variableData") if isinstance(layout, dict) else None
                if not isinstance(columns, list):
                    continue
                have = {column.get("label") for column in columns if isinstance(column, dict)}
                missing = [label for label in widths if label not in have]
                for label in missing:
                    columns.append({"minStart": 0, "altlabel": label, "shown": 1, "fwidth": widths[label], "label": label})
                changed += bool(missing)
            if not changed:
                return 0, []
            saved = await client.put(
                url,
                files={"contents": ("layouts.json", json.dumps(document).encode("utf-8"), "application/json")},
            )
            return (changed, []) if saved.is_success else (0, trouble)
        except (httpx.HTTPError, ValueError):
            return 0, trouble

    async def _create(self, client: httpx.AsyncClient, name: str) -> str:
        response = await client.post(
            f"{self.base}/rh/companies/{quote(self.company, safe='')}/surveys",
            json={"name": (name or "").strip()[:200] or "Survey", "ptype": "beacon", "lang": "english"},
        )
        body = _raise_for_status(response, self.key, None, None)
        path = clean_path(body.get("path") if isinstance(body.get("path"), str) else None)
        if path is None:
            raise DecipherUploadError("Decipher created a survey but did not return its path.", response.status_code)
        return path
