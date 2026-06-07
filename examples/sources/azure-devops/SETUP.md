# Azure DevOps (read-only)

**Server:** official [`@azure-devops/mcp`](https://github.com/microsoft/azure-devops-mcp)
— local stdio, run via `npx -y @azure-devops/mcp <your-org>`. Covers work items
and boards, repos and pull requests, wikis, pipelines/builds, and test plans.

**Read-only enforcement (`credential-only`):** the local server ships **write
tools and has no read-only flag** — so nothing in committed config can guarantee
read-only. The connecting identity is the only guardrail, and the autonomous
runner skips permission prompts. Provision read-only access:

- **Preferred — a read-only-scoped PAT:** create a Personal Access Token with only
  *Read* scopes (Work Items: Read, Code: Read, Build: Read, Wiki: Read, etc.) and
  no write scopes. Azure DevOps then rejects writes the token isn't scoped for.
  Provide it via the environment for the server to use — see the server README for
  the exact variable; the Azure CLI's `AZURE_DEVOPS_EXT_PAT` works when the server
  falls back to CLI auth. Never commit it.
- **Or a view-only account:** sign in (browser/Entra) as a **Stakeholder** or a
  user whose project role is read-only.

## Enable

1. `uv run research source enable azure-devops` (or merge the three files by hand).
2. Replace `YOUR_ADO_ORG` in the wired config with your Azure DevOps organization
   name (the `dev.azure.com/<org>` slug).
3. Authenticate on first tool call (browser/Entra) — or set a read-only PAT in the
   environment as above.
4. Optional: pass `-d <domains>` (e.g. `-d core work-items repositories wiki
   pipelines`) to limit which tool groups load. This narrows the surface but does
   **not** enforce read-only on its own — the credential still must.

## Notes

- The Microsoft-shop equivalent of the Jira + GitHub bundles in one server.
- A cleaner read-only path is coming: the **remote** server
  (`https://mcp.dev.azure.com/{org}`) supports an `X-MCP-Readonly: true` header,
  but Claude Code / Codex / Cursor aren't supported yet (pending Microsoft Entra
  dynamic client registration). Switch to it for config-checkable read-only once
  your client is supported.
