# Notion (read-only)

**Server:** official Notion MCP server — hosted, OAuth. Endpoint
`https://mcp.notion.com/mcp`.

**Read-only enforcement (`credential-only`):** the Notion server can create and update
pages if the connected integration is granted write access. There is **no read-only
flag** — read-only is enforced by **what you share with the integration**. Grant it
read access to the pages/databases you want searchable, and never create or update
pages.

## Enable

1. `uv run research source enable notion` (or merge the bundle by hand).
2. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor); grant the integration
   read access to the relevant pages/databases.

## Notes

- Covers workspace pages, databases, and discussions.
