# GA4 (read-only)

**Server:** official Google Analytics MCP server
([`googleanalytics/google-analytics-mcp`](https://github.com/googleanalytics/google-analytics-mcp))
— stdio, run via `pipx run analytics-mcp`. It wraps the live GA4 Data API
(`run_report`, `run_realtime_report`, `run_funnel_report`) plus read-only Admin
API calls. This replaces the old `research ga4` CLI.

**Read-only enforcement (`scope:analytics.readonly`):** the server is read-only
by nature — Google states it serves *read* requests only and the sole OAuth scope
is `analytics.readonly`, so it cannot edit GA4 configuration. The scope is the
guarantee; there is no separate flag.

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`. Verify the install command
   against the upstream repo (it may publish as `pipx install google-analytics-mcp`).
3. Authenticate with ADC scoped read-only:
   ```bash
   gcloud auth application-default login \
     --scopes="https://www.googleapis.com/auth/analytics.readonly"
   ```
   or point `GOOGLE_APPLICATION_CREDENTIALS` at a service account granted Viewer
   on the GA4 property.

## Notes

- Pass the GA4 property id in your query (the server resolves account/property
  summaries); no fixed property env var is required.
- For large properties the Data API samples/thresholds — if you need unsampled
  data, query the GA4 → BigQuery export via the `bigquery` source instead.
