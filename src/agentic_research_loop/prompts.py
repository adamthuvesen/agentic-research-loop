from __future__ import annotations

from pathlib import Path
from typing import Any

from .hints import build_cycle_hints
from .io import extract_section, load_json_object_or_empty, read_text
from .layout import (
    brief_path,
    cycles_dir,
    plan_path,
    sources_path,
)
from .case_contracts import CaseProfile


RESEARCHER_FRAMING = """# Research Cycle

Each cycle, advance this case with one or two focused threads — not a broad sweep.

## Scope: Go Deep, Not Wide

Pick **1–2 threads** for this cycle. No more. Depth beats coverage.

A thread is a **research question**, not a source check. Querying a warehouse,
then following up on a related experiment or flag change, then checking a doc
for supporting context — that's still one thread if it all serves the same
question. Don't count source lookups against your thread budget.

A cycle that investigates one finding across multiple sources beats one that
skims five threads. If you find something surprising mid-cycle, **follow that
thread** before parking it as a lead.

Good cycle objectives:
- Deep-dive a single hypothesis with data from 2–3 source types
- Follow an unexpected finding into adjacent tables, related experiments, or
  supporting docs before logging it as a lead and moving on — this is one
  thread, not three
- Follow up on a lead from the previous cycle
- Cross-reference a quantitative finding with qualitative context (comms, docs, issue tracking)
- Stress-test your working theory with disconfirming evidence
- Write up findings in the report (only when evidence is solid)

Query sources, read data, and record what changed. When you have substantive
progress on your chosen threads, stop and update `notes.md` and `report.md` as
needed.

## Cycle Shape: Hypothesis First

Before source work, choose **1–2 active hypotheses, leads, or plan threads**.
For each one, name the strongest rival explanation and the evidence that would
change your confidence. Then run the sharpest available test: query data, pull
context, inspect source docs, or cross-check with another source family.

At the end of the cycle, update `notes.md` with:
- which hypothesis moved and how (`supported`, `weakened`, `rejected`, or `pivoted`)
- the evidence and caveats that caused the change
- any dead ends or discarded leads
- the next sharpest check

## Research habits

- **Form a working theory early** and actively try to break it.
- **Follow surprising threads** — if something doesn't fit, that's your best lead.
- **Cross-check** — don't trust a single source for a critical claim. For any
  high-confidence finding, verify with at least one additional source type
  (e.g. a warehouse metric plus the comms or docs that explain it).
- **Use the plan as a decision tool** — prioritize threads with the sharpest
  discriminating tests, and stop when a thread's completion threshold is met.
- **Know when you're saturating** — if three searches return the same signal,
  stop searching and start thinking.
- **Challenge your own conclusions** — what would make you wrong?
- **Be honest about uncertainty** — "I don't know" with clear reasoning is
  better than a confident guess.

## Working Artifacts

**notes.md** is your working space. Use it for evidence, reasoning, and leads.
Structure your leads so the next cycle can pick them up:

```
## Leads
- **<finding>** [high/medium/low]
  Why it matters: <impact on the case>
  Next: <specific next steps>
  Sources to check: <which source types>
```

**report.md** is the deliverable. Don't write or update report.md until you've
worked through all high-priority threads, or the answer is solid enough to
present. A premature report makes the case feel done when it isn't. Build
evidence in notes.md across cycles; write up the report when the picture is
clear.

Maintain a working theory in notes.md. Update it as evidence evolves. Track
your open questions."""


GUIDELINES = """## Guidelines
- Stay read-only with all external systems.
- Don't modify brief.md.
- Use the MCP server or CLI for whichever sources are enabled (see config/sources.json and .mcp.json); every source is read-only.
- Write evidence and reasoning to notes.md. Keep the hypothesis ledger, evidence log, dead ends, open questions, and leads current.
- Only write/update report.md when your evidence is solid — not every cycle.
- Update thread statuses in plan.md as you work.
- If the case reframes, preserve brief.md and record the changed theory in
  notes.md plus the relevant thread entry in plan.md.
- When done with this cycle: end with <promise>CYCLE_DONE</promise>
- When the case is complete: end with <promise>CASE_COMPLETE</promise>"""


CHALLENGE_FRAMING = """# Challenge Cycle

You are running the mandatory challenge review before the case can close.
This is a focused quality-control pass, not a fresh investigation.

Start from the current `report.md`, `notes.md`, and `plan.md`. Stress-test the
answer hard enough to catch overreach, weak support, and fragile caveats without
inventing fake objections.

## Required Review Questions

Answer all of these in your reasoning and reflect them in the artifacts:

1. What is the strongest competing explanation for the current conclusion?
2. What is the weakest-supported important claim in the current report?
3. What is the most fragile source, freshness, or caveat dependency?
4. Does the current answer already resolve those objections, or is a material
   objection still open?

## Artifact Contract

Update `notes.md` by adding or refreshing a `## Challenge Review` section with:
- Strongest competing explanation
- Weakest-supported important claim
- Most fragile dependency
- Resolution status: `resolved` or `unresolved`
- Next cycle target if unresolved

Update `report.md` by adding or refreshing a `## Challenge Review` section that
shows the human reader:
- which rival explanation you tested
- which claim or dependency looked weakest
- what survived scrutiny
- what remains open, if anything

If the report already has `## Risks And Caveats` or `## Open Questions`, keep
those aligned with the challenge outcome.

## Completion Rule

- If a material unresolved objection remains, downgrade the answer as needed,
  point the next normal cycle at the exact objection to resolve, and end with
  `<promise>CYCLE_DONE</promise>`.
- If the objections are already resolved or appropriately contained in the
  report, make the surviving caveats explicit and end with
  `<promise>CASE_COMPLETE</promise>`.

Only query live sources if a concrete objection needs a quick verification. Do
not restart the whole case."""


