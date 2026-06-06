from __future__ import annotations

from pathlib import Path

from agentic_research_loop.cli import build_parser
from agentic_research_loop.runner import BUILTIN_RUNNERS, builtin_runner_path


def test_run_resume_plan_default_runner_is_claude() -> None:
    parser = build_parser()
    for cmd in ("run", "resume", "plan"):
        args = parser.parse_args([cmd, "inv-1"])
        assert args.runner == "claude"


def test_runner_codex_is_accepted() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "inv-1", "--runner", "codex"])
    assert args.runner == "codex"


def test_builtin_runner_filenames() -> None:
    root = Path("/repo")
    assert builtin_runner_path(root, "claude") == root / "config/runners/claude.json"
    assert builtin_runner_path(root, "codex") == root / "config/runners/codex.json"
    assert builtin_runner_path(root, "demo") == root / "config/runners/demo.json"
    assert (
        builtin_runner_path(root, "claude-local")
        == root / "config/runners/claude-local.json"
    )
    assert set(BUILTIN_RUNNERS) == {"claude", "codex", "demo", "claude-local"}
