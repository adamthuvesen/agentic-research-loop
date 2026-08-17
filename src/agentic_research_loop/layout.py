from __future__ import annotations

import re
from datetime import date
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        pyproject_path = candidate / "pyproject.toml"
        if pyproject_path.exists():
            text = pyproject_path.read_text(encoding="utf-8")
        else:
            continue
        if (
            'name = "agentic-research-loop"' in text
            or "name = 'agentic-research-loop'" in text
        ):
            return candidate
    raise FileNotFoundError(
        "Could not locate the agentic-research-loop repo root from the current directory."
    )


MAX_SLUG_LENGTH = 60

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "can",
        "could",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
        "up",
        "about",
        "into",
        "over",
        "after",
        "before",
        "between",
        "under",
        "during",
        "and",
        "but",
        "or",
        "not",
        "so",
        "yet",
        "both",
        "either",
        "neither",
        "each",
        "every",
        "all",
        "any",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "only",
        "same",
        "than",
        "too",
        "very",
        "just",
        "because",
        "as",
        "until",
        "while",
        "how",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "that",
        "these",
        "those",
        "this",
        "it",
        "its",
        "my",
        "our",
        "your",
        "their",
        "his",
        "her",
        "we",
        "they",
        "he",
        "she",
        "i",
        "me",
        "us",
        "them",
        "last",
        "many",
    }
)


def slugify(value: str, *, max_length: int = MAX_SLUG_LENGTH) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    content = [w for w in words if w not in STOP_WORDS]
    if not content:
        content = words
    unique = list(dict.fromkeys(content))
    slug = "-".join(unique)
    if not slug:
        raise ValueError("Slug must contain at least one letter or number.")
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    if not slug:
        slug = "-".join(unique)[:max_length]
    return slug


def case_slug(question_or_slug: str, today: date | None = None) -> str:
    return f"{(today or date.today()).isoformat()}-{slugify(question_or_slug)}"


def research_dir(repo_root: Path) -> Path:
    return repo_root / "research"


def case_dir(repo_root: Path, case_id: str) -> Path:
    return research_dir(repo_root) / case_id


def brief_path(case_path: Path) -> Path:
    return case_path / "brief.md"


def notes_path(case_path: Path) -> Path:
    return case_path / "notes.md"


def report_path(case_path: Path) -> Path:
    return case_path / "report.md"


def queries_path(case_path: Path) -> Path:
    return case_path / "queries.sql"


def source_objects_path(case_path: Path) -> Path:
    return case_path / "source-objects.md"


def plan_path(case_path: Path) -> Path:
    return case_path / "plan.md"
