"""End-to-end smoke test for the offline `demo` runner.

Runs the real loop wiring (config/runners/demo.json + runners/demo_runner.py)
against the bundled synthetic data in examples/local-sources/, with no network
or LLM. Guards the showcase: the demo must always reach a completed case with a
challenge review.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agentic_research_loop.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def project_cwd(monkeypatch) -> Path:
    monkeypatch.chdir(PROJECT_ROOT)
    return PROJECT_ROOT


def _research_dirs() -> set[Path]:
    research = PROJECT_ROOT / "research"
    return set(research.iterdir()) if research.exists() else set()


def test_demo_runner_completes_case_offline(project_cwd: Path) -> None:
    before = _research_dirs()
    case_path: Path | None = None
    try:
        assert (
            main(
                [
                    "init",
                    "demo-smoke",
                    "--template",
                    "root-cause",
                    "--mode",
                    "autonomous",
                    "--context-path",
                    "examples/local-sources",
                ]
            )
            == 0
        )
        new_dirs = _research_dirs() - before
        assert len(new_dirs) == 1
        case_path = new_dirs.pop()

        exit_code = main(
            ["run", case_path.name, "--runner", "demo", "--max-cycles", "6"]
        )
        assert exit_code == 0

        report = (case_path / "report.md").read_text(encoding="utf-8")
        assert "## Challenge Review" in report
        assert "success rate" in report.lower()
        assert "scheduler" in report.lower()
        # The report quotes a figure computed from the bundled CSV.
        assert "%" in report

        import json

        progress = json.loads(
            (case_path / "state" / "progress.json").read_text(encoding="utf-8")
        )
        assert progress["status"] == "complete"
        assert progress["last_challenge_outcome"] == "passed"
    finally:
        if case_path is not None and case_path.exists():
            shutil.rmtree(case_path)
