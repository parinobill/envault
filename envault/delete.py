"""Delete one or more secrets from the vault."""

from __future__ import annotations

from typing import List

from envault.store import load_secrets, save_secrets, vault_exists


class DeleteError(Exception):
    """Raised when a delete operation fails."""


def delete_secret(
    key: str,
    passphrase: str,
    project: str = "default",
    base_dir: str | None = None,
) -> None:
    """Remove *key* from the vault for *project*.

    Raises
    ------
    DeleteError
        If the vault does not exist or *key* is not present.
    """
    if not vault_exists(project=project, base_dir=base_dir):
        raise DeleteError(f"No vault found for project '{project}'.")

    secrets = load_secrets(passphrase=passphrase, project=project, base_dir=base_dir)

    if key not in secrets:
        raise DeleteError(f"Key '{key}' not found in vault for project '{project}'.")

    del secrets[key]
    save_secrets(secrets, passphrase=passphrase, project=project, base_dir=base_dir)


def delete_secrets(
    keys: List[str],
    passphrase: str,
    project: str = "default",
    base_dir: str | None = None,
) -> int:
    """Remove multiple *keys* from the vault in a single operation.

    Returns the number of keys actually deleted.  Keys that do not exist
    are silently skipped.

    Raises
    ------
    DeleteError
        If the vault does not exist.
    """
    if not vault_exists(project=project, base_dir=base_dir):
        raise DeleteError(f"No vault found for project '{project}'.")

    secrets = load_secrets(passphrase=passphrase, project=project, base_dir=base_dir)

    removed = 0
    for key in keys:
        if key in secrets:
            del secrets[key]
            removed += 1

    if removed:
        save_secrets(secrets, passphrase=passphrase, project=project, base_dir=base_dir)

    return removed
