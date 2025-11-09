"""Web scrapers and adapters for third-party lead sources."""

from .base import BrowserScraper, BrowserScraperConfig  # noqa: F401
from .fast_people_search import FastPeopleSearchScraper  # noqa: F401
from .sample import EchoScraper  # noqa: F401

__all__ = [
    "BrowserScraper",
    "BrowserScraperConfig",
    "FastPeopleSearchScraper",
    "EchoScraper",
]

try:  # pragma: no cover - optional dependency
    from .true_people_search import TruePeopleSearchConfig, TruePeopleSearchScraper  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    TruePeopleSearchConfig = None  # type: ignore[assignment]
    TruePeopleSearchScraper = None  # type: ignore[assignment]
else:  # pragma: no cover - optional dependency
    __all__ += ["TruePeopleSearchConfig", "TruePeopleSearchScraper"]
