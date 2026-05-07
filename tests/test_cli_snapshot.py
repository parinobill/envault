"""Unit tests for envault.cli_snapshot."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_snapshot import register_snapshot_parser, cmd_snapshot


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_snapshot_parser(sub)
    return p


def test_snapshot_subcommand_registered(parser):
    args = parser.parse_args(["snapshot"])
    assert args.command == "snapshot"


def test_snapshot_default_project(parser):
    args = parser.parse_args(["snapshot"])
    assert args.project == "default"


def test_snapshot_custom_project(parser):
    args = parser.parse_args(["snapshot", "--project", "myapp"])
    assert args.project == "myapp"


def test_snapshot_default_index(parser):
    args = parser.parse_args(["snapshot"])
    assert args.index == -1


def test_snapshot_custom_index(parser):
    args = parser.parse_args(["snapshot", "--index", "2"])
    assert args.index == 2


def test_snapshot_short_flags(parser):
    args = parser.parse_args(["snapshot", "-p", "svc", "-i", "0"])
    assert args.project == "svc"
    assert args.index == 0


def test_snapshot_sets_func(parser):
    args = parser.parse_args(["snapshot"])
    assert args.func is cmd_snapshot


def test_cmd_snapshot_exits_when_no_vault(tmp_path, monkeypatch):
    import argparse as ap
    args = ap.Namespace(project="ghost", index=-1, base_dir=str(tmp_path))
    with pytest.raises(SystemExit) as exc_info:
        cmd_snapshot(args)
    assert exc_info.value.code == 1
