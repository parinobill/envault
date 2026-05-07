"""Unit tests for envault.cli_export."""

from __future__ import annotations

import argparse

import pytest

from envault.cli_export import register_export_parser


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="envault")
    sub = root.add_subparsers(dest="command")
    register_export_parser(sub)
    return root


def test_export_subcommand_registered(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export"])
    assert args.command == "export"


def test_export_default_project(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export"])
    assert args.project == "default"


def test_export_custom_project(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export", "-p", "myapp"])
    assert args.project == "myapp"


def test_export_default_format(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export"])
    assert args.format == "dotenv"


def test_export_json_format(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export", "-f", "json"])
    assert args.format == "json"


def test_export_csv_format(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export", "-f", "csv"])
    assert args.format == "csv"


def test_export_default_output(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export"])
    assert args.output == ""


def test_export_custom_output(parser: argparse.ArgumentParser):
    args = parser.parse_args(["export", "-o", "secrets.env"])
    assert args.output == "secrets.env"


def test_export_sets_func(parser: argparse.ArgumentParser):
    from envault.cli_export import cmd_export
    args = parser.parse_args(["export"])
    assert args.func is cmd_export
