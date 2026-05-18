"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.watch import (
    WatchError,
    WatchEvent,
    _changed_keys,
    _file_hash,
    watch,
)
from envault.store import save_secrets, load_secrets


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_file_hash_stable(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=val\n")
    assert _file_hash(f) == _file_hash(f)


def test_file_hash_changes_on_edit(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=val\n")
    h1 = _file_hash(f)
    f.write_text("KEY=other\n")
    assert _file_hash(f) != h1


def test_changed_keys_added():
    assert _changed_keys({}, {"A": "1"}) == ["A"]


def test_changed_keys_removed():
    assert _changed_keys({"A": "1"}, {}) == ["A"]


def test_changed_keys_modified():
    assert _changed_keys({"A": "old"}, {"A": "new"}) == ["A"]


def test_changed_keys_unchanged():
    assert _changed_keys({"A": "1"}, {"A": "1"}) == []


# ---------------------------------------------------------------------------
# watch() integration
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_base(tmp_path):
    return tmp_path / "vaults"


def _make_env(path: Path, content: str) -> None:
    path.write_text(content)


def test_watch_raises_if_file_missing(vault_base):
    with pytest.raises(WatchError, match="not found"):
        watch(
            env_file=Path("/no/such/.env"),
            project="p",
            passphrase="x",
            base_dir=vault_base,
            _stop=lambda: True,
        )


def test_watch_detects_change_and_pushes(tmp_path, vault_base):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    events: list[WatchEvent] = []
    calls = {"n": 0}

    def _stop():
        calls["n"] += 1
        if calls["n"] == 1:
            # Mutate the file before the first poll
            env_file.write_text("FOO=changed\nBAR=new\n")
        return calls["n"] >= 2

    watch(
        env_file=env_file,
        project="proj",
        passphrase="secret",
        base_dir=vault_base,
        interval=0.0,
        on_change=events.append,
        _stop=_stop,
    )

    assert len(events) == 1
    assert set(events[0].changed_keys) == {"FOO", "BAR"}
    secrets = load_secrets("proj", "secret", base_dir=vault_base)
    assert secrets["FOO"] == "changed"
    assert secrets["BAR"] == "new"


def test_watch_no_change_emits_no_event(tmp_path, vault_base):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    events: list[WatchEvent] = []
    calls = {"n": 0}

    def _stop():
        calls["n"] += 1
        return calls["n"] >= 3

    watch(
        env_file=env_file,
        project="proj",
        passphrase="secret",
        base_dir=vault_base,
        interval=0.0,
        on_change=events.append,
        _stop=_stop,
    )

    assert events == []
