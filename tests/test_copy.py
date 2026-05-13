"""Unit tests for envault.copy."""

from __future__ import annotations

import pytest

from envault.copy import CopyError, copy_secret
from envault.store import load_secrets, save_secrets


@pytest.fixture()
def vault_base(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def populated_vault(vault_base):
    secrets = {"API_KEY": "abc123", "DB_PASS": "secret"}
    save_secrets(secrets, "hunter2", project="myapp")
    return secrets


def test_copy_creates_dest_key(populated_vault, vault_base):
    copy_secret("API_KEY", "API_KEY_BACKUP", "hunter2", project="myapp")
    result = load_secrets("hunter2", project="myapp")
    assert result["API_KEY_BACKUP"] == "abc123"


def test_copy_preserves_source_key(populated_vault, vault_base):
    copy_secret("API_KEY", "API_KEY_BACKUP", "hunter2", project="myapp")
    result = load_secrets("hunter2", project="myapp")
    assert result["API_KEY"] == "abc123"


def test_copy_preserves_other_keys(populated_vault, vault_base):
    copy_secret("API_KEY", "API_KEY_BACKUP", "hunter2", project="myapp")
    result = load_secrets("hunter2", project="myapp")
    assert result["DB_PASS"] == "secret"


def test_copy_missing_source_raises(populated_vault, vault_base):
    with pytest.raises(CopyError, match="Source key not found"):
        copy_secret("MISSING", "NEW_KEY", "hunter2", project="myapp")


def test_copy_same_key_raises(populated_vault, vault_base):
    with pytest.raises(CopyError, match="identical"):
        copy_secret("API_KEY", "API_KEY", "hunter2", project="myapp")


def test_copy_existing_dest_raises_without_overwrite(populated_vault, vault_base):
    with pytest.raises(CopyError, match="already exists"):
        copy_secret("API_KEY", "DB_PASS", "hunter2", project="myapp")


def test_copy_existing_dest_succeeds_with_overwrite(populated_vault, vault_base):
    copy_secret("API_KEY", "DB_PASS", "hunter2", project="myapp", overwrite=True)
    result = load_secrets("hunter2", project="myapp")
    assert result["DB_PASS"] == "abc123"


def test_copy_wrong_passphrase_raises(populated_vault, vault_base):
    with pytest.raises(Exception):
        copy_secret("API_KEY", "API_KEY_BACKUP", "wrongpass", project="myapp")
