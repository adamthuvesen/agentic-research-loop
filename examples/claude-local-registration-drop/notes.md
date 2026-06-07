# Research Notes

## Working Theory

- **Current best explanation (refined cycle 2):** The registration drop at
  2026-03-09 is **two effects with different temporal signatures**, not one:
  - **Effect A — instantaneous v→s step (dominant, ~90% of the loss).** visitor →
    signup_started fell from *exactly* 20.000% to *exactly* 17.000% in the launch
    week and is dead-flat on both sides. A clean step like this is the signature of
    a one-time structural change and matches the **Homepage v3** CTA-moved-below-
    fold mechanism. This is the headline cause.
  - **Effect B — gradual s→r erosion (secondary, ~10%), DECELERATING toward a floor
    (refined cycle 3).** signup_started → registration drifts down monotonically
    post-launch (65.0% → 62.95%), but the week-over-week decline is **slowing**, not
    constant: Δ = −0.55, −0.57, −0.35, −0.29pp. The marginal Effect-B reg loss
    peaked in post-week 3 (+44) then fell (+25, +22), and the last two weeks have
    **identical registrations (4709/4709)** despite higher visitors and signups — a
    floor signature. So Effect B is approaching a new lower plateau (≈62–62.5% s→r),
    **not** running away. This corrects the cycle-2 "still falling, no floor, may
    exceed −15%" claim. A *ramp* on a *different* funnel step is still a different
    signature than the CTA step and is **not explained by the CTA hypothesis**, so
    it remains a distinct (likely second) cause — but its steady-state damage is
    bounded, putting total steady-state drop at ≈ −15.5 to −16%, converging.
- **Confidence:** Moderate-high on Effect A *within the local source*; the timing,
  localization, and mechanism line up cleanly. Low/open on Effect B's cause. The
  whole case is capped because every cross-source reconciliation and the device
  discriminating test are **unavailable in this offline runner** (no Snowflake MCP,
  GA4 unset, Slack/Notion/Linear/Confidence not reachable — re-verified cycle 2).
- **Update (cycle 3):** local source is now fully exhausted — every cross-source
  thread (T1 reconcile, T2 corroboration, T3 device split, T4 triangulation, T5
  segmentation, T7 ownership) remains hard-blocked by the offline runner, re-verified
  this cycle (no Snowflake MCP tools; `research ga4` → GA4_PROPERTY_ID unset). The
  only new signal extractable was Effect B's shape (E7). No further local moves left.
- **Update (cycle 4):** confirmed the offline block is **by design**, not a bug —
  this is the `claude-local` runner (commit 2b72f6e), which pins Claude Code with
  `--strict-mcp-config` + an empty MCP config specifically to run over only the
  bundled local data with no MCP servers. So "everything cross-source is blocked"
  is the runner's contract, not a transient failure; re-checking it further is
  wasted effort. **Independently re-verified all arithmetic** (v→s 20.000→17.000,
  s→r 65.000→62.955, r→a flat ~60, 90.1/9.9 A/B split) — every prior-cycle number
  holds. Added one genuinely new local move cycles 1–3 missed: the
  **selection-sign argument** (E8), which sharpens the two-causes claim via
  mechanism, not just temporal shape. Ran the mandatory **challenge
  cycle** (see below). Local source now genuinely exhausted.
- **What would change this:** a device split showing Effect A is *uniform* across
  desktop/mobile (refutes the desktop-CTA mechanism → global cause); a confirmed
  tracking/definition change at 2026-03-09; a second same-week change explaining
  Effect B; or live data showing the s→r erosion was generator noise, not real.

## Environment constraint (important, governs every thread)

This case is running in the **offline / claude-local runner**. Verified this cycle:
- No Snowflake MCP tools are exposed to the session (`ToolSearch +snowflake` →
  none).
- `research ga4` fails: `GA4_PROPERTY_ID is not set`.
- Notion / Slack / Linear / Confidence / GSC are configured in `.mcp.json` but
  not reachable as callable tools here.

