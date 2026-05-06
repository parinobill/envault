"""Tests for envault.team — bundle export/import."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.team import export_bundle, import_bundle
from envault.store import load_secrets


PASSPHRASE = "shared-team-secret"
PROJECT = "myapp"
SECRETS = {"DB_URL": "postgres://localhost/db", "API_KEY": "abc123"}


@pytest.fixture()
def vault_base(tmp_path: Path) -> Path:
    """Pre-populate a vault so export tests have something to read."""
    from envault.store import save_secrets

    save_secrets(PROJECT, SECRETS, PASSPHRASE, base_dir=tmp_path)
    return tmp_path


def test_export_creates_file(vault_base: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    result = export_bundle(PROJECT, PASSPHRASE, output_path=out, base_dir=vault_base)
    assert result == out
    assert out.exists()


def test_export_bundle_is_valid_json(vault_base: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    export_bundle(PROJECT, PASSPHRASE, output_path=out, base_dir=vault_base)
    data = json.loads(out.read_text())
    assert data["project"] == PROJECT
    assert data["version"] == 1
    assert isinstance(data["data"], str)


def test_export_default_output_name(vault_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(vault_base)
    result = export_bundle(PROJECT, PASSPHRASE, base_dir=vault_base)
    assert result.name == f"{PROJECT}.envault-bundle.json"
    assert result.exists()


def test_import_roundtrip(vault_base: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    export_bundle(PROJECT, PASSPHRASE, output_path=out, base_dir=vault_base)

    import_base = tmp_path / "new_vault"
    imported_project = import_bundle(out, PASSPHRASE, base_dir=import_base)

    assert imported_project == PROJECT
    recovered = load_secrets(PROJECT, PASSPHRASE, base_dir=import_base)
    assert recovered == SECRETS


def test_import_custom_project_name(vault_base: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    export_bundle(PROJECT, PASSPHRASE, output_path=out, base_dir=vault_base)

    import_base = tmp_path / "new_vault"
    imported_project = import_bundle(out, PASSPHRASE, project="renamed", base_dir=import_base)

    assert imported_project == "renamed"
    recovered = load_secrets("renamed", PASSPHRASE, base_dir=import_base)
    assert recovered == SECRETS


def test_import_wrong_passphrase_raises(vault_base: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    export_bundle(PROJECT, PASSPHRASE, output_path=out, base_dir=vault_base)

    with pytest.raises(Exception):
        import_bundle(out, "wrong-passphrase", base_dir=tmp_path / "other")


def test_import_unsupported_version_raises(tmp_path: Path) -> None:
    bad_bundle = tmp_path / "bad.json"
    bad_bundle.write_text(json.dumps({"project": "x", "version": 99, "data": ""}))
    with pytest.raises(ValueError, match="Unsupported bundle version"):
        import_bundle(bad_bundle, PASSPHRASE, base_dir=tmp_path)
