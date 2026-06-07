# GitHub (read-only)

**Server:** official GitHub MCP server — remote, hosted at
`https://api.githubcopilot.com/mcp/`.

**Read-only enforcement (`url-suffix:/readonly`):** the bundle wires the
`/readonly` endpoint. GitHub's read-only filter is strict — it disables every
write tool (open/edit/comment/merge) regardless of other config or token scope,
so it overrides whatever the credential could otherwise do.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Authenticate:
   - **Claude Code / Cursor:** run `/mcp` (Claude) or the Settings → MCP panel
     (Cursor) and complete GitHub OAuth.
   - **Codex:** `codex mcp login github`.
4. **Defense in depth (recommended):** authenticate with a fine-grained PAT
   scoped to read-only (no write/admin permissions) on only the repos you need.
   The `/readonly` filter already blocks writes; a least-privilege token means
   the credential can't either.

## Notes

- Covers issues, pull requests, commits, code search, and repo metadata.
- Local Docker alternative (`ghcr.io/github/github-mcp-server`) supports the same
  read-only mode via `--read-only` / `GITHUB_READ_ONLY=1` if you prefer stdio.
