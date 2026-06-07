# Confluence (read-only)

**Server:** official Atlassian remote MCP server — hosted at
`https://mcp.atlassian.com/v1/mcp` (OAuth 2.1). The **same server as the Jira
bundle** — it covers Confluence and Jira together.

**Read-only enforcement (`credential-only`):** the Atlassian server has **no
read-only flag** and can create/edit pages and comment if the connected account can.
Read-only is enforced entirely by the **account you connect** — provision a
**view-only Atlassian account** with Confluence read access (Browse/View; no
add/edit/comment). This is the only guardrail, which is why the source is
`credential-only`.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`. **If you already enabled the Jira
   bundle, you're connected to the same Atlassian server** — you can reuse a single
   server entry (e.g. name it `atlassian`) and skip adding a second.
3. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor); `codex mcp login
   confluence`. Sign in as the view-only account.

## Notes

- Covers spaces, pages (content as Markdown), CQL search, page history, comments.
- Community alternative `sooperset/mcp-atlassian` offers a real `READ_ONLY_MODE=true`
  flag if you prefer server-level enforcement over an account-scoped one.
