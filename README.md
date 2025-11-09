# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails

## Getting Started

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```
2. **Install dependencies** declared in `pyproject.toml`:
   ```bash
   pip install -e .
   ```
3. **Launch the forthcoming integrated tool** (placeholder command):
   ```bash
   python -m lead_verifier
   ```
   The command above will host the orchestrated scrapers and UI once the
   implementation lands. For now it serves as the entry point for development.

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
