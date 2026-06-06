#!/usr/bin/env python3
"""Deterministic, offline demo runner for Agentic Research Loop.

This stands in for a real agent runner (claude / codex) so the loop can be
demonstrated end-to-end with no network, no LLM, and no credentials. It scripts
a believable multi-cycle root-cause investigation over the bundled synthetic
dataset in ``examples/local-sources/`` and produces real artifacts:

  plan -> explore -> build evidence -> conclude (CASE_COMPLETE)
       -> mandatory challenge cycle -> complete

The figures in the report are computed from the CSV at runtime, so the output
reflects the bundled data rather than canned text.

Invoked by ``config/runners/demo.json`` as:
    python3 runners/demo_runner.py {case_dir} {agent_message_file} {cycle_id}
with the cycle prompt on stdin.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

LAUNCH_WEEK = "2026-03-09"  # synthetic "Homepage v3" launch — see local-sources notes

CYCLE_DONE = "<promise>CYCLE_DONE</promise>"
CASE_COMPLETE = "<promise>CASE_COMPLETE</promise>"


def _emit(message_path: Path, marker: str) -> None:
    message_path.parent.mkdir(parents=True, exist_ok=True)
    message_path.write_text(marker + "\n", encoding="utf-8")
    print(marker)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _find_dataset(case_dir: Path) -> Path | None:
    """Locate the bundled CSV via the case's recorded local context folder."""
    sources = _load_json(case_dir / "state" / "sources.json")
    for folder in sources.get("local_context_folders", []):
        candidate = Path(folder.get("path", "")) / "registrations_weekly.csv"
        if candidate.exists():
            return candidate
    fallback = Path("examples/local-sources/registrations_weekly.csv")
    return fallback if fallback.exists() else None


def _pct(before: float, after: float) -> float:
    return (after - before) / before * 100.0 if before else 0.0


def _analyze(csv_path: Path) -> dict[str, float]:
    pre: dict[str, list[float]] = {
        k: [] for k in ("visitors", "signups_started", "registrations")
    }
    post: dict[str, list[float]] = {k: [] for k in pre}
    with csv_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            bucket = pre if row["week_starting"] < LAUNCH_WEEK else post
            for key in pre:
                bucket[key].append(float(row[key]))

    def avg(values: list[float]) -> float:
        return statistics.mean(values) if values else 0.0

    pre_signup_cr = avg(pre["signups_started"]) / avg(pre["visitors"]) * 100.0
    post_signup_cr = avg(post["signups_started"]) / avg(post["visitors"]) * 100.0
    return {
        "reg_pre": avg(pre["registrations"]),
        "reg_post": avg(post["registrations"]),
        "reg_drop": _pct(avg(pre["registrations"]), avg(post["registrations"])),
        "visitors_change": _pct(avg(pre["visitors"]), avg(post["visitors"])),
        "signup_started_drop": _pct(
            avg(pre["signups_started"]), avg(post["signups_started"])
        ),
        "signup_cr_pre": pre_signup_cr,
        "signup_cr_post": post_signup_cr,
    }


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #


def _write_plan(case_dir: Path) -> None:
    (case_dir / "plan.md").write_text(
        """# Research Plan

### T1: Confirm and localize the registration drop
**Priority:** high
**Source:** Local files
**Objective:** Confirm registrations fell and find where in the funnel it concentrates.
**Main Explanation:** A real conversion change at a funnel step caused the drop.
**Strongest Rival:** Traffic fell, or the movement is normal week-to-week variance.
**Discriminating Test:** Compare visitors, signup starts, and registrations before vs after the launch week.
**Evidence Needed:** A concentrated step-level drop with steady traffic.
**Completion Threshold:** done when the affected funnel step is explicit.
**Confounders / Freshness Risks:** Partial-week data near the window edges.
**Cross-Check:** Reconcile with the launch timeline in the context notes.
**Depends on:** none
**Status:** pending

### T2: Tie the drop to a specific change
**Priority:** medium
**Source:** Local files (context notes)
**Objective:** Check whether a known change lines up with the inflection.
**Main Explanation:** The homepage redesign reduced visitor -> signup conversion.
**Strongest Rival:** An unrelated change or measurement shift explains it.
**Discriminating Test:** Match the inflection week to the documented launch date.
**Evidence Needed:** Timing alignment plus a plausible mechanism.
**Completion Threshold:** done when timing and mechanism are established.
**Confounders / Freshness Risks:** Other changes in the same window.
**Cross-Check:** Confirm no tracking change in the window.
**Depends on:** T1
**Status:** pending
""",
        encoding="utf-8",
    )


def _write_explore(case_dir: Path, stats: dict[str, float]) -> None:
    (case_dir / "notes.md").write_text(
        f"""# Research Notes

## Working Theory

- Current best explanation: Weekly registrations stepped down after the {LAUNCH_WEEK} homepage launch.
- Confidence: medium — the drop is clear, the mechanism still needs a funnel cut.
- What would change this: evidence that traffic fell, or that the drop predates the launch.

## Evidence Log

- Registrations fell from ~{stats["reg_pre"]:.0f}/wk to ~{stats["reg_post"]:.0f}/wk ({stats["reg_drop"]:.1f}%).
- Visitors are essentially flat ({stats["visitors_change"]:+.1f}%), so this is not a traffic problem.

## Open Questions

- Which funnel step absorbs the drop — signup start or signup completion?

## Leads To Pull Next

- Compute the visitor -> signup-start conversion before vs after the launch.
""",
        encoding="utf-8",
    )


