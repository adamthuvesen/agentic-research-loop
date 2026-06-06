from __future__ import annotations

import json
from io import BytesIO
import urllib.error
import urllib.request
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agentic_research_loop.google_api import (
    GoogleApiError,
    GoogleAuthError,
    ga4_report,
    gsc_query,
)


def _mock_urlopen(response_body: dict[str, Any]):
    """Create a mock for urllib.request.urlopen that returns the given response."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read.return_value = json.dumps(response_body).encode()
    return cm


@pytest.fixture(autouse=True)
def _google_env(monkeypatch):
    """Provide the account-specific Google config the API helpers read from env."""
    monkeypatch.setenv("GCP_QUOTA_PROJECT", "example-quota-project")
    monkeypatch.setenv("GSC_SITE", "https://www.example.com/")
    monkeypatch.setenv("GA4_PROPERTY_ID", "123456789")


@pytest.fixture(autouse=True)
def _fake_credentials():
    """Patch google.auth.default to return a fake credential with a valid token."""
    creds = MagicMock()
    creds.valid = True
    creds.token = "fake-token-123"
    with patch(
        "agentic_research_loop.google_api.google.auth.default",
        return_value=(creds, "proj"),
    ):
        import agentic_research_loop.google_api as mod

        mod._credentials = None
        yield creds
        mod._credentials = None


class TestGscQuery:
    def test_basic_query(self):
        response = {"rows": [{"keys": ["example"], "clicks": 100}]}
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen(response)
        ) as mock:
            result = gsc_query("2026-03-01", "2026-04-06", ["query"])

            assert result == response
            call_args = mock.call_args[0][0]
            assert call_args.method == "POST"
            assert "searchAnalytics/query" in call_args.full_url
            body = json.loads(call_args.data)
            assert body["dimensions"] == ["query"]
            assert body["startDate"] == "2026-03-01"
            assert body["rowLimit"] == 100
            assert body["startRow"] == 0

    def test_pagination_params(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            gsc_query(
                "2026-03-01", "2026-04-06", ["query"], row_limit=50, start_row=200
            )

            body = json.loads(mock.call_args[0][0].data)
            assert body["rowLimit"] == 50
            assert body["startRow"] == 200

    def test_multiple_dimensions(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            gsc_query("2026-03-01", "2026-04-06", ["query", "page", "date"])

            body = json.loads(mock.call_args[0][0].data)
            assert body["dimensions"] == ["query", "page", "date"]

    def test_auth_headers(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            gsc_query("2026-03-01", "2026-04-06", ["query"])

            req = mock.call_args[0][0]
            assert req.get_header("Authorization") == "Bearer fake-token-123"
            assert req.get_header("X-goog-user-project") == "example-quota-project"


class TestGa4Report:
    def test_basic_report(self):
        response = {
            "rows": [
                {
                    "dimensionValues": [{"value": "/"}],
                    "metricValues": [{"value": "100"}],
                }
            ]
        }
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen(response)
        ) as mock:
            result = ga4_report(
                "2026-03-01", "2026-04-06", ["pagePath"], ["screenPageViews"]
            )

            assert result == response
            body = json.loads(mock.call_args[0][0].data)
            assert body["dimensions"] == [{"name": "pagePath"}]
            assert body["metrics"] == [{"name": "screenPageViews"}]
            assert body["limit"] == 25
            assert body["offset"] == 0
            assert "orderBys" not in body

    def test_order_by(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            ga4_report(
                "2026-03-01",
                "2026-04-06",
                ["pagePath"],
                ["sessions"],
                order_by="sessions",
            )

            body = json.loads(mock.call_args[0][0].data)
            assert body["orderBys"] == [
                {"metric": {"metricName": "sessions"}, "desc": True}
            ]

    def test_pagination(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            ga4_report(
                "2026-03-01",
                "2026-04-06",
                ["pagePath"],
                ["sessions"],
                limit=50,
                offset=100,
            )

            body = json.loads(mock.call_args[0][0].data)
            assert body["limit"] == 50
            assert body["offset"] == 100

    def test_auth_headers(self):
        with patch.object(
            urllib.request, "urlopen", return_value=_mock_urlopen({})
        ) as mock:
            ga4_report("2026-03-01", "2026-04-06", ["pagePath"], ["sessions"])

            req = mock.call_args[0][0]
            assert req.get_header("Authorization") == "Bearer fake-token-123"
            assert req.get_header("X-goog-user-project") == "example-quota-project"


class TestAuthErrors:
    def test_missing_credentials_raises_google_auth_error(self):
        import google.auth.exceptions

        import agentic_research_loop.google_api as mod

        mod._credentials = None
        with patch(
            "agentic_research_loop.google_api.google.auth.default",
            side_effect=google.auth.exceptions.DefaultCredentialsError("not found"),
        ):
            with pytest.raises(GoogleAuthError, match="ADC credentials not found"):
                gsc_query("2026-03-01", "2026-04-06", ["query"])

    def test_refresh_failure_raises_google_auth_error(self):
        import google.auth.exceptions

        import agentic_research_loop.google_api as mod

        creds = MagicMock()
        creds.valid = False
        creds.refresh.side_effect = google.auth.exceptions.RefreshError("expired")
        mod._credentials = creds
        with pytest.raises(GoogleAuthError, match="Token refresh failed"):
            gsc_query("2026-03-01", "2026-04-06", ["query"])
        assert mod._credentials is None


class TestApiErrors:
    def test_http_error_raises_google_api_error(self):
        error_body = b'{"error":{"message":"Invalid dimension"}}'
        http_error = urllib.error.HTTPError(
            url="https://example.test",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=BytesIO(error_body),
        )

        with patch.object(urllib.request, "urlopen", side_effect=http_error):
            with pytest.raises(GoogleApiError, match="400"):
                gsc_query("2026-03-01", "2026-04-06", ["badDimension"])

    def test_url_error_raises_google_api_error(self):
        with patch.object(
            urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("network down"),
        ):
            with pytest.raises(GoogleApiError, match="network down"):
                ga4_report("2026-03-01", "2026-04-06", ["pagePath"], ["sessions"])
