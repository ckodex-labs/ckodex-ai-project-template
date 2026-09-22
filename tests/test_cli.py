"""
Tests for CKODEX AIOps CLI commands.
Verifies command dispatch, exit codes, and output formatting.
"""

from typer.testing import CliRunner

from ckodex_aiops.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "quickstart" in result.stdout
    assert "cockpit" in result.stdout
    assert "tour" in result.stdout
    assert "conformance" in result.stdout


def test_cli_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "CKODEX AIOps Platform Preflight Doctor" in result.stdout


def test_cli_conformance() -> None:
    result = runner.invoke(app, ["conformance"])
    assert result.exit_code == 0
    assert "CKODEX Multi-Dimensional Conformance Suite" in result.stdout


def test_cli_explain() -> None:
    result = runner.invoke(app, ["explain", "data/06_models/model.safetensors"])
    assert result.exit_code == 0
    assert "Deep Observability Explanation" in result.stdout


def test_cli_quickstart_auto() -> None:
    result = runner.invoke(app, ["quickstart", "--auto", "--skip-doctor", "--no-browser"])
    assert result.exit_code == 0
    assert "Step 1/4" in result.stdout
    assert "Step 4/4" in result.stdout
