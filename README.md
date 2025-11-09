# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails

## Getting Started

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
Install dependencies declared in pyproject.toml:

bash
Copy code
pip install -e .
Launch the forthcoming integrated tool (placeholder command):

bash
Copy code
python -m lead_verifier
The command above will host the orchestrated scrapers and UI once the
implementation lands. For now it serves as the entry point for development.

Scraper setup
The new Python scrapers live under lead_verifier/scrapers. They rely on
Microsoft Playwright to drive a Chromium
browser instance. Install the runtime dependencies with:

bash
Copy code
pip install playwright
playwright install chromium
TruePeopleSearch may occasionally challenge automated traffic with a CAPTCHA.
Run the scraper in headful mode (disable headless) so a human can solve the
challenge before continuing. The TruePeopleSearchConfig class exposes
headless and throttle_seconds settings to help control execution.

Repository Layout
lead_verifier/ – Python package containing ingestion, scraping, orchestration,
and UI components.

assets/ – Shared example datasets and reusable assets for local testing.

fastpeoplesearch.com-scraper-main/ and truepeoplesearch-master/ – Legacy
scrapers maintained for reference while the unified toolkit evolves.

pyproject.toml – Dependency and packaging metadata.

Contributing
Please open an issue or pull request to discuss substantial changes. When
adding new modules, update pyproject.toml if additional third-party
dependencies are required.