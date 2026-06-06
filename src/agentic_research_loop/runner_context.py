from __future__ import annotations

from pathlib import Path


def build_runner_context(
    *,
    repo_root: Path,
    case_path: Path,
    cycle_dir: Path,
    prompt_file: Path,
    agent_message_file: Path,
    cycle_id: str,
) -> dict[str, str]:
    return {
        "repo_root": str(repo_root.resolve()),
        "case_dir": str(case_path.resolve()),
        "cycle_dir": str(cycle_dir.resolve()),
        "prompt_file": str(prompt_file.resolve()),
        "agent_message_file": str(agent_message_file.resolve()),
        "cycle_id": cycle_id,
    }
