"""Tests for envault.merge."""

from __future__ import annotations

import pytest

from envault.merge import MergeError, MergeResult, merge_secrets
from envault.store import load_secrets, save_secrets


@pytest.fixture()
def vault_base(tmp_path):
    return str(tmp_path)


def _make_vault(base, project, passphrase, secrets):
    save_secrets(project, secrets, passphrase, base_dir=base)


# ---------------------------------------------------------------------------
# MergeResult helpers
# ---------------------------------------------------------------------------

def test_merge_result_total_changed():
    r = MergeResult(added=["A", "B"], overwritten=["C"], skipped=["D"])
    assert r.total_changed == 3


# ---------------------------------------------------------------------------
# merge_secrets — happy paths
# ---------------------------------------------------------------------------

def test_merge_adds_new_keys(vault_base):
    _make_vault(vault_base, "src", "src-pass", {"FOO": "foo", "BAR": "bar"})
    _make_vault(vault_base, "dst", "dst-pass", {"BAZ": "baz"})

    result = merge_secrets("src", "dst", "src-pass", "dst-pass", base_dir=vault_base)

    assert set(result.added) == {"FOO", "BAR"}
    assert result.skipped == []
    assert result.overwritten == []

    merged = load_secrets("dst", "dst-pass", base_dir=vault_base)
    assert merged["FOO"] == "foo"
    assert merged["BAR"] == "bar"
    assert merged["BAZ"] == "baz"


def test_merge_skips_existing_without_overwrite(vault_base):
    _make_vault(vault_base, "src", "sp", {"KEY": "new-value"})
    _make_vault(vault_base, "dst", "dp", {"KEY": "old-value"})

    result = merge_secrets("src", "dst", "sp", "dp", base_dir=vault_base)

    assert result.skipped == ["KEY"]
    assert result.added == []
    dst = load_secrets("dst", "dp", base_dir=vault_base)
    assert dst["KEY"] == "old-value"


def test_merge_overwrites_when_flag_set(vault_base):
    _make_vault(vault_base, "src", "sp", {"KEY": "new-value"})
    _make_vault(vault_base, "dst", "dp", {"KEY": "old-value"})

    result = merge_secrets("src", "dst", "sp", "dp", overwrite=True, base_dir=vault_base)

    assert result.overwritten == ["KEY"]
    dst = load_secrets("dst", "dp", base_dir=vault_base)
    assert dst["KEY"] == "new-value"


def test_merge_specific_keys_only(vault_base):
    _make_vault(vault_base, "src", "sp", {"A": "1", "B": "2", "C": "3"})
    _make_vault(vault_base, "dst", "dp", {})

    result = merge_secrets("src", "dst", "sp", "dp", keys=["A", "C"], base_dir=vault_base)

    assert set(result.added) == {"A", "C"}
    dst = load_secrets("dst", "dp", base_dir=vault_base)
    assert "B" not in dst


# ---------------------------------------------------------------------------
# merge_secrets — error paths
# ---------------------------------------------------------------------------

def test_merge_missing_src_raises(vault_base):
    _make_vault(vault_base, "dst", "dp", {})
    with pytest.raises(MergeError, match="Source vault"):
        merge_secrets("no-such-src", "dst", "sp", "dp", base_dir=vault_base)


def test_merge_missing_dst_raises(vault_base):
    _make_vault(vault_base, "src", "sp", {"K": "v"})
    with pytest.raises(MergeError, match="Destination vault"):
        merge_secrets("src", "no-such-dst", "sp", "dp", base_dir=vault_base)


def test_merge_missing_specific_key_raises(vault_base):
    _make_vault(vault_base, "src", "sp", {"A": "1"})
    _make_vault(vault_base, "dst", "dp", {})
    with pytest.raises(MergeError, match="Keys not found"):
        merge_secrets("src", "dst", "sp", "dp", keys=["A", "MISSING"], base_dir=vault_base)
