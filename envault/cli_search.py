"""CLI sub-command: envault search."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault.search import SearchError, format_results, search_secrets


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_search(args: argparse.Namespace) -> None:
    if args.pattern is None and args.tag is None:
        print("error: provide --pattern and/or --tag", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase()

    try:
        results = search_secrets(
            args.base_dir,
            args.project,
            passphrase,
            pattern=args.pattern,
            tag=args.tag,
        )
    except SearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(format_results(results, show_values=args.show_values))


def register_search_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("search", help="Search secrets by key pattern or tag")
    p.add_argument("-p", "--project", default="default", help="Project name")
    p.add_argument("-b", "--base-dir", default=".envault", dest="base_dir")
    p.add_argument("--pattern", default=None, help="Glob pattern for key names")
    p.add_argument("--tag", default=None, help="Filter by tag")
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Include secret values in output",
    )
    p.set_defaults(func=cmd_search)
