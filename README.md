# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails.

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
