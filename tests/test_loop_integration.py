from __future__ import annotations

import json
from pathlib import Path

from tests.support.loop_helpers import init_with_question

from agentic_research_loop.cli import main
from agentic_research_loop.loop import run_loop


def test_run_executes_a_cycle_with_fake_runner(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "reg-drop", "Why did registrations drop after the launch?"
    )
    # Pre-populate plan so the plan step doesn't run and consume the first diff
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Check metrics\n**Status:** pending\n",
        encoding="utf-8",
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    assert (case_path / "state" / "cycles" / "0001" / "cycle_summary.json").exists()
    summary = json.loads(
        (case_path / "state" / "cycles" / "0001" / "cycle_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["result"] == "progress"
    status = (case_path / "status.md").read_text(encoding="utf-8")
    assert "## Current Answer" in status
    assert "## Recent Cycles" in status


def test_mixed_source_rollout_case(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "rollout-signup", "Did the rollout hurt signup?"
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    report = (case_path / "report.md").read_text(encoding="utf-8")
    assert "rollout as the leading cause" in report


def test_mixed_source_context_case(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    context_dir = repo_root / "history-pack"
    context_dir.mkdir()
    (context_dir / "onboarding-rollout.md").write_text(
        "# rollout history\n", encoding="utf-8"
    )
    case_path = init_with_question(
        repo_root,
        "onboarding-ctx",
        "Give me the historical onboarding context",
        template="exploration",
        mode="guided",
        extra_args=["--context-path", str(context_dir)],
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    report = (case_path / "report.md").read_text(encoding="utf-8")
    assert (
        "stitched together curated context, historical docs, and local notes" in report
    )


def test_mixed_source_notion_web_case(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "workspace-redesign",
        "Explain the workspace redesign external context",
        template="exploration",
        mode="guided",
        extra_args=[
            "--gsc-hint",
            "Workspace redesign",
            "--web-search-hint",
            "competitor launch",
        ],
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    report = (case_path / "report.md").read_text(encoding="utf-8")
    assert "live workspace context, internal notes, and external context" in report


def test_no_progress_increments_stall_counter(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "stalled-source", "Investigate the stalled source path"
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    assert progress["consecutive_no_progress_cycles"] == 1


def test_challenge_cycle_can_confirm_completion(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "challenge-confirm",
        "Investigate the case that survives challenge immediately",
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "2"])

    assert exit_code == 0
    first_summary = json.loads(
        (case_path / "state" / "cycles" / "0001" / "cycle_summary.json").read_text(
            encoding="utf-8"
        )
    )
    second_summary = json.loads(
        (case_path / "state" / "cycles" / "0002" / "cycle_summary.json").read_text(
            encoding="utf-8"
        )
    )
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    report = (case_path / "report.md").read_text(encoding="utf-8")
    notes = (case_path / "notes.md").read_text(encoding="utf-8")

    assert first_summary["result"] == "challenge_required"
    assert first_summary["challenge_cycle"] is False
    assert first_summary["completion_marker"] == "CASE_COMPLETE"
    assert second_summary["result"] == "complete"
    assert second_summary["challenge_cycle"] is True
    assert second_summary["completion_marker"] == "CASE_COMPLETE"
    assert progress["status"] == "complete"
    assert progress["pending_challenge_cycle"] is False
    assert progress["last_challenge_outcome"] == "passed"
    assert "## Challenge Review" in report
    assert "Outcome: Resolved." in report
    assert "Resolution status: resolved." in notes


def test_challenge_cycle_can_reopen_case(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "challenge-reopen",
        "Investigate the case that reopens after challenge",
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "2"])

    assert exit_code == 0
    first_summary = json.loads(
        (case_path / "state" / "cycles" / "0001" / "cycle_summary.json").read_text(
            encoding="utf-8"
        )
    )
    second_summary = json.loads(
        (case_path / "state" / "cycles" / "0002" / "cycle_summary.json").read_text(
            encoding="utf-8"
        )
    )
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    report = (case_path / "report.md").read_text(encoding="utf-8")
    notes = (case_path / "notes.md").read_text(encoding="utf-8")

    assert first_summary["result"] == "challenge_required"
    assert first_summary["challenge_cycle"] is False
    assert second_summary["result"] == "progress"
    assert second_summary["challenge_cycle"] is True
    assert second_summary["completion_marker"] == "CYCLE_DONE"
    assert progress["status"] == "active"
    assert progress["pending_challenge_cycle"] is False
    assert progress["last_challenge_outcome"] == "reopened"
    assert "## Challenge Review" in report
    assert "Outcome: Unresolved." in report
    assert "Resolution status: unresolved." in notes


def test_io_read_count_per_cycle(repo_root: Path, monkeypatch) -> None:
    """Per-cycle file reads must stay within budget."""
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "active-users-q1", "Why are active users missing the Q1 target?"
    )

    import agentic_research_loop.io as io_module

    read_calls: list[str] = []
    _orig_read = io_module.read_text
    _orig_load = io_module.load_json
    _orig_load_object = io_module.load_json_object_or_empty

    def _counting_read(path: Path) -> str:
        read_calls.append(f"read_text:{path.name}")
        return _orig_read(path)

    def _counting_load(path: Path):
        read_calls.append(f"load_json:{path.name}")
        return _orig_load(path)

    def _counting_load_object(path: Path):
        read_calls.append(f"load_json_object_or_empty:{path.name}")
        return _orig_load_object(path)

    monkeypatch.setattr(io_module, "read_text", _counting_read)
    monkeypatch.setattr(io_module, "load_json", _counting_load)
    monkeypatch.setattr(io_module, "load_json_object_or_empty", _counting_load_object)

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 0
    assert "active users" in (case_path / "report.md").read_text(encoding="utf-8")

    total = len(read_calls)
    assert total <= 40, f"Too many I/O reads in one cycle: {total}\n" + "\n".join(
        f"  {c}" for c in read_calls
    )


def test_run_reports_elapsed_time_in_terminal_output(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "reg-drop-elapsed", "Why did registrations drop after the launch?"
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Elapsed" in captured.out
    assert "Stop reason" in captured.out


def test_run_terminal_header_says_research(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "header-title-check", "Why did signups drop in Q1?"
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Research" in captured.out
    assert "Business Research" not in captured.out


def test_successful_cycle_with_advisory_still_uses_progress_semantics(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "advisory-progress",
        "Why did registrations drop after the launch?",
    )
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Check metrics\n**Status:** pending\n",
        encoding="utf-8",
    )
    progress_path = case_path / "state" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["cycle_count"] = 1
    progress_path.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")

    summaries = run_loop(repo_root, case_path, runner_name="claude", max_cycles=1)

    assert summaries[0].result == "progress"
    assert summaries[0].made_progress is True


def test_retry_exhaustion_keeps_notes_from_first_attempt(
    repo_root: Path, monkeypatch
) -> None:
    """If attempt 1 wrote notes but attempt 2 failed, notes must survive exhaustion."""
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "partial-progress", "What is the partial progress case?"
    )
    # Pre-populate plan so planning step is skipped
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Check metrics\n**Status:** pending\n",
        encoding="utf-8",
    )
    failing_runner = repo_root / "partial_progress_runner.py"
    failing_runner.write_text(
        """
from __future__ import annotations

import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
counter_path = case_dir / "state" / "partial_counter.txt"
count = int(counter_path.read_text(encoding="utf-8")) if counter_path.exists() else 0
counter_path.write_text(str(count + 1), encoding="utf-8")
if count == 0:
    notes_path = case_dir / "notes.md"
    notes_path.write_text(
        notes_path.read_text(encoding="utf-8")
        + "\\n## Working Theory\\n\\n- new lead from attempt 1\\n",
        encoding="utf-8",
    )
""".strip()
        + "\n",
        encoding="utf-8",
    )
    runner_config = {
        "command": ["python3", str(failing_runner), "{case_dir}"],
        "prompt_via_stdin": True,
        "timeout_seconds": 30,
        "env": {},
    }
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(runner_config, indent=2) + "\n",
        encoding="utf-8",
    )

    run_loop(repo_root, case_path, runner_name="claude", max_cycles=1)

    final_notes = (case_path / "notes.md").read_text(encoding="utf-8")
    assert "new lead from attempt 1" in final_notes


def test_run_loop_stops_after_three_consecutive_failed_cycles(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "failure-limit", "What happens when the runner keeps failing?"
    )
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Check metrics\n**Status:** pending\n",
        encoding="utf-8",
    )

    failing_runner = repo_root / "always_fails_runner.py"
    failing_runner.write_text(
        "import sys\nsys.exit(42)\n",
        encoding="utf-8",
    )
    runner_config = {
        "command": ["python3", str(failing_runner)],
        "prompt_via_stdin": True,
        "timeout_seconds": 30,
        "env": {},
    }
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(runner_config, indent=2) + "\n",
        encoding="utf-8",
    )

    summaries = run_loop(repo_root, case_path, runner_name="claude", max_cycles=10)
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )

    assert [summary.result for summary in summaries] == ["failed"] * 3
    assert progress["consecutive_failures"] == 3
    assert progress["stop_reason"] == "consecutive_failures"


