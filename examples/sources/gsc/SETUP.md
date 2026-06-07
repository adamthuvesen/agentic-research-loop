# GSC — Google Search Console (read-only)

**Transport:** `cli` — the `research gsc` subcommand, not an MCP server. This is an
**MCP-less bundle**: it ships only `source.json` and this `SETUP.md`, so enabling it
registers the source for planning and prompting but wires no server into the MCP
configs.

**Read-only enforcement (`scope:webmasters.readonly`):** the CLI authenticates with
the **`webmasters.readonly` OAuth scope**, which grants read access to Search
Analytics and nothing that can modify a property. Read-only is enforced by the
**scope** on the credential, not by a config flag.

## Default path: the warehouse, not this CLI

Prefer a **warehouse-synced copy** of GSC (Snowflake or BigQuery, via Fivetran or
the GSC bulk export) for organic-search metrics — query the semantic views / marts
or synced staging tables. The `research gsc` CLI is the **API fallback**: reach for
it only when the sync is lagging, you need fresher data, or you want an API-only
slice.

## Enable

1. Run `uv run research source enable gsc` (or merge [`source.json`](source.json)
   into `config/sources.json` by hand). No MCP config changes — there is no server.
2. Authenticate with Application Default Credentials, requesting the read-only
   scope (`agentic_research_loop.google_api` picks ADC up automatically):

   ```bash
   gcloud auth application-default login \
     --client-id-file="$HOME/.config/gcloud/oauth-client.json" \
     --scopes="https://www.googleapis.com/auth/webmasters.readonly,https://www.googleapis.com/auth/cloud-platform"
   ```

3. Set the environment the CLI reads:
   - `GSC_SITE` — the verified Search Console property URL (e.g.
     `https://www.example.com/` or `sc-domain:example.com`).
   - `GCP_QUOTA_PROJECT` — optional; a GCP project to bill the API quota to.

## Use

```bash
research gsc --start-date 2026-03-01 --end-date 2026-04-06 --dimensions query,page
```

- Dimensions: `query`, `page`, `country`, `device`, `searchAppearance`, `date`.
- `--row-limit` and `--start-row` paginate.
- `--start-date` / `--end-date` are validated locally as real `YYYY-MM-DD` dates,
  and inverted ranges are rejected before any API call.
