"""Tests for envault.cli_lint argument parsing and cmd_lint behaviour."""
import argparse
import pytest
from unittest.mock import patch, MagicMock

from envault.cli_lint import register_lint_parser, cmd_lint


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_lint_parser(sub)
    return p


def test_lint_subcommand_registered(parser):
    args = parser.parse_args(["lint"])
    assert args.command == "lint"


def test_lint_default_project(parser):
    args = parser.parse_args(["lint"])
    assert args.project == "default"


def test_lint_custom_project(parser):
    args = parser.parse_args(["lint", "-p", "myapp"])
    assert args.project == "myapp"


def test_lint_default_min_length(parser):
    args = parser.parse_args(["lint"])
    assert args.min_length == 8


def test_lint_custom_min_length(parser):
    args = parser.parse_args(["lint", "--min-length", "16"])
    assert args.min_length == 16


def test_lint_no_key_convention_flag(parser):
    args = parser.parse_args(["lint", "--no-key-convention"])
    assert args.no_key_convention is True


def test_lint_sets_func(parser):
    args = parser.parse_args(["lint"])
    assert args.func is cmd_lint


def test_cmd_lint_exits_when_no_vault(tmp_path):
    args = argparse.Namespace(project="nonexistent", min_length=8, no_key_convention=False)
    with patch("envault.cli_lint.vault_exists", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(args)
        assert exc_info.value.code == 1


def test_cmd_lint_ok_exits_zero(tmp_path):
    args = argparse.Namespace(project="myproj", min_length=8, no_key_convention=False)
    clean_secrets = {"API_KEY": "supersecretvalue123"}
    with patch("envault.cli_lint.vault_exists", return_value=True), \
         patch("envault.cli_lint._prompt_passphrase", return_value="pass"), \
         patch("envault.cli_lint.load_secrets", return_value=clean_secrets):
        # Should not raise SystemExit (exit code 0 means no explicit call)
        cmd_lint(args)


def test_cmd_lint_errors_exits_2(tmp_path):
    args = argparse.Namespace(project="myproj", min_length=8, no_key_convention=False)
    bad_secrets = {"MY_KEY": ""}  # empty value -> error
    with patch("envault.cli_lint.vault_exists", return_value=True), \
         patch("envault.cli_lint._prompt_passphrase", return_value="pass"), \
         patch("envault.cli_lint.load_secrets", return_value=bad_secrets):
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(args)
        assert exc_info.value.code == 2
