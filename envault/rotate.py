"""Passphrase rotation for envault vaults.

Allows re-encrypting all secrets in a vault under a new passphrase
without exposing plaintext secrets to disk.
"""

from __future__ import annotations

from pathlib import Path

from envault.store import load_secrets, save_secrets, vault_exists, _vault_path
from envault.audit import record_event


class RotationError(Exception):
    """Raised when passphrase rotation fails."""


def rotate_passphrase(
    old_passphrase: str,
    new_passphrase: str,
    project: str = "default",
    base_dir: Path | None = None,
) -> int:
    """Re-encrypt vault secrets under *new_passphrase*.

    Parameters
    ----------
    old_passphrase:
        The current passphrase used to decrypt the vault.
    new_passphrase:
        The replacement passphrase to encrypt the vault with.
    project:
        Project name whose vault should be rotated.
    base_dir:
        Override the base directory (used in tests).

    Returns
    -------
    int
        Number of secrets that were re-encrypted.

    Raises
    ------
    RotationError
        If the vault does not exist or decryption with the old passphrase fails.
    """
    if not vault_exists(project, base_dir=base_dir):
        raise RotationError(f"No vault found for project '{project}'.")

    if old_passphrase == new_passphrase:
        raise RotationError("New passphrase must differ from the old passphrase.")

    try:
        secrets = load_secrets(old_passphrase, project=project, base_dir=base_dir)
    except Exception as exc:
        raise RotationError(f"Failed to decrypt vault: {exc}") from exc

    save_secrets(secrets, new_passphrase, project=project, base_dir=base_dir)

    record_event(
        "rotate",
        project=project,
        detail=f"rotated {len(secrets)} secret(s)",
        base_dir=base_dir,
    )

    return len(secrets)
