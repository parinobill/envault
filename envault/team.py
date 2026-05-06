"""Team sharing support: export/import encrypted vault bundles for sharing."""

from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import Optional

from envault.store import _vault_path, load_secrets, save_secrets
from envault.crypto import encrypt, decrypt


def export_bundle(
    project: str,
    passphrase: str,
    output_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """Export an encrypted vault bundle to a portable JSON file.

    The bundle contains the re-encrypted secrets so the recipient can import
    them with the *same* passphrase used here (team-shared passphrase).

    Returns the path of the written bundle file.
    """
    secrets = load_secrets(project, passphrase, base_dir=base_dir)

    # Re-encrypt the plaintext payload so the bundle is self-contained.
    payload = json.dumps(secrets).encode()
    blob = encrypt(payload, passphrase)

    bundle = {
        "project": project,
        "version": 1,
        "data": base64.b64encode(blob).decode(),
    }

    if output_path is None:
        output_path = Path(f"{project}.envault-bundle.json")

    output_path.write_text(json.dumps(bundle, indent=2))
    return output_path


def import_bundle(
    bundle_path: Path,
    passphrase: str,
    project: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> str:
    """Import secrets from a bundle file into the local vault.

    Returns the project name the secrets were stored under.
    """
    raw = json.loads(bundle_path.read_text())

    if raw.get("version") != 1:
        raise ValueError(f"Unsupported bundle version: {raw.get('version')}")

    blob = base64.b64decode(raw["data"])
    payload = decrypt(blob, passphrase)  # raises on wrong passphrase
    secrets: dict[str, str] = json.loads(payload.decode())

    target_project = project or raw["project"]
    save_secrets(target_project, secrets, passphrase, base_dir=base_dir)
    return target_project
