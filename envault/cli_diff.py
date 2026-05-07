"""CLI subcommand: envault diff — compare local .env against the vault."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.diff import diff_secrets, format_diff, has_changes
from envault.dotenv_io import read_dotenv_file
from envault.store import load_secrets, vault_exists


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_diff(args: argparse.Namespace) -> None:
    project: str = args.project
    env_file: str = args.env_file
    show_values: bool = args.show_values

    if not vault_exists(project):
        print(f"[envault] No vault found for project '{project}'.", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase()

    try:
        vault_secrets = load_secrets(project, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"[envault] Failed to load vault: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        local_secrets = read_dotenv_file(env_file)
    except FileNotFoundError:
        print(f"[envault] Local file '{env_file}' not found.", file=sys.stderr)
        sys.exit(1)

    entries = diff_secrets(local_secrets, vault_secrets)

    if not has_changes(entries):
        print("[envault] Local file is in sync with vault.")
        return

    print(f"[envault] Diff for project '{project}' ({env_file} vs vault):")
    print(format_diff(entries, show_values=show_values))


def register_diff_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Show differences between local .env and vault")
    p.add_argument("--project", "-p", default="default", help="Project name")
    p.add_argument("--env-file", "-e", default=".env", help="Local .env file path")
    p.add_argument(
        "--show-values",
        action="store_true",
        default=False,
        help="Show old/new values for changed keys",
    )
    p.set_defaults(func=cmd_diff)
