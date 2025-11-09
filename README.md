# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails.

## Getting Started

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. **Install dependencies** declared in `pyproject.toml`:
   ```bash
   pip install -e .
   ```
3. **Launch the integrated tool (dev entry point):**
   ```bash
   python -m lead_verifier
   ```
   The command above will host the orchestrated scrapers and (eventual) UI once the
   implementation lands. For now it serves as the entry point for development.

## Lead verification orchestrator

The `lead_verifier` package bundles an extensible orchestration layer that can
run multiple scrapers either sequentially or concurrently for each input lead.

### Running from the command line

```bash
python -m lead_verifier.cli path/to/input.xlsx path/to/output.csv --config config/lead_verifier.example.yaml
```

**Key options:**

- `--mode` – choose `sequential` (default) or `concurrent` execution across scrapers.
- `--max-workers` – cap the number of worker threads used in concurrent mode.
- `--raise-on-error` – propagate scraper exceptions instead of annotating the output with error details.

The CLI accepts CSV or Excel spreadsheets for both input and output. When using
Excel files make sure the `openpyxl` package is installed.

### Configuration

Scrapers are enabled and tuned through a YAML or JSON configuration file. See
[`config/lead_verifier.example.yaml`](config/lead_verifier.example.yaml) or
[`config/lead_verifier.example.json`](config/lead_verifier.example.json) for a
template. (YAML support requires the optional `pyyaml` dependency; otherwise use
the JSON variant.) Each scraper entry can:

- Enable or disable the scraper via the `enabled` flag.
- Point to the implementing class using the `class` field.
- Provide constructor arguments with the `options` mapping.
- Apply artificial delays via `delay_seconds`.
- Enforce rate limiting with `rate_limit_per_minute`.

### Bundled example scraper

The repository includes a simple `EchoScraper` implementation that echoes back
phone numbers and email addresses already present in the input spreadsheet. Use
it as a template for wiring in real-world scrapers.

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
`headless` and `throttle_seconds` settings to help control execution.

## Repository Layout

- `lead_verifier/` – Python package containing ingestion, scraping, orchestration,
  and UI components.
- `assets/` – Shared example datasets and reusable assets for local testing.
- `fastpeoplesearch.com-scraper-main/` and `truepeoplesearch-master/` – Legacy
  scrapers maintained for reference while the unified toolkit evolves.
- `pyproject.toml` – Dependency and packaging metadata.

## Contributing

Please open an issue or pull request to discuss substantial changes. When
adding new modules, update `pyproject.toml` if additional third-party
dependencies are required.