**Consequence:** the only live, queryable source this cycle is the local context
folder (`examples/local-sources`), whose data is explicitly *synthetic*. Every
plan thread that requires a live cross-check is therefore **blocked by
environment**, not by analysis. Findings below are "confirmed in local source;
cross-source reconciliation pending a live run."

## Hypotheses

### H1 (T1): Persistent top-of-funnel break at visitor → signup_started
- **Status:** supported (local source); cross-source check blocked
- **Why plausible:** Weekly rates show v→s = exactly 20.0% for all 9 pre weeks,
  then exactly 17.0% for all 5 post weeks, starting 2026-03-09. s→r (~65%→~63%)
  and r→a (flat 60%) are essentially unchanged. Visitors are flat (~43.1k pre →
  ~44.0k post). So it is not traffic volume and not a downstream-rate problem.
- **Strongest rival:** normal variance / one-week blip that mean-reverts.
- **Discriminating test (run):** pre-period v→s standard deviation = **0.000pp**
  (zero scatter), and the post level holds for 5 consecutive weeks with no
  recovery. A blip or variance is impossible against zero pre-period scatter.
  Rival **rejected**.
- **Evidence so far:** see Evidence Log E1–E2.
- **Next check:** reconcile the CSV weekly funnel against the live Snowflake
  funnel mart / GA4 for the same weeks (blocked until a live run).

### H2 (T2): Homepage v3 is the mechanism
- **Status:** supported (local source); independent-system corroboration blocked
- **Why plausible:** Launch notes date Homepage v3 to **2026-03-09 — exactly the
  break week** — and its stated mechanism (CTA moved below the fold on desktop)
  directly targets the step that broke (signup_started). The nearby 2026-02-16
  pricing-copy refresh is a decoy: v→s stays 20.0% through 2026-03-02, so it
  caused no break.
- **Strongest rival:** a *different* change in the same week (tracking, infra,
  pricing, paid-traffic shift) is the real driver and v3 is coincidental.
- **Discriminating test:** build a dated change log around 2026-03-09 from
  Confidence/Linear/Notion. **Blocked** — those systems aren't reachable here.
  Within the local record, Homepage v3 is the only dated change matching both
  timing and mechanism.
- **Next check:** corroborate the 2026-03-09 date with an independent system
  (Linear ticket / Notion release page / Confidence rollout) on a live run.

### H5 (NEW, cycle 2): A second, gradual mid-funnel effect on s→r, distinct from the CTA move
- **Status:** open on cause; SHAPE refined cycle 3 — decelerating toward a floor,
  not runaway (E7). Steady-state damage is bounded (~−15.5 to −16% total), which
  downgrades the cycle-2 "may exceed −15% without bound" concern.
- **Why it matters:** Last cycle parked the s→r decline as a "low-priority,
  possibly synthetic-artifact" footnote. Quantified precisely, it is a real,
  perfectly-monotonic, **still-worsening** erosion that the single-cause Homepage
  v3 story does not explain. Two effects with two signatures usually means two
  causes.
- **Discriminating signature:** Effect A (v→s) is a *step* (instantaneous, then
  flat) → structural/one-time change. Effect B (s→r) is a *ramp* (gradual, no
  floor) → something accumulating: a registration-form regression in v3 that
  compounds, a cohort/composition drift, a slow rollout, or a second change. The
  CTA-below-fold mechanism predicts **flat** s→r (it only gates form opens), so it
  cannot be Effect B's cause.
- **Strongest rival:** Effect B is a synthetic-generator artifact / rounding drift
  with no real-world referent (plausible — this dataset is explicitly fictional).
  Cannot be distinguished without live data.