def test_failed_cycle_restores_plan_mutations(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "plan-restore", "Can failed attempts mutate the plan?"
    )
    original_plan = "# Research Plan\n\n### T1: Stable plan\n**Status:** pending\n"
    (case_path / "plan.md").write_text(original_plan, encoding="utf-8")

    failing_runner = repo_root / "plan_mutating_failure.py"
    failing_runner.write_text(
        """
import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
(case_dir / "plan.md").write_text("mutated plan", encoding="utf-8")
sys.exit(42)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(
            {
                "command": ["python3", str(failing_runner), "{case_dir}"],
                "prompt_via_stdin": True,
                "timeout_seconds": 30,
                "env": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    summaries = run_loop(repo_root, case_path, runner_name="claude", max_cycles=1)

    assert summaries[0].result == "failed"
    assert (case_path / "plan.md").read_text(encoding="utf-8") == original_plan


def test_challenge_cycle_requires_progress_and_review(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "noop-challenge",
        "Investigate the case with a no-op challenge cycle",
    )
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Stable plan\n**Status:** pending\n",
        encoding="utf-8",
    )
    progress_path = case_path / "state" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["pending_challenge_cycle"] = True
    progress["last_challenge_outcome"] = "queued"
    progress_path.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
    (case_path / "report.md").write_text(
        "# Research Report\n\n## Executive Summary\n\n"
        "This report already has enough content to be meaningful, but the challenge "
        "cycle still has to write review evidence before it can pass.\n",
        encoding="utf-8",
    )

    noop_runner = repo_root / "noop_challenge_runner.py"
    noop_runner.write_text(
        """
import sys
from pathlib import Path

message_path = Path(sys.argv[1])
message_path.write_text("<promise>CASE_COMPLETE</promise>\\n", encoding="utf-8")
print("<promise>CASE_COMPLETE</promise>")
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(
            {
                "command": ["python3", str(noop_runner), "{agent_message_file}"],
                "prompt_via_stdin": True,
                "timeout_seconds": 30,
                "env": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    summaries = run_loop(repo_root, case_path, runner_name="claude", max_cycles=1)
    progress = json.loads(progress_path.read_text(encoding="utf-8"))

    assert summaries[0].result == "failed"
    assert progress["pending_challenge_cycle"] is True
    assert progress["last_challenge_outcome"] == "queued"
