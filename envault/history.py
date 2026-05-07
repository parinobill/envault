"""Secret version history tracking for envault vaults."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_FILENAME = "history.jsonl"


def _history_path(base_dir: str, project: str) -> Path:
    """Return the path to the history file for a project."""
    return Path(base_dir) / project / HISTORY_FILENAME


def record_snapshot(
    base_dir: str,
    project: str,
    secrets: dict[str, str],
    actor: str = "local",
    action: str = "push",
) -> None:
    """Append a snapshot of current secrets to the project history."""
    path = _history_path(base_dir, project)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "keys": sorted(secrets.keys()),
        "count": len(secrets),
    }

    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_history(base_dir: str, project: str) -> list[dict[str, Any]]:
    """Return all history entries for a project, oldest first."""
    path = _history_path(base_dir, project)
    if not path.exists():
        return []

    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def format_history(entries: list[dict[str, Any]]) -> str:
    """Return a human-readable summary of history entries."""
    if not entries:
        return "No history recorded."

    lines: list[str] = []
    for i, entry in enumerate(entries, 1):
        ts = entry.get("timestamp", "unknown")
        actor = entry.get("actor", "?")
        action = entry.get("action", "?")
        count = entry.get("count", 0)
        keys = ", ".join(entry.get("keys", []))
        lines.append(f"[{i}] {ts}  actor={actor}  action={action}  secrets={count}")
        if keys:
            lines.append(f"     keys: {keys}")
    return "\n".join(lines)


def history_exists(base_dir: str, project: str) -> bool:
    """Return True if a history file exists for the project."""
    return _history_path(base_dir, project).exists()
