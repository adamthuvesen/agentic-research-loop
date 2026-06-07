# Confidence (read-only)

**Server:** Confidence **experiments** MCP server — hosted, OAuth. Endpoint
`https://mcp.confidence.dev/mcp/experiments`. (The separate `…/mcp/docs` server is
Confidence SDK *documentation*, not a research data source — not wired here.)

**Read-only enforcement (`credential-only`):** connect with read access; never modify
experiments or flags. Read-only is enforced by the connected account's permissions —
there is no read-only flag.

## Enable

1. `uv run research source enable confidence` (or merge the bundle by hand).
2. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor); `codex mcp login
   confidence-experiments` for Codex.

## Notes

- Covers rollout timing, experiment state, decision history, and results. Treat as a
  primary source for rollout/experiment questions.
