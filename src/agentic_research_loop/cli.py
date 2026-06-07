from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .research import (
    create_manual,
    resolve_case_path,
)
from .terminal import print_run_footer
from .io import load_json_optional
from .layout import find_repo_root
from .loop import run_loop, run_plan_step
from .publish import publish
from .sources import VALID_SOURCES
from .status import render_status_markdown
from .validation import collect_validation_warnings, validate_case

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified AI research engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create an empty case workspace")
    init_parser.add_argument("slug", help="Short case slug")
    init_parser.add_argument(
        "--template",
        choices=("exploration", "root-cause", "comparison"),
        default="exploration",
    )
    init_parser.add_argument(
        "--mode",
        choices=("quick", "guided", "autonomous"),
        default="guided",
    )
    init_parser.add_argument(
        "--from-spec",
        type=Path,
        default=None,
        help=(
            "Directory containing pre-authored brief.md / plan.md / notes.md. "
            "Files present are used verbatim in place of default templates; "
            "files absent fall back to defaults. The Source Registry section "
            "of brief.md is always generated from --*-hint flags."
        ),
    )
    _add_source_args(init_parser)

    run_parser = subparsers.add_parser("run", help="Run autonomous cycles for a case")
    run_parser.add_argument("case", help="Case id or path")
    run_parser.add_argument(
        "--runner",
        choices=("claude", "codex", "demo", "claude-local"),
        default="claude",
        help="External agent CLI (default: claude).",
    )
    run_parser.add_argument("--max-cycles", type=_positive_int, default=10)

    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume an autonomous case (alias of run)",
    )
    resume_parser.add_argument("case", help="Case id or path")
    resume_parser.add_argument(
        "--runner",
        choices=("claude", "codex", "demo", "claude-local"),
        default="claude",
        help="External agent CLI (default: claude).",
    )
    resume_parser.add_argument("--max-cycles", type=_positive_int, default=10)

    status_parser = subparsers.add_parser("status", help="Show case status")
    status_parser.add_argument("case", help="Case id or path")

    validate_parser = subparsers.add_parser("validate", help="Validate a case")
    validate_parser.add_argument("case", help="Case id or path")
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Full completion gate: design contract + challenge cycle + meaningful "
            "report.md. Use only as a publish pre-flight."
        ),
    )
    validate_parser.add_argument(
        "--design",
        action="store_true",
        help=(
            "Enforce design contract on high-priority threads. Safe to run at "
            "scaffold/planning time — does not gate on challenge cycle or report.md."
        ),
    )

    publish_parser = subparsers.add_parser(
        "publish", help="Publish a case as a durable finding"
    )
    publish_parser.add_argument("case", help="Case id or path")

    plan_parser = subparsers.add_parser(
        "plan", help="Generate a research plan for a case"
    )
    plan_parser.add_argument("case", help="Case id or path")
    plan_parser.add_argument(
        "--runner",
        choices=("claude", "codex", "demo", "claude-local"),
        default="claude",
        help="External agent CLI (default: claude).",
    )

    gsc_parser = subparsers.add_parser(
        "gsc",
        help="GSC Search Analytics API (fallback — prefer Snowflake for synced GSC data)",
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


def _run_case(repo_root: Path, args: argparse.Namespace) -> int:
    """Run or resume autonomous cycles (same behavior)."""
    case_path = resolve_case_path(repo_root, args.case)
    summaries = run_loop(
        repo_root,
        case_path,
        runner_name=args.runner,
        max_cycles=args.max_cycles,
    )
    print_run_footer([summary.to_payload() for summary in summaries])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = find_repo_root()

    if args.command == "init":
        result = create_manual(
            repo_root,
            args.slug,
            template=args.template,
            mode=args.mode,
            from_spec_path=args.from_spec,
            **_source_kwargs(args),
        )
        print(f"Created case: {result.case_id}")
        print(f"Path: {result.path}")
        return 0

    if args.command in {"run", "resume"}:
        return _run_case(repo_root, args)

    if args.command == "status":
        case_path = resolve_case_path(repo_root, args.case)
        status_file = case_path / "state" / "status.json"
        try:
            status_payload = load_json_optional(status_file)
        except (json.JSONDecodeError, OSError):
            status_payload = None
        if not isinstance(status_payload, dict):
            print(f"Error: status.json not found or invalid at {status_file}")
            return 1
        print(render_status_markdown(case_path, status_payload))
        return 0

    if args.command == "validate":
        case_path = resolve_case_path(repo_root, args.case)
        warnings = collect_validation_warnings(case_path)
        errors = validate_case(
            case_path,
            strict_completion=args.strict,
            strict_design=args.design,
        )
        if warnings and not (args.strict or args.design):
            print("Validation warnings:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Validation passed: {case_path}")
        return 0

    if args.command == "publish":
        case_path = resolve_case_path(repo_root, args.case)
        output_path = publish(case_path)
        print(f"Published finding to {output_path}")
        return 0

    if args.command == "plan":
        case_path = resolve_case_path(repo_root, args.case)
        success = run_plan_step(repo_root, case_path, runner_name=args.runner)
        if success:
            print(f"Research plan written to {case_path.name}/plan.md")
        else:
            print(f"Planning step did not produce a plan for {case_path.name}")
            return 1
        return 0

    if args.command == "gsc":
        import sys
        from .google_api import gsc_query, GoogleApiError, GoogleAuthError

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

    if args.command == "source":
        import sys

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
            action = (
                enable_bundle if args.source_command == "enable" else disable_bundle
            )
            for line in action(repo_root, args.name):
                print(f"- {line}")
        except (BundleError, ValueError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    return 1


def _entry() -> None:
    import sys

    sys.exit(main())
