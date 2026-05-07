"""Tests for envault.cli_history module."""

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.cli_history import cmd_history, register_history_parser


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_history_parser(sub)
    return p


def test_history_subcommand_registered(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["history"])
    assert hasattr(args, "func")


def test_history_default_project(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["history"])
    assert args.project == "default"


def test_history_custom_project(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["history", "-p", "myapp"])
    assert args.project == "myapp"


def test_history_default_limit(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["history"])
    assert args.limit == 0


def test_history_custom_limit(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["history", "-n", "5"])
    assert args.limit == 5


def test_history_sets_func(parser: argparse.ArgumentParser) -> None:
    from envault.cli_history import cmd_history as expected_func
    args = parser.parse_args(["history"])
    assert args.func is expected_func


def test_cmd_history_no_history(tmp_path: Path, capsys) -> None:
    args = argparse.Namespace(project="ghost", limit=0, base_dir=str(tmp_path))
    with pytest.raises(SystemExit) as exc_info:
        cmd_history(args)
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "No history" in captured.out


def test_cmd_history_shows_entries(tmp_path: Path, capsys) -> None:
    from envault.history import record_snapshot
    record_snapshot(str(tmp_path), "proj", {"FOO": "bar"}, actor="alice", action="push")
    args = argparse.Namespace(project="proj", limit=0, base_dir=str(tmp_path))
    cmd_history(args)
    captured = capsys.readouterr()
    assert "alice" in captured.out
    assert "push" in captured.out
