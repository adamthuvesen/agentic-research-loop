# DuckDB (read-only)

**Server:** `mcp-server-motherduck` (MotherDuck) — stdio, run via
`uvx mcp-server-motherduck`. One server covers both a local DuckDB file and
cloud MotherDuck.

**Read-only enforcement (`arg-absent:--read-write`):** the server is **read-only
by default**. For a local file it opens DuckDB in read-only mode and does not
hold the file lock. Adding `--read-write` enables writes — so the read-only
guarantee is simply *not passing that flag*, which is what this bundle ships.

## Enable (local DuckDB file)

1. Merge [`source.json`](source.json) into `config/sources.json`.
2. Paste the [`mcp.snippet.json`](mcp.snippet.json) blocks into `.mcp.json`,
   `.cursor/mcp.json`, and `.codex/config.toml`.
3. Set `--db-path` to the absolute path of your `.duckdb` file. Done — no
   credentials needed for a local file.

## MotherDuck cloud (optional)

Instead of `--db-path`, set a `motherduck_token` env var. **For true read-only,
use a read-scaling token** — a regular MotherDuck token effectively needs
`--read-write`, so the token type is what enforces read-only in the cloud. Keep
the token in your environment / secret manager, not in committed config.
