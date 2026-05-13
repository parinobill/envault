"""CLI sub-command: merge secrets from one project into another."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.merge import MergeError, merge_secrets


def _prompt_passphrase(prompt: str) -> str:
    return getpass.getpass(prompt)


def cmd_merge(args: argparse.Namespace) -> None:
    src_pass = _prompt_passphrase(f"Passphrase for source project '{args.src}': ")
    if args.src == args.dst:
        dst_pass = src_pass
    else:
        dst_pass = _prompt_passphrase(f"Passphrase for destination project '{args.dst}': ")

    keys = args.keys if args.keys else None

    try:
        result = merge_secrets(
            src_project=args.src,
            dst_project=args.dst,
            src_passphrase=src_pass,
            dst_passphrase=dst_pass,
            overwrite=args.overwrite,
            keys=keys,
        )
    except MergeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.added:
        print(f"Added    ({len(result.added)}): {', '.join(sorted(result.added))}")
    if result.overwritten:
        print(f"Overwrote ({len(result.overwritten)}): {', '.join(sorted(result.overwritten))}")
    if result.skipped:
        print(f"Skipped  ({len(result.skipped)}): {', '.join(sorted(result.skipped))}")

    if result.total_changed == 0:
        print("Nothing changed.")
    else:
        print(f"Merge complete: {result.total_changed} secret(s) written to '{args.dst}'.")


def register_merge_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "merge",
        help="Merge secrets from one project vault into another.",
    )
    p.add_argument("src", help="Source project name.")
    p.add_argument("dst", help="Destination project name.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=[],
        help="Specific keys to merge (default: all).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in the destination vault.",
    )
    p.set_defaults(func=cmd_merge)
