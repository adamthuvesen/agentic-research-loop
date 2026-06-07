from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research_loop.cli import main


def _spec_dir(tmp_path: Path, **files: str) -> Path:
    """Create a spec directory with the given files."""
    spec = tmp_path / "spec-input"
    spec.mkdir()
    for name, content in files.items():
        (spec / name).write_text(content, encoding="utf-8")
    return spec


def test_init_from_spec_all_three_files(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    brief = (
        "# Research Brief\n\n"
        "## Question\n\nWhy did the metric move?\n\n"
        "## Hypotheses\n\n- H1: real shift\n- H2: attribution\n\n"
        "## Source Registry\n\n- placeholder, should be replaced\n"
    )
    plan = "# Custom Plan\n\n## T1: hand-authored thread\n"
    notes = "# Custom Notes\n\n- working theory: X\n"
    spec = _spec_dir(
        tmp_path, **{"brief.md": brief, "plan.md": plan, "notes.md": notes}
    )

    exit_code = main(
        [
            "init",
            "pricing-impact",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--from-spec",
            str(spec),
            "--web-search-hint",
            "payments table for ARPU pre/post",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    brief_out = (case_path / "brief.md").read_text(encoding="utf-8")
    plan_out = (case_path / "plan.md").read_text(encoding="utf-8")
    notes_out = (case_path / "notes.md").read_text(encoding="utf-8")

    # Supplied content preserved
    assert "Why did the metric move?" in brief_out
    assert "H1: real shift" in brief_out
    assert "- Selected mode: `autonomous`" in brief_out
    assert "- Research shape: `root-cause`" in brief_out
    assert plan_out == plan
    assert notes_out == notes

    # Source Registry spliced with CLI hint, placeholder gone
    assert "placeholder, should be replaced" not in brief_out
    assert "payments table for ARPU pre/post" in brief_out
    assert "## Source Registry" in brief_out


def test_init_from_spec_partial_fallback(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    brief = "# Research Brief\n\n## Question\n\nAsked question\n"
    spec = _spec_dir(tmp_path, **{"brief.md": brief})

    exit_code = main(
        [
            "init",
            "partial-case",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--from-spec",
            str(spec),
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    brief_out = (case_path / "brief.md").read_text(encoding="utf-8")
    plan_out = (case_path / "plan.md").read_text(encoding="utf-8")
    notes_out = (case_path / "notes.md").read_text(encoding="utf-8")

    assert "Asked question" in brief_out
    assert "- Selected mode: `autonomous`" in brief_out
    assert "- Research shape: `root-cause`" in brief_out
    assert "## Source Registry" in brief_out
    # plan & notes should fall back to default templates
    assert plan_out != ""
    assert notes_out != ""
    assert "Asked question" not in plan_out


def test_init_from_spec_missing_dir_fails(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    missing = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError) as exc_info:
        main(
            [
                "init",
                "missing-dir",
                "--template",
                "root-cause",
                "--mode",
                "autonomous",
                "--from-spec",
                str(missing),
            ]
        )
    assert str(missing) in str(exc_info.value)


def test_init_from_spec_empty_dir_warns_and_uses_defaults(
    repo_root: Path, tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.chdir(repo_root)
    empty = tmp_path / "empty"
    empty.mkdir()

    exit_code = main(
        [
            "init",
            "empty-spec",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--from-spec",
            str(empty),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "empty" in captured.err
    case_path = sorted((repo_root / "research").iterdir())[0]
    # Default template content shows up
    brief_out = (case_path / "brief.md").read_text(encoding="utf-8")
    assert "# Research Brief" in brief_out
    assert "## Source Registry" in brief_out


def test_init_without_from_spec_unchanged(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        [
            "init",
            "no-from-spec",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    brief_out = (case_path / "brief.md").read_text(encoding="utf-8")
    # Default template produces these markers
    assert "# Research Brief" in brief_out
    assert "## Research Design Contract" not in brief_out  # brief doesn't have this
    assert "## Source Registry" in brief_out
    plan_out = (case_path / "plan.md").read_text(encoding="utf-8")
    # Default plan has the design contract header for root-cause/autonomous
    assert "Research Plan" in plan_out or "plan" in plan_out.lower()


def test_init_from_spec_brief_without_source_registry_header(
    repo_root: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    brief = "# Research Brief\n\n## Question\n\nQ?\n\n## Scope\n\n- in scope: X\n"
    spec = _spec_dir(tmp_path, **{"brief.md": brief})

    exit_code = main(
        [
            "init",
            "no-sr-header",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--from-spec",
            str(spec),
            "--web-search-hint",
            "custom web hint",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    brief_out = (case_path / "brief.md").read_text(encoding="utf-8")
    # Source Registry should be appended since original had no header
    assert "## Source Registry" in brief_out
    assert "custom web hint" in brief_out
    # Original content preserved
    assert "in scope: X" in brief_out
