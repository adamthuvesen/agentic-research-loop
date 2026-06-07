# Google Drive (read-only)

**Server:** Google's official Drive MCP server — remote, hosted at
`https://drivemcp.googleapis.com/mcp/v1`. Wraps Drive search + file read for
Docs, Sheets, Slides, and other files.

**Read-only enforcement (`scope:drive.readonly`):** the server acts with the OAuth
scope you grant. Consent to **only** `https://www.googleapis.com/auth/drive.readonly`
— Google's API then rejects every write (create/edit/move/delete). Do **not** grant
`drive` (full) or `drive.file` (write).

## Required: bring your own OAuth client

Unlike GitHub/Notion/Atlassian, this server has **no public OAuth app** — the bare URL
will not connect. Create a Google Cloud OAuth client first:

1. In **Google Cloud Console** → *APIs & Services*, enable the **Google Drive API**.
2. Configure the **OAuth consent screen** and add **only** the
   `https://www.googleapis.com/auth/drive.readonly` scope (add `documents.readonly` /
   `spreadsheets.readonly` for richer Docs/Sheets text). Keep it read-only.
3. Create an **OAuth 2.0 Client ID** (Web application) and add your MCP client's
   redirect URI (for Claude, `https://claude.ai/api/mcp/auth_callback`).
4. Copy the **client ID + client secret** — you configure them in your MCP client,
   not in committed config.

## Enable

1. `uv run research source enable google-drive` (or merge the three files by hand).
2. Configure the OAuth client from above in your MCP client and authenticate:
   - **Claude Code / Cursor:** add the Drive connector with your client ID/secret
     (Settings → Connectors / MCP), then complete Google OAuth granting only the
     read-only scope.
   - **Codex:** `codex mcp login google-drive` after configuring the client.
3. Keep the OAuth client's scope read-only — it's the guardrail.

## Notes

- Covers Drive file search, metadata, and content for Docs, Sheets, Slides, PDFs.
- Drive is where the *narrative* lives (specs, planning docs, decision records), so
  it complements the Notion/Confluence bundles rather than duplicating them.
