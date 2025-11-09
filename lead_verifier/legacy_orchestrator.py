"""Legacy orchestration helpers retained for the desktop UI."""
from __future__ import annotations

import csv
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover - pandas is optional at runtime
    pd = None  # type: ignore

from .models import LeadInput, LeadVerificationResult

ProgressCallback = Callable[[int, int], None]
ResultCallback = Callable[[LeadVerificationResult], None]
CompletionCallback = Callable[[List[LeadVerificationResult]], None]


class LeadVerificationTask:
    """Container representing an ongoing verification job."""

    def __init__(self, future: Future[List[LeadVerificationResult]]) -> None:
        self._future = future

    def cancel(self) -> None:
        """Attempt to cancel the underlying task."""

        self._future.cancel()

    def done(self) -> bool:
        return self._future.done()

    def result(self, timeout: Optional[float] = None) -> List[LeadVerificationResult]:
        return self._future.result(timeout=timeout)


class BaseScraper:
    """Minimal interface expected from scrapers."""

    name: str = "Unknown"

    def verify(self, lead: LeadInput) -> LeadVerificationResult:
        raise NotImplementedError


class MockScraper(BaseScraper):
    """Fallback scraper implementation used when real scrapers are unavailable."""

    def __init__(self, name: str) -> None:
        self.name = name

    def verify(self, lead: LeadInput) -> LeadVerificationResult:
        canonical_phone = (lead.phone or "").replace("-", "").replace(" ", "")
        status = "Verified" if canonical_phone[-1:] in {"0", "2", "4", "6", "8"} else "Not found"
        details = "Even-numbered phone detected" if status == "Verified" else "No match for odd phone"
        return LeadVerificationResult(lead=lead, source=self.name, status=status, details=details)


class LeadVerifierOrchestrator:
    """High level coordinator for file ingestion and scraper execution."""

    REQUIRED_FIELDS = ("name",)

    def __init__(self, scrapers: Optional[Iterable[BaseScraper]] = None) -> None:
        self.scrapers: List[BaseScraper] = list(scrapers or [MockScraper("FastPeopleSearch"), MockScraper("TruePeopleSearch")])
        self._executor = ThreadPoolExecutor(max_workers=max(2, len(self.scrapers)))
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def load_leads(self, file_path: str | Path) -> List[Dict[str, str]]:
        """Load leads from CSV or Excel files."""

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)

        if path.suffix.lower() == ".csv":
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader]
        if path.suffix.lower() in {".xlsx", ".xls"}:
            if pd is None:
                raise RuntimeError("Excel support requires pandas; install pandas to continue")
            frame = pd.read_excel(path)
            return frame.fillna("").to_dict(orient="records")

        raise ValueError(f"Unsupported file type: {path.suffix}")

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    def verify_async(
        self,
        leads: Iterable[Dict[str, str]],
        mapping: Dict[str, str],
        progress_callback: Optional[ProgressCallback] = None,
        result_callback: Optional[ResultCallback] = None,
        completion_callback: Optional[CompletionCallback] = None,
    ) -> LeadVerificationTask:
        """Execute the verification job in the background."""

        self._validate_mapping(mapping)
        leads_list = list(leads)

        future = self._executor.submit(
            self._run_verification,
            leads_list,
            mapping,
            progress_callback,
            result_callback,
            completion_callback,
        )
        return LeadVerificationTask(future)

    # ------------------------------------------------------------------
    def _run_verification(
        self,
        leads: List[Dict[str, str]],
        mapping: Dict[str, str],
        progress_callback: Optional[ProgressCallback],
        result_callback: Optional[ResultCallback],
        completion_callback: Optional[CompletionCallback],
    ) -> List[LeadVerificationResult]:
        total = len(leads)
        results: List[LeadVerificationResult] = []

        for index, lead_row in enumerate(leads, start=1):
            lead = self._normalise_lead(lead_row, mapping)
            for scraper in self.scrapers:
                result = scraper.verify(lead)
                results.append(result)
                if result_callback:
                    result_callback(result)
            if progress_callback:
                progress_callback(index, total)

        if completion_callback:
            completion_callback(results)
        return results

    # ------------------------------------------------------------------
    def _validate_mapping(self, mapping: Dict[str, str]) -> None:
        missing = [field for field in self.REQUIRED_FIELDS if not mapping.get(field)]
        if missing:
            raise ValueError(f"Missing required mapping for: {', '.join(missing)}")

    def _normalise_lead(self, lead_row: Dict[str, str], mapping: Dict[str, str]) -> LeadInput:
        name_value = lead_row.get(mapping["name"], "")
        metadata = {key: lead_row.get(column, "") for key, column in mapping.items() if key not in {"name", "phone", "email"}}
        return LeadInput(
            name=name_value,
            phone=lead_row.get(mapping.get("phone", ""), "") if mapping.get("phone") else None,
            email=lead_row.get(mapping.get("email", ""), "") if mapping.get("email") else None,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        with self._lock:
            self._executor.shutdown(wait=False, cancel_futures=True)


__all__ = [
    "BaseScraper",
    "LeadVerifierOrchestrator",
    "LeadVerificationTask",
    "MockScraper",
]
