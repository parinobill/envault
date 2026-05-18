"""CLI sub-commands for per-key access control."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.access import AccessError, grant, is_allowed, load_acl, revoke

_DEFAULT_BASE = Path.home() / ".envault"


def cmd_grant(args: argparse.Namespace) -> None:
    base = Path(args.base) if hasattr(args, "base") and args.base else _DEFAULT_BASE
    try:
        grant(base, args.project, args.key, args.identity)
        print(f"Granted '{args.identity}' access to '{args.key}' in project '{args.project}'.")
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_revoke(args: argparse.Namespace) -> None:
    base = Path(args.base) if hasattr(args, "base") and args.base else _DEFAULT_BASE
    try:
        revoke(base, args.project, args.key, args.identity)
        print(f"Revoked '{args.identity}' access to '{args.key}' in project '{args.project}'.")
    except AccessError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_acl(args: argparse.Namespace) -> None:
    base = Path(args.base) if hasattr(args, "base") and args.base else _DEFAULT_BASE
    acl = load_acl(base, args.project)
    if not acl:
        print("No access restrictions defined.")
        return
    for key, identities in sorted(acl.items()):
        if identities:
            print(f"{key}: {', '.join(sorted(identities))}")
        else:
            print(f"{key}: (open)")


def cmd_check(args: argparse.Namespace) -> None:
    base = Path(args.base) if hasattr(args, "base") and args.base else _DEFAULT_BASE
    allowed = is_allowed(base, args.project, args.key, args.identity)
    status = "ALLOWED" if allowed else "DENIED"
    print(f"{args.identity} -> {args.key}: {status}")
    if not allowed:
        sys.exit(1)


def register_access_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    access_p = subparsers.add_parser("access", help="Manage per-key access control.")
    access_p.add_argument("--project", "-p", default="default")
    access_sub = access_p.add_subparsers(dest="access_cmd", required=True)

    # grant
    g = access_sub.add_parser("grant", help="Grant an identity access to a key.")
    g.add_argument("key")
    g.add_argument("identity")
    g.set_defaults(func=cmd_grant)

    # revoke
    r = access_sub.add_parser("revoke", help="Revoke an identity's access to a key.")
    r.add_argument("key")
    r.add_argument("identity")
    r.set_defaults(func=cmd_revoke)

    # list
    ls = access_sub.add_parser("list", help="List all access restrictions for a project.")
    ls.set_defaults(func=cmd_list_acl)

    # check
    ck = access_sub.add_parser("check", help="Check whether an identity can access a key.")
    ck.add_argument("key")
    ck.add_argument("identity")
    ck.set_defaults(func=cmd_check)
