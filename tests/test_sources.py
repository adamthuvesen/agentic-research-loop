"""Tests for the pluggable source registry and local-only mode."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_research_loop import sources
from agentic_research_loop.sources import (
    SOURCE_CONFIGS,
    build_sources_config,
    register_source,
)

_VALID_SPEC = {
    "key": "zendesk_mcp",
    "hint_field": "focus",
    "label": "Zendesk focus",
    "display_label": "Zendesk",
    "freshness_caveat_group": "docs",
    "transport": "stdio",
    "read_only_mechanism": "credential-only",
    "plan_line": "Zendesk for support tickets.",
    "base_notes": "Search support tickets. Read-only.",
}


@pytest.fixture()
def _restore_registry():
    """Keep registry mutations from leaking across tests."""
    snapshot = dict(SOURCE_CONFIGS)
    yield
    SOURCE_CONFIGS.clear()
    SOURCE_CONFIGS.update(snapshot)


def test_register_source_adds_to_registry(_restore_registry) -> None:
    register_source("zendesk", dict(_VALID_SPEC))  # type: ignore[arg-type]
    assert "zendesk" in SOURCE_CONFIGS
    config = build_sources_config(hints={"zendesk": "billing tickets"})
    assert config["zendesk_mcp"]["enabled"] is True
    assert config["zendesk_mcp"]["focus"] == "billing tickets"


def test_register_source_rejects_collision(_restore_registry) -> None:
    with pytest.raises(ValueError, match="already exists"):
        register_source("web-search", dict(_VALID_SPEC))  # type: ignore[arg-type]
    # override=True is allowed
    register_source("web-search", dict(_VALID_SPEC), override=True)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_spec, match",
    [
        ({**_VALID_SPEC, "key": ""}, "non-empty string"),
        (
            {k: v for k, v in _VALID_SPEC.items() if k != "plan_line"},
            "missing required",
        ),
        ({**_VALID_SPEC, "surprise": "x"}, "unknown field"),
    ],
)
def test_register_source_validates_spec(_restore_registry, bad_spec, match) -> None:
    with pytest.raises(ValueError, match=match):
        register_source("zendesk", bad_spec)  # type: ignore[arg-type]


def test_register_source_rejects_unknown_transport(_restore_registry) -> None:
    with pytest.raises(ValueError, match="unknown transport"):
        register_source(  # type: ignore[arg-type]
            "zendesk", {**_VALID_SPEC, "transport": "carrier-pigeon"}
        )


def test_register_source_rejects_unknown_read_only_mechanism(_restore_registry) -> None:
    with pytest.raises(ValueError, match="read_only_mechanism"):
        register_source(  # type: ignore[arg-type]
            "zendesk", {**_VALID_SPEC, "read_only_mechanism": "trust-me"}
        )


def test_local_only_disables_every_external_source() -> None:
    config = build_sources_config(local_only=True, local_context_paths=None)
    external_keys = [spec["key"] for spec in SOURCE_CONFIGS.values()]
    assert all(config[key]["enabled"] is False for key in external_keys)


def test_build_sources_config_rejects_unknown_source() -> None:
    with pytest.raises(ValueError, match="Unknown source"):
        build_sources_config(enabled={"nope": True})


def test_user_sources_file_is_loaded(tmp_path, monkeypatch, _restore_registry) -> None:
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    (repo / "pyproject.toml").write_text(
        "[project]\nname = 'agentic-research-loop'\n", encoding="utf-8"
    )
    (repo / "config" / "sources.json").write_text(
        json.dumps({"sources": {"zendesk": _VALID_SPEC}}), encoding="utf-8"
    )
    monkeypatch.setattr(sources, "find_repo_root", lambda *a, **k: repo)
    sources._load_user_sources()
    assert "zendesk" in SOURCE_CONFIGS


def test_user_sources_file_rejects_builtin_collision(
    tmp_path, monkeypatch, _restore_registry
) -> None:
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    (repo / "config" / "sources.json").write_text(
        json.dumps({"sources": {"web-search": _VALID_SPEC}}), encoding="utf-8"
    )
    monkeypatch.setattr(sources, "find_repo_root", lambda *a, **k: repo)
    with pytest.raises(ValueError, match="redefines built-in"):
        sources._load_user_sources()


def test_cli_local_only_disables_external_sources(repo_root, monkeypatch) -> None:
    from agentic_research_loop.cli import main

    monkeypatch.chdir(repo_root)
    exit_code = main(
        [
            "init",
            "reg",
            "--template",
            "root-cause",
            "--mode",
            "autonomous",
            "--local-only",
        ]
    )
    assert exit_code == 0
    case = sorted((repo_root / "research").iterdir())[-1]
    config = json.loads((case / "state" / "sources.json").read_text(encoding="utf-8"))
    keys = [spec["key"] for spec in SOURCE_CONFIGS.values()]
    assert all(config[key]["enabled"] is False for key in keys)


def test_example_sources_file_is_valid() -> None:
    """The committed example must parse and validate."""
    example = Path(__file__).resolve().parents[1] / "config" / "sources.json.example"
    payload = json.loads(example.read_text(encoding="utf-8"))
    for name, spec in payload["sources"].items():
        sources._validate_source_spec(name, spec)
