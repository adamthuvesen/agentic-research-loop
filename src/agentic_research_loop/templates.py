from __future__ import annotations

from collections.abc import Iterable
from datetime import date


def format_list(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    return "\n".join(f"- {value}" for value in values) if values else "- (none)"


def root_cause_hypothesis_starters(question: str) -> str:
    metric_label = question.rstrip(" ?")
    return "\n".join(
        [
            "- **H1: A real behavior shift changed the metric in a concentrated segment or cohort.** [priority: high, status: untested]",
            f"  - Discriminating test: Break `{metric_label}` by segment, cohort, geography, or workflow step and confirm the shift survives at least one cross-source check.",
            "  - Strongest rival: The apparent movement is mostly composition drift, seasonality, or normal variance.",
            "  - Evidence needed: A concentrated change with a plausible mechanism, plus corroboration from a second source family or adjacent metric.",
            "  - Completion threshold: Done when the leading segment(s) and direction of effect are explicit, or blocked with the exact missing cut/data dependency named.",
            "- **H2: Upstream inputs or feeder cohorts changed before the observed metric moved.** [priority: high, status: untested]",
            f"  - Discriminating test: Check the upstream driver for `{metric_label}` one step earlier in the funnel or lifecycle and compare timing, magnitude, and affected slices.",
            "  - Strongest rival: The outcome changed without a matching upstream shift, which points to downstream execution or retention instead.",
            "  - Evidence needed: A lead/lag relationship or a clearly weaker feeder cohort that lines up with the downstream pattern.",
            "  - Completion threshold: Done when the upstream contribution is quantified or directionally clear enough to rank against other drivers, or ruled out as too small or mistimed.",
            "- **H3: Measurement, attribution, or freshness issues explain part of the movement.** [priority: medium, status: untested]",
            f"  - Discriminating test: Verify `{metric_label}` with an independent definition, source, or cutoff date and inspect known tracking, routing, or reporting changes near the inflection.",
            "  - Strongest rival: Multiple independent sources show the same movement, so the change is real even if measurement is noisy.",
            "  - Evidence needed: A concrete mismatch between sources/definitions or a confirmed instrumentation change that overlaps the observed shift.",
            "  - Completion threshold: Done when measurement risk is either ruled in as material or bounded tightly enough that the remaining explanation is still trustworthy.",
        ]
    )


def root_cause_cross_check_lines() -> str:
    return "\n".join(
        [
            "- Name the main freshness hazard before comparing live data with snapshots or local exports.",
            "- Cross-check every high-confidence claim in at least two source families when possible.",
            "- Record the strongest rival explanation for each major thread before calling it done.",
            "- If a surprising finding changes the case, preserve `brief.md` and log the pivot in `notes.md` plus the relevant thread status in `plan.md`.",
        ]
    )


def brief_template(
    *,
    question: str,
    template: str,
    mode: str,
    source_plan: list[str],
    source_registry_lines: list[str],
    success_criteria: list[str],
    today: date | None = None,
) -> str:
    today_text = (today or date.today()).isoformat()
    if template == "root-cause" and mode == "autonomous":
        return f"""# Research Brief

## Question

{question}

## Mode

- Selected mode: `{mode}`
- Research shape: `{template}`
- Created: `{today_text}`

## Decision Or Deliverable

What decision, update, or deliverable should this case support?

## Scope

- In scope:
- Out of scope:

## Hypotheses

{root_cause_hypothesis_starters(question)}

## Source Plan

{format_list(source_plan)}

## Source Registry

{format_list(source_registry_lines)}

## Known Confounders

- Which seasonality, composition, routing, or attribution effects could mimic the observed change?
- Which freshness caveats matter before you compare sources?

## Required Cross-Checks

{root_cause_cross_check_lines()}

## Freshness Requirements

- Which facts must be verified live?
- Which context can come from existing docs?

## Success Criteria

{format_list(success_criteria)}
"""
    return f"""# Research Brief

## Question

{question}

## Mode

- Selected mode: `{mode}`
- Research shape: `{template}`
- Created: `{today_text}`

## Decision Or Deliverable

What decision, update, or deliverable should this case support?

## Scope

- In scope:
- Out of scope:

## Source Plan

{format_list(source_plan)}

## Source Registry

{format_list(source_registry_lines)}

## Freshness Requirements

- Which facts must be verified live?
- Which context can come from existing docs?

## Success Criteria

{format_list(success_criteria)}
"""


def plan_template(*, template: str, mode: str) -> str:
    if template == "root-cause" and mode == "autonomous":
        return """# Research Plan

## Research Design Contract

- Every high-priority thread needs a main explanation, strongest rival, discriminating test, evidence target, and completion threshold.
- Completion thresholds should say what counts as `done`, when to mark a thread `blocked`, and what would justify a `pivoted` status.
- Record the biggest confounder or freshness hazard for each major thread and the source you will use to cross-check it.

## Thread Template

Use the exact bold field names below — they are machine-parsed by validation.

```md
### T<n>: <short title>
**Priority:** high / medium / low
**Source:** <which source family to use>
**Objective:** What specific question this thread answers
**Main Explanation:** <current best explanation under test>
**Strongest Rival:** <best competing explanation>
**Discriminating Test:** <the concrete check that would move confidence>
**Evidence Needed:** <what would count as enough evidence>
**Completion Threshold:** done when ... / blocked when ... / pivot when ...
**Confounders / Freshness Risks:** <what could mislead this thread>
**Cross-Check:** <which second source or method will validate the claim>
**Depends on:** none / T<n>
**Status:** pending
```

## Threads

No plan yet. Run `research plan <id>` or let the next cycle generate one automatically.
"""
    return """# Research Plan

No plan yet. Run `research plan <id>` or let the next cycle generate one automatically.
"""


def notes_template() -> str:
    return """# Research Notes

## Working Theory

- Current best explanation:
- Confidence:
- What would change this:

## Hypotheses

Use this as a lightweight ledger, not a form to fill perfectly.

### H1: <short hypothesis>
- **Status:** active | supported | weakened | rejected | pivoted
- **Why plausible:**
- **Strongest rival:**
- **Discriminating test:**
- **Evidence so far:**
- **Next check:**

## Evidence Log

- **Claim:**
  **Source family:**
  **Source detail:**
  **Supports:**
  **Caveat / freshness:**

## Dead Ends

- 

## Open Questions

- 

## Leads

-
"""


def report_template(template: str, question: str, initial_summary: str) -> str:
    if template == "root-cause":
        sections = [
            "## Executive Summary",
            initial_summary,
            "## Ranked Causes",
            "",
            "## Evidence Highlights",
            "",
            "## Rejected Leads",
            "",
            "## Recommended Next Actions",
            "",
        ]
    elif template == "comparison":
        sections = [
            "## Executive Summary",
            initial_summary,
            "## Key Differences",
            "",
            "## Evidence Highlights",
            "",
            "## Risks And Caveats",
            "",
            "## Recommended Next Actions",
            "",
        ]
    else:
        sections = [
            "## Executive Summary",
            initial_summary,
            "## Current Picture",
            "",
            "## Evidence Highlights",
            "",
            "## Open Questions",
            "",
            "## Recommended Next Actions",
            "",
        ]
    return (
        "# Research Report\n\n## Question\n\n"
        + question
        + "\n\n"
        + "\n".join(sections)
        + "\n"
    )


def finding_template(
    *,
    title: str,
    short_answer: str,
    conclusion: str,
    sources: list[str],
    source_families: list[str],
    research_shifts: list[str],
    ruled_out: list[str],
    process_caveats: list[str],
    last_verified: str,
    freshness_caveats: list[str],
    reverification_triggers: list[str],
) -> str:
    return f"""# {title}

## Short Answer

{short_answer}

## Conclusion

{conclusion}

## Sources Used

{format_list(sources)}

## Source Families Used

{format_list(source_families)}

## Research Shifts

{format_list(research_shifts)}

## Ruled Out Or Weakened Leads

{format_list(ruled_out)}

## Research Caveats

{format_list(process_caveats)}

## Last Verified

{last_verified}

## Freshness Caveats

{format_list(freshness_caveats)}

## Re-verification Triggers

{format_list(reverification_triggers)}
"""
