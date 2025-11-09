"""Scraper implementations for third-party people search providers."""

from .base import BrowserScraper, BrowserScraperConfig  # noqa: F401
from .fast_people_search import FastPeopleSearchScraper  # noqa: F401
from .true_people_search import TruePeopleSearchConfig, TruePeopleSearchScraper  # noqa: F401
