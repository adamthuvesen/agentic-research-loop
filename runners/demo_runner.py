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

CHANGE_WEEK = "2026-03-09"  # synthetic scheduler change — see local-sources notes

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
        candidate = Path(folder.get("path", "")) / "exports_weekly.csv"
        if candidate.exists():
            return candidate
    fallback = Path("examples/local-sources/exports_weekly.csv")
    return fallback if fallback.exists() else None


def _pct(before: float, after: float) -> float:
    return (after - before) / before * 100.0 if before else 0.0


def _success_rate(succeeded: float, scheduled: float) -> float:
    return succeeded / scheduled * 100.0 if scheduled else 0.0


def _analyze(csv_path: Path) -> dict[str, float]:
    pre: dict[str, list[float]] = {
        k: []
        for k in (
            "jobs_scheduled",
            "jobs_succeeded",
            "jobs_failed",
            "avg_queue_minutes",
        )
    }
    post: dict[str, list[float]] = {k: [] for k in pre}
    with csv_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            bucket = pre if row["week_starting"] < CHANGE_WEEK else post
            for key in pre:
                bucket[key].append(float(row[key]))

    def avg(values: list[float]) -> float:
        return statistics.mean(values) if values else 0.0

    pre_rate = _success_rate(avg(pre["jobs_succeeded"]), avg(pre["jobs_scheduled"]))
    post_rate = _success_rate(avg(post["jobs_succeeded"]), avg(post["jobs_scheduled"]))
    return {
        "scheduled_pre": avg(pre["jobs_scheduled"]),
        "scheduled_post": avg(post["jobs_scheduled"]),
        "scheduled_change": _pct(
            avg(pre["jobs_scheduled"]), avg(post["jobs_scheduled"])
        ),
        "success_pre": pre_rate,
        "success_post": post_rate,
        "success_drop_pp": post_rate - pre_rate,
        "failed_change": _pct(avg(pre["jobs_failed"]), avg(post["jobs_failed"])),
        "queue_pre": avg(pre["avg_queue_minutes"]),
        "queue_post": avg(post["avg_queue_minutes"]),
        "queue_change": _pct(
            avg(pre["avg_queue_minutes"]), avg(post["avg_queue_minutes"])
        ),
    }


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #


def _write_plan(case_dir: Path) -> None:
    (case_dir / "plan.md").write_text(
        """# Research Plan

### T1: Confirm and localize the export reliability break
**Priority:** high
**Source:** Local files
**Objective:** Confirm export success rate fell and check whether volume or queue pressure changed.
**Main Explanation:** Queue contention from rescheduled heavy jobs caused more failures.
**Strongest Rival:** Job volume rose and overwhelmed capacity, unrelated to the schedule change.
**Discriminating Test:** Compare success rate, failure count, and queue minutes before vs after the change week.
**Evidence Needed:** A step down in success rate with a matching queue spike while scheduled volume stays flat.
**Completion Threshold:** done when the break magnitude and timing are explicit.
**Confounders / Freshness Risks:** Partial-week data near the window edges.
**Cross-Check:** Reconcile with the scheduler change date in the context notes.
**Depends on:** none
**Status:** pending

### T2: Tie the break to the scheduler change
**Priority:** medium
**Source:** Local files (context notes)
**Objective:** Check whether the documented schedule change lines up with the inflection.
**Main Explanation:** Moving heavy exports into business hours overloaded the shared queue.
**Strongest Rival:** An unrelated platform or counting change explains the failures.
**Discriminating Test:** Match the inflection week to the documented 2026-03-09 schedule change.
**Evidence Needed:** Timing alignment plus a plausible queue-contention mechanism.
**Completion Threshold:** done when timing and mechanism are established.
**Confounders / Freshness Risks:** Other operational changes in the same window.
**Cross-Check:** Confirm no metric-definition change in the window.
**Depends on:** T1
**Status:** pending
""",
        encoding="utf-8",
    )


