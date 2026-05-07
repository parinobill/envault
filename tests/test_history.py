"""Tests for envault.history module."""

import json
from pathlib import Path

import pytest

from envault.history import (
    format_history,
    history_exists,
    read_history,
    record_snapshot,
    _history_path,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


SECRETS = {"DB_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}


def test_history_path_structure(tmp_base: Path) -> None:
    path = _history_path(str(tmp_base), "myproject")
    assert path.parent.name == "myproject"
    assert path.name == "history.jsonl"


def test_record_creates_file(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", SECRETS)
    assert _history_path(str(tmp_base), "proj").exists()


def test_record_valid_json(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", SECRETS)
    path = _history_path(str(tmp_base), "proj")
    with path.open() as fh:
        entry = json.loads(fh.readline())
    assert "timestamp" in entry
    assert "keys" in entry
    assert entry["count"] == 2


def test_record_multiple_appends(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", SECRETS, action="push")
    record_snapshot(str(tmp_base), "proj", {"A": "1"}, action="rotate")
    entries = read_history(str(tmp_base), "proj")
    assert len(entries) == 2
    assert entries[0]["action"] == "push"
    assert entries[1]["action"] == "rotate"


def test_read_history_empty(tmp_base: Path) -> None:
    entries = read_history(str(tmp_base), "nonexistent")
    assert entries == []


def test_keys_are_sorted(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", {"Z": "1", "A": "2", "M": "3"})
    entries = read_history(str(tmp_base), "proj")
    assert entries[0]["keys"] == ["A", "M", "Z"]


def test_actor_stored(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", SECRETS, actor="alice")
    entries = read_history(str(tmp_base), "proj")
    assert entries[0]["actor"] == "alice"


def test_format_history_empty() -> None:
    result = format_history([])
    assert "No history" in result


def test_format_history_shows_entries(tmp_base: Path) -> None:
    record_snapshot(str(tmp_base), "proj", SECRETS, actor="bob", action="push")
    entries = read_history(str(tmp_base), "proj")
    text = format_history(entries)
    assert "bob" in text
    assert "push" in text
    assert "DB_URL" in text


def test_history_exists(tmp_base: Path) -> None:
    assert not history_exists(str(tmp_base), "proj")
    record_snapshot(str(tmp_base), "proj", SECRETS)
    assert history_exists(str(tmp_base), "proj")
