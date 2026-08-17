#!/usr/bin/env python3
"""Copy the repo into a blind native-goal canary workspace.

The export carries current uncommitted changes but strips everything that would
let a run read the answer instead of deriving it: prior cases, the committed
demo output, the decision record, and past canary results.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_ROOT_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "htmlcov",
    "research",
    # The canary claims no MCP and no network. The export carries uncommitted
    # changes, so an operator with sources enabled would otherwise ship their
    # live server wiring straight into the run. `.claude/` itself stays — it
    # holds the skills symlink the run needs — but its settings do not.
    ".mcp.json",
    ".codex",
    ".cursor",
}


def prepare_workspace(source_root: Path, target: Path) -> Path:
    source_root = source_root.resolve()
    target = target.expanduser().resolve()
    if target.exists():
        raise FileExistsError(f"Target already exists: {target}")
    if target.is_relative_to(source_root):
        raise ValueError("Target must be outside the source repository")

    def ignored_names(source: str, names: list[str]) -> set[str]:
        relative = Path(source).resolve().relative_to(source_root)
        ignored = {
            name
            for name in names
            if name == ".env" or name.startswith(".env.") or name == "__pycache__"
        }
        if relative == Path("."):
            ignored.update(EXCLUDED_ROOT_NAMES & set(names))
        # Keep the skills symlink, drop the operator's own permission settings.
        if relative == Path(".claude"):
            ignored.update(name for name in names if name.startswith("settings"))
        # The committed demo case answers the canary question outright.
        if relative == Path("examples"):
            ignored.add("demo-export-reliability")
        if relative == Path(".agents/docs"):
            ignored.add("decisions")
        if relative == Path("evals/native-goal"):
            ignored.add("results")
        return ignored

    shutil.copytree(source_root, target, symlinks=True, ignore=ignored_names)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    try:
        workspace = prepare_workspace(ROOT, args.target)
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"Could not prepare canary workspace: {exc}", file=sys.stderr)
        return 1

    print(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
