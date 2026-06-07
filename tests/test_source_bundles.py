"""Tests for `research source enable/disable/list`."""

from __future__ import annotations

import json
import tomllib

import pytest

from agentic_research_loop import source_bundles as sb

_SPEC = {
    "key": "foo_mcp",
    "hint_field": "focus",
    "label": "Foo focus",
    "display_label": "Foo",
    "freshness_caveat_group": "docs",
    "transport": "http-oauth",
    "read_only_mechanism": "credential-only",
    "plan_line": "Foo for things.",
    "base_notes": "Search foo. Read-only.",
}

_SNIPPET = {
    "server_name": "foo",
    "read_only_mechanism": "credential-only",
    "claude": {"foo": {"type": "http", "url": "https://foo.example/mcp"}},
    "cursor": {"foo": {"url": "https://foo.example/mcp"}},
    "codex_toml": '[mcp_servers.foo]\nurl = "https://foo.example/mcp"\nenabled = true',
}


@pytest.fixture()
def repo(tmp_path):
    """A fake repo with one `foo` bundle and neutral committed MCP configs."""
    bundle = tmp_path / "examples" / "sources" / "foo"
    bundle.mkdir(parents=True)
    (bundle / "source.json").write_text(json.dumps({"sources": {"foo": _SPEC}}))
    (bundle / "mcp.snippet.json").write_text(json.dumps(_SNIPPET))
    (bundle / "SETUP.md").write_text("# Foo (read-only)\n")

    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"existing": {"type": "http", "url": "x"}}})
    )
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        json.dumps({"mcpServers": {"existing": {"url": "x"}}})
    )
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "config.toml").write_text(
        '# header\n\n[mcp_servers.existing]\nurl = "x"\nenabled = true\n'
    )
    return tmp_path


def _claude(repo):
    return json.loads((repo / ".mcp.json").read_text())["mcpServers"]


def _cursor(repo):
    return json.loads((repo / ".cursor" / "mcp.json").read_text())["mcpServers"]


def _codex(repo):
    return tomllib.loads((repo / ".codex" / "config.toml").read_text())["mcp_servers"]


def _sources(repo):
    return json.loads((repo / "config" / "sources.json").read_text())["sources"]


def test_enable_wires_registry_and_all_three_mcp_configs(repo):
    sb.enable_bundle(repo, "foo")

    assert "foo" in _sources(repo)
    assert _sources(repo)["foo"] == _SPEC
    # existing servers are preserved; foo is added everywhere
    assert set(_claude(repo)) == {"existing", "foo"}
    assert set(_cursor(repo)) == {"existing", "foo"}
    assert set(_codex(repo)) == {"existing", "foo"}
    assert _codex(repo)["foo"]["url"] == "https://foo.example/mcp"


def test_enable_is_idempotent(repo):
    sb.enable_bundle(repo, "foo")
    sb.enable_bundle(repo, "foo")
    # no duplicate codex block, single registry entry
    text = (repo / ".codex" / "config.toml").read_text()
    assert text.count("[mcp_servers.foo]") == 1
    assert list(_sources(repo)) == ["foo"]


def test_disable_reverses_enable(repo):
    sb.enable_bundle(repo, "foo")
    sb.disable_bundle(repo, "foo")

    assert "foo" not in _sources(repo)
    assert set(_claude(repo)) == {"existing"}
    assert set(_cursor(repo)) == {"existing"}
    assert set(_codex(repo)) == {"existing"}
    # the codex file remains valid TOML with the header preserved
    assert "# header" in (repo / ".codex" / "config.toml").read_text()


def test_list_reflects_enabled_state(repo):
    rows = {r["name"]: r for r in sb.list_bundles(repo)}
    assert rows["foo"]["enabled"] is False
    sb.enable_bundle(repo, "foo")
    rows = {r["name"]: r for r in sb.list_bundles(repo)}
    assert rows["foo"]["enabled"] is True
    assert rows["foo"]["read_only_mechanism"] == "credential-only"


def test_unknown_bundle_raises(repo):
    with pytest.raises(sb.BundleError, match="No bundle"):
        sb.enable_bundle(repo, "nope")


def test_rejects_path_traversal(repo):
    with pytest.raises(sb.BundleError, match="Invalid bundle name"):
        sb.enable_bundle(repo, "../../etc")


def test_enable_creates_sources_file_when_absent(repo):
    assert not (repo / "config" / "sources.json").exists()
    sb.enable_bundle(repo, "foo")
    assert (repo / "config" / "sources.json").exists()


_BARE_SPEC = {
    "key": "bare_cli",
    "hint_field": "focus",
    "label": "Bare focus",
    "display_label": "Bare",
    "freshness_caveat_group": "live",
    "transport": "cli",
    "read_only_mechanism": "scope:example.readonly",
    "plan_line": "Bare CLI source.",
    "base_notes": "Query via the bare CLI. Read-only.",
}


def _add_mcpless_bundle(repo):
    """A bundle with no mcp.snippet.json — a cli/native source like GSC."""
    bundle = repo / "examples" / "sources" / "bare"
    bundle.mkdir(parents=True)
    (bundle / "source.json").write_text(json.dumps({"sources": {"bare": _BARE_SPEC}}))
    (bundle / "SETUP.md").write_text("# Bare (read-only)\nEnforced by scope.\n")


def test_mcpless_bundle_enables_without_touching_mcp_configs(repo):
    _add_mcpless_bundle(repo)
    actions = sb.enable_bundle(repo, "bare")

    assert _sources(repo)["bare"] == _BARE_SPEC
    # the three MCP configs keep only their pre-existing server, untouched
    assert set(_claude(repo)) == {"existing"}
    assert set(_cursor(repo)) == {"existing"}
    assert set(_codex(repo)) == {"existing"}
    assert not any("server" in action for action in actions)


def test_mcpless_bundle_disable_removes_only_registry_entry(repo):
    _add_mcpless_bundle(repo)
    sb.enable_bundle(repo, "bare")
    sb.disable_bundle(repo, "bare")

    assert "bare" not in _sources(repo)
    assert set(_codex(repo)) == {"existing"}


def test_mcpless_bundle_listed_with_enabled_state(repo):
    _add_mcpless_bundle(repo)
    rows = {r["name"]: r for r in sb.list_bundles(repo)}
    assert rows["bare"]["enabled"] is False
    sb.enable_bundle(repo, "bare")
    rows = {r["name"]: r for r in sb.list_bundles(repo)}
    assert rows["bare"]["enabled"] is True
