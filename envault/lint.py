"""Lint secrets in the vault against configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning'
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
_MIN_SECRET_LENGTH = 8
_COMMON_WEAK = {"password", "secret", "123456", "changeme", "admin", "test"}


def lint_secrets(
    secrets: Dict[str, str],
    min_length: int = _MIN_SECRET_LENGTH,
    enforce_key_convention: bool = True,
) -> LintResult:
    """Run lint rules over a dict of secrets and return a LintResult."""
    if not isinstance(secrets, dict):
        raise LintError("secrets must be a dict")

    result = LintResult()

    for key, value in secrets.items():
        # Rule 1: key naming convention
        if enforce_key_convention and not _KEY_PATTERN.match(key):
            result.issues.append(
                LintIssue(key=key, severity="warning",
                          message=f"Key '{key}' does not follow UPPER_SNAKE_CASE convention")
            )

        # Rule 2: empty value
        if value == "":
            result.issues.append(
                LintIssue(key=key, severity="error",
                          message=f"Key '{key}' has an empty value")
            )
            continue

        # Rule 3: value too short
        if len(value) < min_length:
            result.issues.append(
                LintIssue(key=key, severity="warning",
                          message=f"Key '{key}' value is shorter than {min_length} characters")
            )

        # Rule 4: weak / placeholder value
        if value.lower() in _COMMON_WEAK:
            result.issues.append(
                LintIssue(key=key, severity="error",
                          message=f"Key '{key}' appears to use a weak or placeholder value")
            )

    return result


def format_lint_result(result: LintResult) -> str:
    """Return a human-readable summary of lint issues."""
    if result.ok:
        return "No lint issues found."
    lines = []
    for issue in result.issues:
        prefix = "[ERROR]  " if issue.severity == "error" else "[WARN]   "
        lines.append(f"{prefix}{issue.key}: {issue.message}")
    return "\n".join(lines)
