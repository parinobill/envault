"""Tests for envault.diff module."""

import pytest

from envault.diff import DiffEntry, diff_secrets, format_diff, has_changes


LOCAL = {"DB_HOST": "localhost", "DB_PORT": "5432", "NEW_KEY": "hello"}
VAULT = {"DB_HOST": "localhost", "DB_PORT": "3306", "OLD_KEY": "bye"}


def test_unchanged_key():
    entries = diff_secrets({"A": "1"}, {"A": "1"})
    assert len(entries) == 1
    assert entries[0].status == "unchanged"
    assert entries[0].key == "A"


def test_added_key():
    entries = diff_secrets({"A": "1"}, {})
    assert entries[0].status == "added"
    assert entries[0].local_value == "1"
    assert entries[0].vault_value is None


def test_removed_key():
    entries = diff_secrets({}, {"A": "1"})
    assert entries[0].status == "removed"
    assert entries[0].vault_value == "1"
    assert entries[0].local_value is None


def test_changed_key():
    entries = diff_secrets({"A": "new"}, {"A": "old"})
    assert entries[0].status == "changed"
    assert entries[0].local_value == "new"
    assert entries[0].vault_value == "old"


def test_mixed_diff():
    entries = diff_secrets(LOCAL, VAULT)
    statuses = {e.key: e.status for e in entries}
    assert statuses["DB_HOST"] == "unchanged"
    assert statuses["DB_PORT"] == "changed"
    assert statuses["NEW_KEY"] == "added"
    assert statuses["OLD_KEY"] == "removed"


def test_keys_sorted():
    entries = diff_secrets({"Z": "1", "A": "1"}, {"M": "1"})
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_has_changes_true():
    entries = diff_secrets(LOCAL, VAULT)
    assert has_changes(entries) is True


def test_has_changes_false():
    d = {"A": "1", "B": "2"}
    entries = diff_secrets(d, d)
    assert has_changes(entries) is False


def test_format_diff_symbols():
    entries = diff_secrets(LOCAL, VAULT)
    output = format_diff(entries)
    assert "+ NEW_KEY" in output
    assert "- OLD_KEY" in output
    assert "~ DB_PORT" in output
    assert "  DB_HOST" in output


def test_format_diff_show_values():
    entries = diff_secrets({"PORT": "9000"}, {"PORT": "8000"})
    output = format_diff(entries, show_values=True)
    assert "local='9000'" in output or "local=\"9000\"" in output or "local=" in output


def test_format_diff_empty():
    assert format_diff([]) == "(no keys)"
