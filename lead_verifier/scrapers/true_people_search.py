"""TruePeopleSearch.com email scraper.

Prerequisites
-------------
* Requires :mod:`playwright` with Chromium installed (``playwright install``).
* The public TruePeopleSearch site can present CAPTCHAs.  Automated runs must
  be monitored so a human can solve the challenge when prompted.
* Respect the web site's terms of service.  The throttling options exposed by
  :class:`TruePeopleSearchScraper` default to generous pauses between requests
  to reduce load and lower the risk of automated blocking.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from ..models import PersonSearch, ScraperResult
from .base import BrowserScraper, BrowserScraperConfig


@dataclass
class TruePeopleSearchConfig(BrowserScraperConfig):
    """Extends :class:`BrowserScraperConfig` with scraper specific options."""

    wait_for_captcha: bool = False


class TruePeopleSearchScraper(BrowserScraper):
    """Scraper that replicates the interface of :class:`FastPeopleSearchScraper`.

    Parameters
    ----------
    config:
        Optional :class:`TruePeopleSearchConfig` controlling browser behaviour.
        The base options add throttling and headless/headful controls, while
        :attr:`TruePeopleSearchConfig.wait_for_captcha` can be toggled to pause
        execution once a CAPTCHA dialog is detected.
    """

    provider = "truepeoplesearch.com"
    NOT_FOUND_TEXT = "We could not find any records for that search criteria."
    EMAIL_SECTION_TITLE = "Email Addresses"

    def __init__(self, config: Optional[TruePeopleSearchConfig] = None) -> None:
        super().__init__(config=config or TruePeopleSearchConfig())

    def search(self, query: PersonSearch) -> ScraperResult:
        """Search TruePeopleSearch and return discovered email addresses."""

        query.require_name()
        result = ScraperResult(provider=self.provider, query=query, found=False)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.config.headless)
            try:
                page = browser.new_page()
                page.set_default_navigation_timeout(self.config.navigation_timeout * 1000)
                target_url = self._build_query_url(query)
                page.goto(target_url, wait_until="domcontentloaded")
                self._apply_throttle()

                if self._is_not_found(page):
                    result.add_note("No records returned by TruePeopleSearch.")
                    return result

                if getattr(self.config, "wait_for_captcha", False) and self._is_captcha_present(page):
                    result.add_note("Execution paused for manual CAPTCHA resolution.")
                    page.wait_for_event("dialog")

                emails = self._extract_emails(page)
                for address in emails:
                    result.add_email(address)

                result.found = bool(emails)
                if not emails:
                    result.add_note("Result page did not expose an email section.")
                return result
            finally:
                with contextlib.suppress(PlaywrightError):
                    browser.close()

    # ------------------------------------------------------------------
    # Helpers
    def _build_query_url(self, query: PersonSearch) -> str:
        params = {
            "name": query.full_name,
            "citystatezip": query.city_state_zip or "",
            "rid": "0x0",
        }
        return f"https://www.truepeoplesearch.com/results?{urlencode(params)}"

    def _is_not_found(self, page) -> bool:
        try:
            text = page.text_content("div.content-center div.row.pl-1.record-count div")
            if text and text.strip() == self.NOT_FOUND_TEXT:
                return True
        except PlaywrightTimeoutError:
            return False
        except PlaywrightError as exc:
            raise RuntimeError("Unable to determine search result state") from exc
        return False

    def _is_captcha_present(self, page) -> bool:
        with contextlib.suppress(PlaywrightError):
            return bool(page.query_selector("iframe[src*='captcha']"))
        return False

    def _extract_emails(self, page) -> List[str]:
        try:
            emails = page.evaluate(
                """
                (desc) => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const header = elements.find((node) => node.textContent.trim() === desc);
                    if (!header || !header.parentElement) {
                        return [];
                    }
                    const parent = header.parentElement;
                    const children = Array.from(parent.children).slice(1);
                    return children
                        .map((child) => child.textContent.trim())
                        .filter((value) => value.length > 0);
                }
                """,
                self.EMAIL_SECTION_TITLE,
            )
            return emails or []
        except PlaywrightError as exc:
            raise RuntimeError("Failed to extract email addresses from response") from exc
