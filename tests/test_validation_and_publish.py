from __future__ import annotations

import json
from pathlib import Path

from agentic_research_loop.cli import main
from agentic_research_loop.validation import (
    collect_validation_warnings,
    report_has_substance,
    validate_case,
)


def _first_case(repo_root: Path) -> Path:
    cases = sorted((repo_root / "research").iterdir())
    return cases[0]


def test_validate_passes_for_new_guided_workspace(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "exec-summary", "--template", "exploration", "--mode", "guided"])

    exit_code = main(["validate", str(_first_case(repo_root))])

    assert exit_code == 0


def test_validate_warns_for_root_cause_plan_missing_design_fields(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "reg-drop-warn", "--template", "root-cause", "--mode", "autonomous"])
    case_path = _first_case(repo_root)
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Source:** Snowflake\n"
        "**Objective:** Confirm the drop.\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )

    warnings = collect_validation_warnings(case_path)

    assert any("missing `Discriminating Test`" in warning for warning in warnings)
    assert any("missing `Completion Threshold`" in warning for warning in warnings)


def test_validate_strict_fails_for_root_cause_plan_missing_design_fields(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "reg-drop-strict", "--template", "root-cause", "--mode", "autonomous"]
    )
    case_path = _first_case(repo_root)
    (case_path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Source:** Snowflake\n"
        "**Objective:** Confirm the drop.\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )
    (case_path / "report.md").write_text(
        "# Research Report\n\n## Question\n\nWhy did registrations drop after launch?\n\n## Executive Summary\n\nThe report points to launch friction as the leading cause, with enough supporting detail to exceed the strict content threshold.\n",
        encoding="utf-8",
    )

    exit_code = main(["validate", str(case_path), "--strict"])

    assert exit_code == 1


def test_golden_root_cause_example_has_no_design_warnings() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    golden_path = (
        repo_root / "tests" / "golden_investigations" / "root-cause-registration-drop"
    )

    warnings = collect_validation_warnings(golden_path)

    assert warnings == []


def test_publish_creates_finding(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "reg-drop-publish", "--template", "root-cause", "--mode", "autonomous"]
    )
    case_path = _first_case(repo_root)

    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    progress["pending_challenge_cycle"] = False
    progress["last_challenge_outcome"] = "passed"
    (case_path / "state" / "findings.json").write_text(
        json.dumps(
            [
                {
                    "id": "F1",
                    "summary": "Registrations fell after launch per Snowflake data.",
                    "confidence": 0.9,
                },
                {
                    "id": "F2",
                    "summary": "Launch friction is the leading explanation based on timing.",
                    "confidence": 0.8,
                },
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )
    (case_path / "plan.md").write_text(_FULL_PLAN, encoding="utf-8")
    (case_path / "report.md").write_text(
        "# Research Report\n\n## Question\n\nWhy did registrations drop after launch?\n\n"
        "## Executive Summary\n\nThe report points to launch friction as the leading "
        "cause, with enough supporting detail to meet the strict publishing gate.\n\n"
        "## Ranked Causes\n\n- Launch friction\n",
        encoding="utf-8",
    )

    exit_code = main(["publish", case_path.name])

    assert exit_code == 0
    published = case_path / "published.md"
    assert published.exists()
    finding_text = published.read_text(encoding="utf-8")
    assert "Short Answer" in finding_text
    assert "Source Families Used" in finding_text
    assert "Research Shifts" in finding_text
    assert "Ruled Out Or Weakened Leads" in finding_text
    assert "Research Caveats" in finding_text


def test_publish_skips_malformed_cycle_summaries(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "publish-bad-cycle-summary",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    case_path = _first_case(repo_root)
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    progress["pending_challenge_cycle"] = False
    progress["last_challenge_outcome"] = "passed"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )
    (case_path / "plan.md").write_text(_FULL_PLAN, encoding="utf-8")
    (case_path / "report.md").write_text(_MEANINGFUL_REPORT, encoding="utf-8")
    cycle_path = case_path / "state" / "cycles" / "0001"
    cycle_path.mkdir(parents=True)
    (cycle_path / "cycle_summary.json").write_text("{ bad", encoding="utf-8")

    exit_code = main(["publish", case_path.name])

    assert exit_code == 0
    published = (case_path / "published.md").read_text(encoding="utf-8")
    assert "No recorded case shifts." in published


def test_validate_fails_for_missing_brief(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "test-missing-brief", "--template", "exploration", "--mode", "guided"]
    )
    case_path = _first_case(repo_root)
    (case_path / "brief.md").unlink()

    exit_code = main(["validate", str(case_path)])

    assert exit_code == 1


def test_validate_strict_fails_for_empty_report(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "test-empty-report", "--template", "exploration", "--mode", "guided"])
    case_path = _first_case(repo_root)
    (case_path / "report.md").write_text("# Report\n", encoding="utf-8")
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )

    exit_code = main(["validate", str(case_path), "--strict"])

    assert exit_code == 1


