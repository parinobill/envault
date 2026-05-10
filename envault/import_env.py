"""Import secrets from external sources (dotenv file, JSON, CSV) into the vault."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Dict

from envault.dotenv_io import parse_dotenv
from envault.store import save_secrets, load_secrets, vault_exists


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _from_dotenv(text: str) -> Dict[str, str]:
    return parse_dotenv(text)


def _from_json(text: str) -> Dict[str, str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    bad = [k for k, v in data.items() if not isinstance(v, str)]
    if bad:
        raise ImportError(f"All values must be strings; bad keys: {bad}")
    return data


def _from_csv(text: str) -> Dict[str, str]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or set(reader.fieldnames) < {"key", "value"}:
        raise ImportError("CSV must have 'key' and 'value' columns")
    result: Dict[str, str] = {}
    for row in reader:
        result[row["key"]] = row["value"]
    return result


_PARSERS = {
    "dotenv": _from_dotenv,
    "json": _from_json,
    "csv": _from_csv,
}


def import_secrets(
    source_path: Path,
    passphrase: str,
    *,
    fmt: str = "dotenv",
    project: str = "default",
    merge: bool = False,
    base_dir: Path | None = None,
) -> int:
    """Import secrets from *source_path* into the vault.

    Args:
        source_path: Path to the file being imported.
        passphrase: Vault passphrase.
        fmt: One of 'dotenv', 'json', 'csv'.
        project: Project name.
        merge: If True, merge with existing secrets; otherwise overwrite.
        base_dir: Override vault base directory (used in tests).

    Returns:
        Number of secrets imported.
    """
    if fmt not in _PARSERS:
        raise ImportError(f"Unknown format '{fmt}'. Choose from: {list(_PARSERS)}")

    text = source_path.read_text(encoding="utf-8")
    incoming = _PARSERS[fmt](text)

    if not incoming:
        raise ImportError("No secrets found in source file")

    if merge and vault_exists(project=project, base_dir=base_dir):
        existing = load_secrets(passphrase, project=project, base_dir=base_dir)
        existing.update(incoming)
        secrets = existing
    else:
        secrets = incoming

    kwargs = {"project": project}
    if base_dir is not None:
        kwargs["base_dir"] = base_dir
    save_secrets(secrets, passphrase, **kwargs)
    return len(incoming)
