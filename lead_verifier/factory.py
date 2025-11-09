"""Factory helpers for constructing scraper instances from configuration."""
from __future__ import annotations

import importlib
from typing import Any, Dict, List

from .config import ConfigurationError, iter_enabled_scraper_configs
from .rate_limit import DelayPolicy, RateLimitedScraper, RateLimiter


def _load_class(path: str):
    module_name, _, attr = path.rpartition(".")
    if not module_name:
        raise ConfigurationError(f"Invalid scraper class path '{path}'")
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attr)
    except AttributeError as exc:
        raise ConfigurationError(f"Module '{module_name}' does not define '{attr}'") from exc


def build_scrapers(config: Dict[str, Any]) -> List[RateLimitedScraper]:
    """Instantiate scraper classes defined in the configuration file."""

    scrapers: List[RateLimitedScraper] = []
    for scraper_cfg in iter_enabled_scraper_configs(config):
        class_path = scraper_cfg.get("class")
        if not class_path:
            raise ConfigurationError("Scraper configuration missing required 'class' field")

        options = scraper_cfg.get("options", {})
        scraper_cls = _load_class(class_path)
        scraper_instance = scraper_cls(**options)

        display_name = scraper_cfg.get("name")
        delay_seconds = float(scraper_cfg.get("delay_seconds", 0) or 0)
        calls_per_minute = scraper_cfg.get("rate_limit_per_minute")
        rate_limiter = RateLimiter(float(calls_per_minute)) if calls_per_minute else RateLimiter(None)

        scrapers.append(
            RateLimitedScraper(
                scraper_instance,
                display_name=display_name,
                delay_policy=DelayPolicy(delay_seconds=delay_seconds),
                rate_limiter=rate_limiter,
            )
        )
    return scrapers
