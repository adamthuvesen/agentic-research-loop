from __future__ import annotations

from pathlib import Path
from typing import TypedDict


_READ_ONLY_POLICY = (
    "All sources are strictly read-only. "
    "Search, query, and retrieve only — never send messages, create or update issues, "
    "modify data, post comments, or alter any external system."
)


class SourceSpec(TypedDict):
    key: str
    hint_field: str
    label: str
    display_label: str
    freshness_caveat_group: str
    plan_line: str
    base_notes: str


SOURCE_CONFIGS: dict[str, SourceSpec] = {
    "notion": {
        "key": "notion_mcp",
        "hint_field": "target",
        "label": "Notion target",
        "display_label": "Notion",
        "freshness_caveat_group": "docs",
        "plan_line": "Notion for workspace pages, databases, and discussions.",
        "base_notes": "Search Notion pages, databases, and discussions. Read-only — never create or update pages.",
    },
    "slack": {
        "key": "slack_mcp",
        "hint_field": "focus",
        "label": "Slack focus",
        "display_label": "Slack",
        "freshness_caveat_group": "docs",
        "plan_line": "Slack for recent discussions, decisions, and informal context. Ephemeral — cite with caveat.",
        "base_notes": "Search recent discussions, decisions, and informal context. Read-only — never send or schedule messages. Slack is ephemeral — note this when citing.",
    },
    "linear": {
        "key": "linear_mcp",
        "hint_field": "focus",
        "label": "Linear focus",
        "display_label": "Linear",
        "freshness_caveat_group": "docs",
        "plan_line": "Linear for project status, issue tracking, and ownership context.",
        "base_notes": "Search project status, issue tracking, cycle planning, and ownership context. Read-only — never create or update issues.",
    },
    "web-search": {
        "key": "web_search",
        "hint_field": "focus",
        "label": "Web focus",
        "display_label": "web",
        "freshness_caveat_group": "web",
        "plan_line": "Web tools for external context and public changes.",
        "base_notes": "Search for external context, public incidents, competitor moves, and platform changes. Read-only.",
    },
    "snowflake": {
        "key": "snowflake",
        "hint_field": "focus",
        "label": "Snowflake focus",
        "display_label": "Snowflake",
        "freshness_caveat_group": "live",
        "plan_line": "Snowflake for live metrics and warehouse-backed evidence.",
        "base_notes": (
            "Query live metrics via the Snowflake MCP server (configured in .mcp.json). "
            "Prefer semantic views and curated marts when they cover the question; else "
            "query staging tables. Verify objects live (describe_semantic_view / "
            "SHOW TABLES / DESCRIBE) before querying. "
            "Read-only — SELECT queries only, never ALTER/DELETE/DROP."
        ),
    },
    "confidence": {
        "key": "confidence_mcp",
        "hint_field": "focus",
        "label": "Confidence focus",
        "display_label": "Confidence",
        "freshness_caveat_group": "live",
        "plan_line": "Confidence for experiments, rollouts, and decision history.",
        "base_notes": "Query rollout timing, experiment state, decision history, and results. Read-only — never modify experiments or flags.",
    },
    "gsc": {
        "key": "gsc",
        "hint_field": "focus",
        "label": "GSC focus",
        "display_label": "GSC",
        "freshness_caveat_group": "live",
        "plan_line": "GSC organic search — default Snowflake (synced); `research gsc` only as API fallback.",
        "base_notes": (
            "Google Search Console data for organic search performance — clicks, impressions, CTR, "
            "positions by query, page, device, country, and date. Read-only.\n"
            "**Default:** Snowflake, if your warehouse syncs GSC (e.g. via Fivetran); prefer "
            "semantic views / marts when they cover the question, else the synced staging "
            "tables, e.g. a keyword+page report (query + page + country + device + date) and a "
            "page report (page + country + device + date, no query dimension).\n"
            "**Fallback:** `research gsc` CLI for fresher data, when sync is lagging, or for API-only slices.\n"
            "  Example: research gsc --start-date 2026-03-01 --end-date 2026-04-06 --dimensions query,page\n"
            "  Dimensions: query, page, country, device, searchAppearance, date\n"
            "  Supports --row-limit and --start-row for pagination."
        ),
    },
    "ga4": {
        "key": "ga4",
        "hint_field": "focus",
        "label": "GA4 focus",
        "display_label": "GA4",
        "freshness_caveat_group": "live",
        "plan_line": "Google Analytics 4 for site analytics — page views, sessions, users, engagement, and conversions.",
        "base_notes": (
            "Google Analytics 4 data for site analytics — page views, sessions, active users, "
            "engagement, conversions by page, source/medium, device, country, and date. Read-only.\n"
            "Use `research ga4` CLI to query the GA4 Data API (property from the GA4_PROPERTY_ID env var).\n"
            "  Example: research ga4 --start-date 2026-03-01 --end-date 2026-04-06 "
            "--dimensions pagePath --metrics screenPageViews,sessions\n"
            "  Common dimensions: pagePath, pageTitle, country, city, deviceCategory, "
            "sessionSource, sessionMedium, date\n"
            "  Common metrics: screenPageViews, sessions, activeUsers, newUsers, bounceRate, "
            "averageSessionDuration, conversions\n"
            "  Supports --limit, --offset for pagination and --order-by for sorting."
        ),
    },
}

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
) -> dict:
    enabled = enabled or {}
    hints = hints or {}

    for name in enabled:
        if name not in VALID_SOURCES:
            raise ValueError(
                f"Unknown source {name!r} in enabled. "
                f"Valid sources: {', '.join(sorted(VALID_SOURCES))}"
            )

    config: dict = {
        "read_only_policy": _READ_ONLY_POLICY,
    }

    for name, spec in SOURCE_CONFIGS.items():
        is_enabled = enabled.get(name, True)
        hint = hints.get(name, "")
        entry = {spec["hint_field"]: hint, "notes": spec["base_notes"]}
        entry["enabled"] = is_enabled
        config[spec["key"]] = entry

    config["local_context_folders"] = [
        {
            "path": str(_resolve_local_context_path(path)),
            "notes": "Search and read local context files. Read-only.",
        }
        for path in (local_context_paths or [])
    ]

    return config


def _resolve_local_context_path(path: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not (resolved.is_file() or resolved.is_dir()):
        raise FileNotFoundError(f"Local context path does not exist: {resolved}")
    return resolved


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

    return lines
