"""Tests for envault/tags.py"""

import json
import pytest
from pathlib import Path

from envault.tags import (
    add_tag,
    filter_by_tag,
    format_tags,
    load_tags,
    remove_tag,
    save_tags,
    TagError,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


PROJECT = "myapp"


def test_load_tags_missing_file_returns_empty(base):
    assert load_tags(base, PROJECT) == {}


def test_save_and_load_roundtrip(base):
    tags = {"DB_URL": ["database", "prod"], "API_KEY": ["external"]}
    save_tags(base, PROJECT, tags)
    loaded = load_tags(base, PROJECT)
    assert loaded == tags


def test_save_creates_parent_dirs(base):
    nested_base = base / "deep" / "nested"
    save_tags(nested_base, PROJECT, {"X": ["a"]})
    assert (nested_base / PROJECT / "tags.json").exists()


def test_add_tag_new_key(base):
    add_tag(base, PROJECT, "SECRET", "sensitive")
    assert load_tags(base, PROJECT) == {"SECRET": ["sensitive"]}


def test_add_tag_existing_key_appends(base):
    add_tag(base, PROJECT, "SECRET", "sensitive")
    add_tag(base, PROJECT, "SECRET", "prod")
    assert set(load_tags(base, PROJECT)["SECRET"]) == {"sensitive", "prod"}


def test_add_tag_duplicate_is_noop(base):
    add_tag(base, PROJECT, "SECRET", "sensitive")
    add_tag(base, PROJECT, "SECRET", "sensitive")
    assert load_tags(base, PROJECT)["SECRET"].count("sensitive") == 1


def test_remove_tag_existing(base):
    add_tag(base, PROJECT, "SECRET", "sensitive")
    add_tag(base, PROJECT, "SECRET", "prod")
    remove_tag(base, PROJECT, "SECRET", "sensitive")
    assert load_tags(base, PROJECT)["SECRET"] == ["prod"]


def test_remove_last_tag_deletes_key(base):
    add_tag(base, PROJECT, "SECRET", "only")
    remove_tag(base, PROJECT, "SECRET", "only")
    assert "SECRET" not in load_tags(base, PROJECT)


def test_remove_tag_noop_if_missing(base):
    add_tag(base, PROJECT, "SECRET", "prod")
    remove_tag(base, PROJECT, "SECRET", "nonexistent")  # should not raise
    assert load_tags(base, PROJECT)["SECRET"] == ["prod"]


def test_filter_by_tag(base):
    add_tag(base, PROJECT, "DB_URL", "database")
    add_tag(base, PROJECT, "DB_PASS", "database")
    add_tag(base, PROJECT, "API_KEY", "external")
    result = filter_by_tag(base, PROJECT, "database")
    assert set(result) == {"DB_URL", "DB_PASS"}


def test_filter_by_tag_no_matches(base):
    add_tag(base, PROJECT, "X", "a")
    assert filter_by_tag(base, PROJECT, "z") == []


def test_load_tags_corrupt_file_raises(base):
    path = base / PROJECT / "tags.json"
    path.parent.mkdir(parents=True)
    path.write_text("not json{{{")
    with pytest.raises(TagError, match="Corrupt"):
        load_tags(base, PROJECT)


def test_load_tags_wrong_type_raises(base):
    path = base / PROJECT / "tags.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(["list", "not", "dict"]))
    with pytest.raises(TagError, match="JSON object"):
        load_tags(base, PROJECT)


def test_format_tags_empty():
    assert format_tags({}) == "(no tags defined)"


def test_format_tags_sorted_output():
    tags = {"Z_KEY": ["b", "a"], "A_KEY": ["x"]}
    output = format_tags(tags)
    lines = output.strip().splitlines()
    assert lines[0].startswith("  A_KEY")
    assert lines[1].startswith("  Z_KEY")
    assert "a, b" in lines[1]  # tags sorted within key
