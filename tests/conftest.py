from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "agentic-research-loop"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        "[project]\nname = 'agentic-research-loop'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    (root / "program.md").write_text("# test program\n", encoding="utf-8")
    return root
