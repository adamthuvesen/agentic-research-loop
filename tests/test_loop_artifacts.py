from __future__ import annotations

import json
from pathlib import Path


from tests.support.loop_helpers import make_case

from agentic_research_loop.loop import (
    apply_cycle_result,
    artifact_snapshot,
    compute_progress,
    mutable_artifact_texts,
)
from agentic_research_loop.runtime_artifacts import (
    partial_progress_artifact_texts,
    protected_input_texts,
    protected_inputs_changed,
    restore_artifacts,
)
from agentic_research_loop.runtime_state import CycleSummary


def test_compute_progress_detects_notes_change() -> None:
    before = {"notes_hash": "aaa", "report_hash": "bbb"}
    after = {"notes_hash": "ccc", "report_hash": "bbb"}
    assert compute_progress(before, after) is True


def test_compute_progress_detects_report_change() -> None:
    before = {"notes_hash": "aaa", "report_hash": "bbb"}
    after = {"notes_hash": "aaa", "report_hash": "ddd"}
    assert compute_progress(before, after) is True


def test_compute_progress_returns_false_when_unchanged() -> None:
    before = {"notes_hash": "aaa", "report_hash": "bbb"}
    after = {"notes_hash": "aaa", "report_hash": "bbb"}
    assert compute_progress(before, after) is False


def test_mutable_artifact_texts_has_expected_keys(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)
    backup = mutable_artifact_texts(inv, snapshot=snapshot)
    assert "notes.md" in backup
    assert "report.md" in backup
    assert "plan.md" in backup
    assert "state/sources.json" in backup
    assert "state/progress.json" in backup
    assert "state/findings.json" not in backup


def test_artifact_helpers_restore_and_detect_changes(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    mutable = mutable_artifact_texts(inv)
    protected = protected_input_texts(inv)

    (inv / "notes.md").write_text("changed notes", encoding="utf-8")
    (inv / "brief.md").write_text("changed brief", encoding="utf-8")

    assert partial_progress_artifact_texts(inv, mutable) == {
        "notes.md": "changed notes"
    }
    assert protected_inputs_changed(inv, protected) == ["brief.md"]

    restore_artifacts(inv, mutable)
    restore_artifacts(inv, protected)

    assert (inv / "notes.md").read_text(encoding="utf-8") == mutable["notes.md"]
    assert (inv / "brief.md").read_text(encoding="utf-8") == protected["brief.md"]


def test_artifact_snapshot_has_no_findings(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)
    assert "findings" not in snapshot
    assert "finding_ids" not in snapshot
    assert "notes_hash" in snapshot
    assert "report_hash" in snapshot


def test_failed_cycle_breaks_no_progress_streak(tmp_path: Path) -> None:
    case_path = make_case(tmp_path)
    progress_path = case_path / "state" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["consecutive_no_progress_cycles"] = 2
    progress["consecutive_failures"] = 0
    progress_path.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")

    updated = apply_cycle_result(
        case_path,
        CycleSummary.from_payload(
            {
                "cycle_id": "0002",
                "completed_at": "2026-05-22T00:00:00+00:00",
                "result": "failed",
                "made_progress": False,
                "attempts": [{"attempt": 1}],
            }
        ),
        runner_name="claude",
    )

    assert updated["consecutive_no_progress_cycles"] == 0
    assert updated["consecutive_failures"] == 1


def test_artifact_snapshot_handles_invalid_sources_json(tmp_path: Path) -> None:
    case_path = make_case(tmp_path)
    (case_path / "state" / "sources.json").write_text(
        "{ not valid json", encoding="utf-8"
    )

    snapshot = artifact_snapshot(case_path)  # must not raise
    assert snapshot["sources"] == {}
    assert snapshot["sources_parse_error"] is not None
    assert (
        "not valid json" in snapshot["sources_parse_error"]
        or snapshot["sources_parse_error"]
    )


def test_apply_cycle_result_normalizes_agent_written_complete(tmp_path: Path) -> None:
    case_path = make_case(tmp_path)
    progress_path = case_path / "state" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["status"] = "complete"
    progress_path.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")

    updated = apply_cycle_result(
        case_path,
        CycleSummary.from_payload(
            {
                "cycle_id": "0001",
                "completed_at": "2026-05-07T00:00:00+00:00",
                "result": "no_progress",
                "made_progress": False,
                "attempts": [{"attempt": 1}],
            }
        ),
        runner_name="claude",
    )

    assert updated["status"] == "active"
    assert updated["stop_reason"] is None