- **Sharpened (cycle 4) — selection-sign argument (E8):** per `funnel-definitions.md`,
  s→r is the *form-completion* rate of people who already **opened** the form. The
  CTA-below-fold change gates who *reaches/opens* the form; the visitors it removes
  are the marginal, lower-intent ones who won't scroll to a below-fold CTA. The
  openers who **remain** should therefore skew *higher* intent → the mechanism
  predicts s→r **flat or rising**. Observed s→r **falls** (65.0%→63.0%) — the
  *opposite sign*. So Effect B cannot be a positive-selection side-effect of Effect
  A; it needs a separate cause (or is a generator artifact). This disconfirms the
  single-cause story by *mechanism*, independently of the step-vs-ramp temporal
  argument — strengthening H5's "distinct second contributor" status.
- **Next check (live only):** does s→r erosion appear in Snowflake/GA4 over the
  same weeks, and does it keep declining after 2026-04-06? If real, segment the
  form-completion step by device, browser, and form version.

### H3 (T4): Measurement / tracking artifact
- **Status:** weakened (local reasoning); cross-check blocked
- **Why plausible to test:** brief H3 + the launch notes *claim* "no infrastructure
  or tracking change" — a claim that should be verified, not accepted.
- **Argument against (this cycle):** a tracking/counting change typically deflates
  multiple steps or whole-funnel counts. Here the break is isolated to one step
  (v→s) while r→a stays exactly 60% and s→r barely moves — a shape that is hard to
  produce with broad instrumentation breakage and easy to produce with a real
  entry-point UX change. So measurement is a weaker explanation, but **not ruled
  out** without three-source agreement.
- **Next check:** compare the same metric across CSV vs Snowflake vs GA4 over the
  inflection; scan Linear/Notion for analytics/consent/tagging changes (blocked).

## Evidence Log

- **E1 — Claim:** visitor→signup_started conversion dropped from 20.0% to 17.0%
  at the week of 2026-03-09 and held for 5 weeks; downstream rates unchanged.
  **Source family:** Local context (synthetic).
  **Source detail:** `examples/local-sources/registrations_weekly.csv` (14 weeks,
  2026-01-05 → 2026-04-06); rates computed per week.
  **Supports:** H1.
  **Caveat / freshness:** static snapshot ending 2026-04-06; synthetic data; no
  live cross-check available this run.

- **E2 — Claim:** the pre-period v→s rate has zero variance (stdev 0.000pp, all
  weeks exactly 20.00%), so the post-launch 17.0% level is a true break, not noise.
  **Source family:** Local context (synthetic).
  **Source detail:** same CSV, population stdev of v→s across the 9 pre weeks.
  **Supports:** H1 (rejects the variance rival).
  **Caveat:** zero variance reflects synthetic generation; real data will scatter,
  so the *significance* argument must be re-made on live data.

- **E3 — Claim:** Homepage v3 shipped 2026-03-09, moving the "Sign up free" CTA
  below the fold on desktop; no other funnel-relevant change is dated in that week.
  **Source family:** Local context (synthetic).
  **Source detail:** `examples/local-sources/context/launch-notes.md`.
  **Supports:** H2.
  **Caveat:** single uncorroborated source; the "no tracking change" claim is
  self-reported and not independently verified.

- **E4 — Claim:** business impact ≈ **−838 registrations/week (−14.9%)**, ~**4,189
  fewer registrations** across the 5 post weeks; activations −503/week (−14.9%)
  with registration→activation held flat at 60%.
  **Source family:** Local context (synthetic).
  **Source detail:** same CSV; pre vs post weekly means.
  **Supports:** T6 — damage is pure upstream signup-volume loss, not downstream
  quality/retention degradation.
  **Caveat:** activations can lag registration, so the most recent post weeks may
  understate; magnitude needs live reconciliation. **See E6 — this caveat is now
  superseded: activations are a deterministic 60% of registrations in this data.**

