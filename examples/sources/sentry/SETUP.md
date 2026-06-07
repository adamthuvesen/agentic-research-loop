# Sentry (read-only)

**Server:** official Sentry MCP server
([`getsentry/sentry-mcp`](https://github.com/getsentry/sentry-mcp)) — stdio, run via
`npx @sentry/mcp-server@latest`. Wraps issues, events, stack traces, releases, and
search (`search_events`, `search_issues`, `get_issue_details`, `get_trace_details`).

**Read-only enforcement (`scope:org:read,project:read,event:read`):** the server has
**no read-only flag** and ships write tools (`update_issue`, `add_issue_note`,
`create_project`, …). Read-only is enforced by the **token scopes**:

- Do **not** use the hosted `https://mcp.sentry.dev/mcp` OAuth flow — its grant
  includes write scopes (`project:write`, `event:write`), so it is not read-only-safe.
- Use stdio with a **User Auth Token scoped read-only**: create one at
  *Settings → Auth Tokens* with only `org:read`, `project:read`, `event:read` — **no
  write/admin scopes**. Sentry's API rejects mutations the token isn't scoped for.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Export the read-only token via your environment (never committed config):
   ```bash
   export SENTRY_AUTH_TOKEN="$(op read 'op://vault/sentry-readonly/token')"
   # self-hosted Sentry: also export SENTRY_HOST=sentry.example.com
   ```

## Notes

- Covers issues, events, stack traces, releases, traces, and replays.
- The token scopes are the only guardrail — keep them read-only.
