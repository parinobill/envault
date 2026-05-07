"""Integration tests: history is recorded during push/pull via store + history."""

from pathlib import Path

import pytest

from envault.store import save_secrets, load_secrets
from envault.history import record_snapshot, read_history, format_history


@pytest.fixture()
def vault_base(tmp_path: Path) -> Path:
    return tmp_path


SECRETS_V1 = {"API_KEY": "key1", "DB_PASS": "pass1"}
SECRETS_V2 = {"API_KEY": "key2", "DB_PASS": "pass1", "NEW_VAR": "hello"}
PASS = "hunter2"


def test_history_grows_with_pushes(vault_base: Path) -> None:
    base = str(vault_base)
    save_secrets(base, "proj", SECRETS_V1, PASS)
    record_snapshot(base, "proj", SECRETS_V1, action="push")

    save_secrets(base, "proj", SECRETS_V2, PASS)
    record_snapshot(base, "proj", SECRETS_V2, action="push")

    entries = read_history(base, "proj")
    assert len(entries) == 2
    assert entries[0]["count"] == 2
    assert entries[1]["count"] == 3


def test_history_after_rotation(vault_base: Path) -> None:
    from envault.rotate import rotate_passphrase

    base = str(vault_base)
    save_secrets(base, "proj", SECRETS_V1, PASS)
    record_snapshot(base, "proj", SECRETS_V1, action="push")

    rotate_passphrase(base, "proj", PASS, "newpass")
    loaded = load_secrets(base, "proj", "newpass")
    record_snapshot(base, "proj", loaded, action="rotate")

    entries = read_history(base, "proj")
    assert len(entries) == 2
    assert entries[1]["action"] == "rotate"


def test_format_history_integration(vault_base: Path) -> None:
    base = str(vault_base)
    record_snapshot(base, "proj", SECRETS_V1, actor="ci", action="push")
    record_snapshot(base, "proj", SECRETS_V2, actor="alice", action="push")

    entries = read_history(base, "proj")
    text = format_history(entries)

    assert "ci" in text
    assert "alice" in text
    assert "[1]" in text
    assert "[2]" in text
    assert "API_KEY" in text


def test_history_limit_slice(vault_base: Path) -> None:
    base = str(vault_base)
    for i in range(5):
        record_snapshot(base, "proj", {f"KEY_{i}": str(i)}, action="push")

    entries = read_history(base, "proj")
    last_two = entries[-2:]
    assert len(last_two) == 2
    assert last_two[-1]["keys"] == ["KEY_4"]
