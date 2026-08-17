"""Validate durable case artifacts without inspecting agent runtime state.

The native goal owns execution; the only thing worth checking afterwards is the
record it left behind. `validate_case(..., strict_completion=True)` is the goal's
terminal condition, so every check here has to be something an agent can fix by
doing better research rather than by editing bookkeeping.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import extract_section, read_text
from .layout import (
    brief_path,
    notes_path,
    plan_path,
    queries_path,
    report_path,
    source_objects_path,
)
from .sql_safety import (
    ALLOWED_SQL_STARTS,
    first_forbidden_sql_word,
    sql_code_only,
    sql_statements,
    statement_start,
)

MIN_SUBSTANTIVE_CONTENT_LENGTH = 60
MIN_SOURCE_OBJECTS_LENGTH = 50

VALID_TEMPLATES = frozenset({"exploration", "root-cause", "comparison"})

REQUIRED_FILES = {
    "brief.md": brief_path,
    "notes.md": notes_path,
    "report.md": report_path,
    "queries.sql": queries_path,
    "source-objects.md": source_objects_path,
}

# Field names a high-priority root-cause thread must carry. The research-spec
# skill writes these exact strings; changing one here breaks that contract.
ROOT_CAUSE_DESIGN_FIELDS = (
    "Discriminating Test",
    "Strongest Rival",
    "Completion Threshold",
    "Cross-Check",
)

_ROOT_CAUSE_BRIEF_SECTIONS = (
    ("## Hypotheses", "root-cause brief should include a `## Hypotheses` section"),
    ("## Known Confounders", "root-cause brief should capture `## Known Confounders`"),
    (
        "## Required Cross-Checks",
        "root-cause brief should capture `## Required Cross-Checks`",
    ),
)

THREAD_PATTERN = re.compile(
    r"^###\s+(T[^\n:]*:[^\n]*?)\n(?P<body>.*?)(?=^###\s+T|\Z)", re.MULTILINE | re.DOTALL
)
FIELD_PATTERN = re.compile(r"^\*\*(?P<name>[^*]+):\*\*\s*(?P<value>.+)$", re.MULTILINE)

# Reviewer values that name no one in particular, or name the researcher. An
# independent challenge that the researcher performed on itself is not one.
_INVALID_REVIEWER_VALUES = frozenset(
    {
        "subagent name or task identifier",
        "independent subagent",
        "main agent",
        "primary agent",
        "primary researcher",
        "research agent",
        "not assigned",
    }
)
_INVALID_REVIEWER_WORDS = frozenset({"me", "self", "tbd", "todo", "unknown"})


def report_has_substance(report_text: str) -> bool:
    summary = extract_section(report_text, "Executive Summary")
    if summary is None:
        return False
    if "complete this section" in summary.lower():
        return False
    return len(" ".join(summary.split())) >= MIN_SUBSTANTIVE_CONTENT_LENGTH


def _section_is_placeholder(text: str, heading: str, phrases: tuple[str, ...]) -> bool:
    section = extract_section(text, heading)
    if section is None:
        return True
    normalized = " ".join(section.lower().split())
    return any(phrase in normalized for phrase in phrases)


def _field_value(text: str, label: str) -> str | None:
    """Read a `- Label: value` bullet, or None when the value is blank.

    The value must sit on the label's own line. A `\\s*` gap here would match
    the newline and let an empty field absorb the next bullet as its value,
    which passes every completeness check on a wholly unfilled template.
    """
    match = re.search(rf"(?im)^[ \t]*-[ \t]*{re.escape(label)}:[ \t]*(\S[^\n]*)$", text)
    return match.group(1).strip() if match is not None else None


def _has_complete_evidence_record(evidence_log: str) -> bool:
    records = re.split(r"(?im)(?=^\s*-\s*Claim:\s*)", evidence_log)
    return any(
        all(_field_value(record, label) for label in ("Claim", "Source", "Supports"))
        for record in records
    )


def _reviewer_is_independent(reviewer: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", reviewer.lower()).strip()
    if len(normalized) < 3:
        return False
    # Exact-set membership, not substring: a real name like
    # `independent-subagent-challenger` contains a placeholder phrase without
    # being one.
    if normalized in _INVALID_REVIEWER_VALUES:
        return False
    return not set(normalized.split()) & _INVALID_REVIEWER_WORDS


def _challenge_is_complete(challenge: str) -> bool:
    reviewer = _field_value(challenge, "Independent reviewer")
    if reviewer is None or not _reviewer_is_independent(reviewer):
        return False

    findings = (
        "Strongest competing explanation",
        "Weakest-supported material claim",
        "Most fragile source or calculation",
    )
    if not all(_field_value(challenge, label) for label in findings):
        return False

    resolution = _field_value(challenge, "Resolution")
    if resolution is None:
        return False
    normalized = " ".join(resolution.lower().split())
    if normalized in {"open", "pending", "tbd", "unresolved", "open | resolved"}:
        return False
    # Disclosing an unresolved objection is allowed; leaving it bare is not.
    return normalized.startswith(
        ("resolved", "unresolved because", "unresolved:", "not resolved because")
    )


def parse_plan_threads(plan_text: str) -> list[dict[str, Any]]:
    threads: list[dict[str, Any]] = []
    for match in THREAD_PATTERN.finditer(plan_text):
        heading = match.group(1).strip()
        fields = {
            field.group("name").strip(): field.group("value").strip()
            for field in FIELD_PATTERN.finditer(match.group("body"))
        }
        threads.append({"heading": heading, "fields": fields})
    return threads


def _thread_design_errors(threads: list[dict[str, Any]]) -> list[str]:
    return [
        f"{thread['heading']} is high priority but missing `{field_name}`"
        for thread in threads
        if thread["fields"].get("Priority", "").lower() == "high"
        for field_name in ROOT_CAUSE_DESIGN_FIELDS
        if field_name not in thread["fields"]
    ]


def _case_template(brief_text: str) -> tuple[str | None, list[str]]:
    """Read the case's research shape from the brief.

    Returns the template and any errors. An unreadable shape is an error rather
    than a silent `None`: falling through would skip the whole root-cause design
    contract while validation still reported success.
    """
    # Tolerate the bold variants a hand-written brief tends to use:
    # `- Research shape:`, `- **Research shape:**`, `- **Research shape**:`.
    match = re.search(
        r"(?im)^[ \t]*-[ \t]*\*{0,2}Research shape\*{0,2}:\*{0,2}[ \t]*`?([A-Za-z-]+)`?",
        brief_text,
    )
    if match is None:
        return None, [
            "brief.md needs a `- Research shape: <template>` line in `## Scope`"
        ]
    template = match.group(1).lower()
    if template not in VALID_TEMPLATES:
        return None, [
            f"brief.md has an unknown research shape {template!r}. "
            f"Use one of: {', '.join(sorted(VALID_TEMPLATES))}"
        ]
    return template, []


def _root_cause_design_errors(case_path: Path, brief_text: str) -> list[str]:
    """Check the design contract that makes a root-cause case falsifiable."""
    errors = [
        message
        for heading, message in _ROOT_CAUSE_BRIEF_SECTIONS
        if heading not in brief_text
    ]

    plan_file = plan_path(case_path)
    if not plan_file.exists():
        return errors

    plan_text = read_text(plan_file)
    if "No plan yet" in plan_text:
        return errors
    threads = parse_plan_threads(plan_text)
    if not threads:
        errors.append("plan.md has content but no numbered research threads")
        return errors
    errors.extend(_thread_design_errors(threads))
    return errors


def _sql_errors(sql: str) -> tuple[list[str], str]:
    """Return SQL safety errors plus the comment-stripped SQL for later checks."""
    try:
        executable = sql_code_only(sql)
    except ValueError as exc:
        return [f"queries.sql is invalid: {exc}"], ""

    forbidden = first_forbidden_sql_word(executable)
    if forbidden:
        return (
            [f"queries.sql contains forbidden write statement: {forbidden}"],
            executable,
        )

    unsupported = next(
        (
            start
            for statement in sql_statements(executable)
            if (start := statement_start(statement)) not in ALLOWED_SQL_STARTS
        ),
        None,
    )
    if unsupported is not None:
        return (
            [
                f"queries.sql contains unsupported statement starting with: {unsupported}"
            ],
            executable,
        )
    return [], executable


def _sql_provenance_errors(sql: str, executable: str) -> list[str]:
    has_read_sql = any(
        statement_start(statement) in ALLOWED_SQL_STARTS
        for statement in sql_statements(executable)
    )
    if has_read_sql:
        return []
    if re.search(r"(?im)^\s*--\s*no sql used:\s*\S+", sql):
        return []
    return [
        "queries.sql needs a read-only query or an explicit `-- No SQL used: <reason>`"
    ]


def _report_errors(report: str) -> list[str]:
    errors: list[str] = []
    if not report_has_substance(report):
        errors.append("report.md needs a meaningful Executive Summary")
    placeholder_sections = (
        ("Evidence", ("replace this", "complete this")),
        ("Reconciliation", ("show how calculated contributions", "explain why")),
        ("Rejected Leads", ("replace this", "complete this")),
        ("Risks And Caveats", ("replace this", "complete this")),
    )
    errors.extend(
        f"report.md needs a completed {heading} section"
        for heading, phrases in placeholder_sections
        if _section_is_placeholder(report, heading, phrases)
    )
    return errors


def validate_case(case_path: Path, *, strict_completion: bool = False) -> list[str]:
    """Validate durable case artifacts.

    The default pass checks structure and read-only SQL safety — safe to run at
    scaffold time. `strict_completion` adds the end-of-case gate: a real answer,
    traceable evidence, preserved provenance, and a completed independent
    challenge.
    """
    errors: list[str] = []
    texts: dict[str, str] = {}
    for name, path_for in REQUIRED_FILES.items():
        path = path_for(case_path)
        if not path.exists():
            errors.append(f"Missing required file: {name}")
            continue
        try:
            texts[name] = read_text(path)
        except OSError as exc:
            errors.append(f"Could not read {name}: {exc}")

    sql = texts.get("queries.sql", "")
    executable_sql = ""
    if sql:
        sql_errors, executable_sql = _sql_errors(sql)
        errors.extend(sql_errors)

    if errors:
        return errors

    brief = texts["brief.md"]
    template, template_errors = _case_template(brief)
    errors.extend(template_errors)
    if template == "root-cause":
        errors.extend(_root_cause_design_errors(case_path, brief))

    if not strict_completion:
        return errors

    question = extract_section(brief, "Question")
    if question is None or question.lower().startswith("research:"):
        errors.append("brief.md needs a specific research question")

    errors.extend(_report_errors(texts["report.md"]))

    notes = texts["notes.md"]
    evidence_log = extract_section(notes, "Evidence Log")
    if evidence_log is None or not _has_complete_evidence_record(evidence_log):
        errors.append("notes.md needs a completed Evidence Log section")

    challenge = extract_section(notes, "Final Challenge")
    if challenge is None or not _challenge_is_complete(challenge):
        errors.append(
            "notes.md needs a completed Final Challenge section naming an "
            "independent reviewer"
        )

    source_objects = " ".join(texts["source-objects.md"].lower().split())
    if (
        "replace this line" in source_objects
        or len(source_objects) < MIN_SOURCE_OBJECTS_LENGTH
    ):
        errors.append("source-objects.md needs at least one concrete source object")

    errors.extend(_sql_provenance_errors(sql, executable_sql))
    return errors
