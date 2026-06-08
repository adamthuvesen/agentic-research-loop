from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .layout import find_repo_root


_READ_ONLY_POLICY = (
    "All sources are strictly read-only. "
    "Search, query, and retrieve only — never send messages, create or update issues, "
    "modify data, post comments, or alter any external system."
)

# Where users register their own sources without editing this file. See
# config/sources.json.example for the shape.
USER_SOURCES_FILE = "config/sources.json"


class SourceSpec(TypedDict):
    key: str
    hint_field: str
    label: str
    display_label: str
    freshness_caveat_group: str
    transport: str
    read_only_mechanism: str
    plan_line: str
    base_notes: str


# Transports a source uses to reach its system. "native" = a built-in agent tool
# (e.g. web search); "cli" = a `research <x>` subcommand; "stdio" / "http-oauth"
# = an MCP server.
VALID_TRANSPORTS: frozenset[str] = frozenset({"http-oauth", "stdio", "cli", "native"})

# read_only_mechanism taxonomy. A "config" mechanism names a token that must be
# present (or, for arg-absent, absent) in the shipped MCP config and is checked
# mechanically. A "documented" mechanism is enforced outside the MCP args — an
# OAuth scope, a credential/grant, a SQL statement allowlist, or a native
# read-only tool — and must instead be covered by setup notes.
_CONFIG_PRESENT_PREFIXES = ("url-suffix:", "server-flag:", "tool-allowlist:")
_CONFIG_ABSENT_PREFIXES = ("arg-absent:",)
_DOCUMENTED_PREFIXES = ("scope:",)
_DOCUMENTED_BARE = frozenset({"statement-allowlist", "credential-only", "native"})


@dataclass(frozen=True)
class ReadOnlyMechanism:
    """A parsed ``read_only_mechanism``.

    ``family`` is "config" (the token must be present/absent in the shipped MCP
    config) or "documented" (read-only is enforced outside the MCP args and must
    be described in setup notes).
    """

    raw: str
    family: str
    token: str
    expect_present: bool


def classify_read_only_mechanism(value: str) -> ReadOnlyMechanism | None:
    """Parse a read_only_mechanism string, or return None if it is unrecognized.

    Used by source validation (to reject unknown mechanisms) and by the read-only
    contract test (to check the shipped config or setup notes).
    """
    text = value.strip()
    if not text:
        return None
    for prefix in _CONFIG_PRESENT_PREFIXES:
        if text.startswith(prefix):
            token = text[len(prefix) :].strip()
            return ReadOnlyMechanism(text, "config", token, True) if token else None
    for prefix in _CONFIG_ABSENT_PREFIXES:
        if text.startswith(prefix):
            token = text[len(prefix) :].strip()
            return ReadOnlyMechanism(text, "config", token, False) if token else None
    for prefix in _DOCUMENTED_PREFIXES:
        if text.startswith(prefix):
            token = text[len(prefix) :].strip()
            return ReadOnlyMechanism(text, "documented", token, True) if token else None
    if text in _DOCUMENTED_BARE:
        return ReadOnlyMechanism(text, "documented", "", True)
    return None


_BUILTIN_SOURCES: dict[str, SourceSpec] = {
    "web-search": {
        "key": "web_search",
        "transport": "native",
        "read_only_mechanism": "native",
        "hint_field": "focus",
        "label": "Web focus",
        "display_label": "web",
        "freshness_caveat_group": "web",
        "plan_line": "Web tools for external context and public changes.",
        "base_notes": "Search for external context, public incidents, competitor moves, and platform changes. Read-only.",
    },
}

# The live registry: built-ins plus anything registered at runtime or loaded
# from config/sources.json. Extend it via register_source() or that file rather
# than editing the built-ins above.
SOURCE_CONFIGS: dict[str, SourceSpec] = dict(_BUILTIN_SOURCES)

_REQUIRED_SPEC_KEYS: frozenset[str] = frozenset(SourceSpec.__annotations__)


def _validate_source_spec(name: str, spec: object) -> SourceSpec:
    if not isinstance(spec, dict):
        raise ValueError(
            f"Source {name!r} must be an object, got {type(spec).__name__}."
        )
    missing = _REQUIRED_SPEC_KEYS - spec.keys()
    if missing:
        raise ValueError(
            f"Source {name!r} is missing required field(s): {', '.join(sorted(missing))}."
        )
    extra = spec.keys() - _REQUIRED_SPEC_KEYS
    if extra:
        raise ValueError(
            f"Source {name!r} has unknown field(s): {', '.join(sorted(extra))}."
        )
    for field, value in spec.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Source {name!r} field {field!r} must be a non-empty string."
            )
    transport = str(spec["transport"])
    if transport not in VALID_TRANSPORTS:
        raise ValueError(
            f"Source {name!r} has unknown transport {transport!r}. "
            f"Valid transports: {', '.join(sorted(VALID_TRANSPORTS))}."
        )
    if classify_read_only_mechanism(str(spec["read_only_mechanism"])) is None:
        raise ValueError(
            f"Source {name!r} has an unrecognized read_only_mechanism "
            f"{spec['read_only_mechanism']!r}."
        )
    return spec  # type: ignore[return-value]


