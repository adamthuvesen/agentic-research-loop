# Salesforce (read-only — Beta server, credential-enforced)

**Server:** official Salesforce DX MCP server
([`@salesforce/mcp`](https://github.com/salesforcecli/mcp)) — local stdio, **Developer
Preview / Beta**. It's dev-tooling-oriented, but `run_soql_query` (in the `data`
toolset) covers CRM data reads for revenue/pipeline.

**Read-only enforcement (`credential-only`):** this server is **read+write with no
read-only flag**, and the `data` toolset **includes record DML** (create/update/delete
via the Data API) — so pinning `--toolsets=data` does **not** make it read-only. The
only real guardrail is a **read-only permission set** on the Salesforce user the CLI is
logged in as:

- Provision a permission set granting **Read** on the objects you need and **no**
  Create/Edit/Delete and no "Modify All Data". Do **not** authenticate as a System
  Administrator. Salesforce then rejects DML server-side.
- `--toolsets=data` is kept only to **narrow the loaded surface** (it drops the
  metadata-deploy, Apex, and devops toolsets), not as a read-only control.

**Warning:** with a broad `--toolsets` (or the default) this server can deploy metadata
and run Apex; with a write-capable org user even the `data` toolset can mutate records.
The autonomous runner skips permission prompts, so the org user's permissions are the
only guardrail — keep them read-only. **Beta** — re-check the toolset list against the docs.

## Enable

1. `uv run research source enable salesforce` (or merge by hand).
2. Authenticate the CLI as a **read-only org user**: `sf org login web`. The server
   reuses that org's auth; `--orgs DEFAULT_TARGET_ORG` whitelists it.

## Notes

- Covers opportunities, accounts, contacts, leads, and custom objects via SOQL —
  pipeline, stage, amount, close-date, ownership.
- Avoid community Salesforce MCP servers that add create/update/delete-record DML
  unless their read-only mode is locked on.
