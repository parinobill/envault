"""Tests for envault.access."""
from pathlib import Path

import pytest

from envault.access import (
    AccessError,
    _access_path,
    filter_secrets,
    grant,
    is_allowed,
    load_acl,
    revoke,
    save_acl,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# path helpers
# ---------------------------------------------------------------------------

def test_access_path_structure(base: Path) -> None:
    p = _access_path(base, "myproject")
    assert p == base / "myproject" / "access.json"


# ---------------------------------------------------------------------------
# load / save round-trip
# ---------------------------------------------------------------------------

def test_load_missing_returns_empty(base: Path) -> None:
    assert load_acl(base, "proj") == {}


def test_save_and_load_roundtrip(base: Path) -> None:
    acl = {"SECRET_KEY": ["alice", "bob"], "DB_PASS": []}
    save_acl(base, "proj", acl)
    assert load_acl(base, "proj") == acl


def test_save_creates_parent_dirs(base: Path) -> None:
    save_acl(base, "nested/proj", {"KEY": ["alice"]})
    assert _access_path(base, "nested/proj").exists()


# ---------------------------------------------------------------------------
# grant
# ---------------------------------------------------------------------------

def test_grant_new_key(base: Path) -> None:
    grant(base, "proj", "API_KEY", "alice")
    acl = load_acl(base, "proj")
    assert "alice" in acl["API_KEY"]


def test_grant_idempotent(base: Path) -> None:
    grant(base, "proj", "API_KEY", "alice")
    grant(base, "proj", "API_KEY", "alice")
    acl = load_acl(base, "proj")
    assert acl["API_KEY"].count("alice") == 1


def test_grant_multiple_identities(base: Path) -> None:
    grant(base, "proj", "API_KEY", "alice")
    grant(base, "proj", "API_KEY", "bob")
    acl = load_acl(base, "proj")
    assert set(acl["API_KEY"]) == {"alice", "bob"}


# ---------------------------------------------------------------------------
# revoke
# ---------------------------------------------------------------------------

def test_revoke_removes_identity(base: Path) -> None:
    grant(base, "proj", "API_KEY", "alice")
    revoke(base, "proj", "API_KEY", "alice")
    acl = load_acl(base, "proj")
    assert "alice" not in acl["API_KEY"]


def test_revoke_missing_identity_raises(base: Path) -> None:
    with pytest.raises(AccessError, match="does not have access"):
        revoke(base, "proj", "API_KEY", "ghost")


# ---------------------------------------------------------------------------
# is_allowed
# ---------------------------------------------------------------------------

def test_no_acl_entry_allows_all(base: Path) -> None:
    assert is_allowed(base, "proj", "OPEN_KEY", "anyone") is True


def test_empty_list_allows_all(base: Path) -> None:
    save_acl(base, "proj", {"KEY": []})
    assert is_allowed(base, "proj", "KEY", "stranger") is True


def test_restricted_key_allows_listed_identity(base: Path) -> None:
    grant(base, "proj", "SECRET", "alice")
    assert is_allowed(base, "proj", "SECRET", "alice") is True


def test_restricted_key_blocks_unlisted_identity(base: Path) -> None:
    grant(base, "proj", "SECRET", "alice")
    assert is_allowed(base, "proj", "SECRET", "eve") is False


# ---------------------------------------------------------------------------
# filter_secrets
# ---------------------------------------------------------------------------

def test_filter_none_identity_returns_all(base: Path) -> None:
    secrets = {"A": "1", "B": "2"}
    grant(base, "proj", "A", "alice")
    result = filter_secrets(base, "proj", secrets, None)
    assert result == secrets


def test_filter_restricts_keys(base: Path) -> None:
    secrets = {"A": "1", "B": "2"}
    grant(base, "proj", "A", "alice")
    # B has no ACL entry → open; A restricted to alice only
    result = filter_secrets(base, "proj", secrets, "alice")
    assert result == {"A": "1", "B": "2"}


def test_filter_blocks_restricted_key(base: Path) -> None:
    secrets = {"A": "1", "B": "2"}
    grant(base, "proj", "A", "alice")
    result = filter_secrets(base, "proj", secrets, "bob")
    # bob cannot see A; B is open
    assert result == {"B": "2"}