def test_validate_strict_fails_for_missing_report(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "test-no-report", "--template", "exploration", "--mode", "guided"])
    case_path = _first_case(repo_root)
    (case_path / "report.md").unlink()
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )

    exit_code = main(["validate", str(case_path), "--strict"])

    assert exit_code == 1


def test_validate_strict_reports_malformed_progress_object(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "bad-progress", "--template", "exploration", "--mode", "guided"])
    case_path = _first_case(repo_root)
    (case_path / "state" / "progress.json").write_text("[]\n", encoding="utf-8")
    (case_path / "report.md").write_text(
        "# Research Report\n\n## Executive Summary\n\n"
        "This report has enough content that strict validation should fail only on "
        "the malformed progress payload, not crash while checking completion gates.\n",
        encoding="utf-8",
    )

    exit_code = main(["validate", str(case_path), "--strict"])

    assert exit_code == 1


def test_validate_reports_malformed_progress_fields(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "bad-progress-fields",
            "--template",
            "exploration",
            "--mode",
            "guided",
        ]
    )
    case_path = _first_case(repo_root)
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["cycle_count"] = "one"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )

    errors = validate_case(case_path)

    assert errors == ["cycle_count must be an integer"]


def test_validate_reports_invalid_progress_json(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "bad-progress-json",
            "--template",
            "exploration",
            "--mode",
            "guided",
        ]
    )
    case_path = _first_case(repo_root)
    (case_path / "state" / "progress.json").write_text("{ bad", encoding="utf-8")

    errors = validate_case(case_path)

    assert errors == [
        "progress.json is invalid JSON: Expecting property name enclosed in double quotes"
    ]


def test_validate_rejects_malformed_findings_json(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "bad-findings-json", "--template", "exploration", "--mode", "guided"])
    case_path = _first_case(repo_root)
    (case_path / "state" / "findings.json").write_text("{ bad", encoding="utf-8")

    errors = validate_case(case_path)

    assert errors == [
        "findings.json is invalid JSON: Expecting property name enclosed in double quotes"
    ]


def test_validate_rejects_findings_schema_errors(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "bad-findings-schema", "--template", "exploration", "--mode", "guided"]
    )
    case_path = _first_case(repo_root)
    (case_path / "state" / "findings.json").write_text(
        json.dumps([{"id": "", "summary": "ok"}, {"id": "F2"}, "not an object"]) + "\n",
        encoding="utf-8",
    )

    errors = validate_case(case_path)

    assert errors == [
        "findings[0].id must be a non-empty string",
        "findings[1].summary must be a non-empty string",
        "findings[2] must be a JSON object",
    ]


