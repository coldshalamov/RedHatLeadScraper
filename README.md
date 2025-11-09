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

## Desktop UI

A desktop interface is available to orchestrate the verification workflow without writing code. The application guides you through four steps:

1. **Import leads** – load CSV or Excel spreadsheets and preview the first few rows.
2. **Map columns** – tell the verifier which columns contain names, phone numbers, email addresses, and any optional metadata.
3. **Run verification** – launch the scrapers in the background while keeping the UI responsive. Progress is displayed with live updates.
4. **Inspect & export results** – browse results with filtering, colour-coded source badges, and export buttons for CSV/Excel outputs.

### Launching the app

```bash
python -m lead_verifier.ui.app
```

### Usage tips

- CSV imports work out of the box. Excel imports/exports require the optional `pandas` dependency (`pip install pandas`).
- The UI runs verification tasks in background threads so you can keep filtering or exporting while the job continues.
- Use the filter box to quickly narrow down rows; source badges help identify which scraper supplied each result.
- Results can be cleared at any point without re-importing the file.

## Module entry points

- `lead_verifier.orchestrator` – coordinates ingestion, column normalisation, and scraper execution on worker threads.
- `lead_verifier.ingestion` – helper utilities for exporting verification results.
- `lead_verifier.ui.app` – Tkinter-based GUI that ties everything together.

## Development notes

Run the UI directly in editable mode to develop against live code changes:

```bash
python -m lead_verifier.ui.app
```

Use `Ctrl+C` in the terminal to stop the process if you launched it from a console window.

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
