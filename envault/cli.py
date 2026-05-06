"""Command-line interface for envault."""

import sys
import getpass
import argparse

from envault.store import save_secrets, load_secrets, list_keys, vault_exists
from envault.dotenv_io import read_dotenv_file, write_dotenv_file


def cmd_init(args):
    """Initialize a new vault for the current project."""
    if vault_exists(args.project):
        print(f"Vault '{args.project}' already exists.")
        sys.exit(1)
    passphrase = _prompt_new_passphrase()
    save_secrets(args.project, {}, passphrase)
    print(f"Vault '{args.project}' initialized.")


def cmd_push(args):
    """Encrypt and push a .env file into the vault."""
    secrets = read_dotenv_file(args.env_file)
    passphrase = _prompt_passphrase()
    save_secrets(args.project, secrets, passphrase)
    print(f"Pushed {len(secrets)} secret(s) to vault '{args.project}'.")


def cmd_pull(args):
    """Decrypt and write secrets from the vault to a .env file."""
    passphrase = _prompt_passphrase()
    try:
        secrets = load_secrets(args.project, passphrase)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    write_dotenv_file(args.env_file, secrets)
    print(f"Pulled {len(secrets)} secret(s) to '{args.env_file}'.")


def cmd_list(args):
    """List keys stored in the vault without revealing values."""
    passphrase = _prompt_passphrase()
    try:
        keys = list_keys(args.project, passphrase)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if keys:
        print("\n".join(keys))
    else:
        print("(no secrets stored)")


def _prompt_passphrase():
    return getpass.getpass("Passphrase: ")


def _prompt_new_passphrase():
    pw = getpass.getpass("New passphrase: ")
    confirm = getpass.getpass("Confirm passphrase: ")
    if pw != confirm:
        print("Passphrases do not match.", file=sys.stderr)
        sys.exit(1)
    return pw


def build_parser():
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight .env file manager with per-project secret encryption.",
    )
    parser.add_argument("-p", "--project", default="default", help="Vault project name")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize a new vault")

    push_p = sub.add_parser("push", help="Push a .env file into the vault")
    push_p.add_argument("env_file", nargs="?", default=".env", help="Path to .env file")

    pull_p = sub.add_parser("pull", help="Pull secrets from the vault to a .env file")
    pull_p.add_argument("env_file", nargs="?", default=".env", help="Path to .env file")

    sub.add_parser("list", help="List secret keys in the vault")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"init": cmd_init, "push": cmd_push, "pull": cmd_pull, "list": cmd_list}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