- **E5 — Claim (cycle 2):** The drop decomposes into a dominant *instantaneous*
  v→s step (~90% of the loss, ~4,292 of ~4,765 lost regs over 5 post weeks) and a
  secondary *gradual* s→r erosion (~10%, ~473 regs). v→s is exactly 20.000%→17.000%
  with zero scatter on both sides; s→r ramps 65.0%→62.96% at −0.45pp/week and is
  still falling at the 2026-04-06 edge (no floor).
  **Source family:** Local context (synthetic).
  **Source detail:** same CSV; per-week rates + shortfall decomposition vs a
  no-launch counterfactual (v→s=20%, s→r=65%).
  **Supports:** H1 (Effect A) and H5 (Effect B). The two distinct temporal
  signatures argue for two distinct causes.
  **Caveat:** s→r monotonicity could be a generator artifact; needs live data.

- **E7 — Claim (cycle 3):** Effect B is **decelerating toward a floor**, not a
  runaway. Post-launch s→r week-over-week deltas are −0.553, −0.571, −0.354,
  −0.288pp (slowing after post-week 2); marginal Effect-B reg loss rises 21→62→106
  then the *increment* peaks (+44 in week 3) and falls (+25, +22); the final two
  weeks have identical registrations (4709 with visitors 43800→44000 and signups
  7446→7480). Extrapolating the geometric-looking decay puts the s→r asymptote at
  ≈62–62.5% (vs 65% pre), so steady-state total registration drop ≈ −15.5 to −16%,
  **converging — not exceeding −15% without bound.**
  **Source family:** Local context (synthetic).
  **Source detail:** same CSV; per-week s→r deltas + Effect-A-only counterfactual
  (reg = 0.1105 × visitors) decomposition.
  **Supports:** refines H5 / corrects E5 + the cycle-2 report language. The "still
  growing past −15%" warning was an overstatement; damage is bounded.
  **Caveat:** an asymptote read off 5 synthetic points is fragile; the identical
  4709/4709 could be coincidence. Still needs live data past 2026-04-06 to confirm
  the floor. Whether Effect B is a real second regression or a generator artifact
  is still unresolved — only its *shape* is now better characterized.

- **E8 — Claim (cycle 4):** the funnel **definitions** confirm the Effect A / B
  mechanism split, and a selection argument predicts the *opposite sign* for Effect
  B than what a pure CTA-placement change would produce.
  **Source family:** Local context (synthetic).
  **Source detail:** `examples/local-sources/context/funnel-definitions.md` —
  `signups_started` = "Visitors who **opened** the sign-up form",
  `registrations` = "Visitors who **completed** registration". So v→s = reach/open
  the form (what a below-fold CTA gates) and s→r = completion *given* an open (which
  a CTA-placement change does not touch). Moving the CTA below the fold drops the
  marginal lower-intent visitors who won't scroll, so the retained openers skew
  *higher* intent → predicted s→r ≥ 65%. Observed s→r = 64.72→62.96% (falling).
  **Supports:** H2 (CTA gates v→s only) and H5 (Effect B is a distinct cause, not a
  selection side-effect — the observed sign is opposite to the CTA prediction).
  **Caveat:** assumes scroll-behavior correlates with completion intent (reasonable,
  not certain) and that the synthetic generator did not simply impose a decay curve
  on s→r independent of any modeled mechanism (unfalsifiable here).

- **E6 — Claim (cycle 2):** activations = round(0.60 × registrations) **every
  week, pre and post** (r→a = 60.00% with ≤0.01pp integer-rounding scatter). So
  activations carry **no independent signal**; "downstream quality intact" is true
  *by construction*, not evidence.
  **Source family:** Local context (synthetic).
  **Source detail:** same CSV; a/r exact ratio check all 14 weeks.
  **Supports:** corrects E4 — the r→a stability is **not** corroboration that user
  quality held; it is a derived column. Any real downstream-quality question is
  unanswerable from this dataset and needs live activation data.

## Challenge Cycle (cycle 4 — mandatory stress-test)

