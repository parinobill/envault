"""Tests for envault.import_env"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envault.import_env import ImportError as EnvImportError
from envault.import_env import import_secrets
from envault.store import load_secrets, save_secrets

PASS = "test-pass-123"


@pytest.fixture()
def vault_base(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# dotenv format
# ---------------------------------------------------------------------------

def test_import_dotenv(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / ".env"
    src.write_text("API_KEY=abc\nSECRET=xyz\n")
    count = import_secrets(src, PASS, fmt="dotenv", project="p", base_dir=vault_base)
    assert count == 2
    data = load_secrets(PASS, project="p", base_dir=vault_base)
    assert data == {"API_KEY": "abc", "SECRET": "xyz"}


def test_import_dotenv_skips_comments(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / ".env"
    src.write_text("# comment\nFOO=bar\n")
    count = import_secrets(src, PASS, fmt="dotenv", project="p", base_dir=vault_base)
    assert count == 1


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_import_json(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "secrets.json"
    src.write_text(json.dumps({"DB_HOST": "localhost", "DB_PORT": "5432"}))
    count = import_secrets(src, PASS, fmt="json", project="p", base_dir=vault_base)
    assert count == 2
    data = load_secrets(PASS, project="p", base_dir=vault_base)
    assert data["DB_HOST"] == "localhost"


def test_import_json_invalid_raises(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "bad.json"
    src.write_text("not json")
    with pytest.raises(EnvImportError, match="Invalid JSON"):
        import_secrets(src, PASS, fmt="json", project="p", base_dir=vault_base)


def test_import_json_non_string_values_raises(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "bad.json"
    src.write_text(json.dumps({"PORT": 5432}))
    with pytest.raises(EnvImportError, match="All values must be strings"):
        import_secrets(src, PASS, fmt="json", project="p", base_dir=vault_base)


# ---------------------------------------------------------------------------
# CSV format
# ---------------------------------------------------------------------------

def test_import_csv(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "secrets.csv"
    src.write_text("key,value\nTOKEN,abc123\nREGION,us-east-1\n")
    count = import_secrets(src, PASS, fmt="csv", project="p", base_dir=vault_base)
    assert count == 2
    data = load_secrets(PASS, project="p", base_dir=vault_base)
    assert data["TOKEN"] == "abc123"


def test_import_csv_missing_columns_raises(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "bad.csv"
    src.write_text("name,secret\nfoo,bar\n")
    with pytest.raises(EnvImportError, match="CSV must have"):
        import_secrets(src, PASS, fmt="csv", project="p", base_dir=vault_base)


# ---------------------------------------------------------------------------
# merge flag
# ---------------------------------------------------------------------------

def test_import_merge_preserves_existing(vault_base: Path, tmp_path: Path) -> None:
    save_secrets({"EXISTING": "keep"}, PASS, project="p", base_dir=vault_base)
    src = tmp_path / ".env"
    src.write_text("NEW_KEY=hello\n")
    import_secrets(src, PASS, fmt="dotenv", project="p", merge=True, base_dir=vault_base)
    data = load_secrets(PASS, project="p", base_dir=vault_base)
    assert data["EXISTING"] == "keep"
    assert data["NEW_KEY"] == "hello"


def test_import_overwrite_replaces_existing(vault_base: Path, tmp_path: Path) -> None:
    save_secrets({"OLD": "gone"}, PASS, project="p", base_dir=vault_base)
    src = tmp_path / ".env"
    src.write_text("NEW=here\n")
    import_secrets(src, PASS, fmt="dotenv", project="p", merge=False, base_dir=vault_base)
    data = load_secrets(PASS, project="p", base_dir=vault_base)
    assert "OLD" not in data
    assert data["NEW"] == "here"


def test_unknown_format_raises(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / "file.xml"
    src.write_text("<root/>")
    with pytest.raises(EnvImportError, match="Unknown format"):
        import_secrets(src, PASS, fmt="xml", project="p", base_dir=vault_base)


def test_empty_source_raises(vault_base: Path, tmp_path: Path) -> None:
    src = tmp_path / ".env"
    src.write_text("# only comments\n")
    with pytest.raises(EnvImportError, match="No secrets found"):
        import_secrets(src, PASS, fmt="dotenv", project="p", base_dir=vault_base)
