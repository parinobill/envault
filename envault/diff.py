"""Diff utilities for comparing local .env files against vault secrets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    local_value: Optional[str] = None
    vault_value: Optional[str] = None


def diff_secrets(
    local: Dict[str, str],
    vault: Dict[str, str],
) -> List[DiffEntry]:
    """Compare local env dict against vault dict and return diff entries."""
    entries: List[DiffEntry] = []
    all_keys = set(local) | set(vault)

    for key in sorted(all_keys):
        in_local = key in local
        in_vault = key in vault

        if in_local and not in_vault:
            entries.append(DiffEntry(key=key, status="added", local_value=local[key]))
        elif in_vault and not in_local:
            entries.append(DiffEntry(key=key, status="removed", vault_value=vault[key]))
        elif local[key] != vault[key]:
            entries.append(
                DiffEntry(
                    key=key,
                    status="changed",
                    local_value=local[key],
                    vault_value=vault[key],
                )
            )
        else:
            entries.append(
                DiffEntry(
                    key=key,
                    status="unchanged",
                    local_value=local[key],
                    vault_value=vault[key],
                )
            )

    return entries


def format_diff(entries: List[DiffEntry], show_values: bool = False) -> str:
    """Render diff entries as a human-readable string."""
    if not entries:
        return "(no keys)"

    lines: List[str] = []
    symbols = {"added": "+", "removed": "-", "changed": "~", "unchanged": " "}

    for entry in entries:
        sym = symbols[entry.status]
        if show_values and entry.status == "changed":
            lines.append(f"{sym} {entry.key}  (local={entry.local_value!r} vault={entry.vault_value!r})")
        else:
            lines.append(f"{sym} {entry.key}")

    return "\n".join(lines)


def has_changes(entries: List[DiffEntry]) -> bool:
    """Return True if any entry is not 'unchanged'."""
    return any(e.status != "unchanged" for e in entries)
