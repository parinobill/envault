"""Copy a secret from one key to another within the same vault."""

from __future__ import annotations

from envault.store import load_secrets, save_secrets


class CopyError(Exception):
    """Raised when a copy operation cannot be completed."""


def copy_secret(
    source_key: str,
    dest_key: str,
    passphrase: str,
    project: str = "default",
    *,
    overwrite: bool = False,
) -> None:
    """Copy the value of *source_key* to *dest_key* in *project*'s vault.

    Parameters
    ----------
    source_key:
        The existing key whose value should be copied.
    dest_key:
        The key that will receive the copied value.
    passphrase:
        Vault passphrase used for decryption and re-encryption.
    project:
        Project name (default: ``"default"``).
    overwrite:
        When ``False`` (the default) raise :class:`CopyError` if *dest_key*
        already exists.  Set to ``True`` to silently replace it.

    Raises
    ------
    CopyError
        If *source_key* is missing, *dest_key* already exists and
        *overwrite* is ``False``, or *source_key* and *dest_key* are equal.
    """
    if source_key == dest_key:
        raise CopyError(f"Source and destination keys are identical: '{source_key}'")

    secrets = load_secrets(passphrase, project=project)

    if source_key not in secrets:
        raise CopyError(f"Source key not found: '{source_key}'")

    if dest_key in secrets and not overwrite:
        raise CopyError(
            f"Destination key '{dest_key}' already exists. "
            "Use overwrite=True to replace it."
        )

    secrets[dest_key] = secrets[source_key]
    save_secrets(secrets, passphrase, project=project)
