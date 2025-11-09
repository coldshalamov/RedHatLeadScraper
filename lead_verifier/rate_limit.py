"""Utilities for applying delay and rate limiting to scraper calls."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from .models import LeadInput, LeadVerification


@dataclass
class DelayPolicy:
    """Simple policy describing artificial delay behaviour for scrapers."""

    delay_seconds: float = 0.0


class RateLimiter:
    """Token bucket style rate limiter enforcing minimum interval between calls."""

    def __init__(self, calls_per_minute: Optional[float]) -> None:
        self._interval = 60.0 / float(calls_per_minute) if calls_per_minute else 0.0
        self._lock = threading.Lock()
        self._next_available = 0.0

    def acquire(self) -> None:
        if self._interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if now < self._next_available:
                time.sleep(self._next_available - now)
                now = time.monotonic()
            self._next_available = now + self._interval


class RateLimitedScraper:
    """Wrapper that enforces delay and rate limiting when invoking a scraper."""

    def __init__(
        self,
        scraper,
        *,
        display_name: Optional[str] = None,
        delay_policy: Optional[DelayPolicy] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self._scraper = scraper
        self._display_name = display_name
        self._delay_policy = delay_policy or DelayPolicy()
        self._rate_limiter = rate_limiter or RateLimiter(None)

    @property
    def name(self) -> str:  # pragma: no cover - delegation
        if self._display_name:
            return self._display_name
        return getattr(self._scraper, "name", self._scraper.__class__.__name__)

    def verify(self, lead: LeadInput) -> LeadVerification:
        self._rate_limiter.acquire()
        result = self._scraper.verify(lead)
        if self._delay_policy.delay_seconds > 0:
            time.sleep(self._delay_policy.delay_seconds)
        return result

    def __getattr__(self, item):  # pragma: no cover - simple delegation
        return getattr(self._scraper, item)
