"""CLI subcommand: envault history — show secret push/rotation history."""

from __future__ import annotations

import argparse
import os
import sys

from envault.history import format_history, read_history, history_exists

DEFAULT_BASE = os.path.expanduser("~/.envault")


def cmd_history(args: argparse.Namespace) -> None:
    """Display the history log for a project vault."""
    base_dir = getattr(args, "base_dir", DEFAULT_BASE)
    project: str = args.project
    limit: int = args.limit

    if not history_exists(base_dir, project):
        print(f"No history found for project '{project}'.")
        sys.exit(0)

    entries = read_history(base_dir, project)

    if limit > 0:
        entries = entries[-limit:]

    print(f"History for project '{project}' ({len(entries)} entries shown):\n")
    print(format_history(entries))


def register_history_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'history' subcommand with the given subparsers."""
    parser = subparsers.add_parser(
        "history",
        help="Show push/rotation history for a project vault.",
    )
    parser.add_argument(
        "-p",
        "--project",
        default="default",
        help="Project name (default: 'default').",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries (0 = all).",
    )
    parser.set_defaults(func=cmd_history)
