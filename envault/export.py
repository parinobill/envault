"""Export secrets to various plain-text formats (dotenv, JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import Dict, Literal

ExportFormat = Literal["dotenv", "json", "csv"]


class ExportError(Exception):
    """Raised when an unsupported export format is requested."""


def export_secrets(
    secrets: Dict[str, str],
    fmt: ExportFormat = "dotenv",
) -> str:
    """Serialize *secrets* to the requested plain-text format.

    Args:
        secrets: Mapping of key -> value pairs to export.
        fmt:     One of ``"dotenv"``, ``"json"``, or ``"csv"``.

    Returns:
        A string in the requested format.

    Raises:
        ExportError: If *fmt* is not supported.
    """
    if fmt == "dotenv":
        return _to_dotenv(secrets)
    if fmt == "json":
        return _to_json(secrets)
    if fmt == "csv":
        return _to_csv(secrets)
    raise ExportError(f"Unsupported export format: {fmt!r}")


def _to_dotenv(secrets: Dict[str, str]) -> str:
    lines = []
    for key, value in secrets.items():
        # Quote values that contain spaces or special characters.
        if any(c in value for c in (" ", "\t", "#", "'", '"')):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def _to_json(secrets: Dict[str, str]) -> str:
    return json.dumps(secrets, indent=2) + "\n"


def _to_csv(secrets: Dict[str, str]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["key", "value"])
    for key, value in secrets.items():
        writer.writerow([key, value])
    return buf.getvalue()
