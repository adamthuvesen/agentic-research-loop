from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agentic_research_loop.validation import validate_case

COMPLETE_REPORT = """\
# Research Report

## Question

Why did weekly export failures rise in June 2026?

## Executive Summary

Weekly export failures rose from 2.1% to 6.4% in June, concentrated in the
large-workspace cohort after the June 3 scheduler change.

## Ranked Causes

1. The June 3 scheduler change.

## Evidence

Failure rate by week, from the weekly export.

## Reconciliation

Cohort failures sum to 412, matching the 412 total in the export.

## Rejected Leads

Storage quota: flat across the whole window.

## Risks And Caveats

A single static export; no live system cross-check was possible.
"""

COMPLETE_NOTES = """\
# Research Notes

## Evidence Log

- Claim: The failure rate reached 6.4% in June.
  - Source: exports_weekly.csv
  - Supports: H1
  - Caveat or freshness limit: Static export.

## Final Challenge

- Independent reviewer: {reviewer}
- Strongest competing explanation: A seasonal volume spike.
- Weakest-supported material claim: The June 3 attribution.
- Most fragile source or calculation: The single CSV export.
- Resolution: {resolution}
"""

BRIEF = """\
# Research Brief

## Question

Why did weekly export failures rise in June 2026?

## Scope

- Research shape: `exploration`

## Source Constraints

- Local context folder: /tmp/exports
"""


def build_case(
    tmp_path: Path,
    *,
    reviewer: str = "independent-subagent-challenger",
    resolution: str = "resolved after re-checking the change log",
    queries: str = "-- No SQL used: the case reads a CSV export directly.\n",
    brief: str = BRIEF,
    report: str = COMPLETE_REPORT,
) -> Path:
    case = tmp_path / "2026-08-17-exports"
    case.mkdir()
    (case / "brief.md").write_text(brief, encoding="utf-8")
    (case / "notes.md").write_text(
        COMPLETE_NOTES.format(reviewer=reviewer, resolution=resolution),
        encoding="utf-8",
    )
    (case / "report.md").write_text(report, encoding="utf-8")
    (case / "queries.sql").write_text(queries, encoding="utf-8")
    (case / "source-objects.md").write_text(
        "# Source Objects\n\n"
        "- examples/local-sources/exports_weekly.csv (accessed 2026-08-17)\n",
        encoding="utf-8",
    )
    return case


def test_complete_case_passes_strict(tmp_path: Path) -> None:
    assert validate_case(build_case(tmp_path), strict_completion=True) == []


def test_missing_artifact_is_reported(tmp_path: Path) -> None:
    case = build_case(tmp_path)
    (case / "source-objects.md").unlink()

    assert "Missing required file: source-objects.md" in validate_case(case)


# --- The independent challenge -------------------------------------------------
#
# The challenge is the one check an agent can fake by writing a plausible
# paragraph, so the reviewer field is where the strictness has to live.


@pytest.mark.parametrize(
    "reviewer",
    [
        "independent-subagent-challenger",
        "independent subagent reviewer 7",
        "Task(reviewer-a4f21)",
    ],
)
def test_strict_accepts_a_named_reviewer(tmp_path: Path, reviewer: str) -> None:
    """A real identifier may contain placeholder words without being a placeholder."""
    assert (
        validate_case(build_case(tmp_path, reviewer=reviewer), strict_completion=True)
        == []
    )


@pytest.mark.parametrize(
    "reviewer",
    [
        "main agent",
        "research agent",
        "me",
        "self",
        "<subagent name or task identifier>",
        "TBD",
    ],
)
def test_strict_rejects_self_review_and_placeholders(
    tmp_path: Path, reviewer: str
) -> None:
    errors = validate_case(
        build_case(tmp_path, reviewer=reviewer), strict_completion=True
    )

    assert any("Final Challenge" in error for error in errors)


def test_strict_rejects_a_bare_unresolved_challenge(tmp_path: Path) -> None:
    errors = validate_case(
        build_case(tmp_path, resolution="open"), strict_completion=True
    )

    assert any("Final Challenge" in error for error in errors)


def test_strict_accepts_a_disclosed_unresolved_challenge(tmp_path: Path) -> None:
    """Disclosing an objection you could not settle is allowed; hiding it is not."""
    assert (
        validate_case(
            build_case(
                tmp_path,
                resolution="unresolved because no live system was reachable",
            ),
            strict_completion=True,
        )
        == []
    )


# --- Read-only SQL -------------------------------------------------------------


def test_write_sql_is_rejected_without_strict(tmp_path: Path) -> None:
    case = build_case(
        tmp_path,
        queries="SELECT week FROM exports;\nDELETE FROM exports WHERE week = 1;\n",
    )

    assert any("forbidden write statement: DELETE" in e for e in validate_case(case))


def test_write_keyword_inside_a_string_literal_is_allowed(tmp_path: Path) -> None:
    case = build_case(
        tmp_path, queries="SELECT * FROM audit WHERE action = 'delete';\n"
    )

    assert validate_case(case, strict_completion=True) == []


def test_use_is_allowed_because_the_shipped_allowlist_permits_it(
    tmp_path: Path,
) -> None:
    case = build_case(
        tmp_path, queries="USE WAREHOUSE ANALYTICS;\nSELECT count(*) FROM exports;\n"
    )

    assert validate_case(case, strict_completion=True) == []


def test_strict_requires_preserved_sql_or_a_stated_reason(tmp_path: Path) -> None:
    case = build_case(tmp_path, queries="-- nothing preserved here\n")

    errors = validate_case(case, strict_completion=True)

    assert any("No SQL used" in error for error in errors)


