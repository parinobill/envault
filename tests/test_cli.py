"""Tests for the envault CLI commands."""

import pytest
from unittest.mock import patch, MagicMock

from envault.cli import build_parser, cmd_init, cmd_push, cmd_pull, cmd_list


SECRETS = {"DB_HOST": "localhost", "DB_PORT": "5432"}
PASS = "hunter2"


@pytest.fixture()
def parser():
    return build_parser()


def test_parser_default_project(parser):
    args = parser.parse_args(["list"])
    assert args.project == "default"


def test_parser_custom_project(parser):
    args = parser.parse_args(["-p", "myapp", "list"])
    assert args.project == "myapp"


def test_parser_push_default_env_file(parser):
    args = parser.parse_args(["push"])
    assert args.env_file == ".env"


def test_parser_pull_custom_env_file(parser):
    args = parser.parse_args(["pull", ".env.prod"])
    assert args.env_file == ".env.prod"


def test_cmd_init_creates_vault(tmp_path):
    args = MagicMock(project="testproj")
    with patch("envault.cli.vault_exists", return_value=False), \
         patch("envault.cli.save_secrets") as mock_save, \
         patch("envault.cli._prompt_new_passphrase", return_value=PASS):
        cmd_init(args)
    mock_save.assert_called_once_with("testproj", {}, PASS)


def test_cmd_init_exits_if_vault_exists():
    args = MagicMock(project="testproj")
    with patch("envault.cli.vault_exists", return_value=True), \
         pytest.raises(SystemExit):
        cmd_init(args)


def test_cmd_push_saves_secrets():
    args = MagicMock(project="testproj", env_file=".env")
    with patch("envault.cli.read_dotenv_file", return_value=SECRETS), \
         patch("envault.cli.save_secrets") as mock_save, \
         patch("envault.cli._prompt_passphrase", return_value=PASS):
        cmd_push(args)
    mock_save.assert_called_once_with("testproj", SECRETS, PASS)


def test_cmd_pull_writes_env_file():
    args = MagicMock(project="testproj", env_file=".env")
    with patch("envault.cli.load_secrets", return_value=SECRETS), \
         patch("envault.cli.write_dotenv_file") as mock_write, \
         patch("envault.cli._prompt_passphrase", return_value=PASS):
        cmd_pull(args)
    mock_write.assert_called_once_with(".env", SECRETS)


def test_cmd_pull_exits_on_wrong_passphrase():
    args = MagicMock(project="testproj", env_file=".env")
    with patch("envault.cli.load_secrets", side_effect=ValueError("bad pass")), \
         patch("envault.cli._prompt_passphrase", return_value="wrong"), \
         pytest.raises(SystemExit):
        cmd_pull(args)


def test_cmd_list_prints_keys(capsys):
    args = MagicMock(project="testproj")
    with patch("envault.cli.list_keys", return_value=["DB_HOST", "DB_PORT"]), \
         patch("envault.cli._prompt_passphrase", return_value=PASS):
        cmd_list(args)
    captured = capsys.readouterr()
    assert "DB_HOST" in captured.out
    assert "DB_PORT" in captured.out


def test_cmd_list_empty_vault(capsys):
    args = MagicMock(project="testproj")
    with patch("envault.cli.list_keys", return_value=[]), \
         patch("envault.cli._prompt_passphrase", return_value=PASS):
        cmd_list(args)
    captured = capsys.readouterr()
    assert "no secrets" in captured.out
