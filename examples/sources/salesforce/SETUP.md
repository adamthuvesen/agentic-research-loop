# Salesforce (read-only — Beta server, two levers required)

**Server:** official Salesforce DX MCP server
([`@salesforce/mcp`](https://github.com/salesforcecli/mcp)) — local stdio, **Developer
Preview / Beta**. It's dev-tooling-oriented, but `run_soql_query` (in the `data`
toolset) covers CRM data reads for revenue/pipeline.

**Read-only enforcement — stack both, neither alone is enough:**

1. **`--toolsets=data,users`** (pinned in the bundle's `args`, config-checkable) — loads
   only read toolsets, so the dangerous tools (`deploy_metadata`, `run_apex_test`,
   devops writes) are **not loaded** at all.
2. **A read-only permission set** on the Salesforce user the CLI is logged in as (Read
   on objects; no Create/Edit/Delete, no "Modify All Data") — Salesforce then rejects
   DML server-side.

**Warning:** with broad `--toolsets` (or the default), this server can deploy metadata
and run Apex. Keep the allowlist pinned and the org user read-only. **Beta** — re-check
the toolset list against the docs before relying on it.

## Enable

1. `uv run research source enable salesforce` (or merge by hand).
2. Authenticate the CLI to a **read-only org user**: `sf org login web`. The server
   reuses that org's auth; `--orgs DEFAULT_TARGET_ORG` whitelists it.

## Notes

- Covers opportunities, accounts, contacts, leads, and custom objects via SOQL —
  pipeline, stage, amount, close-date, ownership.
- Avoid community Salesforce MCP servers that add create/update/delete-record DML
  unless their read-only mode is locked on.
