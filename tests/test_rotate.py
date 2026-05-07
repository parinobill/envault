"""Tests for envault.rotate — passphrase rotation."""

from __future__ import annotations

import pytest

from envault.rotate import rotate_passphrase, RotationError
from envault.store import save_secrets, load_secrets, vault_exists


SECRETS = {"DB_URL": "postgres://localhost/mydb", "SECRET_KEY": "s3cr3t"}
OLD_PASS = "old-hunter2"
NEW_PASS = "new-hunter3"


@pytest.fixture()
def vault_base(tmp_path):
    save_secrets(SECRETS, OLD_PASS, project="default", base_dir=tmp_path)
    return tmp_path


def test_rotate_returns_secret_count(vault_base):
    count = rotate_passphrase(OLD_PASS, NEW_PASS, project="default", base_dir=vault_base)
    assert count == len(SECRETS)


def test_rotate_old_passphrase_no_longer_works(vault_base):
    rotate_passphrase(OLD_PASS, NEW_PASS, project="default", base_dir=vault_base)
    with pytest.raises(Exception):
        load_secrets(OLD_PASS, project="default", base_dir=vault_base)


def test_rotate_new_passphrase_decrypts_correctly(vault_base):
    rotate_passphrase(OLD_PASS, NEW_PASS, project="default", base_dir=vault_base)
    recovered = load_secrets(NEW_PASS, project="default", base_dir=vault_base)
    assert recovered == SECRETS


def test_rotate_preserves_all_keys(vault_base):
    rotate_passphrase(OLD_PASS, NEW_PASS, project="default", base_dir=vault_base)
    recovered = load_secrets(NEW_PASS, project="default", base_dir=vault_base)
    assert set(recovered.keys()) == set(SECRETS.keys())


def test_rotate_raises_if_vault_missing(tmp_path):
    with pytest.raises(RotationError, match="No vault found"):
        rotate_passphrase(OLD_PASS, NEW_PASS, project="ghost", base_dir=tmp_path)


def test_rotate_raises_on_wrong_old_passphrase(vault_base):
    with pytest.raises(RotationError, match="Failed to decrypt"):
        rotate_passphrase("wrong-pass", NEW_PASS, project="default", base_dir=vault_base)


def test_rotate_raises_when_passphrases_identical(vault_base):
    with pytest.raises(RotationError, match="must differ"):
        rotate_passphrase(OLD_PASS, OLD_PASS, project="default", base_dir=vault_base)


def test_rotate_writes_audit_event(vault_base):
    from envault.audit import read_events
    rotate_passphrase(OLD_PASS, NEW_PASS, project="default", base_dir=vault_base)
    events = read_events(project="default", base_dir=vault_base)
    actions = [e["action"] for e in events]
    assert "rotate" in actions


def test_rotate_custom_project(tmp_path):
    save_secrets(SECRETS, OLD_PASS, project="myapp", base_dir=tmp_path)
    count = rotate_passphrase(OLD_PASS, NEW_PASS, project="myapp", base_dir=tmp_path)
    assert count == len(SECRETS)
    recovered = load_secrets(NEW_PASS, project="myapp", base_dir=tmp_path)
    assert recovered == SECRETS
