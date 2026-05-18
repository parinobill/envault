"""Per-key access control: restrict which keys a given identity can read."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AccessError(Exception):
    """Raised when an access-control operation fails."""


def _access_path(base: Path, project: str) -> Path:
    return base / project / "access.json"


def load_acl(base: Path, project: str) -> Dict[str, List[str]]:
    """Return mapping of key -> list of allowed identities.

    An empty list means *all* identities are allowed (open).
    Returns an empty dict when no ACL file exists.
    """
    path = _access_path(base, project)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_acl(base: Path, project: str, acl: Dict[str, List[str]]) -> None:
    """Persist the ACL mapping to disk."""
    path = _access_path(base, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(acl, fh, indent=2)
        fh.write("\n")


def grant(base: Path, project: str, key: str, identity: str) -> None:
    """Grant *identity* read access to *key*."""
    acl = load_acl(base, project)
    identities = acl.get(key, [])
    if identity not in identities:
        identities.append(identity)
    acl[key] = identities
    save_acl(base, project, acl)


def revoke(base: Path, project: str, key: str, identity: str) -> None:
    """Revoke *identity* read access to *key*."""
    acl = load_acl(base, project)
    identities = acl.get(key, [])
    if identity not in identities:
        raise AccessError(f"Identity '{identity}' does not have access to '{key}'.")
    identities.remove(identity)
    acl[key] = identities
    save_acl(base, project, acl)


def is_allowed(base: Path, project: str, key: str, identity: str) -> bool:
    """Return True when *identity* may read *key*.

    If the key has no ACL entry (or an empty list), access is open to all.
    """
    acl = load_acl(base, project)
    allowed = acl.get(key, [])
    return len(allowed) == 0 or identity in allowed


def filter_secrets(
    base: Path,
    project: str,
    secrets: Dict[str, str],
    identity: Optional[str],
) -> Dict[str, str]:
    """Return only the secrets that *identity* is allowed to read.

    When *identity* is None all secrets are returned (admin / passphrase-only
    access).
    """
    if identity is None:
        return dict(secrets)
    return {
        k: v
        for k, v in secrets.items()
        if is_allowed(base, project, k, identity)
    }
