"""CLI sub-command: render a template file using vault secrets."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.store import load_secrets
from envault.template import TemplateError, render_template_file


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_template(args: argparse.Namespace) -> None:
    passphrase = _prompt_passphrase()
    try:
        secrets = load_secrets(args.project, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load vault — {exc}", file=sys.stderr)
        sys.exit(1)

    template_path = Path(args.template)
    output_path = Path(args.output)

    try:
        result = render_template_file(
            template_path,
            output_path,
            secrets,
            strict=args.strict,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendered {template_path} -> {output_path}")
    if result.resolved:
        print(f"  Substituted: {', '.join(sorted(result.resolved))}")
    if result.missing:
        print(f"  Missing keys (left as-is): {', '.join(sorted(result.missing))}")


def register_template_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "template",
        help="render a template file by substituting vault secrets",
    )
    p.add_argument("template", help="path to the template file")
    p.add_argument("output", help="path to write the rendered output")
    p.add_argument(
        "--project", "-p", default="default", help="vault project name"
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="fail if any placeholder has no matching secret",
    )
    p.set_defaults(func=cmd_template)
