# LaunchDarkly (read-only)

**Server:** official LaunchDarkly MCP server
([`@launchdarkly/mcp-server`](https://github.com/launchdarkly/mcp-server)) — local
stdio via npx. (A hosted OAuth endpoint exists, but the local server lets you pin
`--scope read` in config, so it's the read-only-safe choice.)

**Read-only enforcement (`scope:reader` — credential-enforced at the API):** read-only
is provable here, like PostHog. Two layers — use both:

- **Reader-role API token** — create a LaunchDarkly **API access token with the Reader
  base role**. LaunchDarkly's API rejects every write from a Reader token (403-class),
  regardless of what tools the server exposes.
- **`--scope read`** — already pinned in the bundle's `args` as a second guard.

**Warning — the server ships flag-mutation tools** (`toggle-flag`, `create-flag`,
`delete-flag`, `update-targeting-rules`, `start/stop-experiment-iteration`) that change
**production** behavior. The Reader token is what neutralizes them — **never use a
Writer/Developer token.**

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Export a **Reader-role** token via your environment (never committed config):
   ```bash
   export LAUNCHDARKLY_API_KEY="$(op read 'op://vault/launchdarkly-reader/token')"
   ```

## Notes

- Covers flag configs/status across environments, the change **audit log**
  (who-changed-what-when), experiment definitions/iterations, and code references.
- The audit log + flag status directly answer "did a flag rollout cause the metric move."
