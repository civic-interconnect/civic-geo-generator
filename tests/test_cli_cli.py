# tests/test_cli_cli.py

from typer.testing import CliRunner

from civic_geo_generator.cli.cli import app

runner = CliRunner()


def test_cli_has_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "build" in result.stdout
    assert "validate" in result.stdout
    assert "index" in result.stdout
    assert "run" in result.stdout


def test_index():
    result = runner.invoke(app, ["index"])

    # Debug output
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(
                type(result.exception), result.exception, result.exception.__traceback__
            )

    assert result.exit_code == 0
