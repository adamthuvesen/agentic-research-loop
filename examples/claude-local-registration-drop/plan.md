# Research Plan

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

## Framing

Registrations on the marketing site fell sharply and have stayed depressed. The
durable question for this case is: **what caused the drop, how concentrated is
it, and is it real or an artifact of measurement or composition?**

An early read of the local context (CSV + launch notes) gives a strong starting
shape, which these threads are designed to confirm or break — not assume:

- `registrations` dropped from a ~5,500–5,800/week baseline to ~4,700–4,860/week
  beginning the week of **2026-03-09** (≈ -17%), and has not recovered through
  2026-04-06.
- `visitors` are flat across the whole window (~42k–44k/week), so this is **not**
  a traffic-volume problem.
- The break is at the **top of the funnel**: visitor → `signups_started`
  conversion fell from ~20% to ~17%. The `signups_started` → `registrations`
  rate (~65%) and `registrations` → `activations` rate (~60%) look **unchanged**.
- The 2026-03-09 inflection coincides exactly with the **Homepage v3** launch,
  which moved the primary "Sign up free" CTA **below the fold on desktop**.

That makes the leading explanation a top-of-funnel UX regression from Homepage
v3. The plan's job is to (a) confirm the localization and timing on a second
source, (b) run the device-level discriminating test the desktop-only CTA change
implies, and (c) actively rule out the rivals: measurement change, seasonality,
and traffic-composition drift.

**Primary freshness hazard:** the local `registrations_weekly.csv` is a static
snapshot ending 2026-04-06. Magnitude and recency claims must be reconciled
against live Snowflake/GA4 before they are trusted, and the definition of a
"registration" must be checked for alignment across sources.

## Threads