def _question_line_from_brief(brief_text: str) -> str:
    question_body = extract_section(brief_text, "Question")
    if question_body:
        return question_body.splitlines()[0]
    return next(
        (
            line.strip()
            for line in brief_text.splitlines()
            if line.strip()
            and not line.strip().startswith("#")
            and line.strip() != "---"
        ),
        "Unknown",
    )


def _last_cycle_line(case_path: Path) -> str:
    cycle_summaries = sorted(cycles_dir(case_path).glob("*/cycle_summary.json"))
    if not cycle_summaries:
        return "none yet"
    last_summary = load_json_object_or_empty(cycle_summaries[-1])
    if not last_summary:
        return "none yet"
    return str(last_summary.get("result", "unknown"))


def _append_quoted_section(lines: list[str], title: str, body: str | None) -> None:
    if body:
        lines += ["", title, f"> {body}"]


def render_state_digest(case_path: Path, snapshot: dict[str, Any]) -> str:
    brief_text = read_text(brief_path(case_path))
    question_line = _question_line_from_brief(brief_text)
    cycle_count = snapshot.get("progress", {}).get("cycle_count", 0)
    notes = snapshot.get("notes", "")
    working_theory = extract_section(notes, "Working Theory")
    open_questions = extract_section(notes, "Open Questions") or extract_section(
        notes, "Next Checks"
    )
    leads = extract_section(notes, "Leads")

    lines = [
        "## Where You Left Off",
        "",
        f"**Question**: {question_line}",
        f"**Cycle**: {cycle_count}",
    ]

    _append_quoted_section(
        lines, "**Your working theory** (from notes.md):", working_theory
    )
    lines += ["", f"**What happened last cycle**: {_last_cycle_line(case_path)}"]
    _append_quoted_section(lines, "**Open questions** (from notes.md):", open_questions)
    _append_quoted_section(lines, "**Pending leads** (from notes.md):", leads)

    return "\n".join(lines)


def render_stall_block(snapshot: dict[str, Any]) -> str | None:
    stall_count = snapshot.get("progress", {}).get("consecutive_no_progress_cycles", 0)
    if stall_count == 0:
        return None

    return "\n".join(
        [
            "## You've Been Stuck",
            "",
            f"You've had {stall_count} cycle(s) without visible progress in `notes.md` or `report.md`. Before diving back in,",
            "step back and ask yourself:",
            "",
            "- Am I asking the right question?",
            "- Is my working theory actually testable with the tools I have?",
            "- Which discriminating test have I not run yet?",
            "- What's the most surprising thing I've found? Does it change the picture?",
            "- Should I pivot, update the thread plan, or explicitly mark something as unanswerable?",
            "",
            "Don't repeat what didn't work. Try a different angle, and log pivots in notes.md or plan.md rather than rewriting brief.md.",
        ]
    )


def render_challenge_digest(snapshot: dict[str, Any]) -> str:
    progress = snapshot.get("progress", {})
    executive_summary = extract_section(snapshot.get("report", ""), "Executive Summary")
    challenge_review = extract_section(snapshot.get("report", ""), "Challenge Review")
    open_questions = extract_section(snapshot.get("notes", ""), "Open Questions") or ""

    lines = [
        "## Answer Under Challenge",
        "",
        f"**Cycle**: {progress.get('cycle_count', 0)}",
        f"**Last challenge outcome**: {progress.get('last_challenge_outcome') or 'none yet'}",
        "",
        "**Executive Summary**:",
        f"> {executive_summary or 'No executive summary yet.'}",
    ]
    if challenge_review:
        lines += ["", "**Previous challenge review**:", f"> {challenge_review}"]
    if open_questions:
        lines += ["", "**Open questions still on the board**:", f"> {open_questions}"]
    return "\n".join(lines)


def render_plan_block(case_path: Path) -> str:
    text = read_text(plan_path(case_path)).strip()
    if not text or any(
        line.strip().startswith("No plan yet") for line in text.splitlines()
    ):
        return "## Your Research Plan\n\nNo research plan yet."
    return (
        "## Your Research Plan\n\n"
        + text
        + "\n\nUse each thread's main explanation, strongest rival, discriminating test, and completion threshold to decide what to do next."
        + "\nUpdate thread statuses in `plan.md` as you work: `pending` → `in-progress` → `done` / `pivoted: <reason>` / `blocked: <reason>`."
    )


