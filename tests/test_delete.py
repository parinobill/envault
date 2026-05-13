"""Tests for envault.delete and envault.cli_delete."""

from __future__ import annotations

import argparse
import pytest

from envault.delete import DeleteError, delete_secret, delete_secrets
from envault.store import load_secrets, save_secrets, vault_exists
from envault.cli_delete import register_delete_parser


PASS = "hunter2"


@pytest.fixture()
def vault_base(tmp_path):
    """Return a base dir pre-populated with a small vault."""
    secrets = {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}
    save_secrets(secrets, passphrase=PASS, project="default", base_dir=str(tmp_path))
    return tmp_path


# ---------------------------------------------------------------------------
# delete_secret
# ---------------------------------------------------------------------------

def test_delete_removes_key(vault_base):
    delete_secret("API_KEY", passphrase=PASS, project="default", base_dir=str(vault_base))
    remaining = load_secrets(passphrase=PASS, project="default", base_dir=str(vault_base))
    assert "API_KEY" not in remaining


def test_delete_preserves_other_keys(vault_base):
    delete_secret("API_KEY", passphrase=PASS, project="default", base_dir=str(vault_base))
    remaining = load_secrets(passphrase=PASS, project="default", base_dir=str(vault_base))
    assert "DB_PASS" in remaining
    assert "TOKEN" in remaining


def test_delete_missing_key_raises(vault_base):
    with pytest.raises(DeleteError, match="MISSING"):
        delete_secret("MISSING", passphrase=PASS, project="default", base_dir=str(vault_base))


def test_delete_no_vault_raises(tmp_path):
    with pytest.raises(DeleteError, match="No vault"):
        delete_secret("KEY", passphrase=PASS, project="default", base_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# delete_secrets (bulk)
# ---------------------------------------------------------------------------

def test_delete_secrets_returns_count(vault_base):
    count = delete_secrets(["API_KEY", "TOKEN"], passphrase=PASS, project="default", base_dir=str(vault_base))
    assert count == 2


def test_delete_secrets_skips_missing(vault_base):
    count = delete_secrets(["API_KEY", "NOPE"], passphrase=PASS, project="default", base_dir=str(vault_base))
    assert count == 1


def test_delete_secrets_all_missing_returns_zero(vault_base):
    count = delete_secrets(["X", "Y"], passphrase=PASS, project="default", base_dir=str(vault_base))
    assert count == 0


def test_delete_secrets_no_vault_raises(tmp_path):
    with pytest.raises(DeleteError):
        delete_secrets(["KEY"], passphrase=PASS, project="default", base_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_delete_parser(sub)
    return p


def test_delete_subcommand_registered(parser):
    args = parser.parse_args(["delete", "MY_KEY"])
    assert hasattr(args, "func")


def test_delete_default_project(parser):
    args = parser.parse_args(["delete", "MY_KEY"])
    assert args.project == "default"


def test_delete_custom_project(parser):
    args = parser.parse_args(["delete", "--project", "prod", "MY_KEY"])
    assert args.project == "prod"


def test_delete_multiple_keys(parser):
    args = parser.parse_args(["delete", "KEY1", "KEY2", "KEY3"])
    assert args.keys == ["KEY1", "KEY2", "KEY3"]


def test_delete_sets_func(parser):
    from envault.cli_delete import cmd_delete
    args = parser.parse_args(["delete", "K"])
    assert args.func is cmd_delete
