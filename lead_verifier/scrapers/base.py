"""Common utilities shared by browser based scrapers."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrowserScraperConfig:
    """Runtime configuration shared by all browser based scrapers."""

    headless: bool = True
    throttle_seconds: float = 5.0
    navigation_timeout: float = 30.0


class BrowserScraper:
    """Base class exposing throttling helpers for browser scrapers."""

    def __init__(self, config: Optional[BrowserScraperConfig] = None) -> None:
        self.config = config or BrowserScraperConfig()

    def _apply_throttle(self) -> None:
        if self.config.throttle_seconds > 0:
            time.sleep(self.config.throttle_seconds)
