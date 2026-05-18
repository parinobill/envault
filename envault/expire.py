"""Secret expiry / TTL management for envault."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryEntry:
    key: str
    expires_at: float  # Unix timestamp
    note: str = ""

    def is_expired(self, now: Optional[float] = None) -> bool:
        t = now if now is not None else time.time()
        return t >= self.expires_at

    def seconds_remaining(self, now: Optional[float] = None) -> float:
        t = now if now is not None else time.time()
        return max(0.0, self.expires_at - t)


def _expiry_path(base_dir: Path, project: str) -> Path:
    return base_dir / project / "expiry.json"


def load_expiry(base_dir: Path, project: str) -> Dict[str, ExpiryEntry]:
    path = _expiry_path(base_dir, project)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {
        k: ExpiryEntry(key=k, expires_at=v["expires_at"], note=v.get("note", ""))
        for k, v in data.items()
    }


def save_expiry(base_dir: Path, project: str, entries: Dict[str, ExpiryEntry]) -> None:
    path = _expiry_path(base_dir, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        k: {"expires_at": e.expires_at, "note": e.note}
        for k, e in entries.items()
    }
    path.write_text(json.dumps(data, indent=2))


def set_expiry(base_dir: Path, project: str, key: str, ttl_seconds: float, note: str = "") -> ExpiryEntry:
    """Set a TTL (in seconds from now) for *key*."""
    if ttl_seconds <= 0:
        raise ExpireError("ttl_seconds must be positive")
    entries = load_expiry(base_dir, project)
    entry = ExpiryEntry(key=key, expires_at=time.time() + ttl_seconds, note=note)
    entries[key] = entry
    save_expiry(base_dir, project, entries)
    return entry


def remove_expiry(base_dir: Path, project: str, key: str) -> None:
    """Remove any expiry rule for *key*."""
    entries = load_expiry(base_dir, project)
    entries.pop(key, None)
    save_expiry(base_dir, project, entries)


def get_expired_keys(base_dir: Path, project: str, now: Optional[float] = None) -> List[str]:
    """Return list of keys whose TTL has elapsed."""
    entries = load_expiry(base_dir, project)
    return [k for k, e in entries.items() if e.is_expired(now)]


def format_expiry(entries: Dict[str, ExpiryEntry], now: Optional[float] = None) -> str:
    if not entries:
        return "No expiry rules set."
    lines = []
    for key, entry in sorted(entries.items()):
        remaining = entry.seconds_remaining(now)
        status = "EXPIRED" if entry.is_expired(now) else f"{remaining:.0f}s remaining"
        note_part = f"  # {entry.note}" if entry.note else ""
        lines.append(f"  {key}: {status}{note_part}")
    return "\n".join(lines)
