"""Tests for envault.crypto encryption/decryption."""

import pytest
from envault.crypto import encrypt, decrypt, SALT_SIZE


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/mydb"


def test_encrypt_returns_bytes():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(blob, bytes)


def test_blob_longer_than_salt():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    assert len(blob) > SALT_SIZE


def test_roundtrip():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    recovered = decrypt(blob, PASSPHRASE)
    assert recovered == PLAINTEXT


def test_different_salts_each_call():
    blob1 = encrypt(PLAINTEXT, PASSPHRASE)
    blob2 = encrypt(PLAINTEXT, PASSPHRASE)
    # Salts should differ (random), producing different ciphertexts
    assert blob1 != blob2


def test_wrong_passphrase_raises():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(blob, "wrong-passphrase")


def test_corrupted_blob_raises():
    blob = bytearray(encrypt(PLAINTEXT, PASSPHRASE))
    blob[SALT_SIZE + 5] ^= 0xFF  # flip a bit inside the Fernet token
    with pytest.raises(ValueError):
        decrypt(bytes(blob), PASSPHRASE)


def test_too_short_blob_raises():
    with pytest.raises(ValueError, match="too short"):
        decrypt(b"short", PASSPHRASE)


def test_empty_string_roundtrip():
    blob = encrypt("", PASSPHRASE)
    assert decrypt(blob, PASSPHRASE) == ""


def test_unicode_plaintext_roundtrip():
    secret = "API_KEY=\u00e9\u00e0\u00fc\u4e2d\u6587"
    blob = encrypt(secret, PASSPHRASE)
    assert decrypt(blob, PASSPHRASE) == secret
