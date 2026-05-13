"""Rename a secret key inside a vault without changing its value."""

from __future__ import annotations

from envault.store import load_secrets, save_secrets, vault_exists


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_secret(
    old_key: str,
    new_key: str,
    passphrase: str,
    project: str = "default",
    base_dir: str | None = None,
) -> None:
    """Rename *old_key* to *new_key* in the vault for *project*.

    Raises
    ------
    RenameError
        If the vault does not exist, *old_key* is not found, or *new_key*
        already exists.
    """
    if not vault_exists(project=project, base_dir=base_dir):
        raise RenameError(f"No vault found for project '{project}'.")

    secrets = load_secrets(passphrase=passphrase, project=project, base_dir=base_dir)

    if old_key not in secrets:
        raise RenameError(f"Key '{old_key}' does not exist in the vault.")

    if new_key in secrets:
        raise RenameError(
            f"Key '{new_key}' already exists in the vault. "
            "Remove it first or choose a different name."
        )

    if not new_key or not new_key.isidentifier():
        raise RenameError(
            f"'{new_key}' is not a valid key name. "
            "Keys must be non-empty valid Python identifiers."
        )

    value = secrets.pop(old_key)
    secrets[new_key] = value

    save_secrets(secrets, passphrase=passphrase, project=project, base_dir=base_dir)
