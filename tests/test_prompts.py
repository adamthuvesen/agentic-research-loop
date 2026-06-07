from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.support.loop_helpers import make_case

from agentic_research_loop.loop import artifact_snapshot
from agentic_research_loop.prompts import (
    build_cycle_prompt,
    build_plan_prompt,
    render_hint_block,
    render_plan_block,
    render_research_move_block,
    render_stall_block,
    render_state_digest,
)
from agentic_research_loop.runner import render_shell_placeholders
from agentic_research_loop.status import executive_summary_excerpt


def test_render_state_digest_contains_expected_fields(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)
    block = render_state_digest(inv, snapshot)
    assert "## Where You Left Off" in block
    assert "**Cycle**: 1" in block
    assert "Launch friction" in block
    assert "seasonal" in block


def test_render_state_digest_tolerates_malformed_last_cycle_summary(
    tmp_path: Path,
) -> None:
    inv = make_case(tmp_path)
    cycle_path = inv / "state" / "cycles" / "0001"
    cycle_path.mkdir()
    (cycle_path / "cycle_summary.json").write_text("{ bad", encoding="utf-8")

    block = render_state_digest(inv, artifact_snapshot(inv))

    assert "**What happened last cycle**: none yet" in block


def test_render_state_digest_includes_leads_when_present(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    (tmp_path / "notes.md").write_text(
        "# Research Notes\n\n## Working Theory\n\n- Launch friction\n\n"
        "## Leads\n\n- **Churn spike in cohort X** [high]\n  Why it matters: unexpected\n  Next: check Confidence\n",
        encoding="utf-8",
    )
    snapshot = artifact_snapshot(inv)
    block = render_state_digest(inv, snapshot)
    assert "**Pending leads**" in block
    assert "Churn spike in cohort X" in block


def test_render_state_digest_omits_leads_when_absent(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)
    block = render_state_digest(inv, snapshot)
    assert "**Pending leads**" not in block


def test_executive_summary_excerpt_accepts_single_newline_after_heading() -> None:
    report = (
        "# Report\n\n## Executive Summary\nLine one.\n\nLine two.\n## Next\nMore.\n"
    )
    assert executive_summary_excerpt(report) == "Line one. Line two."


def test_build_cycle_prompt_has_no_human_feedback_section(tmp_path: Path) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)
    text = build_cycle_prompt(inv, snapshot=snapshot)
    assert "Human Feedback" not in text


def test_research_move_block_is_hypothesis_led() -> None:
    text = render_research_move_block()
    assert "1-2 active hypotheses" in text
    assert "strongest rival explanation" in text
    assert "evidence that would change your confidence" in text
    assert "Snowflake -> Confidence -> Notion still counts as one thread" in text


def test_build_cycle_prompt_includes_hypothesis_and_hint_blocks(
    tmp_path: Path,
) -> None:
    inv = make_case(tmp_path)
    snapshot = artifact_snapshot(inv)

    text = build_cycle_prompt(inv, snapshot=snapshot)

    assert "## This Cycle" in text
    assert "## Cycle Hints" in text
    assert "hypothesis ledger" in text


def test_render_stall_block_returns_none_at_zero(tmp_path: Path) -> None:
    snapshot = {"progress": {"consecutive_no_progress_cycles": 0}}
    result = render_stall_block(snapshot)
    assert result is None


def test_render_stall_block_returns_block_at_stall(tmp_path: Path) -> None:
    snapshot = {
        "progress": {"consecutive_no_progress_cycles": 2},
    }
    result = render_stall_block(snapshot)
    assert result is not None
    assert "## You've Been Stuck" in result
    assert "2 cycle(s)" in result
    assert "different angle" in result


def test_render_plan_block_shows_no_plan_when_blank(tmp_path: Path) -> None:
    make_case(tmp_path)
    (tmp_path / "plan.md").write_text(
        "# Research Plan\n\nNo plan yet.\n", encoding="utf-8"
    )
    block = render_plan_block(tmp_path)
    assert "No research plan yet" in block


