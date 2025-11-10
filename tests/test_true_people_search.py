"""Unit tests for the TruePeopleSearch scraper orchestrator adapter."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from lead_verifier.models import LeadInput, PersonSearch, ScraperResult
from lead_verifier.scrapers.true_people_search import TruePeopleSearchScraper


@pytest.fixture
def scraper() -> TruePeopleSearchScraper:
    return TruePeopleSearchScraper()


def test_verify_returns_contacts_when_emails_found(scraper: TruePeopleSearchScraper) -> None:
    queries: list[PersonSearch] = []

    def fake_search(query: PersonSearch) -> ScraperResult:
        queries.append(query)
        result = ScraperResult(provider=scraper.provider, query=query, found=True)
        result.add_email("ada@example.com", label="work")
        return result

    scraper.search = fake_search  # type: ignore[assignment]

    lead = LeadInput(name="Ada Lovelace", metadata={"city": "London", "state": "UK", "zip": "SW1A"})

    verification = scraper.verify(lead)

    assert verification.source == scraper.name
    assert [contact.value for contact in verification.contacts] == ["ada@example.com"]
    assert verification.contacts[0].metadata["label"] == "work"
    assert queries and queries[0].city_state_zip == "London, UK SW1A"
    assert verification.raw_data == {
        "found": True,
        "notes": [],
        "emails": [{"address": "ada@example.com", "label": "work", "metadata": {}}],
        "query": {"full_name": "Ada Lovelace", "city_state_zip": "London, UK SW1A"},
    }


def test_verify_returns_error_when_name_missing(scraper: TruePeopleSearchScraper) -> None:
    def unexpected_search(_query: PersonSearch) -> ScraperResult:  # pragma: no cover - guard
        raise AssertionError("search should not be invoked when the name is missing")

    scraper.search = unexpected_search  # type: ignore[assignment]

    verification = scraper.verify(LeadInput())

    assert verification.source == scraper.name
    assert verification.contacts == []
    assert verification.raw_data == {"error": "Lead is missing a name."}


def test_verify_handles_no_results(scraper: TruePeopleSearchScraper) -> None:
    def fake_search(query: PersonSearch) -> ScraperResult:
        result = ScraperResult(provider=scraper.provider, query=query, found=False)
        result.add_note("No records returned by TruePeopleSearch.")
        return result

    scraper.search = fake_search  # type: ignore[assignment]

    lead = LeadInput(name="Grace Hopper")

    verification = scraper.verify(lead)

    assert verification.source == scraper.name
    assert verification.contacts == []
    assert verification.raw_data == {
        "found": False,
        "notes": ["No records returned by TruePeopleSearch."],
        "emails": [],
        "query": {"full_name": "Grace Hopper", "city_state_zip": None},
    }
