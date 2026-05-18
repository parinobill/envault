"""Watch a .env file for changes and auto-push to the vault."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envault.dotenv_io import read_dotenv_file
from envault.store import save_secrets, load_secrets


class WatchError(Exception):
    """Raised when the watch loop encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    """Emitted each time a change is detected and pushed."""

    env_file: Path
    project: str
    changed_keys: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


def _file_hash(path: Path) -> str:
    """Return a SHA-256 hex digest of *path* contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _changed_keys(old: dict[str, str], new: dict[str, str]) -> list[str]:
    """Return keys that were added, removed, or whose value changed."""
    all_keys = set(old) | set(new)
    return [k for k in all_keys if old.get(k) != new.get(k)]


def watch(
    env_file: Path,
    project: str,
    passphrase: str,
    base_dir: Optional[Path] = None,
    interval: float = 2.0,
    on_change: Optional[Callable[[WatchEvent], None]] = None,
    _stop: Optional[Callable[[], bool]] = None,
) -> None:
    """Poll *env_file* every *interval* seconds; push changes to the vault.

    Args:
        env_file:   Path to the .env file to monitor.
        project:    Vault project name.
        passphrase: Encryption passphrase.
        base_dir:   Root directory for vault storage (default: ~/.envault).
        interval:   Polling interval in seconds.
        on_change:  Optional callback invoked with a WatchEvent on each push.
        _stop:      Optional callable; loop exits when it returns True
                    (used in tests to avoid infinite loops).
    """
    if not env_file.exists():
        raise WatchError(f"File not found: {env_file}")

    kwargs = {"base_dir": base_dir} if base_dir is not None else {}

    try:
        current_secrets = load_secrets(project, passphrase, **kwargs)
    except Exception:
        current_secrets = {}

    last_hash = _file_hash(env_file)

    while True:
        if _stop and _stop():
            break
        time.sleep(interval)
        if not env_file.exists():
            raise WatchError(f"Watched file disappeared: {env_file}")
        new_hash = _file_hash(env_file)
        if new_hash != last_hash:
            new_secrets = read_dotenv_file(env_file)
            changed = _changed_keys(current_secrets, new_secrets)
            if changed:
                save_secrets(project, new_secrets, passphrase, **kwargs)
                event = WatchEvent(
                    env_file=env_file,
                    project=project,
                    changed_keys=changed,
                )
                if on_change:
                    on_change(event)
                current_secrets = new_secrets
            last_hash = new_hash