def test_publish_rejects_incomplete_case(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "test-publish-reject", "--template", "exploration", "--mode", "guided"]
    )
    case_path = _first_case(repo_root)
    # Replace the report with trivial content that fails the substance check
    (case_path / "report.md").write_text("# Report\n\nToo short.\n", encoding="utf-8")
    # Mark as complete so strict validation kicks in
    progress = json.loads(
        (case_path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    (case_path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )

    import pytest as _pytest

    with _pytest.raises(ValueError, match="not ready to publish"):
        from agentic_research_loop.publish import publish

        publish(case_path)


def test_report_has_substance_requires_executive_summary() -> None:
    report = (
        "# Research Report\n\n## Question\n\n"
        "Why did registrations drop across all acquisition channels after launch?\n\n"
        "## Current Picture\n\nThis is not the executive summary.\n"
    )

    assert report_has_substance(report) is False


def test_report_has_substance_rejects_placeholder_summary() -> None:
    report = (
        "# Research Report\n\n## Executive Summary\n\n"
        "Fill in the executive summary before publishing.\n"
    )

    assert report_has_substance(report) is False


def test_status_command(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(["init", "test-status", "--template", "exploration", "--mode", "guided"])
    case_path = _first_case(repo_root)

    exit_code = main(["status", case_path.name])

    assert exit_code == 0


# --- Helpers for new validation tests ---

_FULL_PLAN = (
    "# Research Plan\n\n"
    "### T1: Check metrics\n"
    "**Priority:** high\n"
    "**Source:** Snowflake\n"
    "**Objective:** Confirm the drop.\n"
    "**Discriminating Test:** Segment by cohort.\n"
    "**Completion Threshold:** done when leading slice is explicit.\n"
    "**Strongest Rival:** Composition shift.\n"
    "**Cross-Check:** Validate in a second source.\n"
    "**Status:** pending\n"
)

_MEANINGFUL_REPORT = (
    "# Research Report\n\n## Question\n\nWhy did registrations drop after launch?\n\n"
    "## Executive Summary\n\nThe report points to launch friction as the leading cause, "
    "with enough supporting detail to exceed the strict content threshold.\n"
)


def _setup_complete_autonomous(
    repo_root: Path, monkeypatch, slug: str, **progress_overrides
):
    """Scaffold a complete autonomous root-cause case with all required files."""
    monkeypatch.chdir(repo_root)
    main(["init", slug, "--template", "root-cause", "--mode", "autonomous"])
    path = _first_case(repo_root)
    (path / "plan.md").write_text(_FULL_PLAN, encoding="utf-8")
    (path / "report.md").write_text(_MEANINGFUL_REPORT, encoding="utf-8")
    progress = json.loads(
        (path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    progress.update(progress_overrides)
    (path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )
    return path


# --- H1: Challenge-cycle gate tests ---


def test_strict_fails_when_challenge_cycle_pending(
    repo_root: Path, monkeypatch
) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "challenge-pending",
        pending_challenge_cycle=True,
        last_challenge_outcome=None,
    )

    errors = validate_case(path, strict_completion=True)

    assert any("challenge cycle" in e for e in errors)


def test_strict_fails_when_challenge_outcome_not_passed(
    repo_root: Path, monkeypatch
) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "challenge-failed",
        pending_challenge_cycle=False,
        last_challenge_outcome="failed",
    )

    errors = validate_case(path, strict_completion=True)

    assert any("challenge cycle" in e for e in errors)


def test_strict_passes_when_challenge_cycle_passed(
    repo_root: Path, monkeypatch
) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "challenge-passed",
        pending_challenge_cycle=False,
        last_challenge_outcome="passed",
    )

    errors = validate_case(path, strict_completion=True)

    assert not any("challenge cycle" in e for e in errors)


def test_non_autonomous_skips_challenge_check(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        ["init", "guided-no-challenge", "--template", "exploration", "--mode", "guided"]
    )
    path = _first_case(repo_root)
    (path / "report.md").write_text(_MEANINGFUL_REPORT, encoding="utf-8")
    progress = json.loads(
        (path / "state" / "progress.json").read_text(encoding="utf-8")
    )
    progress["status"] = "complete"
    (path / "state" / "progress.json").write_text(
        json.dumps(progress, indent=2) + "\n", encoding="utf-8"
    )

    errors = validate_case(path, strict_completion=True)

    assert not any("challenge cycle" in e for e in errors)


# --- H2: Strongest Rival promotion + N/A escape ---


def test_strict_fails_when_strongest_rival_missing(
    repo_root: Path, monkeypatch
) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "rival-missing",
        pending_challenge_cycle=False,
        last_challenge_outcome="passed",
    )
    # Rewrite plan without Strongest Rival
    (path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Discriminating Test:** Segment by cohort.\n"
        "**Completion Threshold:** done when leading slice is explicit.\n"
        "**Cross-Check:** Validate in a second source.\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )

    errors = validate_case(path, strict_completion=True)

    assert any("missing `Strongest Rival`" in e for e in errors)


def test_strict_passes_with_na_strongest_rival(repo_root: Path, monkeypatch) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "rival-na",
        pending_challenge_cycle=False,
        last_challenge_outcome="passed",
    )
    (path / "plan.md").write_text(
        "# Research Plan\n\n"
        "### T1: Check metrics\n"
        "**Priority:** high\n"
        "**Discriminating Test:** Segment by cohort.\n"
        "**Completion Threshold:** done when leading slice is explicit.\n"
        "**Strongest Rival:** N/A — single explanation fits all evidence\n"
        "**Cross-Check:** Validate in a second source.\n"
        "**Status:** pending\n",
        encoding="utf-8",
    )

    errors = validate_case(path, strict_completion=True)

    assert not any("missing `Strongest Rival`" in e for e in errors)


# --- M1: Source plan derivation ---


def test_manual_init_no_gsc_excludes_gsc_from_brief(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "no-gsc-test",
            "--template",
            "exploration",
            "--mode",
            "guided",
            "--no-gsc",
        ]
    )
    path = _first_case(repo_root)
    brief_text = (path / "brief.md").read_text(encoding="utf-8")

    assert "GSC" not in brief_text


