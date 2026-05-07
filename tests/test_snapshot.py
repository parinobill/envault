"""Unit tests for envault.snapshot."""

from __future__ import annotations

import json
import os
import pytest

from envault.snapshot import (
    compare_to_snapshot,
    format_snapshot_result,
    SnapshotError,
    SnapshotResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(base_dir: str, project: str, entries: list[dict]) -> None:
    path = os.path.join(base_dir, project, "history.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


@pytest.fixture()
def tmp_base(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_history_raises(tmp_base):
    with pytest.raises(SnapshotError, match="No history"):
        compare_to_snapshot(tmp_base, "myproject", {"KEY": "val"})


def test_index_out_of_range_raises(tmp_base):
    _write_history(tmp_base, "proj", [{"timestamp": "t1", "secrets": {"A": "1"}}])
    with pytest.raises(SnapshotError, match="out of range"):
        compare_to_snapshot(tmp_base, "proj", {"A": "1"}, snapshot_index=5)


def test_no_changes(tmp_base):
    secrets = {"DB": "postgres", "PORT": "5432"}
    _write_history(tmp_base, "proj", [{"timestamp": "2024-01-01", "secrets": secrets}])
    result = compare_to_snapshot(tmp_base, "proj", secrets)
    assert isinstance(result, SnapshotResult)
    assert not result.has_changes


def test_detects_added_key(tmp_base):
    old = {"A": "1"}
    new = {"A": "1", "B": "2"}
    _write_history(tmp_base, "proj", [{"timestamp": "t", "secrets": old}])
    result = compare_to_snapshot(tmp_base, "proj", new)
    assert result.has_changes
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == "added"


def test_detects_removed_key(tmp_base):
    old = {"A": "1", "B": "2"}
    new = {"A": "1"}
    _write_history(tmp_base, "proj", [{"timestamp": "t", "secrets": old}])
    result = compare_to_snapshot(tmp_base, "proj", new)
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == "removed"


def test_detects_changed_value(tmp_base):
    old = {"X": "old_val"}
    new = {"X": "new_val"}
    _write_history(tmp_base, "proj", [{"timestamp": "t", "secrets": old}])
    result = compare_to_snapshot(tmp_base, "proj", new)
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["X"] == "changed"


def test_index_positive(tmp_base):
    entries = [
        {"timestamp": "t0", "secrets": {"K": "v0"}},
        {"timestamp": "t1", "secrets": {"K": "v1"}},
    ]
    _write_history(tmp_base, "proj", entries)
    result = compare_to_snapshot(tmp_base, "proj", {"K": "v1"}, snapshot_index=0)
    assert result.index == 0
    assert result.timestamp == "t0"
    assert result.has_changes


def test_format_no_changes(tmp_base):
    secrets = {"A": "1"}
    _write_history(tmp_base, "proj", [{"timestamp": "2024-06-01T00:00:00", "secrets": secrets}])
    result = compare_to_snapshot(tmp_base, "proj", secrets)
    output = format_snapshot_result(result)
    assert "No changes" in output
    assert "2024-06-01" in output


def test_format_with_changes(tmp_base):
    old = {"A": "1"}
    new = {"A": "1", "B": "2"}
    _write_history(tmp_base, "proj", [{"timestamp": "ts", "secrets": old}])
    result = compare_to_snapshot(tmp_base, "proj", new)
    output = format_snapshot_result(result)
    assert "B" in output
