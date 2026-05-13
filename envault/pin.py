"""Pin a secret to a specific value, preventing accidental overwrites during push/pull."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class PinError(Exception):
    pass


def _pins_path(base_dir: str, project: str) -> Path:
    return Path(base_dir) / project / "pins.json"


def load_pins(base_dir: str, project: str) -> Dict[str, str]:
    """Return {key: pinned_value} for all pinned secrets."""
    path = _pins_path(base_dir, project)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_pins(base_dir: str, project: str, pins: Dict[str, str]) -> None:
    path = _pins_path(base_dir, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(pins, fh, indent=2)
        fh.write("\n")


def pin_secret(base_dir: str, project: str, key: str, value: str) -> None:
    """Pin *key* to *value*. Raises PinError if already pinned."""
    pins = load_pins(base_dir, project)
    if key in pins:
        raise PinError(f"Key '{key}' is already pinned to a value. Unpin it first.")
    pins[key] = value
    save_pins(base_dir, project, pins)


def unpin_secret(base_dir: str, project: str, key: str) -> None:
    """Remove the pin for *key*. Raises PinError if key is not pinned."""
    pins = load_pins(base_dir, project)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned.")
    del pins[key]
    save_pins(base_dir, project, pins)


def list_pins(base_dir: str, project: str) -> List[str]:
    """Return sorted list of pinned key names."""
    return sorted(load_pins(base_dir, project).keys())


def apply_pins(base_dir: str, project: str, secrets: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of *secrets* with pinned values restored."""
    pins = load_pins(base_dir, project)
    merged = dict(secrets)
    for key, value in pins.items():
        merged[key] = value
    return merged
