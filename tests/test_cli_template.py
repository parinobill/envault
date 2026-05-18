"""Unit tests for envault.cli_template argument parsing."""

import argparse
import pytest

from envault.cli_template import register_template_parser, cmd_template


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_template_parser(sub)
    return p


def test_template_subcommand_registered(parser):
    args = parser.parse_args(["template", "tmpl.txt", "out.txt"])
    assert hasattr(args, "func")


def test_template_sets_func(parser):
    args = parser.parse_args(["template", "tmpl.txt", "out.txt"])
    assert args.func is cmd_template


def test_template_default_project(parser):
    args = parser.parse_args(["template", "tmpl.txt", "out.txt"])
    assert args.project == "default"


def test_template_custom_project(parser):
    args = parser.parse_args(["template", "tmpl.txt", "out.txt", "--project", "myapp"])
    assert args.project == "myapp"


def test_template_positional_args(parser):
    args = parser.parse_args(["template", "input.tmpl", "/tmp/output.conf"])
    assert args.template == "input.tmpl"
    assert args.output == "/tmp/output.conf"


def test_template_strict_default_false(parser):
    args = parser.parse_args(["template", "t.txt", "o.txt"])
    assert args.strict is False


def test_template_strict_flag(parser):
    args = parser.parse_args(["template", "t.txt", "o.txt", "--strict"])
    assert args.strict is True
