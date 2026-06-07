# PostHog (read-only)

**Server:** official PostHog MCP server
([`PostHog/posthog`](https://github.com/PostHog/posthog), `services/mcp`) via the
`mcp-remote` shim to the hosted endpoint `https://mcp.posthog.com/mcp` (EU:
`https://mcp-eu.posthog.com/mcp`; self-hosted: set `POSTHOG_BASE_URL`).

**Read-only enforcement (read-scoped personal API key):** this is the *strongest*
read-only mechanism among the analytics sources — enforced by the **credential
itself**, not a role or a runtime toggle. Create a PostHog **personal API key**
(`phx_…`) with **only read scopes** (`insight:read`, `query:read`, `dashboard:read`,
`feature_flag:read`, `person:read`, `cohort:read`, `experiment:read`,
`session_recording:read`, `error_tracking:read`). PostHog rejects every write from a
read-scoped key with a 403, so even though the server exposes `create-/update-/delete-`
tools (including feature flags), the key physically cannot authorize them.

> **Do NOT use the `mcp_server` key preset** — it grants `feature_flag:write`.
> Hand-pick the `:read` scopes.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`. (EU accounts: swap the URL for
   `https://mcp-eu.posthog.com/mcp`.)
3. Export the read-scoped key via your environment (never committed config):
   ```bash
   export POSTHOG_AUTH_HEADER="Bearer phx_your_read_scoped_key"
   ```

## Notes

- Covers insights, trends, funnels, retention, events, persons/cohorts, feature
  flags, error tracking, and HogQL/SQL via the query tool.
- Read-only lives in the key scopes — keep them `:read` only.
