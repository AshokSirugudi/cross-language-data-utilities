import pytest
from click.testing import CliRunner
from schema_snapshooter_diff.cli import cli


# Fixture for CliRunner
@pytest.fixture
def runner():
    """Returns a Click CliRunner for invoking CLI commands."""
    return CliRunner()


# Basic test to check if the CLI can be invoked
def test_cli_invoke_help(runner):
    """Test that the main CLI command can be invoked with --help."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "Commands:" in result.output


# You can add more detailed tests for subcommands (get, compare, validate) here later.
# For example:
# def test_get_command_help(runner):
#     result = runner.invoke(cli, ['get', '--help'])
#     assert result.exit_code == 0
#     assert 'Usage: cli get [OPTIONS]' in result.output
