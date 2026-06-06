# Research Report

## Question

What caused the marketing-site registration drop that began the week of
2026-03-09, how concentrated is it, and is it real or an artifact of measurement
or traffic composition?

## Executive Summary

Registrations fell ~15% (−838/week, ~4,189 fewer over the five weeks through
2026-04-06) and have not recovered. The loss is **a top-of-funnel conversion
break, not a traffic problem** — visitors are flat (~43k–44k/week) throughout.

The break decomposes into **two effects that started the same week but have
different shapes and almost certainly different causes**:

- **Effect A — an instantaneous step at visitor → signup_started (dominant,
  ~90% of the loss).** Conversion dropped from *exactly* 20.0% to *exactly* 17.0%
  in the launch week, dead-flat before and after. A clean step is the signature
  of a one-time structural change, and it lines up date-and-mechanism with the
  **Homepage v3** launch (2026-03-09), which moved the primary "Sign up free" CTA
  below the fold on desktop. This is the headline cause.
- **Effect B — a gradual erosion at signup_started → registration (secondary,
  ~10%), decelerating toward a floor.** This rate ramps down 65.0% → 63.0% over
  five weeks, but the weekly decline is **slowing** (Δ −0.55, −0.57, −0.35,
  −0.29pp) and the last two weeks have identical registrations (4709/4709) despite
  higher traffic — a floor signature. It is approaching a new lower plateau
  (≈62–62.5%), so steady-state total damage is **bounded at roughly −15.5 to −16%,
  not runaway**. A gradual ramp on a *different* funnel step is still **not
  explained by the CTA move**, and the mechanism points the *opposite* way: by the
  funnel definitions, this step is form-completion *given* an open, and a CTA moved
  below the fold drops the lower-intent visitors who won't scroll — so the openers
  who remain should complete at an *equal-or-higher* rate (predicted s→r flat/up).
  Observed s→r *fell*. The opposite sign means Effect B is not a selection
  side-effect of Effect A; it is a distinct, unexplained second contributor.

**Confidence is moderate-high on Effect A within the available data, low/open on
Effect B's cause, and capped overall** because no cross-source verification was
possible in this runner (Snowflake, GA4, Slack, Notion, Linear, Confidence all
unreachable; GA4 property unset). The single sharpest test — a desktop-vs-mobile
device split that would confirm the desktop-only CTA mechanism — could not be run.

> Note: this case ran on an explicitly **synthetic/fictional** local dataset, in
> an offline runner that suppresses all external sources *by design*. Magnitudes
> and the Effect-B trend are real *in that data* but must be reconciled against
> live Snowflake/GA4 before they are trusted operationally. An adversarial
> challenge cycle confirmed the ranking survives review but fixed the confidence
> ceiling: this is a strong **single-source, circumstantial** diagnosis, not a
> verified one — the causal link rests on a bundled launch note no second system
> could corroborate here.

## Ranked Causes

1. **Homepage v3 CTA moved below the fold (desktop)** — top-of-funnel UX
   regression at visitor → signup_started. Best explanation for Effect A (~90% of
   the loss). Timing exact, mechanism targets the exact step that broke, and the
   only-dated-change-in-the-window in the local record. *Confidence: moderate-high
   (local source); the desktop-vs-mobile discriminating test is still unrun.*

2. **A second, unexplained mid-funnel regression** — drives Effect B (gradual
   signup_started → registration erosion, decelerating toward a ~62–62.5% floor).
   Candidate mechanisms: a
   registration-form regression bundled into v3 that compounds, a composition
   drift, or a slow rollout. *Confidence: low; could also be a data artifact.*

### Rivals considered and where they stand

- **Normal variance / one-week blip** — rejected. Pre-period v→s scatter is
  literally zero; the post level holds five weeks.
- **Measurement / tracking artifact** — weakened, not closed. The break is
  isolated to one step rather than deflating the whole funnel, which argues
  against broad instrumentation breakage; but the "no tracking change" claim is
  self-reported and was not independently triangulated (systems unreachable).
- **Traffic volume / seasonality / composition drift** — volume rejected
  (visitors flat). Seasonality and source/medium composition could not be tested
  here (no segmentable live source) and remain genuinely open.

## Evidence Highlights

- **v→s:** exactly 20.000% for all 9 pre weeks, exactly 17.000% for all 5 post
  weeks (pop. stdev 0.000pp on both sides). Step, not noise.
- **s→r:** 65.000% flat pre; post 64.72 → 64.17 → 63.60 → 63.24 → 62.95%,
  monotonic but **decelerating** (Δ −0.55, −0.57, −0.35, −0.29pp); marginal
  Effect-B loss peaks in post-week 3 then falls, and the final two weeks'
  registrations are identical (4709/4709) — consistent with approaching a floor
  near ≈62–62.5%.
- **Impact decomposition vs a no-launch counterfactual (v→s=20%, s→r=65%):**
  Effect A ≈ 4,292 lost regs (90.1%), Effect B ≈ 473 (9.9%), total ≈ 4,765 over
  five weeks.
