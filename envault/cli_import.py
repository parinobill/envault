"""CLI sub-command: envault import-env"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.import_env import import_secrets
from envault.import_env import ImportError as EnvImportError


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_import(args: argparse.Namespace) -> None:
    source = Path(args.file)
    if not source.exists():
        print(f"[error] File not found: {source}", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase("Vault passphrase: ")

    try:
        count = import_secrets(
            source,
            passphrase,
            fmt=args.format,
            project=args.project,
            merge=args.merge,
        )
    except EnvImportError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    action = "merged" if args.merge else "imported"
    print(f"[ok] {action} {count} secret(s) from '{source}' into project '{args.project}'.")


def register_import_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "import-env",
        help="Import secrets from a dotenv/JSON/CSV file into the vault",
    )
    p.add_argument(
        "file",
        help="Path to the source file",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json", "csv"],
        default="dotenv",
        help="Format of the source file (default: dotenv)",
    )
    p.add_argument(
        "--project",
        default="default",
        help="Project name (default: default)",
    )
    p.add_argument(
        "--merge",
        action="store_true",
        default=False,
        help="Merge with existing vault secrets instead of overwriting",
    )
    p.set_defaults(func=cmd_import)
