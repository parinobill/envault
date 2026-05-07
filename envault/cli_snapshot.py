"""CLI sub-command: envault snapshot — compare current vault to a past snapshot."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.store import load_secrets, vault_exists
from envault.snapshot import compare_to_snapshot, format_snapshot_result, SnapshotError


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_snapshot(args: argparse.Namespace) -> None:
    base_dir = args.base_dir if hasattr(args, "base_dir") else ".envault"
    project: str = args.project
    index: int = args.index

    if not vault_exists(base_dir, project):
        print(f"[envault] No vault found for project '{project}'.", file=sys.stderr)
        sys.exit(1)

    passphrase = _prompt_passphrase("Vault passphrase: ")

    try:
        secrets = load_secrets(base_dir, project, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"[envault] Failed to decrypt vault: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result = compare_to_snapshot(base_dir, project, secrets, snapshot_index=index)
    except SnapshotError as exc:
        print(f"[envault] {exc}", file=sys.stderr)
        sys.exit(1)

    print(format_snapshot_result(result))


def register_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "snapshot",
        help="Compare current vault secrets against a historical snapshot.",
    )
    p.add_argument(
        "--project", "-p",
        default="default",
        help="Project name (default: 'default').",
    )
    p.add_argument(
        "--index", "-i",
        type=int,
        default=-1,
        help="History index to compare against (default: -1, i.e. latest snapshot).",
    )
    p.set_defaults(func=cmd_snapshot)