**Strongest competing explanation to the whole case:** *There is no behavioral
"cause" to recover — the dataset is a deterministic synthetic construction, and
"Homepage v3" is the exercise's intended narrative, co-authored with the data in
`launch-notes.md`.* This is the most honest rival. The tells are overwhelming:
v→s is *exactly* 20.000→17.000 with literally zero variance, s→r is *exactly*
65.000 flat then a smooth monotonic decay, and activations are *exactly*
round(0.60 × registrations) every week. Real funnel data never lands this clean.
Within the exercise's frame the answer is "the CTA move"; **epistemically the
causal claim is pattern-matched to a bundled note, not verified.**
→ *Status: UNRESOLVED, and unresolvable in this runner by design* (no independent
source exists to break the data↔note circularity). Not an analytic gap — a
structural ceiling.

**Weakest-supported claim:** "Effect B is a distinct second *real-world*
regression." E8's selection-sign argument cleanly shows it is **not** a side-effect
of the CTA move, but cannot distinguish a real second regression from a generator
decay curve. Confidence stays low; flagged as such in the report.
→ *Status: appropriately hedged; objection accepted and carried as a caveat.*

**Most fragile dependency:** the entire causal chain hangs on a single
self-reported line — "no infrastructure or tracking change in this window" — in
the same file that names the launch. If that line is wrong, the measurement-artifact
rival (H3) reopens. No independent system can corroborate it here.
→ *Status: UNRESOLVED, unverifiable in this runner.*

**Did the challenge change any conclusion?** No reversal. The challenge does *not*
overturn the ranking (Effect A → CTA, ~90%; Effect B → distinct, ~10%, low
confidence) — within the only available source that ranking is the best-supported
reading, and E8 strengthened it. What the challenge establishes is the **correct
confidence ceiling**: this is a strong *circumstantial, single-source* diagnosis,
not a verified one. The report already states exactly this.

**Disposition:** the unresolved objections are all of one kind — *cross-source
verification is structurally impossible in the claude-local runner*. Reopening for
more cycles would only re-confirm the block (as cycles 2–3 already did); there is
no further local move that moves confidence. The case is therefore **complete to
the limit this runner permits**, with the verification work explicitly handed off
to a live run (device split, magnitude/recency reconciliation, independent
change-log corroboration). Challenge passed in the sense that conclusions survived
challenge review *and* their limits are now precisely stated.

## Challenge Review

