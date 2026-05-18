"""CLI subcommands for secret expiry management."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.expire import (
    ExpireError,
    format_expiry,
    get_expired_keys,
    load_expiry,
    remove_expiry,
    set_expiry,
)
from envault.store import load_secrets, save_secrets

_DEFAULT_BASE = Path.home() / ".envault"


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_set_expiry(args: argparse.Namespace) -> None:
    base = Path(args.base_dir)
    passphrase = _prompt_passphrase()
    try:
        load_secrets(base, args.project, passphrase)  # validate passphrase
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    entry = set_expiry(base, args.project, args.key, args.ttl, args.note or "")
    print(f"Expiry set for '{args.key}': expires in {args.ttl:.0f}s")


def cmd_remove_expiry(args: argparse.Namespace) -> None:
    base = Path(args.base_dir)
    remove_expiry(base, args.project, args.key)
    print(f"Expiry rule removed for '{args.key}'.")


def cmd_list_expiry(args: argparse.Namespace) -> None:
    base = Path(args.base_dir)
    entries = load_expiry(base, args.project)
    print(format_expiry(entries))


def cmd_purge_expired(args: argparse.Namespace) -> None:
    """Delete secrets from the vault that have passed their TTL."""
    base = Path(args.base_dir)
    passphrase = _prompt_passphrase()
    try:
        secrets = load_secrets(base, args.project, passphrase)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    expired = get_expired_keys(base, args.project)
    if not expired:
        print("No expired secrets found.")
        return
    for key in expired:
        secrets.pop(key, None)
        remove_expiry(base, args.project, key)
    save_secrets(base, args.project, passphrase, secrets)
    print(f"Purged {len(expired)} expired secret(s): {', '.join(expired)}")


def register_expire_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("expire", help="Manage secret expiry / TTL")
    p.add_argument("--project", default="default")
    p.add_argument("--base-dir", default=str(_DEFAULT_BASE))
    sub = p.add_subparsers(dest="expire_cmd", required=True)

    ps = sub.add_parser("set", help="Set TTL for a secret")
    ps.add_argument("key")
    ps.add_argument("ttl", type=float, help="Seconds until expiry")
    ps.add_argument("--note", default="")
    ps.set_defaults(func=cmd_set_expiry)

    pr = sub.add_parser("remove", help="Remove expiry rule")
    pr.add_argument("key")
    pr.set_defaults(func=cmd_remove_expiry)

    pl = sub.add_parser("list", help="List expiry rules")
    pl.set_defaults(func=cmd_list_expiry)

    pp = sub.add_parser("purge", help="Delete expired secrets from vault")
    pp.set_defaults(func=cmd_purge_expired)
