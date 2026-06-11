#!/usr/bin/env bash
# One-shot local setup after clone: Python deps + readiness check.
#
# MCP configs (`.mcp.json`, `.codex/config.toml`, `.cursor/mcp.json`) are committed
# sources of truth — this script does not modify them.
#
# Exit behavior: if `check_claude_setup.py` fails (e.g. OAuth not done yet), this script
# still exits 0 so you can run it repeatedly while finishing Slack/Snowflake setup.
# To fail the script when the checker fails, run the checker separately without `|| true`.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "Missing prerequisite: \`uv\` is not installed." >&2
  exit 1
fi

echo "Installing Python deps (dev)..."
uv sync --dev

echo "Running setup checker (see .agents/docs/setup.md if anything fails)..."
uv run python scripts/check_claude_setup.py || true

echo ""
echo "Done. Next: read .agents/docs/setup.md — Claude Code (`/mcp`), optional Codex (trust project + \`codex mcp\`), OAuth / Snowflake."
