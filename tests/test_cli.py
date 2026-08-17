from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research_loop.cli import main
from agentic_research_loop.research import resolve_case_path

CASE_FILES = (
    "brief.md",
    "notes.md",
    "report.md",
    "queries.sql",
    "source-objects.md",
    "plan.md",
)


def _init(repo_root: Path, slug: str, *extra: str) -> Path:
    assert main(["init", slug, *extra]) == 0
    return sorted((repo_root / "research").iterdir())[-1]


def test_init_creates_the_case_artifacts(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    case_path = _init(repo_root, "regional-comparison", "--template", "comparison")

    assert case_path.name.endswith("regional-comparison")
    for name in CASE_FILES:
        assert (case_path / name).exists(), name


def test_init_creates_no_machine_state(repo_root: Path, monkeypatch) -> None:
    """Case artifacts are the only durable record; the goal owns execution state."""
    monkeypatch.chdir(repo_root)

    case_path = _init(repo_root, "no-state", "--template", "exploration")

    assert not (case_path / "state").exists()
    assert not (case_path / "status.md").exists()


def test_init_points_at_the_goal_command(repo_root: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(repo_root)

    _init(repo_root, "next-step", "--template", "exploration")

    assert "Next: uv run research goal" in capsys.readouterr().out


def test_init_notes_carry_the_research_sections(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    case_path = _init(repo_root, "hypothesis-ledger", "--template", "exploration")

    notes = (case_path / "notes.md").read_text(encoding="utf-8")
    for heading in (
        "## Working Theory",
        "## Hypotheses",
        "## Evidence Log",
        "## Dead Ends",
        "## Open Questions",
        "## Final Challenge",
    ):
        assert heading in notes


def test_init_records_source_hint_in_the_brief(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    case_path = _init(
        repo_root,
        "onboarding-change",
        "--template",
        "exploration",
        "--web-search-hint",
        "competitor launch",
    )

    brief = (case_path / "brief.md").read_text(encoding="utf-8")
    assert "competitor launch" in brief


def test_init_omits_disabled_source_hints_from_brief(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)

    case_path = _init(
        repo_root,
        "disabled-source-hint",
        "--template",
        "exploration",
        "--no-web-search",
        "--web-search-hint",
        "Do not search this database",
    )

    brief = (case_path / "brief.md").read_text(encoding="utf-8")
    assert "Web tools" not in brief
    assert "Do not search this database" not in brief


def test_init_attaches_context_path(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    context_dir = repo_root / "context-pack"
    context_dir.mkdir()
    (context_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")

    case_path = _init(
        repo_root,
        "onboarding-ctx",
        "--template",
        "exploration",
        "--context-path",
        str(context_dir),
    )

    brief = (case_path / "brief.md").read_text(encoding="utf-8")
    assert str(context_dir.resolve()) in brief


def test_init_rejects_missing_context_path(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    with pytest.raises(FileNotFoundError, match="Local context path"):
        main(
            [
                "init",
                "missing-context",
                "--template",
                "exploration",
                "--context-path",
                str(repo_root / "does-not-exist"),
            ]
        )


def test_init_uses_the_supplied_question(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    case_path = _init(
        repo_root,
        "specific-question",
        "--question",
        "Why did weekly exports fail more often in June?",
    )

    brief = (case_path / "brief.md").read_text(encoding="utf-8")
    assert "Why did weekly exports fail more often in June?" in brief


def test_goal_uses_absolute_paths_and_the_validation_gate(
    repo_root: Path, monkeypatch, capsys
) -> None:
    """A goal handed relative paths can write a correct answer into the wrong
    directory and still look finished. Every path in the contract is absolute."""
    monkeypatch.chdir(repo_root)
    case_path = _init(repo_root, "absolute-paths", "--template", "exploration")
    capsys.readouterr()

    assert main(["goal", case_path.name]) == 0

    output = capsys.readouterr().out
    assert output.startswith("/goal ")
    assert str(case_path.resolve()) in output
    assert f'uv run research validate "{case_path.resolve()}" --strict' in output
    assert "independent subagent" in output


def test_goal_names_the_cases_own_sources(repo_root: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(repo_root)
    context_dir = repo_root / "local-pack"
    context_dir.mkdir()
    case_path = _init(
        repo_root,
        "scoped-sources",
        "--local-only",
        "--context-path",
        str(context_dir),
    )
    capsys.readouterr()

    main(["goal", case_path.name])

    output = capsys.readouterr().out
    assert str(context_dir.resolve()) in output
    assert "Web tools" not in output


def test_goal_resolves_a_short_slug(repo_root: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(repo_root)
    _init(repo_root, "active-users-drop", "--template", "root-cause")
    capsys.readouterr()

    assert main(["goal", "active-users-drop"]) == 0
    assert capsys.readouterr().out.startswith("/goal ")


def test_validate_passes_on_a_fresh_case(repo_root: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(repo_root)
    case_path = _init(repo_root, "fresh-case", "--template", "exploration")
    capsys.readouterr()

    assert main(["validate", case_path.name]) == 0
    assert "Validation passed" in capsys.readouterr().out


def test_validate_reports_a_missing_artifact(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    case_path = _init(repo_root, "missing-artifact", "--template", "exploration")
    (case_path / "source-objects.md").unlink()
    capsys.readouterr()

    assert main(["validate", case_path.name]) == 1
    assert "Missing required file: source-objects.md" in capsys.readouterr().out


def test_resolve_case_path_ambiguous(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    research = repo_root / "research"
    research.mkdir(exist_ok=True)
    (research / "2026-01-01-foo").mkdir()
    (research / "2026-01-02-foo").mkdir()

    with pytest.raises(FileNotFoundError, match="Ambiguous"):
        resolve_case_path(repo_root, "foo")


def test_resolve_case_path_rejects_outside_short_slug_match(repo_root: Path) -> None:
    (repo_root / "research").mkdir()
    (repo_root / "src").mkdir()

    with pytest.raises(FileNotFoundError, match="outside"):
        resolve_case_path(repo_root, "../src")
