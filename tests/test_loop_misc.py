from __future__ import annotations

from pathlib import Path

import pytest


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
