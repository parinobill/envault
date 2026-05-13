"""CLI commands for pinning and unpinning secrets."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.pin import PinError, list_pins, pin_secret, unpin_secret
from envault.store import DEFAULT_BASE_DIR  # type: ignore[attr-defined]


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_pin(args: argparse.Namespace) -> None:
    """Pin a secret key to a fixed value."""
    try:
        pin_secret(args.base_dir, args.project, args.key, args.value)
        print(f"Pinned '{args.key}' for project '{args.project}'.")
    except PinError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_unpin(args: argparse.Namespace) -> None:
    """Remove a pin from a secret key."""
    try:
        unpin_secret(args.base_dir, args.project, args.key)
        print(f"Unpinned '{args.key}' for project '{args.project}'.")
    except PinError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_pins(args: argparse.Namespace) -> None:
    """List all pinned keys for a project."""
    keys = list_pins(args.base_dir, args.project)
    if not keys:
        print(f"No pins set for project '{args.project}'.")
    else:
        print(f"Pinned keys for '{args.project}':")
        for key in keys:
            print(f"  {key}")


def register_pin_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    base_dir = DEFAULT_BASE_DIR

    pin_p = subparsers.add_parser("pin", help="Pin a secret to a fixed value")
    pin_p.add_argument("key", help="Secret key to pin")
    pin_p.add_argument("value", help="Value to pin the key to")
    pin_p.add_argument("--project", default="default", help="Project name")
    pin_p.add_argument("--base-dir", default=base_dir)
    pin_p.set_defaults(func=cmd_pin)

    unpin_p = subparsers.add_parser("unpin", help="Remove a pin from a secret key")
    unpin_p.add_argument("key", help="Secret key to unpin")
    unpin_p.add_argument("--project", default="default", help="Project name")
    unpin_p.add_argument("--base-dir", default=base_dir)
    unpin_p.set_defaults(func=cmd_unpin)

    pins_p = subparsers.add_parser("pins", help="List all pinned keys")
    pins_p.add_argument("--project", default="default", help="Project name")
    pins_p.add_argument("--base-dir", default=base_dir)
    pins_p.set_defaults(func=cmd_list_pins)
