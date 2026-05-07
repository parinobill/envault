"""Unit tests for envault.export."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envault.export import ExportError, export_secrets

SAMPLE: dict[str, str] = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "s3cr3t"}


# ---------------------------------------------------------------------------
# dotenv format
# ---------------------------------------------------------------------------

def test_dotenv_simple_keys():
    result = export_secrets(SAMPLE, fmt="dotenv")
    assert "DB_HOST=localhost" in result
    assert "DB_PORT=5432" in result


def test_dotenv_quotes_value_with_space():
    result = export_secrets({"MSG": "hello world"}, fmt="dotenv")
    assert 'MSG="hello world"' in result


def test_dotenv_ends_with_newline():
    result = export_secrets(SAMPLE, fmt="dotenv")
    assert result.endswith("\n")


def test_dotenv_empty_secrets():
    result = export_secrets({}, fmt="dotenv")
    assert result == ""


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_json_valid():
    result = export_secrets(SAMPLE, fmt="json")
    parsed = json.loads(result)
    assert parsed == SAMPLE


def test_json_ends_with_newline():
    result = export_secrets(SAMPLE, fmt="json")
    assert result.endswith("\n")


# ---------------------------------------------------------------------------
# CSV format
# ---------------------------------------------------------------------------

def test_csv_has_header():
    result = export_secrets(SAMPLE, fmt="csv")
    reader = csv.reader(io.StringIO(result))
    header = next(reader)
    assert header == ["key", "value"]


def test_csv_row_count():
    result = export_secrets(SAMPLE, fmt="csv")
    rows = list(csv.reader(io.StringIO(result)))
    # header + one row per secret
    assert len(rows) == len(SAMPLE) + 1


def test_csv_values_present():
    result = export_secrets({"API_KEY": "abc123"}, fmt="csv")
    assert "API_KEY" in result
    assert "abc123" in result


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported export format"):
        export_secrets(SAMPLE, fmt="xml")  # type: ignore[arg-type]
