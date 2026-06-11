# Source families

A map from *what you need to learn* to *which source can tell you*. Use it in
Phase 2 to turn the causal-system map into concrete source choices.

**Read this first:** only sources that show as **enabled** in
`uv run research source list` (plus the built-in web search and any
`--context-path` folders) are actually reachable this case. The families below are
the menu; the enabled set is what is on the table. If the causal chain needs a
family that is not enabled, say so at the orientation checkpoint and suggest
`research source enable <name>` — do not silently skip a causally critical source.

## Contents

- [The families](#the-families)
- [Pick by question type](#pick-by-question-type)
- [Warehouse-synced vs live (GSC, GA4)](#warehouse-synced-vs-live-gsc-ga4)
- [Triangulation](#triangulation)

## The families

| Family | Example bundles | Good for |
|--------|-----------------|----------|
| **Warehouse / metrics** | `snowflake`, `bigquery`, `postgres`, `redshift`, `databricks`, `duckdb` | The hard numbers: counts, rates, funnels, revenue, reliability. Usually the anchor (T1). Discover objects live, query SELECT-only. |
| **Product analytics** | `posthog`, `amplitude`, `mixpanel`, `ga4` | Funnels, retention, activation, feature adoption, on-site/in-app behavior, session paths. |
| **Search / web traffic** | `gsc`, `ga4` | Organic search (queries, clicks, impressions, CTR, rank) and site analytics (sessions, sources, conversions). Explains acquisition/traffic moves. |
| **Experiments / flags** | `confidence`, `launchdarkly`, `statsig` | The most common hidden cause of metric shifts: rollouts, A/B tests, flag/gate changes, targeting changes. Always check the timeframe — even null experiments rule a surface out. |
| **Docs / knowledge** | `notion`, `confluence`, `google-drive`, `microsoft-365` | The "why": strategy, retros, forecasts, runbooks, RFCs, decision records. |
| **Comms / decisions** | `slack` | Recent decisions, incident threads, informal context not yet in docs. |
| **Issue tracking / eng** | `linear`, `jira`, `github`, `azure-devops` | What shipped and when, ownership, code/PR/commit history. Strong for engineering root-cause. |
| **Observability / incidents** | `sentry`, `datadog`, `azure` | Errors, stack traces, releases, metrics, monitors, logs, traces, incidents. |
| **Revenue / CRM** | `stripe`, `hubspot`, `salesforce` | "Why did revenue, churn, or pipeline move": subscriptions, invoices, disputes, deals, accounts. |
| **External** | web search (built in) | Public incidents, competitor moves, platform/algorithm changes, seasonality context. |
| **Local context** | `--context-path` | Curated CSVs, exports, timelines, notes the user attached for this question. Read early — usually high-signal. |

## Pick by question type

- **Growth / acquisition / activation** (registrations, WAU, signups, conversion):
  warehouse for the funnel → search/web traffic for the top of funnel →
  product analytics for behavior → experiments for what changed → docs/comms for
  the narrative.
- **Reliability / latency / errors** (success rate, p95, failures): warehouse or
  observability for the metric → eng/issue tracking for what shipped →
  comms for incident context.
- **Revenue / churn / pipeline:** revenue/CRM for the money → warehouse for usage
  driving it → experiments for pricing/packaging tests → docs/comms for deals and
  decisions.
- **Quality / engagement / retention:** product analytics for cohorts →
  warehouse for the metric → experiments for feature changes → comms/docs for
  qualitative signal.

These are starting points, not rules. Let the causal-system map decide; reach one
or two levels up and down the chain, not just the metric's own family.

## Warehouse-synced vs live (GSC, GA4)

Some external sources are also synced into the warehouse. When a family is
available both ways, **prefer the warehouse copy** (joinable, consistent grain)
and fall back to the live API only when the warehouse is stale, incomplete for
the slice you need, or missing an API-only dimension.

- **GSC:** if GSC data is synced into your warehouse, query it there first
  (semantic views/marts, or the GSC-synced staging schema). Use the `research gsc`
  CLI fallback for fresher-than-sync data, suspected sync lag, or arbitrary
  dimensions/pagination.
- **GA4:** query the GA4 MCP for site analytics the warehouse does not cover.

## Triangulation

For every high-confidence claim the case will rest on, plan to confirm it in a
**second source family**. A number from the warehouse plus context from comms or
docs (or a second independent metric) is far stronger than either alone — and it
is what `## Required Cross-Checks` and each thread's `**Cross-Check:**` field
commit you to. Pick the smallest source set that still lets every key claim be
cross-checked.
