# Research Report

## Question

Why did weekly registrations drop in recent weeks?

## Executive Summary

Weekly registrations stepped down ~15% after the
2026-03-09 homepage redesign (Homepage v3). Traffic held flat
(+2.1%), so the loss is a **conversion** problem, not a
traffic problem. The drop concentrates at the very top of the funnel: the
visitor -> signup-start conversion fell from 20.0% to
17.0%, which is consistent with the redesign moving the
primary "Sign up free" call-to-action below the fold.

## Ranked Causes

1. **Homepage v3 reduced visitor -> signup-start conversion** (leading). Timing and
   funnel evidence both point here.
2. Downstream signup-completion changes (minor) — completion rate is roughly stable.

## Evidence Highlights

- Registrations: ~5607/wk -> ~4770/wk (-14.9%).
- Visitors flat (+2.1%).
- Signup starts: -13.3%.
- Visitor -> signup-start CR: 20.0% -> 17.0%.

## Recommended Next Actions

- Move the "Sign up free" CTA back above the fold and A/B test against Homepage v3.
- Instrument the hero section to confirm the CTA-visibility hypothesis.

## Confidence

High. The mechanism is well supported by the timing and the step-level funnel cut.

## Challenge Review

- Strongest competing explanation tested: a non-launch change or measurement artifact in the same window. Rejected — the context notes record no tracking change, and the inflection aligns to the launch week.
- Weakest-supported claim tested: that the CTA move is the precise mechanism. The funnel cut localizes the loss to the visitor -> signup-start step, which is consistent with the CTA change; an A/B test is still the clean confirmation.
- Most fragile dependency: partial-week data at the window edges. Re-checked — the step change holds across the full post-launch weeks.
- Outcome: Resolved. The conclusion survives challenge.
