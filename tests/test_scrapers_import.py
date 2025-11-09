"""Regression tests for optional scraper module imports."""

import importlib

import pytest


def test_scrapers_module_imports_with_playwright() -> None:
    """Ensure the scrapers package imports when optional dependencies exist."""

    pytest.importorskip("playwright", reason="Playwright is required for scraper import test")
    module = importlib.import_module("lead_verifier.scrapers")
    assert module.TruePeopleSearchScraper is not None
