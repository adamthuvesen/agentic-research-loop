# Microsoft 365 (read-only)

**Server:** [`@softeria/ms-365-mcp-server`](https://github.com/Softeria/ms-365-mcp-server)
— stdio over Microsoft Graph, run via `npx @softeria/ms-365-mcp-server`. Covers
SharePoint, OneDrive, Teams, Outlook, Calendar, Excel, and OneNote.

**Read-only enforcement (`server-flag:--read-only`):** the bundle runs the server
with `--read-only`, which disables every write tool (Graph mutations are not
registered). `--org-mode` turns on work-account services (Teams, SharePoint,
OneDrive) — required for org content.

## Enable

1. `uv run research source enable microsoft-365` (or merge the three files by hand).
2. Authenticate on first use — run the server's login (device-code) flow and
   consent with your work account:
   ```bash
   npx @softeria/ms-365-mcp-server --login   # device-code login
   ```
   An admin may need to approve the Graph read permissions the first time.
3. **Defense in depth (recommended):** `--read-only` is the guardrail, but you can
   also sign in with an account that only has read access and narrow the tool
   surface with `--allowed-scopes` (run `--list-permissions` to see what the
   enabled tools imply).

## Notes

- Read-only covers: SharePoint sites/pages/lists, OneDrive files, Teams
  channels/messages/chats, Outlook mail, Calendar, Excel, OneNote.
- This is the Microsoft equivalent of the Notion/Confluence (docs) and Slack
  (comms) bundles — enable it for Microsoft-shop knowledge and decisions.
- Outlook mail is in scope when org-mode is on; treat it as sensitive.
