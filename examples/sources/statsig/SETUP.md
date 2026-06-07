# Statsig (read-only)

**Server:** official Statsig MCP server — hosted Console API at
`https://api.statsig.com/v1/mcp`, reached via the `mcp-remote` shim.

**Read-only enforcement (`omni_read_only` Console API key — credential-enforced at the
API):** read-only is provable here, like PostHog. Create a **Console API key with the
`omni_read_only` scope**; the Statsig Console API rejects every write from it,
regardless of what tools the server advertises.

**Warning — the server ships gate/experiment-mutation tools** (`Create_Gate`,
`Update_Gate_Entirely`, `Create_Experiment`, `Update_Experiment_Entirely`) that change
**production** behavior. The `omni_read_only` key is what neutralizes them — **never
use an `omni_read_write` key.**

## Enable

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`. (An org admin / project owner mints
   the key.)
3. Export the read-only key via your environment (never committed config):
   ```bash
   export STATSIG_CONSOLE_API_KEY="$(op read 'op://vault/statsig-readonly/console-key')"
   ```

## Notes

- Covers feature gates (+ stale-gate detection), experiment configs and results,
  dynamic configs, layers/holdouts, and project/audit reads.
- Strong for "which gate or experiment changed, its current rollout, and the results."
