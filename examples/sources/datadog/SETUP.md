# Datadog (read-only)

**Server:** official Datadog managed MCP server — remote, OAuth. Default endpoint
(US1) `https://mcp.datadoghq.com/api/unstable/mcp-server/mcp`. Read-only by design
(no mutation tools in the managed server).

> **Preview:** this is an `unstable` API path and may change — verify against
> Datadog's MCP docs before relying on it in automation.

**Read-only enforcement (`credential-only`):** there is no server-side read-only
flag; read-only is the **account's role**. Authenticate a principal with the
**Datadog Read-Only Role** (or, if you use the community stdio server, an app key
scoped to `*_read` permissions: `metrics_read`, `logs_read_data`, `monitors_read`,
`dashboards_read`, `events_read`, `incident_read`). The role/scope is the guardrail.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`. **Pick your regional endpoint** —
   `.datadoghq.com` (US1), `.datadoghq.eu` (EU), or the `us3`/`us5`/`ap1`/gov
   variants; a mismatched region fails auth.
3. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor); `codex mcp login
   datadog`. Connect the read-only-roled principal.

## Notes

- Covers metrics, monitors, logs, traces/APM, incidents, dashboards, SLOs, hosts.
- Avoid the community `winor30/mcp-server-datadog` for autonomous use unless you
  exclude its mutation tools (mute host, schedule/cancel downtime) and scope keys
  read-only.
