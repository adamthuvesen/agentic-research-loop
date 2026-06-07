"""The read-only contract.

Every registered source SHALL declare a valid transport and a recognized
read-only mechanism. Every opt-in bundle under ``examples/sources/`` SHALL
satisfy its declared mechanism: a config-family token must be present (or absent)
in the shipped MCP snippet, and a documented-family mechanism (e.g.
``credential-only``) must be covered by the bundle's SETUP.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_research_loop import sources
from agentic_research_loop.sources import (
    SOURCE_CONFIGS,
    VALID_TRANSPORTS,
    classify_read_only_mechanism,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLES_DIR = ROOT / "examples" / "sources"


def test_every_source_declares_valid_transport_and_mechanism() -> None:
    for name, spec in SOURCE_CONFIGS.items():
        assert spec["transport"] in VALID_TRANSPORTS, f"{name}: bad transport"
        assert classify_read_only_mechanism(spec["read_only_mechanism"]) is not None, (
            f"{name}: unrecognized read_only_mechanism"
        )


def _bundle_dirs() -> list[Path]:
    if not BUNDLES_DIR.exists():
        return []
    return sorted(p for p in BUNDLES_DIR.iterdir() if p.is_dir())


def test_bundle_keys_are_unique() -> None:
    """No two bundles (or a bundle and a built-in) may share a source ``key``.

    The registry merges on ``key``, so a collision silently clobbers one source's
    enabled/hint/notes state. ``register_source`` rejects this at runtime; this
    pins it for the shipped bundles too.
    """
    seen: dict[str, str] = {
        spec["key"]: name for name, spec in sources._BUILTIN_SOURCES.items()
    }
    for bundle in _bundle_dirs():
        payload = json.loads((bundle / "source.json").read_text(encoding="utf-8"))
        sources_map = payload.get("sources", payload)
        name, spec = next(iter(sources_map.items()))
        key = spec["key"]
        assert key not in seen, (
            f"{bundle.name}: key {key!r} already used by {seen[key]!r}"
        )
        seen[key] = name


@pytest.mark.parametrize("bundle", _bundle_dirs(), ids=lambda p: p.name)
def test_bundle_declares_and_enforces_read_only(bundle: Path) -> None:
    # source.json holds exactly one fully valid registry spec.
    source_json = json.loads((bundle / "source.json").read_text(encoding="utf-8"))
    sources_map = source_json.get("sources", source_json)
    assert len(sources_map) == 1, f"{bundle.name}: expected exactly one source"
    name, spec = next(iter(sources_map.items()))
    sources._validate_source_spec(name, spec)

    mech = classify_read_only_mechanism(spec["read_only_mechanism"])
    assert mech is not None

    # mcp.snippet.json is internally consistent across the three tool shapes.
    snippet = json.loads((bundle / "mcp.snippet.json").read_text(encoding="utf-8"))
    server = snippet["server_name"]
    assert list(snippet["claude"].keys()) == [server], f"{bundle.name}: claude key"
    assert list(snippet["cursor"].keys()) == [server], f"{bundle.name}: cursor key"
    assert f"[mcp_servers.{server}]" in snippet["codex_toml"], f"{bundle.name}: codex"

    setup = (bundle / "SETUP.md").read_text(encoding="utf-8")

    if mech.family == "config":
        blob = (
            json.dumps(snippet["claude"])
            + json.dumps(snippet["cursor"])
            + snippet["codex_toml"]
        )
        if mech.expect_present:
            assert mech.token in blob, (
                f"{bundle.name}: '{mech.token}' missing from config"
            )
        else:
            assert mech.token not in blob, (
                f"{bundle.name}: '{mech.token}' must be absent"
            )
    else:
        # documented (credential-only / scope / native / statement-allowlist):
        # read-only is enforced outside the MCP args, so SETUP.md must both say
        # "read-only" AND name the control that enforces it — a bare mention of
        # the word is not enough. A unit test can't prove the control is *correct*
        # (that needs live verification), but it can require one to be named, which
        # catches a SETUP that only gestures at read-only.
        low = setup.lower()
        assert "read-only" in low, (
            f"{bundle.name}: SETUP.md must document read-only enforcement"
        )
        controls = (
            "scope",
            "account",
            "role",
            "credential",
            "permission",
            "key",
            "token",
            "allowlist",
        )
        assert any(control in low for control in controls), (
            f"{bundle.name}: SETUP.md names no control that enforces read-only "
            "(expected one of: account/role/scope/key/permission/allowlist)"
        )
