"""CLI sub-command: envault watch — monitor a .env file and auto-push changes."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.watch import WatchEvent, WatchError, watch


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_watch(args: argparse.Namespace) -> None:  # pragma: no cover
    passphrase = _prompt_passphrase()

    env_file = Path(args.env_file)
    if not env_file.exists():
        print(f"error: file not found: {env_file}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Watching {env_file} for project '{args.project}' "
        f"(interval: {args.interval}s) — Ctrl-C to stop"
    )

    def on_change(event: WatchEvent) -> None:
        keys = ", ".join(event.changed_keys)
        print(f"[{_ts(event.timestamp)}] pushed {len(event.changed_keys)} change(s): {keys}")

    try:
        watch(
            env_file=env_file,
            project=args.project,
            passphrase=passphrase,
            interval=args.interval,
            on_change=on_change,
        )
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nWatch stopped.")


def _ts(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")


def register_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "watch",
        help="Monitor a .env file and auto-push changes to the vault.",
    )
    p.add_argument(
        "--project", "-p",
        default="default",
        help="Project name (default: default).",
    )
    p.add_argument(
        "--env-file", "-e",
        default=".env",
        dest="env_file",
        help="Path to the .env file to watch (default: .env).",
    )
    p.add_argument(
        "--interval", "-i",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0).",
    )
    p.set_defaults(func=cmd_watch)
