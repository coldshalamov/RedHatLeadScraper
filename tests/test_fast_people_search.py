"""Unit tests for :mod:`lead_verifier.scrapers.fast_people_search`."""

from __future__ import annotations

import pytest

from lead_verifier.models import LeadInput
from lead_verifier.scrapers.fast_people_search import FastPeopleSearchScraper


def _scraper() -> FastPeopleSearchScraper:
    """Return an instance without invoking Selenium-dependent initialisation."""

    return FastPeopleSearchScraper.__new__(FastPeopleSearchScraper)


def test_build_search_url_with_first_and_last_name() -> None:
    scraper = _scraper()
    lead = LeadInput(
        first_name="Jane",
        last_name="Doe",
        metadata={"city": "Portland", "state": "OR"},
    )

    url = scraper._build_search_url(lead)

    assert url == "https://www.fastpeoplesearch.com/name/Jane+Doe/Portland+OR"


def test_build_search_url_with_full_name_only() -> None:
    scraper = _scraper()
    lead = LeadInput(name="Mary Poppins")

    url = scraper._build_search_url(lead)

    assert url == "https://www.fastpeoplesearch.com/name/Mary+Poppins"


def test_build_search_url_without_name_data_raises() -> None:
    scraper = _scraper()
    lead = LeadInput()

    with pytest.raises(ValueError) as excinfo:
        scraper._build_search_url(lead)

    assert "(Unnamed Lead)" in str(excinfo.value)
