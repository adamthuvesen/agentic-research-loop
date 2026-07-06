from __future__ import annotations

from pathlib import Path

import pytest


from agentic_research_loop.cli import main
from agentic_research_loop.loop import case_requires_challenge
from agentic_research_loop.research import resolve_case_path


def test_resolve_case_path_raises_on_empty_identifier(repo_root: Path) -> None:

    with pytest.raises(FileNotFoundError, match="empty"):
        resolve_case_path(repo_root, "")


def test_resolve_case_path_raises_for_out_of_tree_path(
    repo_root: Path, tmp_path: Path
) -> None:

    # Create a directory outside research_dir
    outside = tmp_path / "outside-case"
    outside.mkdir()
    with pytest.raises(FileNotFoundError, match="outside"):
        resolve_case_path(repo_root, str(outside))


def test_case_requires_challenge_requires_status_json(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "challenge-state-required",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    case_path = sorted((repo_root / "research").iterdir())[0]
    (case_path / "state" / "status.json").unlink()

    with pytest.raises(FileNotFoundError, match="status.json"):
        case_requires_challenge(case_path)
