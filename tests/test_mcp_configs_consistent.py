"""The three committed MCP config files SHALL agree on the set of server names.

Per-tool shape differences (Codex `enabled = true`, Cursor dropping `oauth`, etc.)
are intentional and not checked here. Only the set of server names is compared.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_PATH = ROOT / ".mcp.json"
CODEX_PATH = ROOT / ".codex" / "config.toml"
CURSOR_PATH = ROOT / ".cursor" / "mcp.json"
SNOWFLAKE_TOOLS_PATH = ROOT / "config" / "snowflake-mcp-tools.yaml"


def _claude_names() -> set[str]:
    payload = json.loads(CLAUDE_PATH.read_text())
    return set(payload["mcpServers"].keys())


def _codex_names() -> set[str]:
    payload = tomllib.loads(CODEX_PATH.read_text())
    return set(payload.get("mcp_servers", {}).keys())


def _cursor_names() -> set[str]:
    payload = json.loads(CURSOR_PATH.read_text())
    return set(payload["mcpServers"].keys())


def test_mcp_config_files_list_the_same_server_names() -> None:
    claude = _claude_names()
    codex = _codex_names()
    cursor = _cursor_names()

    union = claude | codex | cursor
    missing: dict[str, list[str]] = {}
    for name in sorted(union):
        absent_in = []
        if name not in claude:
            absent_in.append(".mcp.json")
        if name not in codex:
            absent_in.append(".codex/config.toml")
        if name not in cursor:
            absent_in.append(".cursor/mcp.json")
        if absent_in:
            missing[name] = absent_in

    assert not missing, (
        "MCP config files disagree on server names. When you add or remove a "
        "server, edit all three files. Missing servers:\n"
        + "\n".join(f"  - {name}: absent in {files}" for name, files in missing.items())
    )


def test_committed_mcp_configs_ship_neutral() -> None:
    """The committed configs SHALL ship with zero servers (opt-in only).

    ``research source enable`` wires servers locally; the shared repo keeps these
    three files empty so a clone carries nobody's stack. The consistency check
    above passes even if all three drift together, so pin emptiness explicitly.
    """
    assert _claude_names() == set(), ".mcp.json must ship neutral (no servers)"
    assert _codex_names() == set(), ".codex/config.toml must ship neutral"
    assert _cursor_names() == set(), ".cursor/mcp.json must ship neutral"


def test_snowflake_mcp_sql_permissions_are_read_only() -> None:
    text = SNOWFLAKE_TOOLS_PATH.read_text(encoding="utf-8")
    permissions: dict[str, bool] = {}
    in_section = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "sql_statement_permissions:":
            in_section = True
            continue
        if not in_section:
            continue
        if line and not line.startswith("- "):
            break
        if not line:
            continue
        name, value = line.removeprefix("- ").split(":", 1)
        permissions[name.strip()] = value.strip().lower() == "true"

    assert {name for name, allowed in permissions.items() if allowed} == {
        "Select",
        "Describe",
        "Show",
        "Use",
    }
    assert permissions.get("Unknown") is False
