"""Template rendering: substitute vault secrets into template files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.store import load_secrets

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    output: str
    resolved: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def has_missing(self) -> bool:
        return bool(self.missing)


def render_template(
    template_text: str,
    secrets: Dict[str, str],
    *,
    strict: bool = False,
) -> RenderResult:
    """Replace ``{{ KEY }}`` placeholders with values from *secrets*.

    Parameters
    ----------
    template_text:
        Raw template string containing ``{{ KEY }}`` placeholders.
    secrets:
        Mapping of secret key -> plaintext value.
    strict:
        If *True*, raise :class:`TemplateError` when a placeholder has no
        matching secret.  If *False*, leave the placeholder unchanged.
    """
    resolved: List[str] = []
    missing: List[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in secrets:
            resolved.append(key)
            return secrets[key]
        missing.append(key)
        if strict:
            raise TemplateError(f"Missing secret for placeholder: {key!r}")
        return match.group(0)

    output = _PLACEHOLDER_RE.sub(_replace, template_text)
    return RenderResult(output=output, resolved=resolved, missing=missing)


def render_template_file(
    template_path: Path,
    output_path: Path,
    secrets: Dict[str, str],
    *,
    strict: bool = False,
) -> RenderResult:
    """Read *template_path*, render it, and write to *output_path*."""
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    template_text = template_path.read_text(encoding="utf-8")
    result = render_template(template_text, secrets, strict=strict)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.output, encoding="utf-8")
    return result
