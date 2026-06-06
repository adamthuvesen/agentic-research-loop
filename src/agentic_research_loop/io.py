from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_text_optional(path: Path) -> str | None:
    """Return file contents or None if the file does not exist."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    closed = False
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        closed = True
        os.replace(tmp, path)
    except Exception:
        if not closed:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_json_optional(path: Path) -> Any | None:
    """Return parsed JSON or None if the file does not exist."""
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_json_object_or_empty(path: Path) -> dict[str, Any]:
    """Return a JSON object or `{}` when the file is missing, invalid, or another type."""
    try:
        payload = load_json(path)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2) + "\n")


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def extract_section(
    text: str, heading: str, max_chars: int | None = None
) -> str | None:
    """Extract the body of a ## heading section (case-insensitive).

    Returns None if the section is absent or empty.
    """
    pattern = rf"^## {re.escape(heading)}[ \t]*\n+(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match is None:
        return None
    body = match.group(1).strip()
    if not body or body == "-":
        return None
    if max_chars is not None and len(body) > max_chars:
        return body[:max_chars] + "..."
    return body
