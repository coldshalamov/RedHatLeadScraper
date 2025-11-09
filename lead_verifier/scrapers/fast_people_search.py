"""Scraper implementation for fastpeoplesearch.com."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional
from urllib.parse import quote_plus

from ..models import LeadInput, LeadResult, PhoneNumberResult

try:  # pragma: no cover - import guard for optional dependency
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:  # pragma: no cover - handled during runtime
    webdriver = None  # type: ignore
    ChromeOptions = None  # type: ignore
    Service = None  # type: ignore
    By = None  # type: ignore
    WebDriver = object  # type: ignore
    WebDriverWait = None  # type: ignore
    EC = None  # type: ignore
    TimeoutException = Exception  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class FastPeopleSearchConfig:
    """Configuration parameters for :class:`FastPeopleSearchScraper`."""

    driver_path: Optional[str] = None
    headless: bool = True
    user_data_dir: Optional[str] = None
    profile_directory: Optional[str] = None
    binary_location: Optional[str] = None
    implicit_wait_seconds: float = 5.0
    wait_timeout_seconds: float = 15.0
    rate_limit_seconds: float = 0.0


class FastPeopleSearchScraper:
    """Scrape fastpeoplesearch.com and normalize the results."""

    BASE_URL = "https://www.fastpeoplesearch.com"

    def __init__(
        self,
        config: Optional[FastPeopleSearchConfig] = None,
        *,
        driver_factory: Optional[Callable[[], WebDriver]] = None,
        rate_limiter: Optional[Callable[[], None]] = None,
    ) -> None:
        if webdriver is None or ChromeOptions is None:
            raise ImportError(
                "Selenium is required to use FastPeopleSearchScraper. Install with 'pip install selenium'."
            )

        self.config = config or FastPeopleSearchConfig()
        self._driver: Optional[WebDriver] = None
        self._driver_factory = driver_factory
        self._rate_limiter = rate_limiter or self._default_rate_limiter

    def __enter__(self) -> "FastPeopleSearchScraper":
        self._ensure_driver()
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    def _ensure_driver(self) -> WebDriver:
        if self._driver is None:
            if self._driver_factory is not None:
                self._driver = self._driver_factory()
            else:
                options = self._build_options()
                service = Service(executable_path=self.config.driver_path) if self.config.driver_path else Service()
                self._driver = webdriver.Chrome(service=service, options=options)
            implicit_wait = max(self.config.implicit_wait_seconds, 0.0)
            if implicit_wait:
                self._driver.implicitly_wait(implicit_wait)
        return self._driver

    def _build_options(self) -> ChromeOptions:
        options = ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if self.config.user_data_dir:
            options.add_argument(f"--user-data-dir={self.config.user_data_dir}")
        if self.config.profile_directory:
            options.add_argument(f"--profile-directory={self.config.profile_directory}")
        if self.config.binary_location:
            options.binary_location = self.config.binary_location
        options.add_argument("--window-size=1920,1080")
        return options

    def close(self) -> None:
        if self._driver is not None:
            LOGGER.debug("Closing Selenium driver")
            self._driver.quit()
            self._driver = None

    def verify(self, lead: LeadInput) -> LeadResult:
        driver = self._ensure_driver()
        if self._rate_limiter is not None:
            self._rate_limiter()

        search_url = self._build_search_url(lead)
        LOGGER.info("Navigating to %s", search_url)

        phones: List[PhoneNumberResult] = []
        errors: List[str] = []
        try:
            driver.get(search_url)
            phones = self._extract_phone_numbers(driver)
        except Exception as exc:  # pragma: no cover - runtime guard
            LOGGER.exception("Failed to retrieve results for %s %s", lead.first_name, lead.last_name)
            errors.append(str(exc))

        metadata = {
            "search_url": search_url,
            "phone_count": len(phones),
        }

        return LeadResult(lead=lead, phone_numbers=phones, metadata=metadata, errors=errors)

    def _extract_phone_numbers(self, driver: WebDriver) -> List[PhoneNumberResult]:
        wait_timeout = max(self.config.wait_timeout_seconds, 1.0)
        phones: List[PhoneNumberResult] = []
        try:
            WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='tel:']"))
            )
        except TimeoutException:
            LOGGER.warning("Timed out waiting for phone numbers on %s", driver.current_url)
            return phones

        elements: Iterable = driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
        for elem in elements:
            text = elem.text.strip()
            href = elem.get_attribute("href") or ""
            if not text:
                continue
            phones.append(
                PhoneNumberResult(
                    phone_number=text,
                    raw_text=text,
                    label=self._infer_label(elem),
                    is_primary=not phones,
                )
            )
            LOGGER.debug("Discovered phone number %s (href=%s)", text, href)
        return phones

    def _infer_label(self, element) -> Optional[str]:  # type: ignore[override]
        try:
            container = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'result')]")
            header = container.find_element(By.CSS_SELECTOR, "h3, h2")
            return header.text.strip() or None
        except Exception:  # pragma: no cover - best effort metadata
            return None

    def _build_search_url(self, lead: LeadInput) -> str:
        name = quote_plus(f"{lead.first_name} {lead.last_name}")
        if lead.city or lead.state:
            location = " ".join(filter(None, [lead.city, lead.state]))
            location = quote_plus(location)
            return f"{self.BASE_URL}/name/{name}/{location}"
        return f"{self.BASE_URL}/name/{name}"

    def _default_rate_limiter(self) -> None:
        if self.config.rate_limit_seconds > 0:
            LOGGER.debug("Sleeping for %s seconds to respect rate limits", self.config.rate_limit_seconds)
            time.sleep(self.config.rate_limit_seconds)