def _write_report(case_dir: Path, stats: dict[str, float], *, final: bool) -> None:
    confidence = "High" if final else "Medium"
    (case_dir / "notes.md").write_text(
        f"""# Research Notes

## Working Theory

- Current best explanation: The {LAUNCH_WEEK} homepage redesign cut the visitor -> signup-start conversion, dragging registrations down.
- Confidence: {confidence.lower()}.
- What would change this: a non-launch change in the same window, or a measurement artifact.

## Evidence Log

- Registrations: ~{stats["reg_pre"]:.0f}/wk -> ~{stats["reg_post"]:.0f}/wk ({stats["reg_drop"]:.1f}%).
- Visitors: {stats["visitors_change"]:+.1f}% (flat) — not a traffic problem.
- Signup starts: {stats["signup_started_drop"]:.1f}%.
- Visitor -> signup-start conversion: {stats["signup_cr_pre"]:.1f}% -> {stats["signup_cr_post"]:.1f}%.
- The inflection week matches the documented Homepage v3 launch; no tracking change in the window.

## Rejected Leads

- Traffic decline: ruled out, visitors flat.
- Seasonality: the step change aligns to the launch, not a seasonal pattern.
""",
        encoding="utf-8",
    )
    (case_dir / "report.md").write_text(
        f"""# Research Report

## Question

Why did weekly registrations drop in recent weeks?

## Executive Summary

Weekly registrations stepped down ~{abs(stats["reg_drop"]):.0f}% after the
{LAUNCH_WEEK} homepage redesign (Homepage v3). Traffic held flat
({stats["visitors_change"]:+.1f}%), so the loss is a **conversion** problem, not a
traffic problem. The drop concentrates at the very top of the funnel: the
visitor -> signup-start conversion fell from {stats["signup_cr_pre"]:.1f}% to
{stats["signup_cr_post"]:.1f}%, which is consistent with the redesign moving the
primary "Sign up free" call-to-action below the fold.

## Ranked Causes

1. **Homepage v3 reduced visitor -> signup-start conversion** (leading). Timing and
   funnel evidence both point here.
2. Downstream signup-completion changes (minor) — completion rate is roughly stable.

## Evidence Highlights

- Registrations: ~{stats["reg_pre"]:.0f}/wk -> ~{stats["reg_post"]:.0f}/wk ({stats["reg_drop"]:.1f}%).
- Visitors flat ({stats["visitors_change"]:+.1f}%).
- Signup starts: {stats["signup_started_drop"]:.1f}%.
- Visitor -> signup-start CR: {stats["signup_cr_pre"]:.1f}% -> {stats["signup_cr_post"]:.1f}%.

## Recommended Next Actions

- Move the "Sign up free" CTA back above the fold and A/B test against Homepage v3.
- Instrument the hero section to confirm the CTA-visibility hypothesis.

## Confidence

{confidence}. The mechanism is well supported by the timing and the step-level funnel cut.
""",
        encoding="utf-8",
    )


def _write_challenge_review(case_dir: Path) -> None:
    for name in ("notes.md", "report.md"):
        path = case_dir / name
        existing = path.read_text(encoding="utf-8")
        path.write_text(
            existing
            + "\n## Challenge Review\n\n"
            + "- Strongest competing explanation tested: a non-launch change or measurement"
            " artifact in the same window. Rejected — the context notes record no tracking"
            " change, and the inflection aligns to the launch week.\n"
            + "- Weakest-supported claim tested: that the CTA move is the precise mechanism."
            " The funnel cut localizes the loss to the visitor -> signup-start step, which is"
            " consistent with the CTA change; an A/B test is still the clean confirmation.\n"
            + "- Most fragile dependency: partial-week data at the window edges. Re-checked —"
            " the step change holds across the full post-launch weeks.\n"
            + "- Outcome: Resolved. The conclusion survives challenge.\n",
            encoding="utf-8",
        )


def main() -> None:
    case_dir = Path(sys.argv[1])
    message_path = Path(sys.argv[2])
    cycle_id = sys.argv[3] if len(sys.argv) > 3 else ""
    _ = sys.stdin.read()  # prompt is consumed but the scripted runner ignores it

    # Planning step: write the research plan and stop.
    if cycle_id == "plan" or message_path.parent.name == "plan":
        _write_plan(case_dir)
        _emit(message_path, CYCLE_DONE)
        return

    progress = _load_json(case_dir / "state" / "progress.json")

    # Mandatory challenge cycle: stress-test, then confirm completion.
    if progress.get("pending_challenge_cycle"):
        _write_challenge_review(case_dir)
        _emit(message_path, CASE_COMPLETE)
        return

    dataset = _find_dataset(case_dir)
    if dataset is None:
        # No data found — keep the loop honest rather than faking a result.
        sys.stderr.write("demo_runner: bundled dataset not found\n")
        sys.exit(1)
    stats = _analyze(dataset)

    cycle_count = int(progress.get("cycle_count", 0))
    if cycle_count == 0:
        _write_explore(case_dir, stats)
        _emit(message_path, CYCLE_DONE)
    elif cycle_count == 1:
        _write_report(case_dir, stats, final=False)
        _emit(message_path, CYCLE_DONE)
    else:
        _write_report(case_dir, stats, final=True)
        _emit(message_path, CASE_COMPLETE)


if __name__ == "__main__":
    main()
