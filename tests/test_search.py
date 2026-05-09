"""Tests for envault.search and envault.cli_search."""
from __future__ import annotations

import argparse
import pytest

from envault.search import SearchError, format_results, search_secrets
from envault.store import save_secrets
from envault.tags import add_tag
from envault.cli_search import register_search_parser


PASS = "hunter2"
SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123", "API_SECRET": "xyz"}


@pytest.fixture()
def vault_base(tmp_path):
    base = str(tmp_path)
    save_secrets(base, "proj", SECRETS, PASS)
    add_tag(base, "proj", "DB_HOST", "database")
    add_tag(base, "proj", "DB_PORT", "database")
    add_tag(base, "proj", "API_KEY", "api")
    add_tag(base, "proj", "API_SECRET", "api")
    return base


def test_no_criteria_raises(vault_base):
    with pytest.raises(SearchError, match="at least one"):
        search_secrets(vault_base, "proj", PASS)


def test_pattern_match(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="DB_*")
    keys = [r.key for r in results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "API_KEY" not in keys


def test_tag_filter(vault_base):
    results = search_secrets(vault_base, "proj", PASS, tag="api")
    keys = [r.key for r in results]
    assert "API_KEY" in keys
    assert "API_SECRET" in keys
    assert "DB_HOST" not in keys


def test_pattern_and_tag(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="API_*", tag="api")
    keys = [r.key for r in results]
    assert "API_KEY" in keys
    assert "API_SECRET" in keys


def test_no_matches_returns_empty(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="NOPE_*")
    assert results == []


def test_results_sorted(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="*")
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_result_includes_tags(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="DB_HOST")
    assert results[0].tags == ["database"]


def test_format_no_results():
    assert format_results([]) == "No matching secrets found."


def test_format_hides_values_by_default(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="API_KEY")
    output = format_results(results)
    assert "abc123" not in output
    assert "API_KEY" in output


def test_format_shows_values(vault_base):
    results = search_secrets(vault_base, "proj", PASS, pattern="API_KEY")
    output = format_results(results, show_values=True)
    assert "abc123" in output


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_search_parser(sub)
    return p


def test_search_subcommand_registered(parser):
    args = parser.parse_args(["search", "--pattern", "DB_*"])
    assert hasattr(args, "func")


def test_search_default_project(parser):
    args = parser.parse_args(["search", "--pattern", "*"])
    assert args.project == "default"


def test_search_custom_project(parser):
    args = parser.parse_args(["search", "-p", "myapp", "--tag", "api"])
    assert args.project == "myapp"


def test_search_show_values_flag(parser):
    args = parser.parse_args(["search", "--pattern", "*", "--show-values"])
    assert args.show_values is True
