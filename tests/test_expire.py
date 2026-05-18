"""Unit tests for envault.expire."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.expire import (
    ExpireError,
    ExpiryEntry,
    format_expiry,
    get_expired_keys,
    load_expiry,
    remove_expiry,
    save_expiry,
    set_expiry,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


PROJECT = "myapp"


# --- ExpiryEntry ---

def test_entry_not_expired_when_future():
    e = ExpiryEntry(key="K", expires_at=time.time() + 3600)
    assert not e.is_expired()


def test_entry_expired_when_past():
    e = ExpiryEntry(key="K", expires_at=time.time() - 1)
    assert e.is_expired()


def test_entry_seconds_remaining_positive():
    e = ExpiryEntry(key="K", expires_at=time.time() + 100)
    assert e.seconds_remaining() > 90


def test_entry_seconds_remaining_zero_when_expired():
    e = ExpiryEntry(key="K", expires_at=time.time() - 10)
    assert e.seconds_remaining() == 0.0


# --- load / save ---

def test_load_missing_returns_empty(base):
    assert load_expiry(base, PROJECT) == {}


def test_save_and_load_roundtrip(base):
    entries = {"SECRET_KEY": ExpiryEntry(key="SECRET_KEY", expires_at=9999999999.0, note="test")}
    save_expiry(base, PROJECT, entries)
    loaded = load_expiry(base, PROJECT)
    assert "SECRET_KEY" in loaded
    assert loaded["SECRET_KEY"].expires_at == 9999999999.0
    assert loaded["SECRET_KEY"].note == "test"


def test_save_creates_parent_dirs(base):
    entries = {"K": ExpiryEntry(key="K", expires_at=1.0)}
    save_expiry(base, "newproject", entries)
    assert (base / "newproject" / "expiry.json").exists()


# --- set_expiry ---

def test_set_expiry_stores_entry(base):
    entry = set_expiry(base, PROJECT, "DB_PASS", 3600)
    assert entry.key == "DB_PASS"
    assert entry.expires_at > time.time()
    loaded = load_expiry(base, PROJECT)
    assert "DB_PASS" in loaded


def test_set_expiry_negative_ttl_raises(base):
    with pytest.raises(ExpireError):
        set_expiry(base, PROJECT, "K", -1)


def test_set_expiry_zero_ttl_raises(base):
    with pytest.raises(ExpireError):
        set_expiry(base, PROJECT, "K", 0)


# --- remove_expiry ---

def test_remove_expiry_deletes_entry(base):
    set_expiry(base, PROJECT, "API_KEY", 100)
    remove_expiry(base, PROJECT, "API_KEY")
    assert "API_KEY" not in load_expiry(base, PROJECT)


def test_remove_expiry_missing_key_is_noop(base):
    remove_expiry(base, PROJECT, "NONEXISTENT")  # should not raise


# --- get_expired_keys ---

def test_get_expired_keys_returns_expired(base):
    now = time.time()
    entries = {
        "OLD": ExpiryEntry(key="OLD", expires_at=now - 10),
        "FRESH": ExpiryEntry(key="FRESH", expires_at=now + 3600),
    }
    save_expiry(base, PROJECT, entries)
    expired = get_expired_keys(base, PROJECT)
    assert "OLD" in expired
    assert "FRESH" not in expired


def test_get_expired_keys_empty_when_none_expired(base):
    entries = {"K": ExpiryEntry(key="K", expires_at=time.time() + 9999)}
    save_expiry(base, PROJECT, entries)
    assert get_expired_keys(base, PROJECT) == []


# --- format_expiry ---

def test_format_expiry_empty():
    assert "No expiry" in format_expiry({})


def test_format_expiry_shows_expired(base):
    now = time.time()
    entries = {"OLD": ExpiryEntry(key="OLD", expires_at=now - 5)}
    result = format_expiry(entries, now=now)
    assert "EXPIRED" in result
    assert "OLD" in result


def test_format_expiry_shows_remaining(base):
    now = time.time()
    entries = {"FRESH": ExpiryEntry(key="FRESH", expires_at=now + 3600)}
    result = format_expiry(entries, now=now)
    assert "remaining" in result
