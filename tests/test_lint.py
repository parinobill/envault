"""Unit tests for envault.lint."""
import pytest
from envault.lint import (
    LintIssue,
    LintResult,
    LintError,
    lint_secrets,
    format_lint_result,
)


def test_ok_returns_empty_issues():
    result = lint_secrets({"API_KEY": "supersecretvalue"})
    assert result.ok
    assert result.issues == []


def test_empty_value_is_error():
    result = lint_secrets({"DB_PASSWORD": ""})
    assert result.has_errors
    issue = result.issues[0]
    assert issue.severity == "error"
    assert "empty" in issue.message


def test_short_value_is_warning():
    result = lint_secrets({"TOKEN": "abc"}, min_length=8)
    assert result.has_warnings
    issue = next(i for i in result.issues if "shorter" in i.message)
    assert issue.severity == "warning"
    assert issue.key == "TOKEN"


def test_weak_value_is_error():
    for weak in ["password", "secret", "changeme", "admin"]:
        result = lint_secrets({"MY_SECRET": weak})
        assert result.has_errors, f"Expected error for weak value '{weak}'"


def test_bad_key_convention_is_warning():
    result = lint_secrets({"myKey": "strongpassword123"})
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("UPPER_SNAKE_CASE" in w.message for w in warnings)


def test_key_convention_disabled():
    result = lint_secrets({"myKey": "strongpassword123"}, enforce_key_convention=False)
    assert result.ok


def test_multiple_issues_accumulated():
    secrets = {
        "bad_key": "",          # bad name + empty
        "GOOD_KEY": "hi",       # short
        "ANOTHER": "password",  # weak
    }
    result = lint_secrets(secrets)
    assert len(result.issues) >= 3


def test_invalid_input_raises():
    with pytest.raises(LintError):
        lint_secrets(["not", "a", "dict"])  # type: ignore[arg-type]


def test_format_ok():
    result = LintResult()
    text = format_lint_result(result)
    assert "No lint issues" in text


def test_format_shows_severity_prefix():
    result = LintResult(issues=[
        LintIssue(key="X", severity="error", message="bad"),
        LintIssue(key="Y", severity="warning", message="meh"),
    ])
    text = format_lint_result(result)
    assert "[ERROR]" in text
    assert "[WARN]" in text


def test_has_errors_and_warnings_flags():
    result = LintResult(issues=[
        LintIssue(key="A", severity="error", message="e"),
        LintIssue(key="B", severity="warning", message="w"),
    ])
    assert result.has_errors
    assert result.has_warnings
    assert not result.ok
