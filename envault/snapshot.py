"""Snapshot comparison: compare vault state against a previous history entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envault.history import read_history
from envault.diff import DiffEntry, diff_secrets, format_diff, has_changes


@dataclass
class SnapshotResult:
    index: int
    timestamp: str
    entries: list[DiffEntry]

    @property
    def has_changes(self) -> bool:
        return has_changes(self.entries)


class SnapshotError(Exception):
    pass


def compare_to_snapshot(
    base_dir: str,
    project: str,
    current_secrets: dict[str, str],
    snapshot_index: int = -1,
) -> SnapshotResult:
    """Compare *current_secrets* against a historical snapshot.

    *snapshot_index* follows Python list semantics (-1 = latest).
    Raises SnapshotError when no history is available or index is out of range.
    """
    history = read_history(base_dir, project)
    if not history:
        raise SnapshotError(f"No history found for project '{project}'.")

    try:
        entry = history[snapshot_index]
    except IndexError:
        raise SnapshotError(
            f"Snapshot index {snapshot_index} out of range "
            f"(history has {len(history)} entries)."
        )

    past_secrets: dict[str, str] = entry.get("secrets", {})
    timestamp: str = entry.get("timestamp", "unknown")
    real_index = snapshot_index if snapshot_index >= 0 else len(history) + snapshot_index

    diff_entries = diff_secrets(past_secrets, current_secrets)
    return SnapshotResult(index=real_index, timestamp=timestamp, entries=diff_entries)


def format_snapshot_result(result: SnapshotResult) -> str:
    """Return a human-readable summary of a snapshot comparison."""
    lines = [
        f"Comparing against snapshot #{result.index} ({result.timestamp})",
        "-" * 50,
    ]
    if result.has_changes:
        lines.append(format_diff(result.entries))
    else:
        lines.append("No changes since that snapshot.")
    return "\n".join(lines)


def list_snapshots(base_dir: str, project: str) -> list[dict]:
    """Return a summary list of available snapshots for *project*.

    Each item contains ``index``, ``timestamp``, and ``secret_count`` keys.
    Returns an empty list when no history exists.
    """
    history = read_history(base_dir, project)
    return [
        {
            "index": i,
            "timestamp": entry.get("timestamp", "unknown"),
            "secret_count": len(entry.get("secrets", {})),
        }
        for i, entry in enumerate(history)
    ]
