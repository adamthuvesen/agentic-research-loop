"""Test double for external agent runners in loop integration tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CycleScenario:
    report_summary: str
    ranked_causes: str
    evidence_highlights: str
    next_actions: str
    notes_body: str
    rejected_leads: str = "- None yet."
    preserve_existing_text: bool = False
    completion_marker: str = "<promise>CYCLE_DONE</promise>"


DEFAULT_SCENARIO = CycleScenario(
    report_summary="The first cycle found evidence of a post-launch registration drop.",
    ranked_causes="- Launch friction",
    evidence_highlights="- Evidence supports the leading explanation.",
    rejected_leads="- None yet.",
    next_actions="- Validate the funnel step after launch.",
    notes_body="- Launch friction looks plausible.",
)

BRIEF_SCENARIOS: tuple[tuple[str, CycleScenario], ...] = (
    (
        "survives challenge immediately",
        CycleScenario(
            report_summary="Launch timing and funnel evidence look strong enough to test for closure.",
            ranked_causes="- Launch friction",
            evidence_highlights="- Timing and funnel movement line up tightly with the launch.",
            rejected_leads="- None yet.",
            next_actions="- Run the mandatory challenge pass before closing.",
            notes_body="- The case looks ready for a formal challenge pass.",
            completion_marker="<promise>CASE_COMPLETE</promise>",
        ),
    ),
    (
        "reopens after challenge",
        CycleScenario(
            report_summary="The current evidence points toward rollout friction, but the case needs a challenge review before closing.",
            ranked_causes="- Rollout friction",
            evidence_highlights="- Timing lines up, but the cohort split is still thin.",
            rejected_leads="- None yet.",
            next_actions="- Run the mandatory challenge pass before closing.",
            notes_body="- The case is coherent enough to challenge, but the cohort control is still weak.",
            completion_marker="<promise>CASE_COMPLETE</promise>",
        ),
    ),
    (
        "rollout hurt signup",
        CycleScenario(
            report_summary="Confidence timing and Snowflake funnel evidence both point to the rollout as the leading cause.",
            ranked_causes="- Rollout hurt signup",
            evidence_highlights="- Confidence established timing and Snowflake established impact.",
            next_actions="- Audit the affected rollout segment and step.",
            notes_body="- Confidence and Snowflake align around the rollout.",
        ),
    ),
    (
        "historical onboarding context",
        CycleScenario(
            report_summary="The first cycle stitched together curated context, historical docs, and local notes to reconstruct the onboarding timeline.",
            ranked_causes="- Context reconstruction is still in progress.",
            evidence_highlights="- The strongest first step was combining curated, historical, and local context.",
            rejected_leads="- No causal leads rejected yet.",
            next_actions="- Pull live metrics now that the timeline and cohorts are clearer.",
            notes_body="- The mix of curated, historical, and local context clarified the timeline.",
        ),
    ),
    (
        "active users missing",
        CycleScenario(
            report_summary="Snowflake budget data shows active users missed the Q1 target by 3.8% in March, accelerating from 1.9% in February.",
            ranked_causes="- Accelerating retention shortfall vs target",
            evidence_highlights="- The budget-vs-actuals table shows the miss widening month-over-month.",
            rejected_leads="- Seasonal effects not yet ruled out.",
            next_actions="- Segment the miss by cohort to identify which users are churning.",
            notes_body="- Budget table confirms the shortfall; cohort breakdown is the next step.",
        ),
    ),
    (
        "workspace redesign external context",
        CycleScenario(
            report_summary="The first cycle combined live workspace context, internal notes, and external context to frame the redesign question.",
            ranked_causes="- No leading cause yet; cross-source checks established the context.",
            evidence_highlights="- The strongest output is a timeline stitched across Notion, internal docs, and external signals.",
            rejected_leads="- No causal leads rejected yet.",
            next_actions="- Validate whether the redesign changed the key metric in live data.",
            notes_body="- Notion, wiki, and web together clarified the external and internal backdrop.",
        ),
    ),
    (
        "stalled source path",
        CycleScenario(
            report_summary=DEFAULT_SCENARIO.report_summary,
            ranked_causes=DEFAULT_SCENARIO.ranked_causes,
            evidence_highlights=DEFAULT_SCENARIO.evidence_highlights,
            rejected_leads=DEFAULT_SCENARIO.rejected_leads,
            next_actions=DEFAULT_SCENARIO.next_actions,
            notes_body=DEFAULT_SCENARIO.notes_body,
            preserve_existing_text=True,
        ),
    ),
)

PLAN_TEMPLATE = """# Research Plan

### T1: Confirm the drop and localize it
**Priority:** high
**Source:** Snowflake
**Objective:** Confirm the change and identify where it concentrates.
**Main Explanation:** A real change in user behavior caused the drop.
**Strongest Rival:** The movement is mostly composition shift or reporting noise.
**Discriminating Test:** Segment the metric by cohort and compare against an adjacent metric.
**Evidence Needed:** A concentrated shift plus corroboration from a second source.
**Completion Threshold:** done when the leading slice is explicit; blocked when the key cut is unavailable; pivot when the signal disappears after cross-checking.
**Confounders / Freshness Risks:** Partial-period data can distort the comparison.
**Cross-Check:** Validate the pattern in a second source family.
**Depends on:** none
**Status:** pending

