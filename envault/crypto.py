"""Encryption and decryption utilities for envault secrets.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
derived from a user-supplied passphrase via PBKDF2.
"""

import base64
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
ITERATIONS = 390_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet-compatible key from *passphrase* and *salt*."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = kdf.derive(passphrase.encode())
    return base64.urlsafe_b64encode(raw_key)


def encrypt(plaintext: str, passphrase: str) -> bytes:
    """Encrypt *plaintext* with *passphrase*.

    Returns a blob of the form: ``<16-byte salt><fernet token>``.
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(passphrase, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    return salt + token


def decrypt(blob: bytes, passphrase: str) -> str:
    """Decrypt a blob produced by :func:`encrypt`.

    Raises
    ------
    ValueError
        If the passphrase is wrong or the blob is corrupted.
    """
    if len(blob) <= SALT_SIZE:
        raise ValueError("Invalid encrypted blob: too short.")
    salt, token = blob[:SALT_SIZE], blob[SALT_SIZE:]
    key = _derive_key(passphrase, salt)
    try:
        return Fernet(key).decrypt(token).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed: wrong passphrase or corrupted data.") from exc
