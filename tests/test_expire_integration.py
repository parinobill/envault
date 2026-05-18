"""Integration tests for secret expiry with the vault store."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.expire import (
    get_expired_keys,
    load_expiry,
    remove_expiry,
    set_expiry,
)
from envault.store import load_secrets, save_secrets

PASS = "hunter2"
PROJECT = "integration"


@pytest.fixture()
def vault_base(tmp_path: Path) -> Path:
    secrets = {"DB_PASS": "secret1", "API_KEY": "secret2", "TOKEN": "secret3"}
    save_secrets(tmp_path, PROJECT, PASS, secrets)
    return tmp_path


def test_set_expiry_does_not_alter_vault(vault_base):
    set_expiry(vault_base, PROJECT, "DB_PASS", 3600)
    secrets = load_secrets(vault_base, PROJECT, PASS)
    assert secrets["DB_PASS"] == "secret1"


def test_expired_key_detected(vault_base):
    now = time.time()
    # Manually set an already-expired entry
    from envault.expire import ExpiryEntry, save_expiry
    entries = {"API_KEY": ExpiryEntry(key="API_KEY", expires_at=now - 1)}
    save_expiry(vault_base, PROJECT, entries)
    expired = get_expired_keys(vault_base, PROJECT)
    assert "API_KEY" in expired


def test_purge_removes_expired_from_vault(vault_base):
    from envault.expire import ExpiryEntry, save_expiry
    now = time.time()
    entries = {"TOKEN": ExpiryEntry(key="TOKEN", expires_at=now - 1)}
    save_expiry(vault_base, PROJECT, entries)

    expired = get_expired_keys(vault_base, PROJECT)
    secrets = load_secrets(vault_base, PROJECT, PASS)
    for key in expired:
        secrets.pop(key, None)
        remove_expiry(vault_base, PROJECT, key)
    save_secrets(vault_base, PROJECT, PASS, secrets)

    refreshed = load_secrets(vault_base, PROJECT, PASS)
    assert "TOKEN" not in refreshed
    assert "DB_PASS" in refreshed
    assert "API_KEY" in refreshed


def test_purge_leaves_non_expired_intact(vault_base):
    from envault.expire import ExpiryEntry, save_expiry
    now = time.time()
    entries = {
        "DB_PASS": ExpiryEntry(key="DB_PASS", expires_at=now - 5),
        "API_KEY": ExpiryEntry(key="API_KEY", expires_at=now + 9999),
    }
    save_expiry(vault_base, PROJECT, entries)

    expired = get_expired_keys(vault_base, PROJECT)
    secrets = load_secrets(vault_base, PROJECT, PASS)
    for key in expired:
        secrets.pop(key, None)
        remove_expiry(vault_base, PROJECT, key)
    save_secrets(vault_base, PROJECT, PASS, secrets)

    refreshed = load_secrets(vault_base, PROJECT, PASS)
    assert "DB_PASS" not in refreshed
    assert "API_KEY" in refreshed
    assert "TOKEN" in refreshed


def test_expiry_rules_cleared_after_purge(vault_base):
    from envault.expire import ExpiryEntry, save_expiry
    now = time.time()
    entries = {"DB_PASS": ExpiryEntry(key="DB_PASS", expires_at=now - 1)}
    save_expiry(vault_base, PROJECT, entries)

    expired = get_expired_keys(vault_base, PROJECT)
    secrets = load_secrets(vault_base, PROJECT, PASS)
    for key in expired:
        secrets.pop(key, None)
        remove_expiry(vault_base, PROJECT, key)
    save_secrets(vault_base, PROJECT, PASS, secrets)

    remaining_rules = load_expiry(vault_base, PROJECT)
    assert "DB_PASS" not in remaining_rules