Structured challenge pass for the close decision (expands the narrative in
`## Challenge Cycle` above into the contract's required fields).

- **Strongest competing explanation:** the conclusion is "Homepage v3's
  below-fold CTA caused Effect A." Its strongest rival inside the data is the
  **measurement/tracking artifact (H3)** — a counting/definition change at
  2026-03-09 deflated measured signups without a real behavior change. It is
  weakened (the break is isolated to one step, not a whole-funnel deflation) but
  not killed, because the only thing ruling it out is a self-reported line. The
  deeper rival is structural: the dataset is a deterministic synthetic
  construction and "Homepage v3" is a bundled narrative, so the causal link is
  pattern-matched to a co-authored note, not independently discovered.
- **Weakest-supported important claim:** "Effect B is a distinct second
  *real-world* regression." E8's selection-sign argument shows it is **not** a
  side-effect of the CTA move, but cannot distinguish a genuine second regression
  from a synthetic decay curve. Held at low confidence and labeled as such.
- **Most fragile dependency:** the entire causal chain leans on one self-reported
  sentence — "no infrastructure or tracking change in this window" — in the same
  file (`launch-notes.md`) that names the launch. If that line is wrong, H3
  reopens. No independent system can corroborate it in this runner.
- **Resolution status:** `resolved` (contained, not reopenable). Every unresolved
  objection reduces to the same root: cross-source verification is structurally
  impossible in the claude-local runner *by design* (commit 2b72f6e). The report
  already states the correct confidence ceiling — a strong **single-source,
  circumstantial** diagnosis, not a verified one — and carries each objection as
  an explicit caveat. Cycles 2–3 demonstrated that reopening only re-confirms the
  block; there is no further local move that shifts confidence.
- **Next cycle target if unresolved:** N/A in this runner. The verification work
  is handed off to a live run: (1) desktop-vs-mobile device split on
  visitor→signup_started, (2) live magnitude/recency reconciliation past
  2026-04-06, (3) independent corroboration of the launch date + "no tracking
  change" line via Linear/Notion/Confidence.

## Dead Ends

- **Variance / one-week-blip explanation for the drop** — rejected: zero
  pre-period scatter + a sustained 5-week post level (E2).
- **2026-02-16 pricing-copy refresh as the cause** — rejected: v→s stays 20.0%
  through 2026-03-02; no break at or after that date.
- **Traffic-volume explanation** — rejected for now: visitors are flat/slightly up
  post-launch, so this is a conversion-rate break, not a volume loss.
- **Web search for external/seasonal events (T5 angle)** — dead end *by design*:
  the dataset and launch notes are explicitly fictional ("None of this is real"),
  so no external event can corroborate or explain these synthetic numbers. Not
  worth a search call in this runner.

## Open Questions

- **[H5 — refined cycle 3.] The s→r erosion is real in-data but DECELERATING toward
  a floor.** signup_started→registration ramps 65.0% → 64.72 → 64.17 → 63.60 →
  63.24 → 62.95%, with the week-over-week decline *slowing* (Δ −0.55, −0.57, −0.35,
  −0.29pp) and the last two weeks' registrations identical (4709/4709) — a floor
  signature (E7). It is still a *gradual* effect on a *different* step than the CTA
  move, so the Homepage v3 CTA hypothesis does not explain it. Open: is it a real
  second regression (form/checkout in v3?), a composition drift, or a generator
  artifact? Resolvable only on live data. **Steady-state damage now looks bounded
  (~−15.5 to −16% total), not runaway** — correcting the cycle-2 warning.
- Is the v→s drop **desktop-concentrated** (predicted by the desktop-only CTA
  move) or uniform across devices? This is the single sharpest test and is
  currently unanswerable (no GA4/Snowflake device dimension here).
- Did the drop persist *past* 2026-04-06? The snapshot ends there; "still
  depressed today" is unverified.
- Was the drop already noticed internally, and who owns the homepage funnel?
  (Slack/Notion/Linear — unreachable here.)

## Leads

- **Desktop-vs-mobile device split on visitor→signup_started** [high]
  Why it matters: the single discriminating test for the desktop-CTA mechanism;
  desktop concentration would clinch it, uniformity would refute it.
  Next: on a live run, GA4 `deviceCategory` split of sessions→signup conversion
  for ~6 weeks before/after 2026-03-09; cross-check any Snowflake device funnel.
  Sources to check: GA4, Snowflake.

- **Independent corroboration of the 2026-03-09 launch date + "no tracking change"
  claim** [high]
  Why it matters: the whole causal chain leans on one self-reported note.
  Next: find a Linear ticket / Notion release page / Confidence rollout dated to
  the launch week; scan for any analytics/consent/tagging change in the window.
  Sources to check: Linear, Notion, Confidence.

- **Live magnitude + recency reconciliation** [medium]
  Why it matters: confirms the snapshot's ~15% drop is real and still ongoing.
  Next: Snowflake funnel mart for the same weeks + weeks after 2026-04-06.
  Sources to check: Snowflake, GA4.

- **Traffic-composition / seasonality check** [medium]
  Why it matters: rules out the "worse incoming audience" rival.
  Next: segment v→s by source/medium, country, new/returning around the inflection;
  check whether the drop is within-segment vs a mix shift.
  Sources to check: GA4, Snowflake; web search for external events.

- **Effect B: the still-worsening s→r erosion (NEW, cycle 2)** [high]
  Why it matters: it's a second, unexplained cause the CTA story doesn't cover,
  and it's still growing — so steady-state damage may exceed −15%.
  Next: on live data, confirm s→r declined post-2026-03-09 and whether it kept
  falling after 2026-04-06; segment the form-completion step by device, browser,
  and form version; check whether v3 also changed the registration form itself.
  Sources to check: Snowflake, GA4, Linear/Notion (v3 scope).
