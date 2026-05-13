"""CLI sub-command: delete — remove one or more secrets from the vault."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.delete import DeleteError, delete_secrets


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_delete(args: argparse.Namespace) -> None:
    """Handle the *delete* sub-command."""
    passphrase = _prompt_passphrase()

    try:
        removed = delete_secrets(
            keys=args.keys,
            passphrase=passphrase,
            project=args.project,
        )
    except DeleteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if removed == 0:
        print("No matching keys found; vault unchanged.")
    elif removed == 1:
        print(f"Deleted 1 secret from project '{args.project}'.")
    else:
        print(f"Deleted {removed} secrets from project '{args.project}'.")


def register_delete_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *delete* sub-command to *subparsers*."""
    parser = subparsers.add_parser(
        "delete",
        help="Remove one or more secrets from the vault.",
    )
    parser.add_argument(
        "keys",
        nargs="+",
        metavar="KEY",
        help="Secret key(s) to delete.",
    )
    parser.add_argument(
        "--project",
        default="default",
        help="Project name (default: default).",
    )
    parser.set_defaults(func=cmd_delete)
