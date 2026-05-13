"""CLI sub-command: envault rename <old_key> <new_key>"""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.rename import RenameError, rename_secret


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_rename(args: argparse.Namespace) -> None:
    passphrase = _prompt_passphrase()

    try:
        rename_secret(
            old_key=args.old_key,
            new_key=args.new_key,
            passphrase=passphrase,
            project=args.project,
        )
    except RenameError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Renamed '{args.old_key}' -> '{args.new_key}' in project '{args.project}'.")


def register_rename_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "rename",
        help="Rename a secret key inside the vault.",
    )
    parser.add_argument(
        "old_key",
        help="Existing key name.",
    )
    parser.add_argument(
        "new_key",
        help="New key name.",
    )
    parser.add_argument(
        "--project",
        default="default",
        help="Project name (default: 'default').",
    )
    parser.set_defaults(func=cmd_rename)
