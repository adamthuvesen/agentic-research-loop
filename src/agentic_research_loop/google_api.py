"""Thin wrapper for the Google Search Console Search Analytics API.

Uses Application Default Credentials (ADC) with auto-refresh.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

import google.auth
import google.auth.transport.requests

# These are read from the environment so the repo carries no account-specific values.
#   GCP_QUOTA_PROJECT — billing/quota project for the API calls (optional)
#   GSC_SITE          — verified Search Console site URL, e.g. https://www.example.com/
_GSC_BASE = "https://searchconsole.googleapis.com/webmasters/v3"


def _quota_project() -> str | None:
    return os.environ.get("GCP_QUOTA_PROJECT") or None


def _gsc_site() -> str:
    site = os.environ.get("GSC_SITE")
    if not site:
        raise GoogleApiError(
            "GSC_SITE is not set. Export your verified Search Console site URL, "
            "e.g. GSC_SITE=https://www.example.com/"
        )
    return site


_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
]

_RE_AUTH_COMMAND = (
    "gcloud auth application-default login "
    "--client-id-file=$HOME/.config/gcloud/oauth-client.json "
    '--scopes="https://www.googleapis.com/auth/webmasters.readonly,'
    'https://www.googleapis.com/auth/cloud-platform"'
)

_credentials: google.auth.credentials.Credentials | None = None


class GoogleAuthError(RuntimeError):
    """Raised when ADC credentials are missing or cannot be refreshed."""


class GoogleApiError(RuntimeError):
    """Raised when a Google API request fails after authentication succeeds."""


def _get_credentials() -> google.auth.credentials.Credentials:
    global _credentials
    if _credentials is None:
        try:
            _credentials, _ = google.auth.default(scopes=_SCOPES)
        except google.auth.exceptions.DefaultCredentialsError as exc:
            raise GoogleAuthError(
                f"ADC credentials not found: {exc}\n\nRe-authenticate with:\n  {_RE_AUTH_COMMAND}"
            ) from exc
    if not _credentials.valid:
        try:
            _credentials.refresh(google.auth.transport.requests.Request())
        except google.auth.exceptions.RefreshError as exc:
            _credentials = None
            raise GoogleAuthError(
                f"Token refresh failed: {exc}\n\nRe-authenticate with:\n  {_RE_AUTH_COMMAND}"
            ) from exc
    return _credentials


def _authed_request(url: str, body: dict[str, Any] | None = None) -> Any:
    creds = _get_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    quota_project = _quota_project()
    if quota_project:
        headers["x-goog-user-project"] = quota_project
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if body else "GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        detail = body.strip() or exc.reason
        raise GoogleApiError(
            f"Google API request failed ({exc.code}): {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise GoogleApiError(f"Google API request failed: {exc.reason}") from exc


# ---------------------------------------------------------------------------
# Google Search Console
# ---------------------------------------------------------------------------


def gsc_query(
    start_date: str,
    end_date: str,
    dimensions: list[str],
    row_limit: int = 100,
    start_row: int = 0,
) -> dict[str, Any]:
    """Query GSC Search Analytics API."""
    url = f"{_GSC_BASE}/sites/{urllib.request.quote(_gsc_site(), safe='')}/searchAnalytics/query"
    body: dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "startRow": start_row,
    }
    return _authed_request(url, body)