def render_research_move_block() -> str:
    return "\n".join(
        [
            "## This Cycle",
            "",
            "Pick 1-2 active hypotheses, leads, or plan threads. Before source work, write down:",
            "",
            "- the hypothesis or lead you are testing",
            "- the strongest rival explanation",
            "- the evidence that would change your confidence",
            "- the source path most likely to produce that evidence",
            "",
            "A research question may span multiple source checks. A warehouse query, then a related experiment, then a supporting doc still counts as one thread when all checks test the same explanation.",
            "If a source reveals something surprising, follow it far enough to sharpen or falsify the hypothesis before parking it as a lead.",
        ]
    )


def render_hint_block(case_path: Path, snapshot: dict[str, Any] | None) -> str | None:
    hints = build_cycle_hints(case_path, snapshot=snapshot)
    if not hints:
        return None
    return "\n".join(
        [
            "## Cycle Hints",
            "",
            "Local artifact checks surfaced these nudges. Use judgment; they do not override the research plan.",
            "",
            *[f"- {hint}" for hint in hints],
        ]
    )


def build_plan_prompt(repo_root: Path, case_path: Path) -> str:
    profile = CaseProfile.load(case_path)
    stronger_design_mode = profile.strong_design_contract

    thread_fields = [
        "### T<n>: <short title>",
        "**Priority:** high / medium / low",
        "**Source:** <which source family to use>",
        "**Objective:** What specific question this thread answers",
    ]
    if stronger_design_mode:
        thread_fields.extend(
            [
                "**Main Explanation:** <current best explanation under test>",
                "**Strongest Rival:** <best competing explanation>",
                "**Discriminating Test:** <the concrete check that would move confidence>",
                "**Evidence Needed:** <what would count as enough evidence>",
                "**Completion Threshold:** done when ... / blocked when ... / pivot when ...",
                "**Confounders / Freshness Risks:** <what could mislead this thread>",
                "**Cross-Check:** <which second source or method will validate the claim>",
            ]
        )
    thread_fields.extend(
        [
            "**Depends on:** none / T<n>",
            "**Status:** pending",
        ]
    )

    design_requirements: list[str] = []
    if stronger_design_mode:
        design_requirements = [
            "",
            "## Research design requirements",
            "- For every high-priority thread, name the main explanation under test and the strongest rival explanation.",
            "- The discriminating test must be concrete enough to tell the agent what evidence would change confidence.",
            "- The completion threshold must say what counts as done, blocked, or pivoted for that thread.",
            "- Call out the biggest confounder or freshness hazard and the cross-check source before moving on.",
        ]

    return (
        "\n".join(
            [
                "# Research Planning",
                "",
                "Read the case brief and produce a structured research plan.",
                "Do not investigate yet — only plan.",
                "",
                "## Context",
                f"- Brief: `{brief_path(case_path).resolve()}`",
                f"- Sources registry: `{sources_path(case_path).resolve()}`",
                f"- Operating manual: `{(repo_root / 'program.md').resolve()}`",
                "",
                "## Your task",
                "",
                f"Write a structured research plan to `{plan_path(case_path).resolve()}`.",
                "",
                "The plan should contain 4–8 numbered research threads. For each thread:",
                "",
                "```",
                *thread_fields,
                "```",
                "",
                "Order threads by priority — highest signal value first, dependencies before dependents.",
                "Be honest: flag threads that may not pan out.",
                *design_requirements,
                "",
                "## Constraints",
                "- Write ONLY to `plan.md`. Do not touch any other artifact.",
                "- Do not query any live sources.",
                "- Do not write completion markers.",
            ]
        )
        + "\n"
    )


def build_cycle_prompt(
    case_path: Path,
    *,
    snapshot: dict[str, Any] | None = None,
) -> str:
    challenge_cycle = bool(
        snapshot is not None
        and snapshot.get("progress", {}).get("pending_challenge_cycle", False)
    )
    sections: list[str] = [CHALLENGE_FRAMING if challenge_cycle else RESEARCHER_FRAMING]

    if snapshot is not None:
        if challenge_cycle:
            sections.append(render_challenge_digest(snapshot))
        else:
            sections.append(render_state_digest(case_path, snapshot))

    sections.append(render_plan_block(case_path))

    if snapshot is not None and not challenge_cycle:
        sections.append(render_research_move_block())
        hint_block = render_hint_block(case_path, snapshot)
        if hint_block:
            sections.append(hint_block)
        stall = render_stall_block(snapshot)
        if stall:
            sections.append(stall)

    sections.append(
        GUIDELINES
        if not challenge_cycle
        else "## Reminder\n- All sources stay strictly read-only: search, query, and retrieve only — never write.\n- Keep this pass tightly scoped to the current answer.\n- Record the challenge findings in both `notes.md` and `report.md`.\n- Use `<promise>CYCLE_DONE</promise>` only when a material objection remains unresolved."
    )

    return "\n\n".join(sections) + "\n"
