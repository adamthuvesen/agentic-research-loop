# Redshift (read-only)

**Server:** official AWS Labs Redshift MCP server
([`awslabs.redshift-mcp-server`](https://github.com/awslabs/mcp/tree/main/src/redshift-mcp-server))
— local stdio via `uvx awslabs.redshift-mcp-server@latest`. Auto-discovers both
provisioned clusters and serverless workgroups.

**Read-only enforcement (`native` — engine-enforced):** read-only is provable here.
The server (a) exposes **no write tools** (only list/describe + `execute_query`), and
(b) wraps every query in a database-level **`BEGIN READ ONLY` transaction** — Redshift
itself rejects any INSERT/UPDATE/COPY/DDL inside it. There is no read-only flag because
read-only is the only mode.

> **Caveat:** AWS has read-write on the roadmap (gated behind an `allow_read_write`
> flag, currently hardcoded off). Pin a version and add the IAM/DB guard below so a
> future release can't silently enable writes.

## Enable

1. `uv run research source enable redshift` (or merge the bundle by hand).
2. Provide AWS credentials via the standard chain and set the region in your
   environment (never inline secrets):
   ```bash
   export AWS_PROFILE=your-readonly-profile
   export AWS_DEFAULT_REGION=us-east-1
   ```
3. **Durable read-only guard:** scope the IAM principal to read-only `redshift-data` /
   `GetClusterCredentialsWithIAM` permissions mapped to a **read-only DB user** (`USAGE`
   + `SELECT` only). Then read-only holds regardless of server version.

## Notes

- Covers cluster/serverless discovery, schema browsing (databases/schemas/tables/
  columns), and read-only SQL via the Redshift Data API.
- Prefer this over pointing a generic Postgres MCP at Redshift — Redshift's old catalog
  breaks generic introspection.
