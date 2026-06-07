# Jira (read-only)

**Server:** official Atlassian remote MCP server — hosted at
`https://mcp.atlassian.com/v1/mcp` (covers Jira and Confluence).

**Read-only enforcement (`credential-only`):** the Atlassian server has **no
read-only flag**. Its actions are scoped only to what the authenticated user can
already do, so read-only is enforced entirely by the **account you connect**.
Nothing in committed config can guarantee it — this is why the source is marked
`credential-only`.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. **Provision a view-only Atlassian account** (or group) whose permission
   scheme grants *Browse Projects* but **no** create/edit/transition/comment
   permissions, and authenticate the MCP as that principal:
   - **Claude Code / Cursor:** `/mcp` (Claude) or Settings → MCP (Cursor), sign
     in as the view-only account.
   - **Codex:** `codex mcp login jira`.

## Why this matters

If you connect a read-write account, the agent *can* create and transition
issues even though this tool's policy says read-only. The permission scheme is
your only real guardrail — make it view-only.
