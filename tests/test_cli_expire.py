"""Unit tests for envault.cli_expire argument parsing."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_expire import (
    cmd_list_expiry,
    cmd_purge_expired,
    cmd_remove_expiry,
    cmd_set_expiry,
    register_expire_parser,
)


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_expire_parser(sub)
    return p


def test_expire_subcommand_registered(parser):
    args = parser.parse_args(["expire", "--project", "demo", "list"])
    assert args.command == "expire"


def test_expire_default_project(parser):
    args = parser.parse_args(["expire", "list"])
    assert args.project == "default"


def test_expire_custom_project(parser):
    args = parser.parse_args(["expire", "--project", "prod", "list"])
    assert args.project == "prod"


def test_expire_set_func(parser):
    args = parser.parse_args(["expire", "set", "DB_PASS", "3600"])
    assert args.func is cmd_set_expiry
    assert args.key == "DB_PASS"
    assert args.ttl == 3600.0


def test_expire_set_with_note(parser):
    args = parser.parse_args(["expire", "set", "API_KEY", "86400", "--note", "rotated monthly"])
    assert args.note == "rotated monthly"


def test_expire_remove_func(parser):
    args = parser.parse_args(["expire", "remove", "API_KEY"])
    assert args.func is cmd_remove_expiry
    assert args.key == "API_KEY"


def test_expire_list_func(parser):
    args = parser.parse_args(["expire", "list"])
    assert args.func is cmd_list_expiry


def test_expire_purge_func(parser):
    args = parser.parse_args(["expire", "purge"])
    assert args.func is cmd_purge_expired


def test_expire_default_base_dir(parser):
    args = parser.parse_args(["expire", "list"])
    assert ".envault" in args.base_dir


def test_expire_custom_base_dir(parser):
    args = parser.parse_args(["expire", "--base-dir", "/tmp/vault", "list"])
    assert args.base_dir == "/tmp/vault"
