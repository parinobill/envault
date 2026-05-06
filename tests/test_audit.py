"""Tests for envault.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import (
    _audit_path,
    format_events,
    read_events,
    record_event,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


def test_audit_path_structure(tmp_base: Path) -> None:
    path = _audit_path("myproject", base_dir=tmp_base)
    assert path.name == ".envault_audit.jsonl"
    assert path.parent.name == "myproject"


def test_record_event_creates_file(tmp_base: Path) -> None:
    record_event("proj", "push", actor="alice", base_dir=tmp_base)
    log = _audit_path("proj", base_dir=tmp_base)
    assert log.exists()


def test_record_event_valid_json(tmp_base: Path) -> None:
    record_event("proj", "pull", actor="bob", keys=["DB_URL", "SECRET"], base_dir=tmp_base)
    log = _audit_path("proj", base_dir=tmp_base)
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["action"] == "pull"
    assert event["actor"] == "bob"
    assert event["keys"] == ["DB_URL", "SECRET"]
    assert event["project"] == "proj"
    assert "timestamp" in event


def test_record_multiple_events_appends(tmp_base: Path) -> None:
    for action in ("push", "pull", "push"):
        record_event("proj", action, actor="carol", base_dir=tmp_base)
    events = read_events("proj", base_dir=tmp_base)
    assert len(events) == 3
    assert [e["action"] for e in events] == ["push", "pull", "push"]


def test_read_events_empty_when_no_log(tmp_base: Path) -> None:
    events = read_events("nonexistent", base_dir=tmp_base)
    assert events == []


def test_record_event_without_keys(tmp_base: Path) -> None:
    record_event("proj", "init", actor="dave", base_dir=tmp_base)
    events = read_events("proj", base_dir=tmp_base)
    assert len(events) == 1
    assert "keys" not in events[0]


def test_format_events_empty() -> None:
    output = format_events([])
    assert "no audit events" in output


def test_format_events_contains_actor_and_action(tmp_base: Path) -> None:
    record_event("proj", "push", actor="eve", keys=["API_KEY"], base_dir=tmp_base)
    events = read_events("proj", base_dir=tmp_base)
    output = format_events(events)
    assert "eve" in output
    assert "push" in output
    assert "API_KEY" in output


def test_actor_defaults_to_env_user(tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER", "testuser")
    record_event("proj", "pull", base_dir=tmp_base)
    events = read_events("proj", base_dir=tmp_base)
    assert events[0]["actor"] == "testuser"
