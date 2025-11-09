# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails

## Scraper setup

The new Python scrapers live under `lead_verifier/scrapers`. They rely on
[Microsoft Playwright](https://playwright.dev/python/) to drive a Chromium
browser instance. Install the runtime dependencies with:

```bash
pip install playwright
playwright install chromium
```

TruePeopleSearch may occasionally challenge automated traffic with a CAPTCHA.
Run the scraper in headful mode (disable headless) so a human can solve the
challenge before continuing. The `TruePeopleSearchConfig` class exposes
``headless`` and ``throttle_seconds`` settings to help control execution.
