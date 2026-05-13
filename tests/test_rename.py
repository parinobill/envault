"""Tests for envault.rename and envault.cli_rename."""

from __future__ import annotations

import argparse
import pytest

from envault.rename import RenameError, rename_secret
from envault.store import load_secrets, save_secrets, vault_exists
from envault.cli_rename import register_rename_parser


PASS = "hunter2"
SECRETS = {"API_KEY": "abc123", "DB_PASS": "secret"}


@pytest.fixture()
def vault_base(tmp_path):
    save_secrets(SECRETS, passphrase=PASS, project="test", base_dir=str(tmp_path))
    return str(tmp_path)


def test_rename_changes_key(vault_base):
    rename_secret("API_KEY", "API_TOKEN", passphrase=PASS, project="test", base_dir=vault_base)
    result = load_secrets(passphrase=PASS, project="test", base_dir=vault_base)
    assert "API_TOKEN" in result
    assert "API_KEY" not in result


def test_rename_preserves_value(vault_base):
    rename_secret("API_KEY", "API_TOKEN", passphrase=PASS, project="test", base_dir=vault_base)
    result = load_secrets(passphrase=PASS, project="test", base_dir=vault_base)
    assert result["API_TOKEN"] == "abc123"


def test_rename_preserves_other_keys(vault_base):
    rename_secret("API_KEY", "API_TOKEN", passphrase=PASS, project="test", base_dir=vault_base)
    result = load_secrets(passphrase=PASS, project="test", base_dir=vault_base)
    assert "DB_PASS" in result
    assert result["DB_PASS"] == "secret"


def test_rename_missing_key_raises(vault_base):
    with pytest.raises(RenameError, match="does not exist"):
        rename_secret("MISSING", "NEW_KEY", passphrase=PASS, project="test", base_dir=vault_base)


def test_rename_to_existing_key_raises(vault_base):
    with pytest.raises(RenameError, match="already exists"):
        rename_secret("API_KEY", "DB_PASS", passphrase=PASS, project="test", base_dir=vault_base)


def test_rename_invalid_new_key_raises(vault_base):
    with pytest.raises(RenameError, match="not a valid key name"):
        rename_secret("API_KEY", "123-bad!", passphrase=PASS, project="test", base_dir=vault_base)


def test_rename_no_vault_raises(tmp_path):
    with pytest.raises(RenameError, match="No vault found"):
        rename_secret("API_KEY", "NEW", passphrase=PASS, project="ghost", base_dir=str(tmp_path))


# --- CLI parser tests ---

@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_rename_parser(sub)
    return p


def test_rename_subcommand_registered(parser):
    args = parser.parse_args(["rename", "OLD", "NEW"])
    assert hasattr(args, "func")


def test_rename_default_project(parser):
    args = parser.parse_args(["rename", "OLD", "NEW"])
    assert args.project == "default"


def test_rename_custom_project(parser):
    args = parser.parse_args(["rename", "OLD", "NEW", "--project", "myapp"])
    assert args.project == "myapp"


def test_rename_sets_keys(parser):
    args = parser.parse_args(["rename", "OLD_KEY", "NEW_KEY"])
    assert args.old_key == "OLD_KEY"
    assert args.new_key == "NEW_KEY"
