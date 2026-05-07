"""Tests for the rotate CLI sub-command registration and argument parsing."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_rotate import register_rotate_parser


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser(prog="envault")
    sub = root.add_subparsers(dest="command")
    register_rotate_parser(sub)
    return root


def test_rotate_subcommand_registered(parser):
    args = parser.parse_args(["rotate"])
    assert args.command == "rotate"


def test_rotate_default_project(parser):
    args = parser.parse_args(["rotate"])
    assert args.project == "default"


def test_rotate_custom_project(parser):
    args = parser.parse_args(["rotate", "--project", "myapp"])
    assert args.project == "myapp"


def test_rotate_sets_func(parser):
    from envault.cli_rotate import cmd_rotate
    args = parser.parse_args(["rotate"])
    assert args.func is cmd_rotate


def test_rotate_unknown_flag_raises(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["rotate", "--unknown"])