def _write_explore(case_dir: Path, stats: dict[str, float]) -> None:
    (case_dir / "notes.md").write_text(
        f"""# Research Notes

## Working Theory

- Current best explanation: Export success rate stepped down after the {CHANGE_WEEK} scheduler change.
- Confidence: medium — the drop is clear, queue pressure still needs a full cut.
- What would change this: evidence that scheduled volume spiked, or that the drop predates the change.

## Evidence Log

- Success rate fell from {stats["success_pre"]:.1f}% to {stats["success_post"]:.1f}% ({stats["success_drop_pp"]:+.1f} pp).
- Scheduled jobs are essentially flat ({stats["scheduled_change"]:+.1f}%), so this is not a volume spike.

## Open Questions

- Did average queue minutes rise in the same week as the success-rate break?

## Leads To Pull Next

- Compare queue minutes and failure counts before vs after the change week.
""",
        encoding="utf-8",
    )


def _write_report(case_dir: Path, stats: dict[str, float], *, final: bool) -> None:
    confidence = "High" if final else "Medium"
    (case_dir / "notes.md").write_text(
        f"""# Research Notes

## Working Theory

- Current best explanation: The {CHANGE_WEEK} scheduler change moved heavy export jobs into business hours, overloading the shared queue and cutting success rate.
- Confidence: {confidence.lower()}.
- What would change this: a non-scheduler change in the same window, or a metric-definition shift.

## Evidence Log

- Success rate: {stats["success_pre"]:.1f}% -> {stats["success_post"]:.1f}% ({stats["success_drop_pp"]:+.1f} pp).
- Scheduled jobs: {stats["scheduled_change"]:+.1f}% (flat) — not a volume problem.
- Failed jobs: {stats["failed_change"]:+.1f}% vs pre-change baseline.
- Avg queue minutes: {stats["queue_pre"]:.1f} -> {stats["queue_post"]:.1f} ({stats["queue_change"]:+.1f}%).
- The inflection week matches the documented scheduler change; no counting change in the window.

## Rejected Leads

- Volume spike: ruled out, scheduled jobs flat.
- Random variance: the step change aligns to the schedule change and holds for five post weeks.
""",
        encoding="utf-8",
    )
    (case_dir / "report.md").write_text(
        f"""# Research Report

## Question

Why did weekly export job success rate drop in recent weeks?

## Executive Summary

Export success rate stepped down from {stats["success_pre"]:.1f}% to
{stats["success_post"]:.1f}% after the {CHANGE_WEEK} scheduler change that moved
**large warehouse export jobs** from overnight into business hours. Scheduled
volume held flat ({stats["scheduled_change"]:+.1f}%), so the loss is a **queue
contention** problem, not a demand spike. Average queue wait rose from
{stats["queue_pre"]:.0f} to {stats["queue_post"]:.0f} minutes in the same window,
consistent with heavy jobs competing with interactive load on the shared export queue.

## Ranked Causes

1. **Business-hours scheduling overloaded the export queue** (leading). Timing,
   queue minutes, and flat scheduled volume all point here.
2. Residual retry-policy noise (minor) — a smaller Feb tweak did not move the
   inflection.

## Evidence Highlights

- Success rate: {stats["success_pre"]:.1f}% -> {stats["success_post"]:.1f}%.
- Scheduled jobs flat ({stats["scheduled_change"]:+.1f}%).
- Failed jobs up {stats["failed_change"]:.1f}%.
- Avg queue minutes: {stats["queue_pre"]:.1f} -> {stats["queue_post"]:.1f}.

## Recommended Next Actions

- Move large warehouse exports back to the overnight window and monitor queue minutes.
- Cap concurrent heavy exports during business hours until queue SLO recovers.

## Confidence

{confidence}. The mechanism is well supported by timing, queue pressure, and flat volume.
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
            + "- Strongest competing explanation tested: a volume spike or unrelated"
            " platform change in the same window. Rejected — scheduled jobs stayed flat,"
            " and the context notes record no counting change.\n"
            + "- Weakest-supported claim tested: that the Feb retry-policy tweak"
            " contributed materially. It predates the inflection by two weeks and"
            " success rate held at 98% until the schedule change.\n"
            + "- Most fragile dependency: partial-week data at the window edges."
            " Re-checked — the step change holds across the full post-change weeks.\n"
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
