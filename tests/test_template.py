"""Unit tests for envault.template."""

import pytest

from envault.template import TemplateError, RenderResult, render_template

SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "s3cr3t"}


def test_simple_substitution():
    result = render_template("host={{ DB_HOST }}", SECRETS)
    assert result.output == "host=localhost"
    assert "DB_HOST" in result.resolved


def test_multiple_placeholders():
    result = render_template("{{ DB_HOST }}:{{ DB_PORT }}", SECRETS)
    assert result.output == "localhost:5432"
    assert set(result.resolved) == {"DB_HOST", "DB_PORT"}


def test_missing_key_left_unchanged_by_default():
    result = render_template("key={{ MISSING_KEY }}", SECRETS)
    assert result.output == "key={{ MISSING_KEY }}"
    assert "MISSING_KEY" in result.missing
    assert not result.has_missing is False  # has_missing == True
    assert result.has_missing


def test_missing_key_strict_raises():
    with pytest.raises(TemplateError, match="MISSING_KEY"):
        render_template("key={{ MISSING_KEY }}", SECRETS, strict=True)


def test_no_placeholders_unchanged():
    text = "no placeholders here"
    result = render_template(text, SECRETS)
    assert result.output == text
    assert result.resolved == []
    assert result.missing == []


def test_whitespace_inside_braces():
    result = render_template("{{  API_KEY  }}", SECRETS)
    assert result.output == "s3cr3t"


def test_partial_match_not_replaced():
    # Lowercase keys should NOT match (pattern requires A-Z0-9_)
    result = render_template("{{ db_host }}", SECRETS)
    assert result.output == "{{ db_host }}"
    assert "db_host" in result.missing


def test_render_result_has_missing_false_when_all_resolved():
    result = render_template("{{ DB_HOST }}", SECRETS)
    assert not result.has_missing


def test_empty_secrets_all_missing():
    result = render_template("{{ DB_HOST }} {{ DB_PORT }}", {})
    assert result.missing == ["DB_HOST", "DB_PORT"]
    assert result.resolved == []
