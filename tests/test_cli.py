from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research_loop.cli import main
from agentic_research_loop.research import resolve_case_path


def test_init_creates_guided_workspace(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        ["init", "regional-comparison", "--template", "comparison", "--mode", "guided"]
    )

    assert exit_code == 0
    case_dirs = sorted((repo_root / "research").iterdir())
    assert len(case_dirs) == 1
    case_path = case_dirs[0]
    assert case_path.name.endswith("regional-comparison")
    assert (case_path / "notes.md").exists()
    assert (case_path / "status.md").exists()


def test_init_notes_include_hypothesis_research_sections(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        ["init", "hypothesis-ledger", "--template", "exploration", "--mode", "guided"]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    notes = (case_path / "notes.md").read_text(encoding="utf-8")
    for heading in (
        "## Working Theory",
        "## Hypotheses",
        "## Evidence Log",
        "## Dead Ends",
        "## Open Questions",
        "## Leads",
    ):
        assert heading in notes
    assert "**Strongest rival:**" in notes
    assert "**Discriminating test:**" in notes


def test_init_sets_consecutive_failures_to_zero(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        ["init", "failure-counter", "--template", "exploration", "--mode", "guided"]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    progress = __import__("json").loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    assert progress["consecutive_failures"] == 0


def test_init_registers_confidence_source(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        [
            "init",
            "signup-rollout",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--confidence-hint",
            "signup funnel",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    sources = __import__("json").loads(
        (case_path / "state" / "sources.json").read_text(encoding="utf-8")
    )
    assert sources["confidence_mcp"]["enabled"] is True
    assert sources["confidence_mcp"]["focus"] == "signup funnel"
    assert sources["notion_mcp"]["enabled"] is True
    assert sources["web_search"]["enabled"] is True


def test_init_registers_source_hints(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        [
            "init",
            "onboarding-change",
            "--template",
            "exploration",
            "--mode",
            "guided",
            "--notion-hint",
            "Onboarding DB",
            "--web-search-hint",
            "competitor launch",
            "--snowflake-hint",
            "user funnel",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    sources = __import__("json").loads(
        (case_path / "state" / "sources.json").read_text(encoding="utf-8")
    )
    assert sources["notion_mcp"]["target"] == "Onboarding DB"
    assert sources["web_search"]["focus"] == "competitor launch"
    assert sources["snowflake"]["focus"] == "user funnel"


def test_init_omits_disabled_source_hints_from_brief(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(
        [
            "init",
            "disabled-source-hint",
            "--template",
            "exploration",
            "--mode",
            "guided",
            "--no-notion",
            "--notion-hint",
            "Do not search this database",
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    brief_text = (case_path / "brief.md").read_text(encoding="utf-8")
    assert "Notion" not in brief_text
    assert "Do not search this database" not in brief_text


def test_init_no_findings_file_on_init(repo_root: Path, monkeypatch) -> None:
    """findings.json is no longer created on init."""
    monkeypatch.chdir(repo_root)

    exit_code = main(
        ["init", "reg-drop", "--template", "root-cause", "--mode", "autonomous"]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    assert not (case_path / "state" / "findings.json").exists()


def test_init_attaches_context_path(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    context_dir = repo_root / "context-pack"
    context_dir.mkdir()
    (context_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")

    exit_code = main(
        [
            "init",
            "onboarding-ctx",
            "--template",
            "exploration",
            "--mode",
            "guided",
            "--context-path",
            str(context_dir),
        ]
    )

    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    sources = __import__("json").loads(
        (case_path / "state" / "sources.json").read_text(encoding="utf-8")
    )
    assert len(sources["local_context_folders"]) == 1


def test_init_rejects_missing_context_path(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)

    with pytest.raises(FileNotFoundError, match="Local context path"):
        main(
            [
                "init",
                "missing-context",
                "--template",
                "exploration",
                "--mode",
                "guided",
                "--context-path",
                str(repo_root / "does-not-exist"),
            ]
        )


def test_feedback_subcommand_is_removed(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "reg-drop-fb", "--template", "root-cause", "--mode", "autonomous"])
    case_path = sorted((repo_root / "research").iterdir())[0]

    with pytest.raises(SystemExit) as excinfo:
        main(["feedback", case_path.name, "--note", "x"])
    assert excinfo.value.code == 2


def test_init_does_not_create_feedback_json(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    exit_code = main(
        ["init", "no-feedback-json", "--template", "exploration", "--mode", "guided"]
    )
    assert exit_code == 0
    case_path = sorted((repo_root / "research").iterdir())[0]
    assert not (case_path / "state" / "feedback.json").exists()


def test_run_resolves_short_slug(repo_root: Path, monkeypatch) -> None:
    """Short slug (without date prefix) should resolve to the date-prefixed case dir."""
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "active-users-drop",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )

    # Run with just the short slug — must not raise FileNotFoundError
    exit_code = main(["run", "active-users-drop", "--max-cycles", "1"])
    assert exit_code == 0


def test_run_rejects_zero_max_cycles(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "bad-cycle-limit", "--template", "root-cause", "--mode", "autonomous"]
    )

    with pytest.raises(SystemExit) as excinfo:
        main(["run", "bad-cycle-limit", "--max-cycles", "0"])

    assert excinfo.value.code == 2


def test_resolve_case_path_ambiguous(repo_root: Path, monkeypatch) -> None:
    """Ambiguous short slug (multiple date-prefixed matches) raises a clear error."""
    monkeypatch.chdir(repo_root)
    research = repo_root / "research"
    research.mkdir(exist_ok=True)
    (research / "2026-01-01-foo").mkdir()
    (research / "2026-01-02-foo").mkdir()

    with pytest.raises(FileNotFoundError, match="Ambiguous"):
        resolve_case_path(repo_root, "foo")


def test_resolve_case_path_rejects_traversal_fallback(repo_root: Path) -> None:
    (repo_root / "research").mkdir()
    (repo_root / "src").mkdir()

    with pytest.raises(FileNotFoundError, match="outside"):
        resolve_case_path(repo_root, "../src")


def test_status_command_handles_malformed_status_json(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "bad-status-json", "--template", "exploration", "--mode", "guided"])
    case_path = sorted((repo_root / "research").iterdir())[0]
    (case_path / "state" / "status.json").write_text("{ bad", encoding="utf-8")

    exit_code = main(["status", case_path.name])

    assert exit_code == 1
    assert "status.json not found or invalid" in capsys.readouterr().out


def test_status_command_tolerates_malformed_secondary_state(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "bad-secondary-state", "--template", "exploration", "--mode", "guided"]
    )
    case_path = sorted((repo_root / "research").iterdir())[0]
    (case_path / "state" / "progress.json").write_text("{ bad", encoding="utf-8")
    (case_path / "state" / "sources.json").write_text("[]\n", encoding="utf-8")
    cycle_path = case_path / "state" / "cycles" / "0001"
    cycle_path.mkdir(parents=True)
    (cycle_path / "cycle_summary.json").write_text("{ bad", encoding="utf-8")

    exit_code = main(["status", case_path.name])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Cycle count: `0`" in output
    assert "Sources in play: `none`" in output
    assert "No completed cycles yet" in output
