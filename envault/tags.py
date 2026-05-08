"""Tag management for envault secrets — attach labels to keys for grouping and filtering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TagError(Exception):
    pass


def _tags_path(base_dir: Path, project: str) -> Path:
    return base_dir / project / "tags.json"


def load_tags(base_dir: Path, project: str) -> Dict[str, List[str]]:
    """Return mapping of key -> list of tags. Empty dict if no tags file."""
    path = _tags_path(base_dir, project)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file: {exc}") from exc
    if not isinstance(data, dict):
        raise TagError("Tags file must contain a JSON object.")
    return {k: list(v) for k, v in data.items()}


def save_tags(base_dir: Path, project: str, tags: Dict[str, List[str]]) -> None:
    """Persist the key->tags mapping to disk."""
    path = _tags_path(base_dir, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tags, indent=2, sort_keys=True))


def add_tag(base_dir: Path, project: str, key: str, tag: str) -> None:
    """Add *tag* to *key*. No-op if already present."""
    tags = load_tags(base_dir, project)
    existing = tags.get(key, [])
    if tag not in existing:
        existing.append(tag)
    tags[key] = existing
    save_tags(base_dir, project, tags)


def remove_tag(base_dir: Path, project: str, key: str, tag: str) -> None:
    """Remove *tag* from *key*. No-op if not present."""
    tags = load_tags(base_dir, project)
    existing = tags.get(key, [])
    tags[key] = [t for t in existing if t != tag]
    if not tags[key]:
        del tags[key]
    save_tags(base_dir, project, tags)


def filter_by_tag(base_dir: Path, project: str, tag: str) -> List[str]:
    """Return list of keys that carry the given *tag*."""
    tags = load_tags(base_dir, project)
    return [key for key, key_tags in tags.items() if tag in key_tags]


def format_tags(tags: Dict[str, List[str]]) -> str:
    """Human-readable representation of the tags mapping."""
    if not tags:
        return "(no tags defined)"
    lines = []
    for key in sorted(tags):
        label_list = ", ".join(sorted(tags[key]))
        lines.append(f"  {key}: [{label_list}]")
    return "\n".join(lines)
