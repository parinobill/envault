"""Tests for envault.clone."""

from __future__ import annotations

import pytest

from envault.clone import CloneError, clone_project
from envault.store import load_secrets, save_secrets, vault_exists


@pytest.fixture()
def vault_base(tmp_path):
    """Return a tmp_path-based base_dir with a pre-populated source vault."""
    base = str(tmp_path)
    secrets = {"API_KEY": "abc123", "DB_PASS": "s3cr3t", "TOKEN": "tok"}
    save_secrets("src", secrets, "src-pass", base_dir=base)
    return base


def test_clone_creates_dest_vault(vault_base):
    clone_project("src", "dest", "src-pass", "dest-pass", base_dir=vault_base)
    assert vault_exists("dest", base_dir=vault_base)


def test_clone_returns_secret_count(vault_base):
    count = clone_project("src", "dest", "src-pass", "dest-pass", base_dir=vault_base)
    assert count == 3


def test_clone_dest_decrypts_with_new_passphrase(vault_base):
    clone_project("src", "dest", "src-pass", "dest-pass", base_dir=vault_base)
    result = load_secrets("dest", "dest-pass", base_dir=vault_base)
    assert result == {"API_KEY": "abc123", "DB_PASS": "s3cr3t", "TOKEN": "tok"}


def test_clone_src_passphrase_does_not_decrypt_dest(vault_base):
    clone_project("src", "dest", "src-pass", "dest-pass", base_dir=vault_base)
    with pytest.raises(Exception):
        load_secrets("dest", "src-pass", base_dir=vault_base)


def test_clone_missing_src_raises(vault_base):
    with pytest.raises(CloneError, match="does not exist"):
        clone_project("ghost", "dest", "x", "y", base_dir=vault_base)


def test_clone_existing_dest_raises_without_overwrite(vault_base):
    save_secrets("dest", {"X": "1"}, "dest-pass", base_dir=vault_base)
    with pytest.raises(CloneError, match="already exists"):
        clone_project("src", "dest", "src-pass", "dest-pass", base_dir=vault_base)


def test_clone_overwrite_replaces_dest(vault_base):
    save_secrets("dest", {"OLD": "value"}, "old-pass", base_dir=vault_base)
    clone_project(
        "src", "dest", "src-pass", "new-pass",
        base_dir=vault_base, overwrite=True,
    )
    result = load_secrets("dest", "new-pass", base_dir=vault_base)
    assert "API_KEY" in result
    assert "OLD" not in result


def test_clone_empty_src_raises(tmp_path):
    base = str(tmp_path)
    save_secrets("empty", {}, "pass", base_dir=base)
    with pytest.raises(CloneError, match="no secrets"):
        clone_project("empty", "dest", "pass", "pass2", base_dir=base)
