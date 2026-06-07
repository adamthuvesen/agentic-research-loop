from __future__ import annotations

import json
from pathlib import Path

from agentic_research_loop.hints import build_cycle_hints


def _case(tmp_path: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir()
    (tmp_path / "brief.md").write_text("# Brief\n\n## Question\n\nWhy?\n")
    (tmp_path / "notes.md").write_text(
        "# Research Notes\n\n## Working Theory\n\n- Launch friction\n"
    )
    (tmp_path / "report.md").write_text("# Report\n")
    (tmp_path / "plan.md").write_text("# Plan\n")
    (state / "sources.json").write_text("{}\n")
    (state / "progress.json").write_text(
        json.dumps({"status": "active", "cycle_count": 1}) + "\n"
    )
    return tmp_path


def test_missing_hypothesis_ledger_hint_after_cycle(tmp_path: Path) -> None:
    case_path = _case(tmp_path)
    hints = build_cycle_hints(
        case_path,
        snapshot={
            "notes": (case_path / "notes.md").read_text(encoding="utf-8"),
            "report": (case_path / "report.md").read_text(encoding="utf-8"),
            "progress": {"cycle_count": 1},
        },
    )

    assert any("hypothesis ledger" in hint for hint in hints)


def test_no_retired_hypothesis_hint_after_multiple_cycles(tmp_path: Path) -> None:
    case_path = _case(tmp_path)
    notes = (
        "# Research Notes\n\n"
        "## Hypotheses\n\n"
        "### H1: Launch friction caused the drop\n"
        "- **Status:** active\n"
        "- **Why plausible:** Timing lines up.\n"
    )
    (case_path / "notes.md").write_text(notes, encoding="utf-8")

    hints = build_cycle_hints(
        case_path,
        snapshot={
            "notes": notes,
            "report": "# Report\n",
            "progress": {"cycle_count": 3},
        },
    )

    assert any("retire weak explanations" in hint for hint in hints)


def test_thin_evidence_hint_for_substantive_report(tmp_path: Path) -> None:
    case_path = _case(tmp_path)
    report = (
        "# Research Report\n\n"
        "## Executive Summary\n\n"
        "The current answer points to rollout friction as the leading cause, "
        "with enough detail to present but not yet fully evidenced in the log.\n"
    )

    hints = build_cycle_hints(
        case_path,
        snapshot={
            "notes": "# Research Notes\n\n## Hypotheses\n\n### H1: Rollout friction\n- **Status:** active\n",
            "report": report,
            "progress": {"cycle_count": 1},
        },
    )

    assert any("evidence log is thin" in hint for hint in hints)


def test_missing_thread_fields_hint(tmp_path: Path) -> None:
    case_path = _case(tmp_path)
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Source:** Snowflake\n"
        "**Objective:** Confirm the drop.\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )

    hints = build_cycle_hints(
        case_path,
        snapshot={"notes": "", "report": "", "progress": {"cycle_count": 0}},
    )

    assert any("High-priority thread design is incomplete" in hint for hint in hints)


def test_cycle_hints_are_capped(tmp_path: Path) -> None:
    case_path = _case(tmp_path)
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )
    report = (
        "# Research Report\n\n"
        "## Executive Summary\n\n"
        "The latest current live data points to launch friction as the leading "
        "cause with enough supporting prose to pass the substantive content check.\n"
    )

    hints = build_cycle_hints(
        case_path,
        snapshot={
            "notes": "# Research Notes\n",
            "report": report,
            "progress": {"cycle_count": 3},
        },
        limit=2,
    )

    assert len(hints) == 2
