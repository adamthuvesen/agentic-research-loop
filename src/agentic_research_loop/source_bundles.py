"""Enable/disable opt-in source bundles from ``examples/sources/<name>/``.

A bundle is wired by merging its registry spec into ``config/sources.json`` (the
gitignored user sources file) and its MCP server block into the three MCP configs
(``.mcp.json``, ``.cursor/mcp.json``, ``.codex/config.toml``), creating the
per-tool files if absent. This automates the manual copy-paste documented in
``examples/sources/README.md``.

These edits are a local opt-in: ``.mcp.json`` is tracked by git, so enabling a
bundle dirties it in your working tree; ``.cursor/mcp.json`` and
``.codex/config.toml`` are local-only. Do not commit enabled configs back to the
shared repo, which keeps its committed config neutral.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .sources import _validate_source_spec

_BUNDLES_SUBDIR = ("examples", "sources")
_USER_SOURCES = ("config", "sources.json")
_CLAUDE_CFG = (".mcp.json",)
_CURSOR_CFG = (".cursor", "mcp.json")
_CODEX_CFG = (".codex", "config.toml")

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class BundleError(ValueError):
    """Raised for an unknown bundle name or malformed bundle files."""


def _bundles_dir(repo_root: Path) -> Path:
    return repo_root.joinpath(*_BUNDLES_SUBDIR)


def available_bundles(repo_root: Path) -> list[str]:
    bundles = _bundles_dir(repo_root)
    if not bundles.is_dir():
        return []
    return sorted(
        entry.name
        for entry in bundles.iterdir()
        if entry.is_dir() and (entry / "source.json").is_file()
    )


def _bundle_path(repo_root: Path, name: str) -> Path:
    if not _NAME_RE.match(name):
        raise BundleError(
            f"Invalid bundle name {name!r}; use lowercase letters, digits, '-' or '_'."
        )
    bundles = _bundles_dir(repo_root).resolve()
    path = (bundles / name).resolve()
    if path.parent != bundles:  # reject path traversal
        raise BundleError(f"Invalid bundle name {name!r}.")
    if not (path / "source.json").is_file():
        available = ", ".join(available_bundles(repo_root)) or "(none)"
        raise BundleError(
            f"No bundle {name!r} in examples/sources/. Available: {available}"
        )
    return path


def _load_bundle(repo_root: Path, name: str) -> tuple[str, dict, dict | None]:
    """Return ``(source_name, spec, snippet)``; validates the spec.

    ``snippet`` is ``None`` for an MCP-less bundle — a ``cli`` or ``native`` source
    (e.g. GSC's ``research gsc`` subcommand) that reaches its system without an MCP
    server and so ships only ``source.json`` and ``SETUP.md``.
    """
    path = _bundle_path(repo_root, name)
    payload = json.loads((path / "source.json").read_text(encoding="utf-8"))
    sources = payload.get("sources", payload) if isinstance(payload, dict) else None
    if not isinstance(sources, dict) or len(sources) != 1:
        raise BundleError(f"{name}/source.json must define exactly one source.")
    source_name, spec = next(iter(sources.items()))
    _validate_source_spec(source_name, spec)
    snippet_path = path / "mcp.snippet.json"
    if not snippet_path.is_file():
        return source_name, spec, None
    snippet = json.loads(snippet_path.read_text(encoding="utf-8"))
    for key in ("server_name", "claude", "cursor", "codex_toml"):
        if key not in snippet:
            raise BundleError(f"{name}/mcp.snippet.json is missing {key!r}.")
    return source_name, spec, snippet


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return json.loads(json.dumps(default))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BundleError(f"{path} is not a JSON object.")
    return data


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _user_sources_doc(repo_root: Path) -> tuple[Path, dict]:
    path = repo_root.joinpath(*_USER_SOURCES)
    if not path.exists():
        return path, {"sources": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("sources"), dict):
        return path, payload
    if isinstance(payload, dict):
        return path, {"sources": payload}
    raise BundleError(f"{path} must be a JSON object.")


def enabled_source_names(repo_root: Path) -> set[str]:
    path = repo_root.joinpath(*_USER_SOURCES)
    if not path.exists():
        return set()
    _, doc = _user_sources_doc(repo_root)
    return set(doc["sources"])


def list_bundles(repo_root: Path) -> list[dict]:
    enabled = enabled_source_names(repo_root)
    rows: list[dict] = []
    for name in available_bundles(repo_root):
        source_name, spec, _ = _load_bundle(repo_root, name)
        rows.append(
            {
                "name": name,
                "enabled": source_name in enabled,
                "transport": spec["transport"],
                "read_only_mechanism": spec["read_only_mechanism"],
            }
        )
    return rows


def render_bundle_list(repo_root: Path) -> str:
    rows = list_bundles(repo_root)
    if not rows:
        return "No source bundles found under examples/sources/."
    width = max(len(row["name"]) for row in rows)
    lines = ["Source bundles (* = enabled):", ""]
    for row in rows:
        mark = "*" if row["enabled"] else " "
        lines.append(
            f"  {mark} {row['name']:<{width}}  {row['transport']:<11}  "
            f"{row['read_only_mechanism']}"
        )
    return "\n".join(lines)


def _codex_has_server(text: str, server: str) -> bool:
    header = f"[mcp_servers.{server}]"
    return any(line.strip() == header for line in text.splitlines())


def _codex_remove_server(text: str, server: str) -> tuple[str, bool]:
    header = f"[mcp_servers.{server}]"
    subtable_prefix = f"[mcp_servers.{server}."
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    index = 0
    removed = False
    while index < len(lines):
        stripped = lines[index].strip()
        # Remove the server's table and any dotted subtables (e.g. an
        # `[mcp_servers.<server>.env]` block) so disabling leaves nothing behind.
        if stripped == header or stripped.startswith(subtable_prefix):
            removed = True
            index += 1
            while index < len(lines) and not lines[index].lstrip().startswith("["):
                index += 1
            while out and out[-1].strip() == "":  # drop a blank line left behind
                out.pop()
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            continue
        out.append(lines[index])
        index += 1
    return "".join(out), removed


def enable_bundle(repo_root: Path, name: str) -> list[str]:
    """Wire a bundle into the user sources file and the three MCP configs.

    Every target file is read and parsed before any write, so a malformed config
    aborts cleanly (BundleError) instead of leaving the repo half-wired.
    """
    source_name, spec, snippet = _load_bundle(repo_root, name)

    # Parse every target up front; a malformed file raises here, before any write.
    # An MCP-less bundle (snippet is None) only registers the source spec — there
    # is no server to wire into the three MCP configs.
    su_path, doc = _user_sources_doc(repo_root)
    json_targets = []
    server = snippet["server_name"] if snippet is not None else None
    cx_path = repo_root.joinpath(*_CODEX_CFG)
    cx_text = ""
    if snippet is not None:
        for cfg, label, shapes in (
            (_CLAUDE_CFG, ".mcp.json", snippet["claude"]),
            (_CURSOR_CFG, ".cursor/mcp.json", snippet["cursor"]),
        ):
            path = repo_root.joinpath(*cfg)
            data = _read_json(path, {"mcpServers": {}})
            json_targets.append((path, label, data, shapes))
        cx_text = cx_path.read_text(encoding="utf-8") if cx_path.exists() else ""

    # All targets parsed cleanly; now write.
    actions: list[str] = []
    existed = source_name in doc["sources"]
    doc["sources"][source_name] = spec
    _write_json(su_path, doc)
    actions.append(
        f"{'updated' if existed else 'added'} source '{source_name}' in config/sources.json"
    )

    for path, label, data, shapes in json_targets:
        servers = data.setdefault("mcpServers", {})
        had = server in servers
        servers[server] = shapes[server]
        _write_json(path, data)
        actions.append(f"{'updated' if had else 'wired'} server '{server}' in {label}")

    if snippet is not None:
        if _codex_has_server(cx_text, server):
            actions.append(
                f"server '{server}' already in .codex/config.toml (left as-is)"
            )
        else:
            block = snippet["codex_toml"].rstrip("\n") + "\n"
            if cx_text and not cx_text.endswith("\n"):
                cx_text += "\n"
            cx_path.parent.mkdir(parents=True, exist_ok=True)
            cx_path.write_text(cx_text + "\n" + block, encoding="utf-8")
            actions.append(f"wired server '{server}' in .codex/config.toml")

    actions.append(
        f"next: follow examples/sources/{name}/SETUP.md for credentials and read-only setup"
    )
    return actions


def disable_bundle(repo_root: Path, name: str) -> list[str]:
    """Remove a bundle's wiring from the user sources file and MCP configs."""
    source_name, _, snippet = _load_bundle(repo_root, name)
    server = snippet["server_name"] if snippet is not None else None
    actions: list[str] = []

    su_path = repo_root.joinpath(*_USER_SOURCES)
    if su_path.exists():
        _, doc = _user_sources_doc(repo_root)
        if source_name in doc["sources"]:
            del doc["sources"][source_name]
            _write_json(su_path, doc)
            actions.append(f"removed source '{source_name}' from config/sources.json")

    # An MCP-less bundle wired no server, so there is nothing to unwire.
    if server is not None:
        for cfg, label in (
            (_CLAUDE_CFG, ".mcp.json"),
            (_CURSOR_CFG, ".cursor/mcp.json"),
        ):
            path = repo_root.joinpath(*cfg)
            if not path.exists():
                continue
            data = _read_json(path, {"mcpServers": {}})
            if server in data.get("mcpServers", {}):
                del data["mcpServers"][server]
                _write_json(path, data)
                actions.append(f"removed server '{server}' from {label}")

        cx_path = repo_root.joinpath(*_CODEX_CFG)
        if cx_path.exists():
            new_text, removed = _codex_remove_server(
                cx_path.read_text(encoding="utf-8"), server
            )
            if removed:
                cx_path.write_text(new_text, encoding="utf-8")
                actions.append(f"removed server '{server}' from .codex/config.toml")

    if not actions:
        actions.append(f"'{name}' was not enabled; nothing to do")
    return actions
