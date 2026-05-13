"""Unit tests for envault.cli_copy argument parsing."""

from __future__ import annotations

import argparse

import pytest

from envault.cli_copy import cmd_copy, register_copy_parser


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_copy_parser(sub)
    return p


def test_copy_subcommand_registered(parser):
    args = parser.parse_args(["copy", "SRC", "DST"])
    assert args.command == "copy"


def test_copy_source_and_dest(parser):
    args = parser.parse_args(["copy", "OLD_KEY", "NEW_KEY"])
    assert args.source == "OLD_KEY"
    assert args.dest == "NEW_KEY"


def test_copy_default_project(parser):
    args = parser.parse_args(["copy", "SRC", "DST"])
    assert args.project == "default"


def test_copy_custom_project(parser):
    args = parser.parse_args(["copy", "SRC", "DST", "--project", "myapp"])
    assert args.project == "myapp"


def test_copy_overwrite_default_false(parser):
    args = parser.parse_args(["copy", "SRC", "DST"])
    assert args.overwrite is False


def test_copy_overwrite_flag(parser):
    args = parser.parse_args(["copy", "SRC", "DST", "--overwrite"])
    assert args.overwrite is True


def test_copy_sets_func(parser):
    args = parser.parse_args(["copy", "SRC", "DST"])
    assert args.func is cmd_copy
