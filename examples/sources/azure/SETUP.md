# Azure (read-only)

**Server:** official [Azure MCP Server](https://github.com/microsoft/mcp)
(`@azure/mcp`) — stdio, run via `npx -y @azure/mcp@latest server start`. One
server across Azure services: Monitor/Log Analytics, Azure SQL, Data Explorer
(Kusto), Cosmos DB, Storage, and more.

**Read-only enforcement (`server-flag:--read-only`):** the bundle runs with
`--read-only`, which filters the exposed tools to read-only operations and blocks
writes across every namespace. Narrow further with `--namespace <service>` (e.g.
`monitor`, `sql`, `kusto`) if you only want one area.

## Enable

1. `uv run research source enable azure` (or merge the three files by hand).
2. Authenticate with the Azure CLI before launching the agent:
   ```bash
   az login        # DefaultAzureCredential picks this up
   ```
3. **Defense in depth (strongly recommended):** sign in as an identity that holds
   only the **Reader** role (and **Monitoring Reader** for Log Analytics) on the
   subscriptions/resource groups you need. `--read-only` blocks writes at the
   server; a Reader role means the credential can't write either.

## Notes

- KQL over Log Analytics is the observability path (the Azure equivalent of the
  Datadog bundle); Azure SQL / Kusto cover the warehouse path.
- `--read-only` is a good default for auditing and discovery — keep it on.
- For Azure DevOps work items / repos / pipelines, use the separate `azure-devops`
  bundle (different server, different auth).
