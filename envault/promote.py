"""Promote secrets from one project environment to another (e.g. staging -> production)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_secrets, save_secrets, vault_exists


class PromoteError(Exception):
    """Raised when promotion fails."""


@dataclass
class PromoteResult:
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.promoted) + len(self.overwritten)


def promote_secrets(
    src_project: str,
    dst_project: str,
    src_passphrase: str,
    dst_passphrase: str,
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    base_dir: Optional[str] = None,
) -> PromoteResult:
    """Copy secrets from *src_project* vault into *dst_project* vault.

    Args:
        src_project: Name of the source project.
        dst_project: Name of the destination project.
        src_passphrase: Passphrase for the source vault.
        dst_passphrase: Passphrase for the destination vault.
        keys: Optional list of specific keys to promote.  Promotes all if None.
        overwrite: If True, existing keys in the destination are overwritten.
        base_dir: Override the base directory used for vault paths (testing).

    Returns:
        A :class:`PromoteResult` describing what changed.
    """
    kwargs: Dict = {} if base_dir is None else {"base_dir": base_dir}

    if not vault_exists(src_project, **kwargs):
        raise PromoteError(f"Source vault '{src_project}' does not exist.")

    if not vault_exists(dst_project, **kwargs):
        raise PromoteError(f"Destination vault '{dst_project}' does not exist.")

    src_secrets = load_secrets(src_project, src_passphrase, **kwargs)
    dst_secrets = load_secrets(dst_project, dst_passphrase, **kwargs)

    candidates = keys if keys is not None else list(src_secrets.keys())

    # Validate requested keys exist in source
    missing = [k for k in candidates if k not in src_secrets]
    if missing:
        raise PromoteError(
            f"Keys not found in source vault: {', '.join(sorted(missing))}"
        )

    result = PromoteResult()

    for key in candidates:
        if key in dst_secrets:
            if overwrite:
                dst_secrets[key] = src_secrets[key]
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            dst_secrets[key] = src_secrets[key]
            result.promoted.append(key)

    save_secrets(dst_project, dst_secrets, dst_passphrase, **kwargs)
    return result
