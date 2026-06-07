# Snowflake (read-only)

**Server:** Snowflake MCP server
([`snowflake-labs-mcp`](https://github.com/Snowflake-Labs/mcp)) — local stdio via
`uvx`. Uses your **`default`** Snowflake connection.

**Read-only enforcement (`statement-allowlist`):** read-only is pinned in
[`config/snowflake-mcp-tools.yaml`](../../../config/snowflake-mcp-tools.yaml) (passed
via `--service-config-file`), which permits **`SELECT` / `DESCRIBE` / `SHOW` / `USE`
only** — never `ALTER`/`DELETE`/`DROP`. A test
(`tests/test_mcp_configs_consistent.py`) asserts the allowlist stays read-only.

## Enable

1. `uv run research source enable snowflake` (or merge the bundle by hand).
2. Create a personal `default` connection in `~/.snowflake/config.toml` (copy
   [`agents/docs/examples/snowflake-config.toml.example`](../../../agents/docs/examples/snowflake-config.toml.example)).
   `externalbrowser` auth keeps credentials out of committed config.

## Notes

- Covers semantic views, curated marts, and staging tables. Discover objects live
  (`describe_semantic_view` / `SHOW TABLES` / `DESCRIBE`) before querying.
- Adapt the `agent_services` block in `snowflake-mcp-tools.yaml` to your account, or
  leave it empty to query semantic views / tables directly.
