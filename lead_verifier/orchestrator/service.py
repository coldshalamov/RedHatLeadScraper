"""Verification orchestrator that coordinates multiple scrapers."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Optional, Protocol, Sequence

from ..merge import merge_lead_results
from ..models import AggregatedLeadResult, LeadInput, LeadVerification

LOGGER = logging.getLogger(__name__)


class ScraperProtocol(Protocol):
    """Protocol defining the interface that scraper implementations must follow."""

    name: str

    def verify(self, lead: LeadInput) -> LeadVerification:  # pragma: no cover - runtime protocol
        """Return contact details for the supplied lead."""


class VerificationOrchestrator:
    """Runs a collection of scrapers for each lead and merges the results."""

    def __init__(
        self,
        scrapers: Sequence[ScraperProtocol],
        *,
        merge_function: Callable[[LeadInput, Iterable[LeadVerification]], AggregatedLeadResult] = merge_lead_results,
        concurrent: bool = False,
        max_workers: Optional[int] = None,
        raise_on_error: bool = False,
    ) -> None:
        self._scrapers = list(scrapers)
        self._merge_function = merge_function
        self._concurrent = concurrent
        self._max_workers = max_workers
        self._raise_on_error = raise_on_error

    @property
    def scrapers(self) -> List[ScraperProtocol]:
        return list(self._scrapers)

    def verify(self, leads: Iterable[LeadInput]) -> List[AggregatedLeadResult]:
        """Run all configured scrapers for every lead provided."""

        aggregated: List[AggregatedLeadResult] = []
        for lead in leads:
            raw_results = self._run_scrapers_for_lead(lead)
            aggregated.append(self._merge_function(lead, raw_results))
        return aggregated

    def _run_scrapers_for_lead(self, lead: LeadInput) -> List[LeadVerification]:
        results: List[LeadVerification] = []
        if not self._concurrent or len(self._scrapers) <= 1:
            for scraper in self._scrapers:
                results.append(self._execute_scraper(scraper, lead))
            return results

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [executor.submit(self._execute_scraper, scraper, lead) for scraper in self._scrapers]
            for future in as_completed(futures):
                results.append(future.result())
        order_map = {scraper.name: index for index, scraper in enumerate(self._scrapers)}
        results.sort(key=lambda result: order_map.get(result.source, len(self._scrapers)))
        return results

    def _execute_scraper(self, scraper: ScraperProtocol, lead: LeadInput) -> LeadVerification:
        try:
            LOGGER.debug("Running scraper %s for lead %s", scraper.name, lead)
            return scraper.verify(lead)
        except Exception as exc:  # pragma: no cover - defensive programming
            LOGGER.exception("Scraper %s failed for lead %s", scraper.name, lead)
            if self._raise_on_error:
                raise
            return LeadVerification(source=scraper.name, contacts=[], raw_data={"error": str(exc)})