# --- Design-only strict checks (safe at scaffold time) ---


_PLAN_MISSING_DISCRIMINATING_TEST = (
    "# Research Plan\n\n"
    "### T1: Check metrics\n"
    "**Priority:** high\n"
    "**Source:** Snowflake\n"
    "**Objective:** Confirm the drop.\n"
    "**Completion Threshold:** done when leading slice is explicit.\n"
    "**Strongest Rival:** Composition shift.\n"
    "**Cross-Check:** Validate in a second source.\n"
    "**Status:** pending\n"
)


def test_design_flag_enforces_contract_without_challenge_gate(
    repo_root: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "design-flag-fails",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    path = _first_case(repo_root)
    (path / "plan.md").write_text(_PLAN_MISSING_DISCRIMINATING_TEST, encoding="utf-8")

    errors = validate_case(path, strict_design=True)
    exit_code = main(["validate", str(path), "--design"])
    output = capsys.readouterr().out

    assert any("missing `Discriminating Test`" in e for e in errors)
    assert not any("challenge cycle" in e for e in errors)
    assert not any("report.md" in e for e in errors)
    assert exit_code == 1
    assert "Validation warnings:" not in output
    assert output.count("missing `Discriminating Test`") == 1


def test_design_flag_enforces_missing_root_cause_sections(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "missing-design-sections",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    path = _first_case(repo_root)
    (path / "brief.md").write_text(
        "# Research Brief\n\n"
        "## Question\n\nWhy?\n\n"
        "## Mode\n\n"
        "- Selected mode: `autonomous`\n"
        "- Research shape: `root-cause`\n",
        encoding="utf-8",
    )
    (path / "plan.md").write_text("# Research Plan\n\nNo plan yet.\n", encoding="utf-8")

    errors = validate_case(path, strict_design=True)

    assert any("`## Hypotheses`" in error for error in errors)
    assert any("`## Known Confounders`" in error for error in errors)
    assert any("`## Required Cross-Checks`" in error for error in errors)
    assert any("no research threads" in error for error in errors)


def test_design_flag_passes_with_clean_plan(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "design-flag-passes",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    path = _first_case(repo_root)
    (path / "plan.md").write_text(_FULL_PLAN, encoding="utf-8")

    errors = validate_case(path, strict_design=True)

    assert errors == []


_PLAN_MISSING_CROSS_CHECK = (
    "# Research Plan\n\n"
    "### T1: Check metrics\n"
    "**Priority:** high\n"
    "**Source:** Snowflake\n"
    "**Objective:** Confirm the drop.\n"
    "**Discriminating Test:** Segment by cohort.\n"
    "**Completion Threshold:** done when leading slice is explicit.\n"
    "**Strongest Rival:** Composition shift.\n"
    "**Status:** pending\n"
)


def test_design_flag_enforces_cross_check(repo_root: Path, monkeypatch) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "cross-check-fails",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
        ]
    )
    path = _first_case(repo_root)
    (path / "plan.md").write_text(_PLAN_MISSING_CROSS_CHECK, encoding="utf-8")

    errors = validate_case(path, strict_design=True)

    assert any("missing `Cross-Check`" in e for e in errors)


def test_strict_completion_error_distinguishes_not_run_from_failed(
    repo_root: Path, monkeypatch
) -> None:
    path_not_run = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "challenge-never-run",
        pending_challenge_cycle=False,
        last_challenge_outcome=None,
    )
    errors_not_run = validate_case(path_not_run, strict_completion=True)

    not_run_errors = [e for e in errors_not_run if "challenge cycle" in e]
    assert not_run_errors, "expected a challenge-cycle error for never-run case"
    assert any("has not run one yet" in e for e in not_run_errors)
    assert any("validate --design" in e for e in not_run_errors)

    path_failed = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "challenge-failed-outcome",
        pending_challenge_cycle=False,
        last_challenge_outcome="failed",
    )
    errors_failed = validate_case(path_failed, strict_completion=True)

    failed_errors = [e for e in errors_failed if "challenge cycle" in e]
    assert failed_errors, "expected a challenge-cycle error for failed case"
    assert any("last outcome: 'failed'" in e for e in failed_errors)
    assert not any("has not run one yet" in e for e in failed_errors)


