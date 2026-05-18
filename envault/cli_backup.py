"""CLI sub-commands for vault backup and restore."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.backup import BackupError, create_backup, list_backups, restore_backup


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_backup(args: argparse.Namespace) -> None:
    passphrase = _prompt_passphrase()
    base = Path(args.base)
    try:
        path = create_backup(base, args.project, passphrase, label=args.label)
        print(f"Backup created: {path}")
    except BackupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_restore(args: argparse.Namespace) -> None:
    passphrase = _prompt_passphrase("New passphrase for restored vault: ")
    base = Path(args.base)
    backup_path = Path(args.file)
    try:
        count = restore_backup(base, args.project, backup_path, passphrase)
        print(f"Restored {count} secret(s) into project '{args.project}'.")
    except BackupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_backups(args: argparse.Namespace) -> None:
    base = Path(args.base)
    backups = list_backups(base, args.project)
    if not backups:
        print(f"No backups found for project '{args.project}'.")
        return
    for p in backups:
        print(p)


def register_backup_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("backup", help="Backup and restore vault secrets")
    p.add_argument("--project", default="default", help="Project name")
    p.add_argument("--base", default=".envault", help="Vault base directory")

    sub = p.add_subparsers(dest="backup_cmd", required=True)

    create_p = sub.add_parser("create", help="Create a backup")
    create_p.add_argument("--label", default=None, help="Optional label suffix")
    create_p.set_defaults(func=cmd_backup)

    restore_p = sub.add_parser("restore", help="Restore from a backup file")
    restore_p.add_argument("file", help="Path to backup JSON file")
    restore_p.set_defaults(func=cmd_restore)

    list_p = sub.add_parser("list", help="List available backups")
    list_p.set_defaults(func=cmd_list_backups)
