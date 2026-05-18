"""Tests for envault.backup."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.backup import (
    BackupError,
    _backup_dir,
    create_backup,
    list_backups,
    restore_backup,
)
from envault.store import save_secrets, load_secrets

SECRETS = {"DB_HOST": "localhost", "API_KEY": "s3cr3t", "PORT": "5432"}
PASS = "hunter2"


@pytest.fixture()
def vault_base(tmp_path: Path) -> Path:
    save_secrets(tmp_path, "myproject", PASS, SECRETS)
    return tmp_path


def test_create_backup_returns_path(vault_base: Path) -> None:
    path = create_backup(vault_base, "myproject", PASS)
    assert path.exists()
    assert path.suffix == ".json"


def test_create_backup_stored_in_backup_dir(vault_base: Path) -> None:
    path = create_backup(vault_base, "myproject", PASS)
    assert path.parent == _backup_dir(vault_base, "myproject")


def test_create_backup_valid_json(vault_base: Path) -> None:
    path = create_backup(vault_base, "myproject", PASS)
    data = json.loads(path.read_text())
    assert data["project"] == "myproject"
    assert data["secrets"] == SECRETS


def test_create_backup_with_label(vault_base: Path) -> None:
    path = create_backup(vault_base, "myproject", PASS, label="pre-deploy")
    assert "pre-deploy" in path.name


def test_create_backup_no_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="No vault found"):
        create_backup(tmp_path, "ghost", PASS)


def test_restore_roundtrip(vault_base: Path) -> None:
    backup_path = create_backup(vault_base, "myproject", PASS)
    new_pass = "newpassword"
    count = restore_backup(vault_base, "myproject", backup_path, new_pass)
    assert count == len(SECRETS)
    restored = load_secrets(vault_base, "myproject", new_pass)
    assert restored == SECRETS


def test_restore_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        restore_backup(tmp_path, "myproject", tmp_path / "nope.json", PASS)


def test_restore_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not-json")
    with pytest.raises(BackupError, match="Invalid backup"):
        restore_backup(tmp_path, "myproject", bad, PASS)


def test_restore_missing_secrets_key_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"project": "x"}))
    with pytest.raises(BackupError, match="missing 'secrets'"):
        restore_backup(tmp_path, "myproject", bad, PASS)


def test_list_backups_empty(tmp_path: Path) -> None:
    assert list_backups(tmp_path, "myproject") == []


def test_list_backups_sorted(vault_base: Path) -> None:
    p1 = create_backup(vault_base, "myproject", PASS, label="first")
    time.sleep(0.01)
    p2 = create_backup(vault_base, "myproject", PASS, label="second")
    backups = list_backups(vault_base, "myproject")
    assert backups[0] == p1
    assert backups[1] == p2
