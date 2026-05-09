"""Search and filter secrets by key pattern or tag."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_secrets
from envault.tags import load_tags


@dataclass
class SearchResult:
    key: str
    value: str
    tags: List[str] = field(default_factory=list)


class SearchError(Exception):
    pass


def search_secrets(
    base_dir: str,
    project: str,
    passphrase: str,
    *,
    pattern: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[SearchResult]:
    """Return secrets matching *pattern* (glob) and/or *tag*.

    At least one of *pattern* or *tag* must be supplied.

    Args:
        base_dir: Root directory where project vaults are stored.
        project: Name of the project whose secrets to search.
        passphrase: Decryption passphrase for the vault.
        pattern: Optional glob pattern matched against secret keys (e.g. ``"DB_*"``).
        tag: Optional tag name; only secrets carrying this tag are returned.

    Returns:
        A list of :class:`SearchResult` objects sorted alphabetically by key.

    Raises:
        SearchError: If neither *pattern* nor *tag* is provided.
    """
    if pattern is None and tag is None:
        raise SearchError("Provide at least one of: pattern, tag")

    secrets: Dict[str, str] = load_secrets(base_dir, project, passphrase)
    tags_map: Dict[str, List[str]] = load_tags(base_dir, project)

    results: List[SearchResult] = []
    for key, value in secrets.items():
        key_tags = tags_map.get(key, [])

        if pattern is not None and not fnmatch.fnmatch(key, pattern):
            continue
        if tag is not None and tag not in key_tags:
            continue

        results.append(SearchResult(key=key, value=value, tags=key_tags))

    results.sort(key=lambda r: r.key)
    return results


def format_results(results: List[SearchResult], *, show_values: bool = False) -> str:
    """Return a human-readable table of search results.

    Args:
        results: The list of :class:`SearchResult` objects to format.
        show_values: When ``True``, include the secret value in the output.
            Defaults to ``False`` to avoid accidental exposure.

    Returns:
        A newline-separated string of formatted result lines, or a message
        indicating that no matching secrets were found.
    """
    if not results:
        return "No matching secrets found."

    lines: List[str] = []
    for r in results:
        tag_str = "  [" + ", ".join(r.tags) + "]" if r.tags else ""
        if show_values:
            lines.append(f"{r.key}={r.value}{tag_str}")
        else:
            lines.append(f"{r.key}{tag_str}")
    return "\n".join(lines)
