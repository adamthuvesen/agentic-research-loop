# Mixpanel (read-only — credential-enforced, read-AND-write server)

**Server:** official Mixpanel MCP server — hosted, OAuth. US endpoint
`https://mcp.mixpanel.com/mcp` (EU: `https://mcp-eu.mixpanel.com/mcp`, IN:
`https://mcp-in.mixpanel.com/mcp`). An org admin must enable MCP first
(Settings → Org → Overview).

**Warning — this server is read+write.** It exposes `Delete-Dashboard`,
`Bulk-Edit-Properties` / `Bulk-Edit-Events` (can corrupt the data dictionary), and
taxonomy/metric/experiment/feature-flag edits. There is **no read-only flag**, and
the autonomous runner uses `--dangerously-skip-permissions`, so tool-level blocking
is bypassed. **The connected account's project role is the only guardrail.**

**Read-only enforcement (`credential-only`):**

- Connect a **dedicated Mixpanel user with the Consumer role**. Consumer **cannot
  edit the Lexicon** (blocks `Edit-*` / `Bulk-Edit-*`) and **cannot delete boards** —
  so the destructive tools are rejected at the API layer. Residual: a Consumer can
  still create its own private boards (harmless clutter).
- **Verify before autonomous use:** attempt one edit with the Consumer account and
  confirm it returns 403.
- Authenticate via OAuth (`/mcp` in Claude, Settings → MCP in Cursor) as that account.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Connect the dedicated Consumer account and complete the 403 check above.

## Notes

- Covers events, funnels, flows, retention, segmentation, boards/reports, and a
  JQL-like query path.
- For a *provably* read-only product-analytics source, prefer the **PostHog** bundle.