# Source names must yield a usable ``--<name>-hint`` / ``--no-<name>`` CLI flag,
# so they share the bundle-name charset (lowercase, digits, '-'/'_').
_SOURCE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def register_source(name: str, spec: SourceSpec, *, override: bool = False) -> None:
    """Add a source to the registry. Raises on collision unless override=True."""
    if not _SOURCE_NAME_RE.match(name):
        raise ValueError(
            f"Source name {name!r} must match {_SOURCE_NAME_RE.pattern} "
            "(lowercase letters/digits, '-' or '_', starting alphanumeric)."
        )
    if name in SOURCE_CONFIGS and not override:
        raise ValueError(
            f"Source {name!r} already exists. Pass override=True to replace it."
        )
    validated = _validate_source_spec(name, spec)
    new_key = validated["key"]
    for other, other_spec in SOURCE_CONFIGS.items():
        if other != name and other_spec["key"] == new_key:
            raise ValueError(
                f"Source {name!r} reuses key {new_key!r} already claimed by source "
                f"{other!r}; each source needs a unique key."
            )
    SOURCE_CONFIGS[name] = validated


def _load_user_sources() -> None:
    """Merge user-defined sources from config/sources.json, if present."""
    try:
        repo_root = find_repo_root()
    except FileNotFoundError:
        return
    path = repo_root / USER_SOURCES_FILE
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{USER_SOURCES_FILE} is not valid JSON: {exc}") from exc
    sources = payload.get("sources", payload) if isinstance(payload, dict) else None
    if not isinstance(sources, dict):
        raise ValueError(
            f"{USER_SOURCES_FILE} must be an object mapping source names to specs "
            f'(optionally under a top-level "sources" key).'
        )
    for name, spec in sources.items():
        if name in _BUILTIN_SOURCES:
            raise ValueError(
                f"{USER_SOURCES_FILE} redefines built-in source {name!r}; "
                "choose a different name."
            )
        register_source(name, _validate_source_spec(name, spec))


_load_user_sources()

VALID_SOURCES: frozenset[str] = frozenset(SOURCE_CONFIGS)


def enabled_source_labels(sources_config: dict) -> list[str]:
    """Return display labels for all enabled sources in sources_config."""
    labels = []
    for spec in SOURCE_CONFIGS.values():
        section = sources_config.get(spec["key"], {})
        if section.get("enabled", True):
            labels.append(spec["display_label"])
    return labels


def build_sources_config(
    *,
    enabled: dict[str, bool] | None = None,
    hints: dict[str, str] | None = None,
    local_context_paths: list[str] | None = None,
    local_only: bool = False,
) -> dict:
    enabled = enabled or {}
    hints = hints or {}

    for name in enabled:
        if name not in SOURCE_CONFIGS:
            raise ValueError(
                f"Unknown source {name!r} in enabled. "
                f"Valid sources: {', '.join(sorted(SOURCE_CONFIGS))}"
            )

    config: dict = {
        "read_only_policy": _READ_ONLY_POLICY,
    }

    for name, spec in SOURCE_CONFIGS.items():
        # local_only forces every registered (external) source off, leaving only
        # the local context folders below.
        is_enabled = False if local_only else enabled.get(name, True)
        hint = hints.get(name, "")
        entry = {spec["hint_field"]: hint, "notes": spec["base_notes"]}
        entry["enabled"] = is_enabled
        config[spec["key"]] = entry

    config["local_context_folders"] = [
        _local_context_entry(path) for path in (local_context_paths or [])
    ]

    return config


def _local_context_entry(path: str) -> dict[str, str]:
    resolved = _resolve_local_context_path(path)
    return {
        "path": str(resolved),
        "notes": _local_context_notes(resolved),
    }


def _resolve_local_context_path(path: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not (resolved.is_file() or resolved.is_dir()):
        raise FileNotFoundError(f"Local context path does not exist: {resolved}")
    return resolved


_SENSITIVE_PATH_PARTS = frozenset(
    {
        ".aws",
        ".azure",
        ".config",
        ".docker",
        ".gnupg",
        ".kube",
        ".ssh",
        "Library",
    }
)


def _local_context_notes(path: Path) -> str:
    notes = "Search and read local context files. Read-only."
    home = Path.home().resolve()
    if path == Path(path.anchor) or path == home:
        return (
            notes + " Broad path attached intentionally; avoid unrelated private files."
        )
    if any(part in _SENSITIVE_PATH_PARTS for part in path.parts):
        return (
            notes + " Sensitive-looking path attached; avoid secrets and credentials."
        )
    return notes


def source_plan_lines(config: dict) -> list[str]:
    lines = [
        config.get("read_only_policy", _READ_ONLY_POLICY),
        "",
    ]

    for spec in SOURCE_CONFIGS.values():
        section = config.get(spec["key"], {})
        if section.get("enabled", True):
            lines.append(spec["plan_line"])

    for spec in SOURCE_CONFIGS.values():
        section = config.get(spec["key"], {})
        if not section.get("enabled", True):
            continue
        value = str(section.get(spec["hint_field"], "")).strip()
        if value:
            lines.append(f"{spec['label']}: {value}")

    for entry in config.get("local_context_folders", []):
        path = str(entry.get("path", "")).strip()
        if path:
            lines.append(f"Local context folder: {path}")
        notes = str(entry.get("notes", "")).strip()
        if notes and notes != "Search and read local context files. Read-only.":
            lines.append(f"Local context note: {notes}")

    return lines
