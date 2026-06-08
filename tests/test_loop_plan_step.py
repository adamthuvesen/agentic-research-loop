from __future__ import annotations

import json
from pathlib import Path


from tests.support.loop_helpers import init_with_question, make_case

from agentic_research_loop.cli import main
from agentic_research_loop.loop import is_plan_blank, run_loop, run_plan_step


def test_plan_step_restores_non_plan_artifacts(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "plan-boundary", "Can the planning step mutate other files?"
    )
    original_brief = (case_path / "brief.md").read_text(encoding="utf-8")
    original_notes = (case_path / "notes.md").read_text(encoding="utf-8")
    original_report = (case_path / "report.md").read_text(encoding="utf-8")
    original_sources = (case_path / "state" / "sources.json").read_text(
        encoding="utf-8"
    )

    mutating_planner = repo_root / "mutating_planner.py"
    mutating_planner.write_text(
        """
from __future__ import annotations

import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
(case_dir / "plan.md").write_text(
    "# Research Plan\\n\\n### T1: Real plan\\n**Status:** pending\\n",
    encoding="utf-8",
)
(case_dir / "brief.md").write_text("mutated brief", encoding="utf-8")
(case_dir / "notes.md").write_text("mutated notes", encoding="utf-8")
(case_dir / "report.md").write_text("mutated report", encoding="utf-8")
(case_dir / "state" / "sources.json").write_text("{}", encoding="utf-8")
""".strip()
        + "\n",
        encoding="utf-8",
    )
    runner_config = {
        "command": ["python3", str(mutating_planner), "{case_dir}"],
        "prompt_via_stdin": True,
        "timeout_seconds": 30,
        "env": {},
    }
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(runner_config, indent=2) + "\n",
        encoding="utf-8",
    )

    assert run_plan_step(repo_root, case_path, runner_name="claude") is True
    assert "### T1: Real plan" in (case_path / "plan.md").read_text(encoding="utf-8")
    assert (case_path / "brief.md").read_text(encoding="utf-8") == original_brief
    assert (case_path / "notes.md").read_text(encoding="utf-8") == original_notes
    assert (case_path / "report.md").read_text(encoding="utf-8") == original_report
    assert (case_path / "state" / "sources.json").read_text(
        encoding="utf-8"
    ) == original_sources


def test_plan_step_rejects_nonzero_runner_and_restores_plan(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root, "plan-failure", "Can a failed planner leave partial output?"
    )
    original_plan = (case_path / "plan.md").read_text(encoding="utf-8")

    failing_planner = repo_root / "failing_planner.py"
    failing_planner.write_text(
        """
import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
(case_dir / "plan.md").write_text(
    "# Research Plan\\n\\n### T1: Partial invalid plan\\n",
    encoding="utf-8",
)
sys.exit(2)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(
            {
                "command": ["python3", str(failing_planner), "{case_dir}"],
                "prompt_via_stdin": True,
                "timeout_seconds": 30,
                "env": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    assert run_plan_step(repo_root, case_path, runner_name="claude") is False
    assert (case_path / "plan.md").read_text(encoding="utf-8") == original_plan


def test_run_loop_stops_when_initial_plan_fails(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "plan-fails-before-cycle",
        "Do failed planners start a research cycle?",
    )

    failing_planner = repo_root / "failing_initial_planner.py"
    failing_planner.write_text(
        """
import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
(case_dir / "plan.md").write_text(
    "# Research Plan\\n\\n### T1: Partial invalid plan\\n",
    encoding="utf-8",
)
sys.exit(2)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(
            {
                "command": ["python3", str(failing_planner), "{case_dir}"],
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
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )

    assert summaries == []
    assert progress["cycle_count"] == 0
    assert progress["stop_reason"] == "planning_failed"
    assert not (case_path / "state" / "cycles" / "0001").exists()


def test_cli_run_returns_failure_when_initial_plan_fails(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = init_with_question(
        repo_root,
        "plan-fails-cli",
        "Does the CLI report planning failure?",
    )

    failing_planner = repo_root / "failing_cli_planner.py"
    failing_planner.write_text(
        """
import sys
sys.exit(2)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "runners" / "claude.json").write_text(
        json.dumps(
            {
                "command": ["python3", str(failing_planner)],
                "prompt_via_stdin": True,
                "timeout_seconds": 30,
                "env": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["run", case_path.name, "--max-cycles", "1"])

    assert exit_code == 1


def test_is_plan_blank_returns_false_for_prose_mentioning_sentinel(
    tmp_path: Path,
) -> None:
    make_case(tmp_path)
    (tmp_path / "plan.md").write_text(
        "# Research Plan\n\nSupersedes the 'No plan yet' placeholder from cycle 1.\n",
        encoding="utf-8",
    )
    assert not is_plan_blank(tmp_path)


def test_is_plan_blank_returns_true_for_literal_sentinel(tmp_path: Path) -> None:
    make_case(tmp_path)
    (tmp_path / "plan.md").write_text(
        "# Research Plan\n\nNo plan yet. Run `research plan <id>` to generate one.\n",
        encoding="utf-8",
    )
    assert is_plan_blank(tmp_path)


def test_is_plan_blank_returns_true_for_empty(tmp_path: Path) -> None:
    make_case(tmp_path)
    (tmp_path / "plan.md").write_text("", encoding="utf-8")
    assert is_plan_blank(tmp_path)
