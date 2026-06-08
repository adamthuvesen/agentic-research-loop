from __future__ import annotations

from pathlib import Path

from agentic_research_loop.cli import build_parser
from agentic_research_loop.runner import (
    BUILTIN_RUNNERS,
    builtin_runner_path,
    invoke_runner,
    load_runner_config,
)


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


def test_runner_streams_and_truncates_large_output(tmp_path: Path) -> None:
    config_path = tmp_path / "runner.json"
    config_path.write_text(
        """
{
  "command": [
    "python3",
    "-c",
    "import sys; sys.stdout.write('A' * 2000 + '<promise>CYCLE_DONE</promise>\\\\n')"
  ],
  "prompt_via_stdin": true,
  "timeout_seconds": 30,
  "max_output_bytes": 20,
  "agent_message_tail_bytes": 128,
  "env": {}
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = invoke_runner(
        load_runner_config(config_path),
        repo_root=tmp_path,
        context={},
        prompt_text="prompt",
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        agent_message_path=tmp_path / "agent_message.md",
    )

    assert result["returncode"] == 0
    assert result["stdout_truncated"] is True
    assert result["stdout_bytes"] > 20
    assert "output truncated" in (tmp_path / "stdout.log").read_text(encoding="utf-8")
    assert "<promise>CYCLE_DONE</promise>" in (tmp_path / "agent_message.md").read_text(
        encoding="utf-8"
    )
