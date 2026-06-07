# Slack (read-only)

**Server:** official Slack MCP server — hosted, OAuth. Endpoint
`https://mcp.slack.com/mcp`.

**Read-only enforcement (`credential-only`):** read-only is enforced by the connected
Slack app/user's scopes — grant **read (search/history) scopes only**; never send or
schedule messages. Slack is ephemeral, so cite findings with a freshness caveat.

## Enable

1. `uv run research source enable slack` (or merge the bundle by hand).
2. Replace `YOUR_SLACK_CLIENT_ID` in the snippet's `oauth.clientId`, then authenticate
   via `/mcp` (Claude) or Settings → MCP (Cursor).
3. **Codex only:** add `mcp_oauth_callback_port = 3118` at the top of
   `.codex/config.toml` (`research source enable` wires the server block but not this
   top-level key), then `codex mcp login slack`.

## Notes

- Covers recent discussions, decisions, and informal context — search/history only.