### T2: Rule out upstream or measurement confounders
**Priority:** medium
**Source:** Knowledge + Snowflake
**Objective:** Check whether freshness or attribution changes explain the movement.
**Main Explanation:** Instrumentation or freshness explains part of the change.
**Strongest Rival:** The movement is real across independent sources.
**Discriminating Test:** Compare the metric to an independent definition or cutoff.
**Evidence Needed:** A concrete mismatch or a confirmed instrumentation change.
**Completion Threshold:** done when measurement risk is ruled in or bounded.
**Confounders / Freshness Risks:** Snapshot exports may lag live tables.
**Cross-Check:** Recompute with a matched cutoff date.
**Depends on:** T1
**Status:** pending
"""


def _match_scenario(brief_text: str) -> CycleScenario:
    lower = brief_text.lower()
    for marker, scenario in BRIEF_SCENARIOS:
        if marker in lower:
            return scenario
    return DEFAULT_SCENARIO


def _write_challenge_review_immediate(
    *,
    notes_path: Path,
    report_path: Path,
    existing_notes: str,
    existing_report: str,
) -> None:
    notes_path.write_text(
        existing_notes
        + "\n\n## Challenge Review\n\n"
        + "- Strongest competing explanation: The apparent drop is mostly seasonality.\n"
        + "- Weakest-supported important claim: The launch is the leading cause in every segment.\n"
        + "- Most fragile dependency: Partial-period comparison windows.\n"
        + "- Resolution status: resolved. Segment evidence and timing still favor launch friction after review.\n",
        encoding="utf-8",
    )
    report_path.write_text(
        existing_report
        + "\n\n## Challenge Review\n\n"
        + "- Strongest competing explanation tested: seasonality explains the decline.\n"
        + "- Weakest-supported claim tested: the launch is the leading cause across all segments.\n"
        + "- Fragile dependency reviewed: partial-period comparison windows.\n"
        + "- Outcome: Resolved. The current report already contains enough timing and funnel evidence to keep the conclusion.\n",
        encoding="utf-8",
    )


def _write_challenge_review_reopen(
    *,
    notes_path: Path,
    report_path: Path,
    existing_notes: str,
    existing_report: str,
) -> None:
    notes_path.write_text(
        existing_notes
        + "\n\n## Challenge Review\n\n"
        + "- Strongest competing explanation: Cohort mix drift explains more of the decline than the rollout.\n"
        + "- Weakest-supported important claim: The report treats rollout timing as dispositive.\n"
        + "- Most fragile dependency: Confidence timing without a matched unaffected slice.\n"
        + "- Resolution status: unresolved.\n"
        + "- Next cycle target: compare affected and unaffected cohorts before closing.\n",
        encoding="utf-8",
    )
    report_path.write_text(
        existing_report
        + "\n\n## Challenge Review\n\n"
        + "- Strongest competing explanation tested: cohort mix drift.\n"
        + "- Weakest-supported claim tested: rollout timing alone identifies the leading cause.\n"
        + "- Fragile dependency reviewed: timing evidence without a control slice.\n"
        + "- Outcome: Unresolved. The report still needs a matched cohort check before the case can close.\n",
        encoding="utf-8",
    )


def main() -> None:
    case_dir = Path(sys.argv[1])
    message_path = Path(sys.argv[2])
    prompt_text = sys.stdin.read()
    brief_path = case_dir / "brief.md"
    plan_path = case_dir / "plan.md"
    report_path = case_dir / "report.md"
    notes_path = case_dir / "notes.md"
    existing_report = report_path.read_text(encoding="utf-8")
    existing_notes = notes_path.read_text(encoding="utf-8")
    brief_text = brief_path.read_text(encoding="utf-8").lower()
    is_challenge_cycle = "# challenge cycle" in prompt_text.lower()

    if message_path.parent.name == "plan":
        plan_path.write_text(PLAN_TEMPLATE, encoding="utf-8")
        message_path.write_text("<promise>CYCLE_DONE</promise>\n", encoding="utf-8")
        print("<promise>CYCLE_DONE</promise>")
        return

    if is_challenge_cycle and "survives challenge immediately" in brief_text:
        _write_challenge_review_immediate(
            notes_path=notes_path,
            report_path=report_path,
            existing_notes=existing_notes,
            existing_report=existing_report,
        )
        message_path.write_text("<promise>CASE_COMPLETE</promise>\n", encoding="utf-8")
        print("<promise>CASE_COMPLETE</promise>")
        return

    if is_challenge_cycle and "reopens after challenge" in brief_text:
        _write_challenge_review_reopen(
            notes_path=notes_path,
            report_path=report_path,
            existing_notes=existing_notes,
            existing_report=existing_report,
        )
        message_path.write_text("<promise>CYCLE_DONE</promise>\n", encoding="utf-8")
        print("<promise>CYCLE_DONE</promise>")
        return

    scenario = _match_scenario(brief_text)
    if scenario.preserve_existing_text:
        notes_path.write_text(existing_notes, encoding="utf-8")
        report_path.write_text(existing_report, encoding="utf-8")
    else:
        notes_path.write_text(
            "# Research Notes\n\n## Working Theory\n\n" + scenario.notes_body + "\n",
            encoding="utf-8",
        )
        report_path.write_text(
            "# Research Report\n\n## Question\n\nWhy did registrations drop?\n\n## Executive Summary\n\n"
            + scenario.report_summary
            + "\n\n## Ranked Causes\n\n"
            + scenario.ranked_causes
            + "\n\n## Evidence Highlights\n\n"
            + scenario.evidence_highlights
            + "\n\n## Rejected Leads\n\n"
            + scenario.rejected_leads
            + "\n\n## Recommended Next Actions\n\n"
            + scenario.next_actions
            + "\n",
            encoding="utf-8",
        )

    if (
        "survives challenge immediately" in brief_text
        or "reopens after challenge" in brief_text
    ):
        completion_marker = "<promise>CASE_COMPLETE</promise>"
    else:
        completion_marker = "<promise>CYCLE_DONE</promise>"

    message_path.write_text(completion_marker + "\n", encoding="utf-8")
    print(completion_marker)


if __name__ == "__main__":
    main()
