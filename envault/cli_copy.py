"""CLI sub-command: envault copy <source> <dest> [options]."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.copy import CopyError, copy_secret


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:  # pragma: no cover
    return getpass.getpass(prompt)


def cmd_copy(args: argparse.Namespace) -> None:  # pragma: no cover
    """Handler for the ``copy`` sub-command."""
    passphrase = _prompt_passphrase()

    try:
        copy_secret(
            source_key=args.source,
            dest_key=args.dest,
            passphrase=passphrase,
            project=args.project,
            overwrite=args.overwrite,
        )
    except CopyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    action = "overwritten" if args.overwrite else "created"
    print(f"Copied '{args.source}' → '{args.dest}' ({action}).")


def register_copy_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the ``copy`` sub-command to *subparsers*."""
    parser = subparsers.add_parser(
        "copy",
        help="Copy a secret to a new key within the same vault.",
    )
    parser.add_argument("source", help="Existing key to copy from.")
    parser.add_argument("dest", help="New key to copy to.")
    parser.add_argument(
        "--project",
        default="default",
        help="Project name (default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite destination key if it already exists.",
    )
    parser.set_defaults(func=cmd_copy)
