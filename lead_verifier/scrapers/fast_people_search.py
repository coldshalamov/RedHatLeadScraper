"""FastPeopleSearch scraper placeholder.

The concrete implementation lives in a separate service.  This module only
exists so other components can rely on a shared interface that is mirrored by
:mod:`lead_verifier.scrapers.true_people_search`.
"""
from __future__ import annotations

from typing import Optional

from ..models import PersonSearch, ScraperResult
from .base import BrowserScraper, BrowserScraperConfig


class FastPeopleSearchScraper(BrowserScraper):
    """Placeholder exposing the public interface of the legacy scraper."""

    provider = "fastpeoplesearch.com"

    def __init__(self, config: Optional[BrowserScraperConfig] = None) -> None:
        super().__init__(config=config)

    def search(self, query: PersonSearch) -> ScraperResult:  # pragma: no cover - interface stub
        query.require_name()
        result = ScraperResult(provider=self.provider, query=query, found=False)
        result.add_note("FastPeopleSearch scraper is not bundled with this build.")
        return result