### T1: Localize the drop in the funnel and pin the inflection date
**Priority:** high
**Source:** Local CSV (`registrations_weekly.csv`) + Snowflake (live funnel mart)
**Objective:** Confirm which funnel step broke, the exact week it broke, and that the effect persists rather than being a one-week blip.
**Main Explanation:** The drop is a single, persistent top-of-funnel break at visitor → `signups_started` starting the week of 2026-03-09; downstream conversion rates are unchanged.
**Strongest Rival:** The movement is normal week-to-week variance or a brief dip that has since mean-reverted, not a level shift.
**Discriminating Test:** Compute step-by-step conversion rates per week. A real level shift shows visitor→signup_started dropping ~20%→~17% at 2026-03-09 and holding for ≥4 consecutive weeks, while signup→registration and registration→activation rates stay flat. Variance would show the dip inside normal pre-period scatter or recovering within 1–2 weeks.
**Evidence Needed:** A clear, sustained break at one named step with quantified before/after rates, surviving at least one cross-source check (Snowflake vs CSV).
**Completion Threshold:** done when the broken step, direction, magnitude, and inflection week are explicit and persistent; blocked when Snowflake lacks a funnel mart and the CSV cannot be corroborated (name the missing table); pivot when the break is actually at signup→registration rather than visitor→signup_started.
**Confounders / Freshness Risks:** CSV is a static snapshot; a single noisy week could mislead. Snowflake step definitions may not match the CSV's funnel-step definitions.
**Cross-Check:** Reconcile the CSV weekly funnel against the live Snowflake funnel mart (or GA4 sessions/conversions) for the same weeks.
**Depends on:** none
**Status:** done (local source), refined cycle 2-3: the drop is TWO effects — (A) an instantaneous v→s step 20.000%→17.000% (~90% of loss, matches CTA move) and (B) a gradual s→r erosion 65.0%→62.95% (~10%, NOT explained by CTA; see H5 in notes.md). Cycle 3 (E7): Effect B is DECELERATING toward a floor (weekly Δ −0.55→−0.29pp, last two weeks' regs identical at 4709), so steady-state total damage is bounded ~−15.5 to −16%, NOT runaway — corrects cycle-2 "still-worsening past −15%". pre-period stdev 0.000pp rejects variance. Live Snowflake/GA4 cross-check still pending (offline runner). Local source now fully exhausted.

### T2: Tie the inflection to the Homepage v3 launch (change correlation)
**Priority:** high
**Source:** Local launch notes + Confidence (rollouts/experiments) + Linear / Notion (release records)
**Objective:** Establish that a concrete, dated change to the sign-up entry point landed at the inflection, and rule out other same-week changes competing for the cause.
**Main Explanation:** Homepage v3 (2026-03-09), which moved the "Sign up free" CTA below the fold on desktop, is the mechanism that suppressed `signups_started`.
**Strongest Rival:** A different change in the same week (pricing/copy, infra, tracking, or a paid-traffic shift) is the real driver, and Homepage v3 is coincidental.
**Discriminating Test:** Build a dated change log around 2026-03-09 from Confidence, Linear, Notion, and the launch notes. Confirm Homepage v3 lands in the break week and that its mechanism (CTA below fold) directly targets the step that broke (`signups_started`). Check whether any *other* dated change with a plausible funnel mechanism shares the week.
**Evidence Needed:** A single change whose date and mechanism both align with the broken step, with competing same-week changes either absent or mechanistically unable to explain a top-of-funnel signup drop.
**Completion Threshold:** done when Homepage v3 is confirmed as the only change matching both timing and mechanism, or a rival change is surfaced and queued for testing; blocked when no system records the release date independently of the local notes; pivot when a stronger-matching change appears.
**Confounders / Freshness Risks:** The 2026-02-16 pricing copy refresh is a nearby decoy (wrong week, no funnel mechanism). Confidence may have no record because this was a marketing-led ship, not a feature flag — absence there is not evidence of absence.
**Cross-Check:** Corroborate the launch-notes date with an independent system (Linear ticket, Notion release page, or Confidence rollout entry).
**Depends on:** T1
**Status:** done (local source) / blocked (cross-source): Homepage v3 dated to the break week with matching mechanism; decoy 2026-02-16 ruled out. Cycle 4 (E8): the funnel definitions confirm the CTA gates v→s (form opens) only, and a selection-sign argument shows the CTA cannot produce Effect B's s→r drop — it predicts the opposite sign. Independent-system corroboration (Linear/Notion/Confidence) remains blocked: not reachable in the claude-local runner (MCP suppressed by design, commit 2b72f6e).

### T3: Device-level discriminating test (desktop vs mobile)
**Priority:** high
**Source:** GA4 (`deviceCategory`) + Snowflake (device-split funnel, if available)
**Objective:** Run the sharpest test the leading hypothesis implies — if the CTA moved below the fold *on desktop only*, the signup-start drop should be concentrated on desktop and largely absent on mobile.
**Main Explanation:** The `signups_started` decline is desktop-concentrated, matching a desktop-only CTA regression from Homepage v3.
**Strongest Rival:** The drop is uniform across desktop and mobile (or mobile-led), which would point away from the desktop CTA move and toward a global cause (tracking, traffic mix, or seasonality).
**Discriminating Test:** Split visitor→signup_started conversion by `deviceCategory` for ~6 weeks before vs after 2026-03-09. Desktop conversion should fall materially at the inflection while mobile stays near baseline. A uniform drop refutes the desktop-CTA mechanism.
**Evidence Needed:** A clear desktop-vs-mobile divergence at the inflection date, consistent in GA4 and (if present) Snowflake device-split data.
**Completion Threshold:** done when the device split either confirms desktop concentration (strongly supports the main explanation) or shows uniformity (forces a pivot away from the CTA mechanism); blocked when neither GA4 nor Snowflake exposes a device dimension on the signup-start step (name the gap); pivot when the drop is uniform or mobile-led.
**Confounders / Freshness Risks:** GA4 vs CSV/Snowflake may define "signup started" differently; device-category attribution can be noisy. GA4 is queried live and may carry its own freshness lag vs the CSV snapshot.
**Cross-Check:** Compare the GA4 device split against any Snowflake device-level funnel; sanity-check that pre-period device mix is stable so the split isn't driven by changing traffic composition.
**Depends on:** T2
**Status:** blocked: device dimension unavailable — no GA4 (GA4_PROPERTY_ID unset) or Snowflake MCP in this offline runner. Sharpest discriminating test cannot run here.

### T4: Rule out a measurement / tracking / attribution artifact
**Priority:** medium
**Source:** Snowflake + GA4 + local CSV (three-way definition check) + Linear / Notion (eng change log)
**Objective:** Bound the risk that the "drop" is partly an instrumentation or definition change rather than a real behavior shift (brief H3).
**Main Explanation:** No tracking change occurred in the window; three independent sources show the same drop, so the movement is real.
**Strongest Rival:** A tracking, tagging, consent, or pipeline change near 2026-03-09 deflated the measured `signups_started`/`registrations` without a real behavior change.
**Discriminating Test:** Compare the same metric across CSV, Snowflake, and GA4 over the inflection. If all three move together by similar magnitude, measurement is ruled out. Also scan Linear/Notion for any analytics, tagging, or consent/cookie change dated near the launch. The launch notes *claim* "no infrastructure or tracking change" — verify that against an independent record rather than accepting it.
**Evidence Needed:** Either three-source agreement on the drop (rules measurement out) or a concrete, dated instrumentation change overlapping the inflection (rules it in).
**Completion Threshold:** done when measurement risk is either ruled out by multi-source agreement or quantified as material; blocked when only one source carries the metric and the claim cannot be cross-checked; pivot when a confirmed instrumentation change explains a large share of the drop.
**Confounders / Freshness Risks:** Differing definitions across sources can masquerade as a measurement bug; snapshot-vs-live timing differences can create false mismatches.
**Cross-Check:** This thread *is* the cross-check — its method is source cross-check, feeding confidence back into T1.
**Depends on:** T1
**Status:** in-progress (local reasoning): measurement weakened — break isolated to one step while r→a flat 60% argues against broad instrumentation breakage. Three-source cross-check blocked (offline runner).

### T5: Rule out seasonality and traffic-composition drift
**Priority:** medium
**Source:** Snowflake / GA4 (segment by geography, traffic source/medium, new vs returning) + Web search (external events)
**Objective:** Test the brief's rival that the movement is composition drift, seasonality, or an external traffic-quality shift rather than a UX regression.
**Main Explanation:** Visitor volume and mix are stable, so the conversion drop reflects a real on-site behavior change, not a worse incoming audience.
**Strongest Rival:** The incoming traffic mix degraded at 2026-03-09 (e.g., a paid-channel shift, a seasonal low, or a geo/source change), lowering intent and conversion independent of Homepage v3.
**Discriminating Test:** Check whether visitor composition (source/medium, country, new/returning share) shifted at the inflection. If conversion fell *within* stable segments — each segment converts worse post-launch at flat mix — composition is ruled out. If a large low-intent segment grew, composition is a live confounder. Cross-reference prior-year seasonality and external events via web search.
**Evidence Needed:** Stable pre/post traffic composition with within-segment conversion declines (rules rival out), or a documented mix shift large enough to explain the drop (rules it in).
**Completion Threshold:** done when composition/seasonality is either ruled out or quantified as a contributing share alongside the UX cause; blocked when source/medium segmentation is unavailable in both GA4 and Snowflake; pivot the case framing when composition explains the majority of the drop.
**Confounders / Freshness Risks:** Seasonality is hard to judge from a single ~14-week window with no prior-year baseline — flag this as a genuine limitation. Source/medium attribution can be lossy.
**Cross-Check:** Corroborate any segment finding across GA4 and Snowflake; use web search only for external-event context, not as a primary metric.
**Depends on:** T1
**Status:** blocked: source/medium + geo segmentation unavailable (no GA4/Snowflake in offline runner).

### T6: Quantify business impact and confirm downstream is intact
**Priority:** medium
**Source:** Local CSV + Snowflake (registrations and activations)
**Objective:** Size the cost of the drop and confirm it is purely a lost-signup volume effect, not also a downstream quality/retention problem.
**Main Explanation:** ~800–1,000 fewer registrations/week (≈ -17%), flowing through to a proportional activation drop, with the `registration → activation` rate unchanged (~60%) — so the damage is entirely upstream signup loss.
**Strongest Rival:** Downstream rates also worsened (registration→activation degraded), meaning the cause hurt user quality, not just volume.
**Discriminating Test:** Compare the `registrations → activations` rate before vs after 2026-03-09. If it holds at ~60%, the impact is pure volume; if it fell too, there is a second, downstream problem to explain.
**Evidence Needed:** A quantified weekly registration/activation shortfall plus a stable (or not) downstream conversion rate.
**Completion Threshold:** done when the per-week and cumulative shortfall are stated and the downstream rate is confirmed stable or flagged as a second problem; blocked when activation data is unavailable in both CSV and Snowflake; pivot when downstream rates also dropped (opens a new sub-question).
**Confounders / Freshness Risks:** Activations may lag registration by days/weeks, so the most recent weeks can look artificially low — account for the activation lag before comparing the latest weeks.
**Cross-Check:** Reconcile CSV activation counts against Snowflake; confirm the activation-rate stability holds in live data, not just the snapshot.
**Depends on:** T1
**Status:** done (local source), corrected cycle 2: −838 registrations/wk (−14.9%), ~4,189 lost over 5 post weeks. CAVEAT REVISED: activations = round(0.60 × registrations) every week by construction (E6), so the "r→a flat 60% → downstream intact" claim is true by construction, NOT independent evidence of user quality. Downstream-quality question is unanswerable from this dataset; needs live activation data. Live reconciliation pending.

### T7: Surface existing awareness, ownership, and any planned response
**Priority:** low
**Source:** Slack + Notion + Linear
**Objective:** Find whether the drop was already noticed, who owns the homepage/funnel, and whether a fix, rollback, or A/B test is already in motion — context that shapes the recommendation, not the diagnosis.
**Main Explanation:** The drop is known internally and tied to Homepage v3, with an owner and possibly a remediation already under discussion.
**Strongest Rival:** No one has connected the registration drop to Homepage v3 yet, so the finding is net-new.
**Discriminating Test:** Search Slack/Notion/Linear for "registration", "signup", "Homepage v3", "CTA", and the 2026-03-09 launch. A thread/ticket linking the drop to the launch confirms awareness; absence within search limits suggests it is undiscovered.
**Evidence Needed:** A dated discussion or ticket referencing the drop and/or Homepage v3, or a documented null result after a reasonable search.
**Completion Threshold:** done when awareness/ownership is established or a bounded null result is recorded; blocked when search access to these systems fails; pivot is N/A — this thread is explicitly allowed to not pan out, and thin results are informative, not a failure.
**Confounders / Freshness Risks:** Slack is ephemeral and search-limited — absence of a thread is weak evidence. Keyword search may miss differently-worded discussions.
**Cross-Check:** Triangulate any Slack signal against a more durable Linear ticket or Notion page before citing it.
**Depends on:** T2
**Status:** blocked: Slack/Notion/Linear not reachable in offline runner.

## Thread map and sequencing

1. **T1** (localize + timing) is the spine — every other thread depends on it.
2. **T2** (launch correlation) plus the rival-killers **T4** (measurement) and
   **T5** (composition/seasonality) confirm the cause is real and singular.
3. **T3** (device split) is the single sharpest discriminating test for the
   leading hypothesis — desktop concentration is the prediction that would most
   cleanly confirm or break the CTA mechanism.
4. **T6** sizes the impact; **T7** adds organizational context for the
   recommendation.

## Honest risk flags

- **T2 / Confidence:** a marketing-led homepage ship likely has *no* Confidence
  rollout record. Don't read its absence as disconfirming the launch — fall back
  to Linear / Notion / launch notes.
- **T3 / device data:** the entire device discriminating test depends on a device
  dimension existing on the signup-start step in GA4 or Snowflake. If it doesn't,
  the strongest test is unavailable and confidence rests more heavily on timing.
- **T5 / seasonality:** the ~14-week window has no prior-year baseline, so
  seasonality can be argued down but not fully excluded — state this as a caveat
  rather than claiming it is eliminated.
- **T7 / Slack:** ephemeral and search-bounded; a null result is genuinely weak
  evidence either way.
- **Cross-cutting freshness:** the local CSV ends 2026-04-06 and is a snapshot.
  Any magnitude or "still depressed" claim must be reconciled against live
  Snowflake / GA4 before it is treated as durable.
