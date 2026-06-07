# Databricks (read-only)

**Server:** Databricks managed **Genie** MCP server — hosted, OAuth, per workspace.
Endpoint `https://<workspace-hostname>/api/2.0/mcp/genie` (or
`/api/2.0/mcp/genie/{genie_space_id}` to pin one Genie space).

**Read-only enforcement (`url-suffix:/api/2.0/mcp/genie`):** Genie is **read-only by
design** — it turns natural-language questions into SQL it runs against a Genie Space
(on Unity Catalog tables) and returns the results plus the SQL. It has **no write
path**. This is checkable in committed config: you wired the `/genie` endpoint.

**Do NOT wire the Databricks SQL server** (`/api/2.0/mcp/sql`) for a read-only tool —
it runs arbitrary AI-generated SQL (incl. INSERT/UPDATE/DELETE/DDL) under your Unity
Catalog identity, guarded only by UC grants, with no read-only flag.

## Enable

1. `uv run research source enable databricks` (or merge the bundle by hand).
2. Replace `YOUR-WORKSPACE` in the snippet with your workspace hostname (and pin a
   Genie space id if you want to scope it).
3. Authenticate via OAuth (`/mcp` in Claude, Settings → MCP in Cursor) — queries run
   under your Unity Catalog identity, so UC permissions apply.

## Notes

- Defense in depth: connect under a UC identity granted only `USE` + `SELECT`.
- If you genuinely need raw SQL (not Genie's NL interface), use the SQL server with a
  SELECT-only UC identity and treat it as `credential-only` — but Genie is the
  read-only-safe default.