def test_render_plan_block_shows_plan_when_present(tmp_path: Path) -> None:
    make_case(tmp_path)
    (tmp_path / "plan.md").write_text(
        "# Research Plan\n\n### T1: Check metrics\n**Status:** pending\n",
        encoding="utf-8",
    )
    block = render_plan_block(tmp_path)
    assert "T1" in block
    assert "Update thread statuses" in block


def test_build_plan_prompt_uses_stronger_contract_for_autonomous_root_cause(
    tmp_path: Path,
) -> None:
    make_case(tmp_path)
    (tmp_path / "brief.md").write_text(
        "# Research Brief\n\n"
        "## Question\n\nWhy did registrations drop?\n\n"
        "## Mode\n\n"
        "- Selected mode: `autonomous`\n"
        "- Research shape: `root-cause`\n",
        encoding="utf-8",
    )
    prompt = build_plan_prompt(tmp_path, tmp_path)
    assert "**Discriminating Test:**" in prompt
    assert "**Completion Threshold:**" in prompt
    assert "## Research design requirements" in prompt


def test_build_cycle_prompt_uses_challenge_contract_when_pending(
    tmp_path: Path,
) -> None:
    inv = make_case(tmp_path)
    progress_path = inv / "state" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["pending_challenge_cycle"] = True
    progress["last_challenge_outcome"] = "queued"
    progress_path.write_text(json.dumps(progress) + "\n", encoding="utf-8")

    prompt = build_cycle_prompt(inv, snapshot=artifact_snapshot(inv))

    assert "# Challenge Cycle" in prompt
    assert "## This Cycle" not in prompt
    assert "## Advisory Signals" not in prompt
    assert "## Cycle Hints" not in prompt
    assert "strongest competing explanation" in prompt
    assert "weakest-supported important claim" in prompt
    assert "most fragile source, freshness, or caveat dependency" in prompt
    assert "## Challenge Review" in prompt


def test_render_hint_block_propagates_signal_errors(
    tmp_path: Path, monkeypatch
) -> None:
    inv = make_case(tmp_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("nope")

    monkeypatch.setattr("agentic_research_loop.prompts.build_cycle_hints", _boom)

    with pytest.raises(RuntimeError, match="nope"):
        render_hint_block(inv, artifact_snapshot(inv))


def test_render_shell_placeholders_does_not_re_expand_substituted_values() -> None:
    context = {"case": "run-{date}", "date": "2026-04-17"}
    result = render_shell_placeholders("echo {case}", context)
    # {case} is replaced with a quoted string; {date} inside that value must NOT expand
    assert "2026-04-17" not in result
    assert "run-" in result


def test_render_shell_placeholders_leaves_unknown_keys_literal() -> None:
    context = {"known": "hello"}
    result = render_shell_placeholders("{known} {unknown}", context)
    assert result.startswith("'hello'") or "hello" in result
    assert "{unknown}" in result


def test_executive_summary_excerpt_uses_extract_section() -> None:
    report = (
        "# Report\n\n## Executive Summary\nLine one.\n\nLine two.\n## Next\nMore.\n"
    )
    result = executive_summary_excerpt(report)
    assert result == "Line one. Line two."


def test_executive_summary_excerpt_returns_fallback_when_absent() -> None:
    assert (
        executive_summary_excerpt("# Report\n\n## Other\nstuff\n")
        == "No executive summary yet."
    )


def test_executive_summary_excerpt_returns_fallback_when_empty() -> None:
    assert (
        executive_summary_excerpt("# Report\n\n## Executive Summary\n\n## Other\n")
        == "No executive summary yet."
    )


def test_render_state_digest_uses_question_heading(tmp_path: Path) -> None:
    make_case(tmp_path)
    # brief.md uses ## Question heading per template
    (tmp_path / "brief.md").write_text(
        "# Research Brief\n\n## Question\n\nWhy did churn spike?\n\n## Mode\n\n- Selected mode: `autonomous`\n",
        encoding="utf-8",
    )
    snapshot = artifact_snapshot(tmp_path)
    block = render_state_digest(tmp_path, snapshot)
    assert "Why did churn spike?" in block
