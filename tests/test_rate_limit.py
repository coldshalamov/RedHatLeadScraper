from lead_verifier.models import LeadInput, LeadVerification
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
    assert scraper.calls == 1
    assert scraper.last_lead is lead
