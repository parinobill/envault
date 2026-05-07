"""Integration tests: export secrets stored in a real vault."""

from __future__ import annotations

import json
import csv
import io
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.store import save_secrets
from envault.export import export_secrets
from envault.cli_export import cmd_export


SECRETS = {"APP_ENV": "production", "DB_URL": "postgres://localhost/mydb"}
PASSPHRASE = "integration-pass"


@pytest.fixture()
def vault_base(tmp_path: Path):
    with patch("envault.store._vault_path") as mock_path:
        def _path(project: str) -> Path:
            return tmp_path / project / "vault.enc"
        mock_path.side_effect = _path
        yield tmp_path


@pytest.fixture()
def populated_vault(vault_base: Path):
    save_secrets("myapp", SECRETS, PASSPHRASE)
    return vault_base


def test_export_dotenv_roundtrip(populated_vault):
    from envault.store import load_secrets
    with patch("envault.store._vault_path") as mp:
        mp.side_effect = lambda p: populated_vault / p / "vault.enc"
        secrets = load_secrets("myapp", PASSPHRASE)
    output = export_secrets(secrets, fmt="dotenv")
    assert "APP_ENV=production" in output
    assert "DB_URL=postgres://localhost/mydb" in output


def test_export_json_roundtrip(populated_vault):
    from envault.store import load_secrets
    with patch("envault.store._vault_path") as mp:
        mp.side_effect = lambda p: populated_vault / p / "vault.enc"
        secrets = load_secrets("myapp", PASSPHRASE)
    output = export_secrets(secrets, fmt="json")
    parsed = json.loads(output)
    assert parsed == SECRETS


def test_export_csv_roundtrip(populated_vault):
    from envault.store import load_secrets
    with patch("envault.store._vault_path") as mp:
        mp.side_effect = lambda p: populated_vault / p / "vault.enc"
        secrets = load_secrets("myapp", PASSPHRASE)
    output = export_secrets(secrets, fmt="csv")
    rows = list(csv.DictReader(io.StringIO(output)))
    recovered = {r["key"]: r["value"] for r in rows}
    assert recovered == SECRETS


def test_export_to_file(populated_vault, tmp_path):
    out_file = tmp_path / "exported.env"
    import argparse
    args = argparse.Namespace(project="myapp", format="json", output=str(out_file))
    with (
        patch("envault.store._vault_path", side_effect=lambda p: populated_vault / p / "vault.enc"),
        patch("envault.cli_export._prompt_passphrase", return_value=PASSPHRASE),
        patch("envault.store.vault_exists", return_value=True),
    ):
        cmd_export(args)
    assert out_file.exists()
    parsed = json.loads(out_file.read_text())
    assert parsed == SECRETS
