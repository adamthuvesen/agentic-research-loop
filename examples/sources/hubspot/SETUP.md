# HubSpot (read-only — credential-enforced, read-AND-write server)

**Server:** official HubSpot MCP server — hosted, OAuth. Endpoint
`https://mcp.hubspot.com` (verify against
[developers.hubspot.com/mcp](https://developers.hubspot.com/mcp)). There is no
official local/self-hosted server.

**Warning — this server is read+write** and ships write tools (`manage_crm_objects`,
batch create/update objects, create/update engagements & properties) with **no
read-only flag**. The autonomous runner skips permission prompts, so the OAuth grant
+ user role is the only guardrail.

**Read-only enforcement (`credential-only`):**

- Create the HubSpot **MCP Auth App** and **grant only `*.read` scopes** at the
  consent screen (`crm.objects.deals.read`, `crm.objects.contacts.read`,
  `crm.objects.companies.read`, schema `*.read`, …). HubSpot's API then rejects writes
  with `403 MISSING_SCOPES` — real server-side enforcement, but it lives in the grant,
  not in committed config, so it can't be audited from the repo.
- Connect a **read-only HubSpot user** (actions respect that user's permissions).
- **Verify before autonomous use:** attempt one write and confirm it 403s.

## Enable

1. `uv run research source enable hubspot` (or merge the bundle by hand).
2. Authenticate via `/mcp` (Claude) or Settings → MCP (Cursor), consenting to **read
   scopes only** as the read-only user.

## Notes

- Covers deals/pipeline, contacts, companies, tickets, products, lists, and
  engagements — strong for pipeline and churn analysis.
