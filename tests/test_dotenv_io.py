"""Tests for envault.dotenv_io — .env file parsing and rendering."""

from __future__ import annotations

from envault.dotenv_io import (
    parse_dotenv,
    read_dotenv_file,
    render_dotenv,
    write_dotenv_file,
)


def test_parse_simple():
    text = "KEY=value\nOTHER=123\n"
    assert parse_dotenv(text) == {"KEY": "value", "OTHER": "123"}


def test_parse_skips_comments():
    text = "# comment\nKEY=val\n"
    assert parse_dotenv(text) == {"KEY": "val"}


def test_parse_skips_blank_lines():
    text = "\n\nKEY=val\n\n"
    assert parse_dotenv(text) == {"KEY": "val"}


def test_parse_strips_double_quotes():
    text = 'KEY="hello world"\n'
    assert parse_dotenv(text) == {"KEY": "hello world"}


def test_parse_strips_single_quotes():
    text = "KEY='hello'\n"
    assert parse_dotenv(text) == {"KEY": "hello"}


def test_parse_value_with_equals():
    text = "KEY=a=b=c\n"
    assert parse_dotenv(text) == {"KEY": "a=b=c"}


def test_render_sorted():
    secrets = {"Z": "last", "A": "first"}
    rendered = render_dotenv(secrets)
    assert rendered.index("A=") < rendered.index("Z=")


def test_render_quotes_spaces():
    rendered = render_dotenv({"KEY": "hello world"})
    assert '"hello world"' in rendered


def test_render_no_trailing_newline_empty():
    assert render_dotenv({}) == ""


def test_roundtrip(tmp_path):
    secrets = {"HOST": "localhost", "PORT": "5432", "NAME": "mydb"}
    env_file = tmp_path / ".env"
    write_dotenv_file(secrets, env_file)
    loaded = read_dotenv_file(env_file)
    assert loaded == secrets


def test_write_creates_file(tmp_path):
    env_file = tmp_path / ".env"
    write_dotenv_file({"X": "1"}, env_file)
    assert env_file.exists()
