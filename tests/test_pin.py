"""Tests for envault.pin module."""

import json
import pytest

from envault.pin import (
    PinError,
    _pins_path,
    apply_pins,
    list_pins,
    load_pins,
    pin_secret,
    save_pins,
    unpin_secret,
)


@pytest.fixture()
def base(tmp_path):
    return str(tmp_path)


def test_load_pins_missing_file_returns_empty(base):
    assert load_pins(base, "proj") == {}


def test_pins_path_structure(base):
    path = _pins_path(base, "myproject")
    assert path.name == "pins.json"
    assert path.parent.name == "myproject"


def test_save_and_load_roundtrip(base):
    pins = {"DB_PASS": "secret", "API_KEY": "abc123"}
    save_pins(base, "proj", pins)
    loaded = load_pins(base, "proj")
    assert loaded == pins


def test_save_creates_parent_dirs(base, tmp_path):
    deep_base = str(tmp_path / "a" / "b" / "c")
    save_pins(deep_base, "proj", {"X": "1"})
    assert _pins_path(deep_base, "proj").exists()


def test_pin_secret_adds_key(base):
    pin_secret(base, "proj", "TOKEN", "mytoken")
    pins = load_pins(base, "proj")
    assert pins["TOKEN"] == "mytoken"


def test_pin_secret_already_pinned_raises(base):
    pin_secret(base, "proj", "TOKEN", "v1")
    with pytest.raises(PinError, match="already pinned"):
        pin_secret(base, "proj", "TOKEN", "v2")


def test_unpin_secret_removes_key(base):
    pin_secret(base, "proj", "TOKEN", "v1")
    unpin_secret(base, "proj", "TOKEN")
    assert "TOKEN" not in load_pins(base, "proj")


def test_unpin_missing_key_raises(base):
    with pytest.raises(PinError, match="not pinned"):
        unpin_secret(base, "proj", "GHOST")


def test_list_pins_returns_sorted(base):
    save_pins(base, "proj", {"Z_KEY": "z", "A_KEY": "a", "M_KEY": "m"})
    assert list_pins(base, "proj") == ["A_KEY", "M_KEY", "Z_KEY"]


def test_list_pins_empty(base):
    assert list_pins(base, "proj") == []


def test_apply_pins_overrides_secrets(base):
    pin_secret(base, "proj", "DB_PASS", "pinned_value")
    secrets = {"DB_PASS": "runtime_value", "OTHER": "unchanged"}
    result = apply_pins(base, "proj", secrets)
    assert result["DB_PASS"] == "pinned_value"
    assert result["OTHER"] == "unchanged"


def test_apply_pins_adds_missing_pinned_key(base):
    pin_secret(base, "proj", "FORCED", "forced_val")
    secrets = {"OTHER": "x"}
    result = apply_pins(base, "proj", secrets)
    assert result["FORCED"] == "forced_val"


def test_apply_pins_no_pins_returns_copy(base):
    secrets = {"A": "1", "B": "2"}
    result = apply_pins(base, "proj", secrets)
    assert result == secrets
    assert result is not secrets


def test_pins_file_is_valid_json(base):
    pin_secret(base, "proj", "KEY", "val")
    path = _pins_path(base, "proj")
    with path.open() as fh:
        data = json.load(fh)
    assert data == {"KEY": "val"}
