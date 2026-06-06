from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_ci_runs_ruff_format_check() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "uv run ruff check ." in workflow
    assert "uv run ruff format --check ." in workflow
    assert workflow.index("uv run ruff check .") < workflow.index(
        "uv run ruff format --check ."
    )
