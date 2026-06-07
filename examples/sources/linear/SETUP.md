# Linear (read-only)

**Server:** official Linear MCP server — hosted, OAuth. Endpoint
`https://mcp.linear.app/mcp`.

**Read-only enforcement (`credential-only`):** the Linear server can create/update
issues if the connected account can. There is **no read-only flag** — connect a
**read-only Linear account** and never create or update issues.

## Enable

1. `uv run research source enable linear` (or merge the bundle by hand).
2. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor) as the read-only account.

## Notes

- Covers project status, issue tracking, cycle planning, and ownership context.