def test_manual_init_default_sources_include_builtins(
    repo_root: Path, monkeypatch
) -> None:
    monkeypatch.chdir(repo_root)
    main(
        [
            "init",
            "default-sources-test",
            "--template",
            "exploration",
            "--mode",
            "guided",
        ]
    )
    path = _first_case(repo_root)
    brief_text = (path / "brief.md").read_text(encoding="utf-8")

    # After the bundle migration the default built-ins are GSC + web search;
    # everything else is an opt-in bundle (enable with `research source enable`).
    assert "GSC" in brief_text
    assert "Web tools" in brief_text


def test_publish_rejects_missing_executive_summary(
    repo_root: Path, monkeypatch
) -> None:
    path = _setup_complete_autonomous(
        repo_root,
        monkeypatch,
        "missing-executive-summary",
        pending_challenge_cycle=False,
        last_challenge_outcome="passed",
    )
    (path / "report.md").write_text(
        "# Research Report\n\n## Question\n\nWhy?\n\n"
        "## Conclusion\n\nThis conclusion has enough words to be substantive, but "
        "publish requires the executive summary heading specifically.\n",
        encoding="utf-8",
    )

    from agentic_research_loop.publish import publish

    import pytest as _pytest

    with _pytest.raises(ValueError, match="Executive Summary"):
        publish(path)
