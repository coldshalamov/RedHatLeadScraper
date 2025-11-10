"""Smoke tests for the CLI entry point."""
from __future__ import annotations

import json

import pytest

from lead_verifier import __main__
from lead_verifier.cli import main


def test_cli_smoke_runs_with_echo_scraper(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "scrapers": [
                    {
                        "name": "Echo",
                        "class": "lead_verifier.scrapers.sample.EchoScraper",
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "first_name,last_name,phone,email\nJane,Doe,5551234567,jane@example.com\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "results.csv"

    exit_code = main(
        [
            str(input_path),
            str(output_path),
            "--config",
            str(config_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    contents = output_path.read_text(encoding="utf-8")
    assert "jane@example.com" in contents


def test_module_entry_point_delegates_to_cli(tmp_path) -> None:
    """The package entry point should behave like the CLI."""

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "scrapers": [
                    {
                        "name": "Echo",
                        "class": "lead_verifier.scrapers.sample.EchoScraper",
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "first_name,last_name,phone,email\nJane,Doe,5551234567,jane@example.com\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "results.csv"

    exit_code = __main__.main(
        [
            str(input_path),
            str(output_path),
            "--config",
            str(config_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    contents = output_path.read_text(encoding="utf-8")
    assert "jane@example.com" in contents


def test_module_entry_point_without_arguments_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = __main__.main([])

    captured = capsys.readouterr()
    assert "python -m lead_verifier" in captured.out
    assert exit_code == 2
