"""Clone all secrets from one project vault to another."""

from __future__ import annotations

from envault.store import load_secrets, save_secrets, vault_exists


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_project(
    src_project: str,
    dest_project: str,
    src_passphrase: str,
    dest_passphrase: str,
    *,
    base_dir: str | None = None,
    overwrite: bool = False,
) -> int:
    """Copy all secrets from *src_project* vault into *dest_project* vault.

    Parameters
    ----------
    src_project:      Name of the source project.
    dest_project:     Name of the destination project.
    src_passphrase:   Passphrase used to decrypt the source vault.
    dest_passphrase:  Passphrase used to encrypt the destination vault.
    base_dir:         Override the default vault base directory (testing).
    overwrite:        If *False* (default) raise :class:`CloneError` when the
                      destination vault already exists.

    Returns
    -------
    int
        Number of secrets written to the destination vault.
    """
    kwargs: dict = {} if base_dir is None else {"base_dir": base_dir}

    if not vault_exists(src_project, **kwargs):
        raise CloneError(f"Source vault '{src_project}' does not exist.")

    if vault_exists(dest_project, **kwargs) and not overwrite:
        raise CloneError(
            f"Destination vault '{dest_project}' already exists. "
            "Pass overwrite=True to replace it."
        )

    secrets = load_secrets(src_project, src_passphrase, **kwargs)

    if not secrets:
        raise CloneError(f"Source vault '{src_project}' contains no secrets.")

    save_secrets(dest_project, secrets, dest_passphrase, **kwargs)
    return len(secrets)
