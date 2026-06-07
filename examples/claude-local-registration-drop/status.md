# Research Status: 2026-06-06-registration-drop

- Status: `idle`
- Cycle count: `5`
- Challenge status: `passed`
- Sources in play: `Notion, Slack, Linear, web, Snowflake, Confidence, GSC, GA4, local-context`
- Report state: `substantive`

## Current Answer

Registrations fell ~15% (−838/week, ~4,189 fewer over the five weeks through 2026-04-06) and have not recovered. The loss is **a top-of-funnel conversion break, not a traffic problem** — visitors are flat (~43k–44k/week) throughout. The break decomposes into **two effects that st...

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

## Recent Cycles

- `0003`: `progress`
- `0004`: `challenge_required`
- `0005`: `complete`

## System

- Runner: `claude-local`
- Active cycle: `n/a`
- Stop reason: `case_complete`
