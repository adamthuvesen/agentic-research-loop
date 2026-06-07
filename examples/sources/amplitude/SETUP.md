# Amplitude (read-only — credential-enforced, read-AND-write server)

**Server:** official Amplitude MCP server — hosted, OAuth. US endpoint
`https://mcp.amplitude.com/mcp` (EU: `https://mcp.eu.amplitude.com/mcp`).

**Warning — this server is read+write.** It exposes `create_chart`,
`create_dashboard`, `create_cohort`, `create_metric`, **`create_experiment`, and
`create_feature_flag`** — the last two can change live product behavior. There is
**no read-only flag**, and the autonomous runner uses `--dangerously-skip-permissions`,
so tool-level blocking is bypassed. **The connected account's role is the only
guardrail.**

**Read-only enforcement (`credential-only`):**

- Connect a **dedicated Amplitude account with the Viewer role** (the most
  restricted). Viewer blocks most writes at the API layer.
- **Verify before autonomous use:** Amplitude's docs do not confirm whether Viewer
  blocks `create_experiment` / `create_feature_flag`. Attempt one such call with the
  Viewer account and confirm it returns a permission error (403) before enabling this
  source in an autonomous loop.
- Authenticate via OAuth (`/mcp` in Claude, Settings → MCP in Cursor) as that account.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Connect the dedicated Viewer account and complete the 403 check above.

## Notes

- Covers charts, dashboards, funnels, retention, metrics, cohorts, experiments,
  feature-flag reads, and session replay.
- For a *provably* read-only product-analytics source, prefer the **PostHog** bundle
  (a read-scoped API key the server cannot write past).
