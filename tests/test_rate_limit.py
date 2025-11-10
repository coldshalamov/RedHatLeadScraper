import time

from lead_verifier.io import write_results
from lead_verifier.models import ContactDetail, LeadInput, LeadVerification
from lead_verifier.orchestrator.service import VerificationOrchestrator
from lead_verifier.rate_limit import RateLimitedScraper


class DummyScraper:
    name = "dummy"

    def __init__(self) -> None:
        self.calls = 0
        self.result = LeadVerification(source=self.name, contacts=[])
        self.last_lead = None

    def verify(self, lead: LeadInput) -> LeadVerification:
        self.calls += 1
        self.last_lead = lead
        return self.result


def test_rate_limited_scraper_returns_lead_verification() -> None:
    scraper = DummyScraper()
    wrapper = RateLimitedScraper(scraper)
    lead = LeadInput(name="Example")

    result = wrapper.verify(lead)

    assert result is scraper.result
    assert isinstance(result, LeadVerification)
    assert result.source == wrapper.name
    assert scraper.calls == 1
    assert scraper.last_lead is lead


class SlowDummyScraper:
    def __init__(self, name: str, delay: float, contact: str) -> None:
        self.name = name
        self._delay = delay
        self._contact = contact

    def verify(self, lead: LeadInput) -> LeadVerification:
        time.sleep(self._delay)
        return LeadVerification(
            source=self.name,
            contacts=[ContactDetail(type="email", value=self._contact)],
        )


def test_rate_limited_scraper_normalises_source_for_concurrent_runs(tmp_path) -> None:
    lead = LeadInput(first_name="Ada")

    slow_wrapper = RateLimitedScraper(
        SlowDummyScraper("slow", 0.05, "ada@example.com"),
        display_name="Slow Wrapper",
    )
    fast_wrapper = RateLimitedScraper(
        SlowDummyScraper("fast", 0.0, "ada.fast@example.com"),
        display_name="Fast Wrapper",
    )

    orchestrator = VerificationOrchestrator(
        [slow_wrapper, fast_wrapper],
        concurrent=True,
        max_workers=2,
    )

    aggregated_results = orchestrator.verify([lead])
    assert len(aggregated_results) == 1
    aggregated = aggregated_results[0]

    sources = [result.source for result in aggregated.raw_results]
    assert sources == ["Slow Wrapper", "Fast Wrapper"]

    contact_sources = {contact.value: list(contact.sources) for contact in aggregated.contacts}
    assert contact_sources == {
        "ada@example.com": ["Slow Wrapper"],
        "ada.fast@example.com": ["Fast Wrapper"],
    }

    output_path = tmp_path / "results.csv"
    write_results(output_path, aggregated_results)
    output_contents = output_path.read_text(encoding="utf-8")
    assert "Slow Wrapper" in output_contents
    assert "Fast Wrapper" in output_contents
