"""Merge secrets from one project vault into another."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envault.store import load_secrets, save_secrets, vault_exists


class MergeError(Exception):
    """Raised when a merge operation fails."""


@dataclass
class MergeResult:
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.added) + len(self.overwritten)


def merge_secrets(
    src_project: str,
    dst_project: str,
    src_passphrase: str,
    dst_passphrase: str,
    *,
    overwrite: bool = False,
    keys: List[str] | None = None,
    base_dir: str | None = None,
) -> MergeResult:
    """Merge secrets from *src_project* into *dst_project*.

    Args:
        src_project: Name of the source project vault.
        dst_project: Name of the destination project vault.
        src_passphrase: Passphrase for the source vault.
        dst_passphrase: Passphrase for the destination vault.
        overwrite: When True, existing keys in the destination are overwritten.
        keys: Optional list of specific keys to merge; None means all keys.
        base_dir: Override the base directory for vault storage.

    Returns:
        A :class:`MergeResult` summarising what changed.
    """
    kwargs: Dict = {} if base_dir is None else {"base_dir": base_dir}

    if not vault_exists(src_project, **kwargs):
        raise MergeError(f"Source vault '{src_project}' does not exist.")
    if not vault_exists(dst_project, **kwargs):
        raise MergeError(f"Destination vault '{dst_project}' does not exist.")

    src_secrets = load_secrets(src_project, src_passphrase, **kwargs)
    dst_secrets = load_secrets(dst_project, dst_passphrase, **kwargs)

    candidates = {k: v for k, v in src_secrets.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_secrets)
        if missing:
            raise MergeError(
                f"Keys not found in source vault: {', '.join(sorted(missing))}"
            )

    result = MergeResult()
    for key, value in candidates.items():
        if key in dst_secrets:
            if overwrite:
                dst_secrets[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            dst_secrets[key] = value
            result.added.append(key)

    save_secrets(dst_project, dst_secrets, dst_passphrase, **kwargs)
    return result
