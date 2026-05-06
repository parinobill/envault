"""Helpers for importing/exporting plain .env files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


def parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file text into a dict, skipping comments and blank lines."""
    result: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def render_dotenv(secrets: Dict[str, str]) -> str:
    """Render a secrets dict as .env file text (keys sorted for determinism)."""
    lines = []
    for key in sorted(secrets.keys()):
        value = secrets[key]
        # Quote values that contain spaces or special characters
        if any(c in value for c in (" ", "#", "'", '"', "\n")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def read_dotenv_file(path: str | Path) -> Dict[str, str]:
    """Read and parse a .env file from *path*."""
    content = Path(path).read_text(encoding="utf-8")
    return parse_dotenv(content)


def write_dotenv_file(secrets: Dict[str, str], path: str | Path) -> None:
    """Write secrets dict to a plain .env file at *path*."""
    Path(path).write_text(render_dotenv(secrets), encoding="utf-8")
