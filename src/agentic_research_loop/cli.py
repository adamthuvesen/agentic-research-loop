from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .layout import find_repo_root
from .research import create_manual, render_goal, resolve_case_path
from .sources import VALID_SOURCES
from .validation import validate_case

_SOURCE_NAMES = sorted(VALID_SOURCES)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _iso_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a valid YYYY-MM-DD date") from exc
    return value


def _comma_list(value: str) -> list[str]:
    values = [item.strip() for item in value.split(",")]
    if not values or any(not item for item in values):
        raise argparse.ArgumentTypeError(
            "must be a comma-separated list with no blanks"
        )
    return values


def _add_source_args(parser: argparse.ArgumentParser) -> None:
    for name in _SOURCE_NAMES:
        parser.add_argument(
            f"--no-{name}",
            action="store_true",
            help=f"Disable {name} for this case.",
        )
        parser.add_argument(
            f"--{name}-hint",
            help=f"Optional focus/hint for {name}.",
        )
    parser.add_argument(
        "--context-path",
        action="append",
        default=[],
        help="Attach a local context folder or file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Disable all external sources; investigate only --context-path files.",
    )


def _source_kwargs(args: argparse.Namespace) -> dict:
    enabled: dict[str, bool] = {}
    hints: dict[str, str] = {}
    for name in _SOURCE_NAMES:
        attr_no = f"no_{name.replace('-', '_')}"
        attr_hint = f"{name.replace('-', '_')}_hint"
        if getattr(args, attr_no, False):
            enabled[name] = False
        hint = getattr(args, attr_hint, None)
        if hint:
            hints[name] = hint
    return {
        "enabled": enabled or None,
        "hints": hints or None,
        "local_context_paths": args.context_path or None,
        "local_only": args.local_only,
    }


def _add_case_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("case", help="Case id or path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and validate research cases run with native agent goals"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a case workspace")
    init_parser.add_argument("slug", help="Short case slug")
    init_parser.add_argument("--question", help="Specific research question")
    init_parser.add_argument(
        "--template",
        choices=("exploration", "root-cause", "comparison"),
        default="exploration",
    )
    init_parser.add_argument(
        "--from-spec",
        type=Path,
        default=None,
        help=(
            "Directory containing pre-authored brief.md / plan.md / notes.md. "
            "Files present are used verbatim in place of default templates; "
            "files absent fall back to defaults. The Source Constraints section "
            "of brief.md is always generated from the source flags."
        ),
    )
    _add_source_args(init_parser)

    goal_parser = subparsers.add_parser(
        "goal", help="Print the native /goal command for a case"
    )
    _add_case_arg(goal_parser)

    validate_parser = subparsers.add_parser("validate", help="Validate a case")
    _add_case_arg(validate_parser)
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Completion gate: a real answer, traceable evidence, preserved "
            "provenance, and a completed independent challenge."
        ),
    )

    gsc_parser = subparsers.add_parser(
        "gsc",
        help="GSC Search Analytics API (fallback — prefer your warehouse for synced GSC data)",
    )
    gsc_parser.add_argument(
        "--start-date", required=True, type=_iso_date, help="YYYY-MM-DD"
    )
    gsc_parser.add_argument(
        "--end-date", required=True, type=_iso_date, help="YYYY-MM-DD"
    )
    gsc_parser.add_argument(
        "--dimensions",
        required=True,
        type=_comma_list,
        help="Comma-separated: query,page,country,device,searchAppearance,date",
    )
    gsc_parser.add_argument("--row-limit", type=_positive_int, default=100)
    gsc_parser.add_argument("--start-row", type=_non_negative_int, default=0)

    source_parser = subparsers.add_parser(
        "source", help="Manage opt-in source bundles (examples/sources/)"
    )
    source_sub = source_parser.add_subparsers(dest="source_command", required=True)
    enable_p = source_sub.add_parser(
        "enable", help="Wire a bundle into config/sources.json and the MCP configs"
    )
    enable_p.add_argument("name", help="Bundle name, e.g. github")
    disable_p = source_sub.add_parser("disable", help="Remove a bundle's wiring")
    disable_p.add_argument("name", help="Bundle name")
    source_sub.add_parser("list", help="List bundles and whether they are enabled")

    return parser


def _init_case(
    parser: argparse.ArgumentParser, repo_root: Path, args: argparse.Namespace
) -> int:
    try:
        result = create_manual(
            repo_root,
            args.slug,
            template=args.template,
            question=args.question,
            from_spec_path=args.from_spec,
            **_source_kwargs(args),
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Created case: {result.case_id}")
    print(f"Path: {result.path}")
    print(f"Next: uv run research goal {result.case_id}")
    return 0


def _goal_command(repo_root: Path, args: argparse.Namespace) -> int:
    print(render_goal(resolve_case_path(repo_root, args.case)))
    return 0


def _validate_case_command(repo_root: Path, args: argparse.Namespace) -> int:
    case_path = resolve_case_path(repo_root, args.case)
    errors = validate_case(case_path, strict_completion=args.strict)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: {case_path}")
    return 0


def _gsc_query_command(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> int:
    from .google_api import GoogleApiError, GoogleAuthError, gsc_query

    if args.start_date > args.end_date:
        parser.error("--start-date must be on or before --end-date")
    try:
        result = gsc_query(
            start_date=args.start_date,
            end_date=args.end_date,
            dimensions=args.dimensions,
            row_limit=args.row_limit,
            start_row=args.start_row,
        )
    except (GoogleApiError, GoogleAuthError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _source_command(repo_root: Path, args: argparse.Namespace) -> int:
    from .source_bundles import (
        BundleError,
        disable_bundle,
        enable_bundle,
        render_bundle_list,
    )

    try:
        if args.source_command == "list":
            print(render_bundle_list(repo_root))
            return 0
        action = enable_bundle if args.source_command == "enable" else disable_bundle
        for line in action(repo_root, args.name):
            print(f"- {line}")
    except (BundleError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = find_repo_root()

    if args.command == "init":
        return _init_case(parser, repo_root, args)

    if args.command == "goal":
        return _goal_command(repo_root, args)

    if args.command == "validate":
        return _validate_case_command(repo_root, args)

    if args.command == "gsc":
        return _gsc_query_command(parser, args)

    if args.command == "source":
        return _source_command(repo_root, args)

    return 1


def _entry() -> None:
    try:
        exit_code = main()
    except (FileExistsError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 1
    sys.exit(exit_code)