- **Activations are a derived column:** activations = round(0.60 × registrations)
  every week, pre and post. "Downstream quality intact" is therefore true *by
  construction* and is **not** independent evidence — corrected from cycle 1.
- **Change correlation:** Homepage v3 is dated 2026-03-09 (the break week) with a
  matching mechanism; the 2026-02-16 pricing-copy refresh is ruled out (v→s stays
  20.0% through 2026-03-02).

## Rejected Leads

- **One-week blip / variance** — zero pre-period scatter + sustained 5-week level.
- **2026-02-16 pricing-copy refresh as the cause** — no break at/after that date.
- **Traffic-volume loss** — visitors flat-to-up post-launch.
- **Web search for external/seasonal triggers** — dead end by design: the dataset
  is fictional, so no external event can corroborate it.

## Risks And Caveats

- **No cross-source verification.** Every external system (Snowflake, GA4, Slack,
  Notion, Linear, Confidence) was unreachable; findings rest on one synthetic
  source. Magnitude, recency, and the "no tracking change" claim are
  single-sourced.
- **The sharpest test is unrun.** A desktop-vs-mobile split on visitor→signup
  would confirm (desktop-concentrated) or refute (uniform) the desktop-CTA
  mechanism. It needs a device dimension that no available source exposes here.
- **Effect B may be a generator artifact** — if real, it adds a bounded ~0.5–1pp
  to the steady-state drop (total ≈ −15.5 to −16%), since its weekly decline is
  decelerating toward a floor rather than running away. (This corrects an earlier
  read that it would keep deepening the drop past −15% without bound; the asymptote
  is read off only five synthetic points, so it stays a caveat, not a certainty.)
- **Snapshot ends 2026-04-06.** "Still depressed today" and "still worsening" are
  unverified past that date.
- **No prior-year baseline** in the ~14-week window, so seasonality is argued down
  but not excluded.

## Challenge Review

A mandatory adversarial pass stress-tested the conclusion before close.

- **Rival explanation tested:** the measurement/tracking artifact — that a
  counting or definition change at 2026-03-09 deflated measured signups without a
  real behavior shift. It survives review only as *weakened*, not closed: the
  break is isolated to one funnel step (not a whole-funnel deflation), which is
  hard to produce with broad instrumentation breakage, but the "no tracking
  change" claim is self-reported and could not be triangulated.
- **Weakest claim / most fragile dependency:** the claim that **Effect B is a
  distinct second real-world regression** is the weakest-supported — it could be a
  synthetic decay curve. The most fragile dependency is a single self-reported
  line in the launch note ("no infrastructure or tracking change in this window")
  that the whole causal chain leans on and that no second system could confirm here.
- **What survived scrutiny:** the ranking held — Effect A (CTA move, ~90%) over
  Effect B (distinct, ~10%, low confidence). The selection-sign argument actually
  *strengthened* the two-causes reading by showing the CTA mechanism predicts the
  opposite sign for Effect B than observed. The variance, pricing-copy, and
  volume rivals stayed rejected.
- **What remains open:** every unresolved objection reduces to one structural
  fact — cross-source verification is impossible in this offline runner *by
  design*. So the open items are not analytic gaps but a confidence ceiling: this
  is a strong **single-source, circumstantial** diagnosis, not a verified one. The
  device split, live magnitude/recency reconciliation, and independent launch-date
  corroboration are handed off to a live run (see Recommended Next Actions). The
  objections are appropriately *contained*, not resolved away.

## Recommended Next Actions

1. **Run the device split (highest value).** GA4 `deviceCategory` (or a Snowflake
   device funnel) on visitor→signup_started, ~6 weeks each side of 2026-03-09.
   Desktop concentration clinches the CTA mechanism; uniformity forces a pivot.
2. **Reconcile magnitude and recency on live data.** Pull the live funnel for the
   same weeks *and after 2026-04-06* to confirm the −15% and whether Effect B kept
   declining.
3. **Investigate Effect B separately.** Segment the form-completion step by
   device, browser, and form version; check whether v3 also changed the
   registration form, not just the CTA placement.
4. **Independently corroborate the launch + "no tracking change" claim** via a
   Linear ticket / Notion release page / Confidence rollout, and scan for any
   analytics/consent/tagging change in the window.
5. **Find the owner / existing awareness** (Slack/Notion/Linear) before
   recommending a fix or rollback.

## Conclusion

The registration drop is real, top-of-funnel, and persistent. The dominant cause
(~90%) is best explained by the Homepage v3 CTA moving below the fold, suppressing
who starts a signup — a clean instantaneous step at exactly the launch week. A
smaller, unexplained second effect erodes form completion — decelerating toward a
floor (bounded steady-state ≈ −15.5 to −16% total), and the single-cause story
does not cover it. The diagnosis is solid *within a
synthetic single source*; the device split and live cross-source reconciliation
remain the work that would convert this from a strong circumstantial case into a
confirmed one.
