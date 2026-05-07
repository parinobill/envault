"""CLI sub-command: envault rotate — interactive passphrase rotation."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from envault.rotate import rotate_passphrase, RotationError


def cmd_rotate(args) -> None:  # pragma: no cover — thin I/O wrapper
    """Handle the ``rotate`` sub-command."""
    project: str = args.project
    base_dir: Path | None = getattr(args, "base_dir", None)

    print(f"Rotating passphrase for project '{project}'.")

    old_passphrase = _prompt_passphrase("Current passphrase: ")
    new_passphrase = _prompt_passphrase("New passphrase: ")
    confirm = _prompt_passphrase("Confirm new passphrase: ")

    if new_passphrase != confirm:
        print("Error: new passphrases do not match.", file=sys.stderr)
        sys.exit(1)

    try:
        count = rotate_passphrase(
            old_passphrase,
            new_passphrase,
            project=project,
            base_dir=base_dir,
        )
    except RotationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Success — {count} secret(s) re-encrypted under the new passphrase.")


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:  # pragma: no cover
    """Read a passphrase from the terminal without echoing."""
    value = getpass.getpass(prompt)
    if not value:
        print("Error: passphrase must not be empty.", file=sys.stderr)
        sys.exit(1)
    return value


def register_rotate_parser(subparsers) -> None:
    """Attach the *rotate* sub-command to an existing subparsers action."""
    p = subparsers.add_parser(
        "rotate",
        help="Re-encrypt vault secrets under a new passphrase.",
    )
    p.add_argument(
        "--project",
        default="default",
        metavar="NAME",
        help="Project name (default: 'default').",
    )
    p.set_defaults(func=cmd_rotate)
