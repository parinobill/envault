"""Integration tests: diff against a real vault."""

import pathlib

import pytest

from envault.diff import diff_secrets, has_changes
from envault.dotenv_io import write_dotenv_file
from envault.store import save_secrets, load_secrets


PASSPHRASE = "integration-pass"
PROJECT = "diff-test"


@pytest.fixture()
def vault_base(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_BASE", str(tmp_path))
    # also patch store._vault_path to use tmp_path
    import envault.store as store_mod

    original = store_mod._vault_path

    def patched(project):
        return tmp_path / project / "vault.json.enc"

    monkeypatch.setattr(store_mod, "_vault_path", patched)
    return tmp_path


def test_diff_in_sync(vault_base):
    secrets = {"KEY1": "value1", "KEY2": "value2"}
    save_secrets(PROJECT, secrets, PASSPHRASE)
    vault = load_secrets(PROJECT, PASSPHRASE)
    entries = diff_secrets(secrets, vault)
    assert not has_changes(entries)


def test_diff_detects_local_addition(vault_base):
    vault_secrets = {"KEY1": "v1"}
    save_secrets(PROJECT, vault_secrets, PASSPHRASE)
    local_secrets = {"KEY1": "v1", "EXTRA": "new"}
    vault = load_secrets(PROJECT, PASSPHRASE)
    entries = diff_secrets(local_secrets, vault)
    assert has_changes(entries)
    statuses = {e.key: e.status for e in entries}
    assert statuses["EXTRA"] == "added"


def test_diff_detects_local_removal(vault_base):
    vault_secrets = {"KEY1": "v1", "KEY2": "v2"}
    save_secrets(PROJECT, vault_secrets, PASSPHRASE)
    local_secrets = {"KEY1": "v1"}
    vault = load_secrets(PROJECT, PASSPHRASE)
    entries = diff_secrets(local_secrets, vault)
    statuses = {e.key: e.status for e in entries}
    assert statuses["KEY2"] == "removed"


def test_diff_detects_value_change(vault_base):
    vault_secrets = {"PORT": "8080"}
    save_secrets(PROJECT, vault_secrets, PASSPHRASE)
    local_secrets = {"PORT": "9090"}
    vault = load_secrets(PROJECT, PASSPHRASE)
    entries = diff_secrets(local_secrets, vault)
    statuses = {e.key: e.status for e in entries}
    assert statuses["PORT"] == "changed"
