from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from agentic_research_loop.cli import main
from agentic_research_loop.google_api import GoogleApiError


_GSC_RESPONSE = {
    "rows": [
        {
            "keys": ["example"],
            "clicks": 500,
            "impressions": 10000,
            "ctr": 0.05,
            "position": 3.2,
        }
    ]
}

_GA4_RESPONSE = {
    "dimensionHeaders": [{"name": "pagePath"}],
    "metricHeaders": [{"name": "screenPageViews", "type": "TYPE_INTEGER"}],
    "rows": [
        {
            "dimensionValues": [{"value": "/app/home"}],
            "metricValues": [{"value": "339035"}],
        }
    ],
}


class TestGscCli:
    def test_basic_gsc_query(self, capsys):
        with patch(
            "agentic_research_loop.google_api.gsc_query", return_value=_GSC_RESPONSE
        ) as mock_gsc:
            exit_code = main(
                [
                    "gsc",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query",
                ]
            )

        assert exit_code == 0
        mock_gsc.assert_called_once_with(
            start_date="2026-03-01",
            end_date="2026-04-06",
            dimensions=["query"],
            row_limit=100,
            start_row=0,
        )
        output = json.loads(capsys.readouterr().out)
        assert "rows" in output

    def test_gsc_with_pagination(self):
        with patch(
            "agentic_research_loop.google_api.gsc_query", return_value=_GSC_RESPONSE
        ) as mock_gsc:
            exit_code = main(
                [
                    "gsc",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query,page",
                    "--row-limit",
                    "50",
                    "--start-row",
                    "200",
                ]
            )

        assert exit_code == 0
        mock_gsc.assert_called_once_with(
            start_date="2026-03-01",
            end_date="2026-04-06",
            dimensions=["query", "page"],
            row_limit=50,
            start_row=200,
        )

    def test_gsc_missing_required_args(self):
        try:
            main(["gsc", "--start-date", "2026-03-01", "--end-date", "2026-04-06"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 2

    def test_gsc_rejects_negative_start_row(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "gsc",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query",
                    "--start-row",
                    "-1",
                ]
            )
        assert excinfo.value.code == 2

    def test_gsc_rejects_invalid_date(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "gsc",
                    "--start-date",
                    "2026-02-31",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query",
                ]
            )
        assert excinfo.value.code == 2

    def test_gsc_rejects_inverted_date_range(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "gsc",
                    "--start-date",
                    "2026-04-06",
                    "--end-date",
                    "2026-03-01",
                    "--dimensions",
                    "query",
                ]
            )
        assert excinfo.value.code == 2

    def test_gsc_rejects_blank_dimension_token(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "gsc",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query,",
                ]
            )
        assert excinfo.value.code == 2

    def test_gsc_api_errors_are_printed_without_traceback(self, capsys):
        with patch(
            "agentic_research_loop.google_api.gsc_query",
            side_effect=GoogleApiError("Google API request failed (400): bad request"),
        ):
            exit_code = main(
                [
                    "gsc",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "query",
                ]
            )

        assert exit_code == 1
        assert "bad request" in capsys.readouterr().err


class TestGa4Cli:
    def test_basic_ga4_report(self, capsys):
        with patch(
            "agentic_research_loop.google_api.ga4_report", return_value=_GA4_RESPONSE
        ) as mock_ga4:
            exit_code = main(
                [
                    "ga4",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "screenPageViews,sessions",
                ]
            )

        assert exit_code == 0
        mock_ga4.assert_called_once_with(
            start_date="2026-03-01",
            end_date="2026-04-06",
            dimensions=["pagePath"],
            metrics=["screenPageViews", "sessions"],
            limit=25,
            offset=0,
            order_by=None,
        )
        output = json.loads(capsys.readouterr().out)
        assert "rows" in output

    def test_ga4_with_order_by(self):
        with patch(
            "agentic_research_loop.google_api.ga4_report", return_value=_GA4_RESPONSE
        ) as mock_ga4:
            exit_code = main(
                [
                    "ga4",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "sessions",
                    "--order-by",
                    "sessions",
                    "--limit",
                    "50",
                    "--offset",
                    "10",
                ]
            )

        assert exit_code == 0
        mock_ga4.assert_called_once_with(
            start_date="2026-03-01",
            end_date="2026-04-06",
            dimensions=["pagePath"],
            metrics=["sessions"],
            limit=50,
            offset=10,
            order_by="sessions",
        )

    def test_ga4_rejects_zero_limit(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "ga4",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "sessions",
                    "--limit",
                    "0",
                ]
            )
        assert excinfo.value.code == 2

    def test_ga4_rejects_invalid_date(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "ga4",
                    "--start-date",
                    "not-a-date",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "sessions",
                ]
            )
        assert excinfo.value.code == 2

    def test_ga4_rejects_inverted_date_range(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "ga4",
                    "--start-date",
                    "2026-04-06",
                    "--end-date",
                    "2026-03-01",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "sessions",
                ]
            )
        assert excinfo.value.code == 2

    def test_ga4_rejects_blank_metric_token(self):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "ga4",
                    "--start-date",
                    "2026-03-01",
                    "--end-date",
                    "2026-04-06",
                    "--dimensions",
                    "pagePath",
                    "--metrics",
                    "sessions,,activeUsers",
                ]
            )
        assert excinfo.value.code == 2
