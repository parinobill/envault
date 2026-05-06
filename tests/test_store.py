"""Tests for envault.store — vault file persistence."""

from __future__ import annotations

import pytest

from envault.store import (
    DEFAULT_VAULT_FILENAME,
    list_keys,
    load_secrets,
    save_secrets,
    vault_exists,
)

PASS = "hunter2"
SECRETS = {"DB_HOST": "localhost", "DB_PASS": "s3cr3t", "API_KEY": "abc123"}


def test_save_creates_file(tmp_path):
    path = save_secrets(SECRETS, PASS, tmp_path)
    assert path.exists()
    assert path.name == DEFAULT_VAULT_FILENAME


def test_vault_exists(tmp_path):
    assert not vault_exists(tmp_path)
    save_secrets(SECRETS, PASS, tmp_path)
    assert vault_exists(tmp_path)


def test_roundtrip(tmp_path):
    save_secrets(SECRETS, PASS, tmp_path)
    loaded = load_secrets(PASS, tmp_path)
    assert loaded == SECRETS


def test_list_keys(tmp_path):
    save_secrets(SECRETS, PASS, tmp_path)
    keys = list_keys(PASS, tmp_path)
    assert keys == sorted(SECRETS.keys())


def test_wrong_passphrase_raises(tmp_path):
    save_secrets(SECRETS, PASS, tmp_path)
    with pytest.raises(Exception):
        load_secrets("wrongpassword", tmp_path)


def test_load_missing_vault_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_secrets(PASS, tmp_path)


def test_save_empty_secrets_raises(tmp_path):
    with pytest.raises(ValueError):
        save_secrets({}, PASS, tmp_path)


def test_custom_filename(tmp_path):
    path = save_secrets(SECRETS, PASS, tmp_path, filename=".env.prod.vault")
    assert path.name == ".env.prod.vault"
    loaded = load_secrets(PASS, tmp_path, filename=".env.prod.vault")
    assert loaded == SECRETS


def test_vault_file_is_binary_not_plaintext(tmp_path):
    path = save_secrets(SECRETS, PASS, tmp_path)
    raw = path.read_bytes()
    assert b"DB_PASS" not in raw
    assert b"s3cr3t" not in raw
