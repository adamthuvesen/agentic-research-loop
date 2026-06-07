# BigQuery (read-only)

**Server:** Google-managed BigQuery MCP server — remote, hosted at
`https://bigquery.googleapis.com/mcp` (OAuth 2.0 + IAM).

**Read-only enforcement (`credential-only`):** the managed server exposes both a
writable `execute_sql` tool and a read-only `execute_sql_readonly` tool, so
read-only is **per-tool, not a server-wide flag**. Nothing in committed config
can guarantee it — enforce it at the credential layer:

- Authenticate as a principal granted **BigQuery Data Viewer** + **BigQuery Job
  User** + **MCP Tool User** (`roles/mcp.toolUser`, required to call any MCP tool)
  — and **no** Data Editor / Admin. With viewer-only data IAM the writable tool
  cannot mutate anything.
- Prefer `execute_sql_readonly` for queries; it blocks DML, DDL, and Python UDFs.

This is why the source is marked `credential-only`: the IAM role is the guardrail.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Authenticate (OAuth scope `https://www.googleapis.com/auth/bigquery`):
   - **Claude Code / Cursor:** `/mcp` (Claude) or Settings → MCP (Cursor).
   - **Codex:** `codex mcp login bigquery`.
4. Confirm the authenticated principal has only the read-only IAM roles above.

## Notes

- GA4 and GSC BigQuery exports (if you've enabled them) are queryable here — this
  is the default warehouse path for those analytics sources.
- For a self-hosted alternative, the MCP Toolbox for Databases (`--prebuilt
  bigquery`) works too, but its prebuilt tools include a writable `execute_sql`;
  rely on IAM either way.
