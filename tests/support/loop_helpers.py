from __future__ import annotations

import json
from pathlib import Path

from agentic_research_loop.cli import main


def init_with_question(
    repo_root: Path,
    slug: str,
    question: str,
    *,
    template: str = "root-cause",
    mode: str = "autonomous",
    extra_args: list[str] | None = None,
) -> Path:
    """Create a case via init and inject a custom question into brief.md."""
    cmd = ["init", slug, "--template", template, "--mode", mode]
    if extra_args:
        cmd.extend(extra_args)
    main(cmd)
    case_path = sorted((repo_root / "research").iterdir())[-1]
    brief = case_path / "brief.md"
    text = brief.read_text(encoding="utf-8")
    text = text.replace(f"Research: {slug}", question)
    brief.write_text(text, encoding="utf-8")
    return case_path


def make_case(tmp_path: Path) -> Path:
    inv = tmp_path / "state"
    inv.mkdir(parents=True)
    (tmp_path / "brief.md").write_text(
        "# Research Brief\n\n## Question\n\nWhy?\n", encoding="utf-8"
    )
    (tmp_path / "report.md").write_text(
        "# Report\n\n## Executive Summary\n\nTest answer.\n", encoding="utf-8"
    )
    (tmp_path / "notes.md").write_text(
        "# Research Notes\n\n## Working Theory\n\n- Launch friction\n\n"
        "## Open Questions\n\n- Is it seasonal?\n",
        encoding="utf-8",
    )
    (inv / "progress.json").write_text(
        json.dumps(
            {
                "status": "active",
                "cycle_count": 1,
                "consecutive_no_progress_cycles": 0,
                "stop_reason": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (inv / "sources.json").write_text(
        json.dumps({"snowflake": {"enabled": True}}) + "\n", encoding="utf-8"
    )
    (inv / "status.json").write_text(
        json.dumps(
            {
                "status": "idle",
                "case_id": "test-case",
                "mode": "autonomous",
                "template": "root-cause",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (inv / "cycles").mkdir()
    (tmp_path / "plan.md").write_text(
        "# Research Plan\n\nNo plan yet.\n", encoding="utf-8"
    )
    (tmp_path / "status.md").write_text("# Research Status\n", encoding="utf-8")
    return tmp_path
