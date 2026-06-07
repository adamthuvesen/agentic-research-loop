# Datadog (read-only)

**Server:** official Datadog **Bits AI** managed MCP server — remote, Streamable
HTTP at `mcp.datadoghq.com` (GA). The endpoint shown is a preview path; confirm
the current one against Datadog's MCP docs.

> **Endpoint:** **pick your regional host** — `.datadoghq.com` (US1),
> `.datadoghq.eu` (EU), or the `us3`/`us5`/`ap1`/gov variants; a mismatched region
> fails auth.

**Read-only enforcement (`credential-only`):** there is **no server-side read-only
flag**, and the managed server **does expose write tools** (mute/create/update/delete
monitors, schedule/cancel downtime, dashboards). Read-only is enforced by the
**Application Key's scope**:

- Create a Datadog **Application Key granted only the `MCP Read` scope** (omit
  `MCP Write`), under a **read-only user** for defense in depth. Datadog then rejects
  any write the key isn't scoped for.
- This is why the source is `credential-only` — the key scope, not config, is the
  guardrail. The autonomous runner skips permission prompts, so the key scope is the
  only thing between the agent and a muted monitor.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json` (or
   `uv run research source enable datadog`).
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. **Add your auth headers locally — never commit them.** The Bits AI MCP server
   authenticates with two headers: `DD-API-KEY` and `DD-APPLICATION-KEY` (the
   read-scoped Application Key). Add them to the server entry's `headers` in your
   local `.mcp.json` (and the Cursor/Codex equivalents), sourced from your secret
   manager.

## Notes

- Covers metrics, monitors, logs, traces/APM, incidents, dashboards, SLOs, hosts.
- Community read-only alternative: `dreamiurg/datadog-mcp` ships read-only tools
  only (zero writes) if you prefer server-level enforcement over a key scope.
