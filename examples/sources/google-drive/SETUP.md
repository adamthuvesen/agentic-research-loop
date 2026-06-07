# Google Drive (read-only)

**Server:** Google's official Drive MCP server — remote, hosted at
`https://drivemcp.googleapis.com/mcp/v1`. Wraps Drive search + file read for
Docs, Sheets, Slides, and other files.

**Read-only enforcement (`scope:drive.readonly`):** the server acts with the
OAuth scope you grant it. Consent to **only**
`https://www.googleapis.com/auth/drive.readonly` — Google's API then rejects every
write (create/edit/move/delete). Do **not** grant `drive` (full) or `drive.file`
(write), which the server also supports.

## Enable

1. `uv run research source enable google-drive` (or merge the three files by hand).
2. Authenticate on first use:
   - **Claude Code / Cursor:** run `/mcp` (Claude) or Settings → MCP (Cursor) and
     complete Google OAuth, granting only the read-only Drive scope.
   - **Codex:** `codex mcp login google-drive`.
3. **Defense in depth (recommended):** use a Google Cloud OAuth client whose
   consent screen lists only `drive.readonly` (add `documents.readonly` /
   `spreadsheets.readonly` if you want richer Docs/Sheets text). The scope is the
   guardrail — keep it read-only.

## Notes

- Covers Drive file search, metadata, and content for Docs, Sheets, Slides, PDFs.
- Pairs well with a warehouse for metrics; Drive is where the *narrative* lives —
  specs, planning docs, decision records — so it complements the Notion/Confluence
  bundles rather than duplicating them.
