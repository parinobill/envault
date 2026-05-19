"""Tests for envault.promote."""

import pytest

from envault.store import save_secrets, load_secrets
from envault.promote import PromoteError, PromoteResult, promote_secrets


@pytest.fixture()
def vault_base(tmp_path):
    """Return a base_dir with two pre-populated vaults."""
    base = str(tmp_path)
    save_secrets("staging", {"DB_URL": "postgres://staging", "API_KEY": "s3cr3t"}, "pass-src", base_dir=base)
    save_secrets("production", {"DB_URL": "postgres://prod"}, "pass-dst", base_dir=base)
    return base


def test_promote_result_total_changed():
    r = PromoteResult(promoted=["A", "B"], skipped=["C"], overwritten=["D"])
    assert r.total_changed == 3


def test_promote_adds_new_key(vault_base):
    result = promote_secrets(
        "staging", "production", "pass-src", "pass-dst",
        keys=["API_KEY"], base_dir=vault_base
    )
    assert "API_KEY" in result.promoted
    secrets = load_secrets("production", "pass-dst", base_dir=vault_base)
    assert secrets["API_KEY"] == "s3cr3t"


def test_promote_skips_existing_without_overwrite(vault_base):
    result = promote_secrets(
        "staging", "production", "pass-src", "pass-dst",
        keys=["DB_URL"], base_dir=vault_base
    )
    assert "DB_URL" in result.skipped
    # destination value unchanged
    secrets = load_secrets("production", "pass-dst", base_dir=vault_base)
    assert secrets["DB_URL"] == "postgres://prod"


def test_promote_overwrites_when_flag_set(vault_base):
    result = promote_secrets(
        "staging", "production", "pass-src", "pass-dst",
        keys=["DB_URL"], overwrite=True, base_dir=vault_base
    )
    assert "DB_URL" in result.overwritten
    secrets = load_secrets("production", "pass-dst", base_dir=vault_base)
    assert secrets["DB_URL"] == "postgres://staging"


def test_promote_all_keys(vault_base):
    result = promote_secrets(
        "staging", "production", "pass-src", "pass-dst",
        overwrite=True, base_dir=vault_base
    )
    assert result.total_changed == 2


def test_promote_missing_source_vault_raises(tmp_path):
    base = str(tmp_path)
    save_secrets("production", {}, "pass-dst", base_dir=base)
    with pytest.raises(PromoteError, match="Source vault"):
        promote_secrets("staging", "production", "p", "p", base_dir=base)


def test_promote_missing_dest_vault_raises(tmp_path):
    base = str(tmp_path)
    save_secrets("staging", {"K": "V"}, "pass-src", base_dir=base)
    with pytest.raises(PromoteError, match="Destination vault"):
        promote_secrets("staging", "production", "pass-src", "p", base_dir=base)


def test_promote_missing_key_raises(vault_base):
    with pytest.raises(PromoteError, match="Keys not found"):
        promote_secrets(
            "staging", "production", "pass-src", "pass-dst",
            keys=["NONEXISTENT"], base_dir=vault_base
        )


def test_promote_preserves_other_dst_keys(vault_base):
    promote_secrets(
        "staging", "production", "pass-src", "pass-dst",
        keys=["API_KEY"], base_dir=vault_base
    )
    secrets = load_secrets("production", "pass-dst", base_dir=vault_base)
    assert "DB_URL" in secrets  # original key still present
