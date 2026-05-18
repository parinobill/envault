"""Vault backup and restore utilities."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from envault.store import _vault_path, load_secrets, save_secrets, vault_exists


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backup_dir(base: Path, project: str) -> Path:
    return base / project / "backups"


def _backup_filename(label: str | None = None) -> str:
    ts = int(time.time())
    suffix = f"_{label}" if label else ""
    return f"vault_{ts}{suffix}.json"


def create_backup(
    base: Path,
    project: str,
    passphrase: str,
    label: str | None = None,
) -> Path:
    """Decrypt vault and write a plaintext JSON backup. Returns backup path."""
    if not vault_exists(base, project):
        raise BackupError(f"No vault found for project '{project}'.")

    secrets = load_secrets(base, project, passphrase)
    backup_dir = _backup_dir(base, project)
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / _backup_filename(label)
    backup_path.write_text(
        json.dumps({"project": project, "secrets": secrets}, indent=2),
        encoding="utf-8",
    )
    return backup_path


def restore_backup(
    base: Path,
    project: str,
    backup_path: Path,
    passphrase: str,
) -> int:
    """Read a plaintext JSON backup and re-encrypt it into the vault.

    Returns the number of secrets restored.
    """
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")

    try:
        data = json.loads(backup_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BackupError(f"Invalid backup file: {exc}") from exc

    if "secrets" not in data or not isinstance(data["secrets"], dict):
        raise BackupError("Backup file is missing 'secrets' mapping.")

    secrets: dict[str, str] = data["secrets"]
    save_secrets(base, project, passphrase, secrets)
    return len(secrets)


def list_backups(base: Path, project: str) -> list[Path]:
    """Return sorted list of backup files for *project* (oldest first)."""
    backup_dir = _backup_dir(base, project)
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob("vault_*.json"))
