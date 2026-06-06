# Investigation Brief

## Question

Why did registrations drop after the March launch?

## Mode

- Selected mode: `autonomous`
- Investigation shape: `root-cause`
- Created: `2026-04-05`

## Decision Or Deliverable

Determine whether the March launch caused the registration drop, and whether the right next move is launch rollback, funnel repair, or measurement cleanup.

## Scope

- In scope: Launch timing, registration funnel performance, affected segments, and measurement caveats.
- Out of scope: Pricing strategy, retention diagnosis, and unrelated channel experiments.

## Hypotheses

- **H1: Launch friction reduced conversion for a concentrated segment.** [priority: high, status: untested]
  - Discriminating test: Compare pre/post registration conversion by landing page, device, and country; verify the same break in two independent sources.
  - Strongest rival: Traffic mix changed while conversion stayed stable.
  - Evidence needed: A clear conversion drop concentrated in the post-launch segment, plus a second-source cross-check.
  - Completion threshold: Done when the affected segment and size of the conversion change are explicit, or blocked with the missing cut named.
- **H2: Upstream traffic quality softened before registrations fell.** [priority: high, status: untested]
  - Discriminating test: Compare visitor quality, query mix, and high-intent page traffic before the launch and look for a lead/lag relationship.
  - Strongest rival: Traffic stayed healthy and the issue is downstream conversion.
  - Evidence needed: A measurable shift in qualified demand that predates or matches the registration decline.
  - Completion threshold: Done when upstream softness is ranked against conversion effects, or ruled out as too small or mistimed.
- **H3: Measurement or freshness issues exaggerate the apparent drop.** [priority: medium, status: untested]
  - Discriminating test: Recompute the trend with a matched cutoff date and an independent source definition.
  - Strongest rival: The drop appears consistently across live and snapshot sources.
  - Evidence needed: A concrete mismatch tied to freshness, routing, or tracking changes.
  - Completion threshold: Done when measurement risk is either confirmed as material or bounded tightly enough that the remaining explanation is still actionable.

## Source Plan

- Snowflake for registrations, conversion, and segment cuts
- Confidence for launch and experiment timing
- Notion for launch context and measurement caveats
- Web or local exports for upstream traffic quality cross-checks

## Source Registry

- Snowflake for live metrics and warehouse-backed evidence.
- Confidence for experiments, rollouts, and decision history.
- Notion for workspace pages, databases, and discussions.
- Web tools for external context and public platform changes.

## Known Confounders

- Partial-period March data can distort pre/post comparisons.
- Attribution or routing changes near the launch can mimic real conversion movement.

## Required Cross-Checks

- Cross-check every high-confidence conversion claim in at least two source families.
- Match the freshness cutoff date before comparing live Snowflake data with local or exported snapshots.
- Preserve `brief.md` if the case pivots; record the new theory in `notes.md` and thread status in `plan.md`.

## Freshness Requirements

- Launch timing, registration actuals, and experiment state must be verified live.
- Historical context and measurement caveats can come from existing docs.

## Success Criteria

- The leading explanation is ranked against the strongest rival.
- The main launch effect is either quantified or explicitly ruled out.
- Freshness and measurement risks are bounded clearly enough for action.