# --- Report and question -------------------------------------------------------


def test_strict_rejects_a_placeholder_question(tmp_path: Path) -> None:
    brief = BRIEF.replace(
        "Why did weekly export failures rise in June 2026?",
        "Research: exports",
    )

    errors = validate_case(build_case(tmp_path, brief=brief), strict_completion=True)

    assert any("specific research question" in error for error in errors)


def test_strict_rejects_an_unwritten_report_section(tmp_path: Path) -> None:
    report = COMPLETE_REPORT.replace(
        "Cohort failures sum to 412, matching the 412 total in the export.",
        "Show how calculated contributions reconcile to the source total. "
        "If reconciliation does not apply, explain why.",
    )

    errors = validate_case(build_case(tmp_path, report=report), strict_completion=True)

    assert any("Reconciliation" in error for error in errors)


# --- Root-cause design contract ------------------------------------------------


def test_root_cause_brief_needs_its_design_sections(tmp_path: Path) -> None:
    brief = BRIEF.replace("`exploration`", "`root-cause`")

    errors = validate_case(build_case(tmp_path, brief=brief))

    assert any("Hypotheses" in error for error in errors)
    assert any("Known Confounders" in error for error in errors)
    assert any("Required Cross-Checks" in error for error in errors)


def test_high_priority_thread_needs_a_discriminating_test(tmp_path: Path) -> None:
    brief = BRIEF.replace("`exploration`", "`root-cause`") + textwrap.dedent("""
        ## Hypotheses

        - H1

        ## Known Confounders

        - Seasonality

        ## Required Cross-Checks

        - Second source
        """)
    case = build_case(tmp_path, brief=brief)
    (case / "plan.md").write_text(
        textwrap.dedent("""\
            # Research Plan

            ### T1: Scheduler change
            **Priority:** high
            **Strongest Rival:** Seasonal spike
            **Completion Threshold:** done when the cohort is named
            **Cross-Check:** change log
            """),
        encoding="utf-8",
    )

    errors = validate_case(case)

    assert any("Discriminating Test" in error for error in errors)


def test_committed_demo_case_passes_strict_validation() -> None:
    """The shipped example is the reference output shape; it has to clear the gate."""
    demo = Path(__file__).resolve().parents[1] / "examples" / "demo-export-reliability"

    assert validate_case(demo, strict_completion=True) == []


# --- Regressions -------------------------------------------------------------


def test_blank_fields_do_not_absorb_the_next_line(tmp_path: Path) -> None:
    """A `\\s*` gap after the colon would match the newline, so an empty field
    would take the following bullet as its value and the whole unfilled
    template would pass the completion gate."""
    notes = """\
# Research Notes

## Evidence Log

- Claim:
  - Source:
  - Supports:
  - Caveat or freshness limit:

## Final Challenge

- Independent reviewer:
- Strongest competing explanation: A seasonal volume spike.
- Weakest-supported material claim: The attribution.
- Most fragile source or calculation: The single export.
- Resolution: resolved after re-checking
"""
    case = build_case(tmp_path)
    (case / "notes.md").write_text(notes, encoding="utf-8")

    errors = validate_case(case, strict_completion=True)

    assert any("Evidence Log" in error for error in errors)
    assert any("Final Challenge" in error for error in errors)


def test_untouched_shipped_templates_fail_the_completion_gate(tmp_path: Path) -> None:
    from agentic_research_loop.templates import (
        notes_template,
        queries_template,
        report_template,
        source_objects_template,
    )

    case = build_case(tmp_path)
    (case / "notes.md").write_text(notes_template(), encoding="utf-8")
    (case / "report.md").write_text(
        report_template("exploration", "Why?"), encoding="utf-8"
    )
    (case / "queries.sql").write_text(queries_template(), encoding="utf-8")
    (case / "source-objects.md").write_text(source_objects_template(), encoding="utf-8")

    assert validate_case(case, strict_completion=True) != []


def test_an_unreadable_research_shape_is_an_error_not_a_silent_skip(
    tmp_path: Path,
) -> None:
    """Returning None here would skip the whole root-cause design contract while
    validation still reported success."""
    brief = BRIEF.replace(
        "- Research shape: `exploration`", "- Research shape: `bogus`"
    )

    errors = validate_case(build_case(tmp_path, brief=brief))

    assert any("unknown research shape" in error for error in errors)


def test_missing_research_shape_is_reported(tmp_path: Path) -> None:
    brief = BRIEF.replace("- Research shape: `exploration`\n", "")

    errors = validate_case(build_case(tmp_path, brief=brief))

    assert any("Research shape" in error for error in errors)


@pytest.mark.parametrize(
    "shape_line",
    [
        "- **Research shape:** `root-cause`",
        "- **Research shape**: `root-cause`",
        "- Research shape: `root-cause` (metric regression)",
        "- Research shape: `Root-Cause`",
    ],
)
def test_research_shape_survives_bold_and_trailing_text(
    tmp_path: Path, shape_line: str
) -> None:
    """A brief that annotates the shape line must still get the design contract."""
    brief = BRIEF.replace("- Research shape: `exploration`", shape_line)

    errors = validate_case(build_case(tmp_path, brief=brief))

    assert any("Hypotheses" in error for error in errors)


def test_select_into_is_rejected(tmp_path: Path) -> None:
    """`SELECT ... INTO` creates a table in Postgres and writes a file in MySQL."""
    case = build_case(
        tmp_path, queries="SELECT week INTO exports_snapshot FROM exports;\n"
    )

    assert any("INTO" in error for error in validate_case(case))
