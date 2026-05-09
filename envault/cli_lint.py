"""CLI sub-command: envault lint."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault.store import load_secrets, vault_exists
from envault.lint import lint_secrets, format_lint_result


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_lint(args: argparse.Namespace) -> None:
    project: str = args.project

    if not vault_exists(project):
        print(f"[error] No vault found for project '{project}'.", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase(f"Passphrase for '{project}': ")

    try:
        secrets = load_secrets(project, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] Could not decrypt vault: {exc}", file=sys.stderr)
        sys.exit(1)

    min_length: int = args.min_length
    no_key_check: bool = args.no_key_convention

    result = lint_secrets(
        secrets,
        min_length=min_length,
        enforce_key_convention=not no_key_check,
    )

    print(format_lint_result(result))

    if result.has_errors:
        sys.exit(2)
    elif result.has_warnings:
        sys.exit(1)


def register_lint_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("lint", help="Lint secrets in the vault")
    p.add_argument("-p", "--project", default="default", help="Project name")
    p.add_argument(
        "--min-length",
        type=int,
        default=8,
        dest="min_length",
        help="Minimum value length (default: 8)",
    )
    p.add_argument(
        "--no-key-convention",
        action="store_true",
        default=False,
        help="Disable UPPER_SNAKE_CASE key-naming check",
    )
    p.set_defaults(func=cmd_lint)
