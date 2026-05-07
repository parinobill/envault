"""CLI sub-command: envault export."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.export import ExportError, export_secrets
from envault.store import load_secrets, vault_exists


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the ``export`` sub-command."""
    if not vault_exists(args.project):
        print(f"[envault] No vault found for project '{args.project}'.", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase()

    try:
        secrets = load_secrets(args.project, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"[envault] Failed to decrypt vault: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        output = export_secrets(secrets, fmt=args.format)
    except ExportError as exc:
        print(f"[envault] {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"[envault] Exported {len(secrets)} secret(s) to '{args.output}' ({args.format}).")
    else:
        sys.stdout.write(output)


def register_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("export", help="Export secrets to dotenv / JSON / CSV")
    p.add_argument("-p", "--project", default="default", help="Project name")
    p.add_argument(
        "-f",
        "--format",
        choices=["dotenv", "json", "csv"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p.add_argument("-o", "--output", default="", help="Write output to this file (default: stdout)")
    p.set_defaults(func=cmd_export)
