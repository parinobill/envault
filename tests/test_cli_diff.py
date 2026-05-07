"""Tests for envault.cli_diff module."""

import argparse

import pytest

from envault.cli_diff import register_diff_parser


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_diff_parser(sub)
    return p


def test_diff_subcommand_registered(parser):
    args = parser.parse_args(["diff"])
    assert args.command == "diff"


def test_diff_default_project(parser):
    args = parser.parse_args(["diff"])
    assert args.project == "default"


def test_diff_custom_project(parser):
    args = parser.parse_args(["diff", "--project", "myapp"])
    assert args.project == "myapp"


def test_diff_default_env_file(parser):
    args = parser.parse_args(["diff"])
    assert args.env_file == ".env"


def test_diff_custom_env_file(parser):
    args = parser.parse_args(["diff", "--env-file", ".env.prod"])
    assert args.env_file == ".env.prod"


def test_diff_show_values_default_false(parser):
    args = parser.parse_args(["diff"])
    assert args.show_values is False


def test_diff_show_values_flag(parser):
    args = parser.parse_args(["diff", "--show-values"])
    assert args.show_values is True


def test_diff_sets_func(parser):
    from envault.cli_diff import cmd_diff

    args = parser.parse_args(["diff"])
    assert args.func is cmd_diff
