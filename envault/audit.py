"""Audit log for vault operations — records who did what and when."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

_AUDIT_FILENAME = ".envault_audit.jsonl"


def _audit_path(project: str, base_dir: Path | None = None) -> Path:
    """Return the path to the audit log for *project*."""
    root = base_dir if base_dir is not None else Path.cwd()
    return root / project / _AUDIT_FILENAME


def record_event(
    project: str,
    action: str,
    actor: str | None = None,
    keys: List[str] | None = None,
    base_dir: Path | None = None,
) -> None:
    """Append a single audit event to the project's audit log.

    Parameters
    ----------
    project:
        Name of the envault project (used to locate the log file).
    action:
        Short verb describing the operation, e.g. ``"push"``, ``"pull"``.
    actor:
        Optional identifier for who performed the action (defaults to the
        current OS username).
    keys:
        Optional list of secret key names that were affected.
    base_dir:
        Override the directory that contains project vaults (defaults to cwd).
    """
    if actor is None:
        actor = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    event: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "action": action,
        "actor": actor,
    }
    if keys is not None:
        event["keys"] = keys

    log_path = _audit_path(project, base_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def read_events(
    project: str,
    base_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    """Return all audit events for *project* as a list of dicts."""
    log_path = _audit_path(project, base_dir)
    if not log_path.exists():
        return []
    events: List[Dict[str, Any]] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def format_events(events: List[Dict[str, Any]]) -> str:
    """Return a human-readable table of *events*."""
    if not events:
        return "(no audit events recorded)"
    lines = [f"{'TIMESTAMP':<32} {'ACTOR':<16} {'ACTION':<10} KEYS"]
    lines.append("-" * 72)
    for ev in events:
        keys_str = ", ".join(ev.get("keys") or []) or "-"
        lines.append(
            f"{ev.get('timestamp', ''):<32} "
            f"{ev.get('actor', ''):<16} "
            f"{ev.get('action', ''):<10} "
            f"{keys_str}"
        )
    return "\n".join(lines)
