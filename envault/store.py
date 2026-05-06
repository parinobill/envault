"""Vault store: read/write encrypted .env.vault files per project."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import decrypt, encrypt

DEFAULT_VAULT_FILENAME = ".env.vault"


def _vault_path(directory: str | Path, filename: str = DEFAULT_VAULT_FILENAME) -> Path:
    return Path(directory) / filename


def save_secrets(
    secrets: Dict[str, str],
    passphrase: str,
    directory: str | Path = ".",
    filename: str = DEFAULT_VAULT_FILENAME,
) -> Path:
    """Encrypt *secrets* dict and write to vault file. Returns the vault path."""
    if not secrets:
        raise ValueError("secrets dict must not be empty")
    plaintext = json.dumps(secrets).encode()
    blob = encrypt(plaintext, passphrase)
    path = _vault_path(directory, filename)
    path.write_bytes(blob)
    return path


def load_secrets(
    passphrase: str,
    directory: str | Path = ".",
    filename: str = DEFAULT_VAULT_FILENAME,
) -> Dict[str, str]:
    """Read vault file and decrypt, returning the secrets dict."""
    path = _vault_path(directory, filename)
    if not path.exists():
        raise FileNotFoundError(f"Vault file not found: {path}")
    blob = path.read_bytes()
    plaintext = decrypt(blob, passphrase)
    return json.loads(plaintext.decode())


def list_keys(
    passphrase: str,
    directory: str | Path = ".",
    filename: str = DEFAULT_VAULT_FILENAME,
) -> list[str]:
    """Return sorted list of secret keys stored in the vault."""
    return sorted(load_secrets(passphrase, directory, filename).keys())


def vault_exists(
    directory: str | Path = ".",
    filename: str = DEFAULT_VAULT_FILENAME,
) -> bool:
    """Return True if a vault file exists in *directory*."""
    return _vault_path(directory, filename).exists()
