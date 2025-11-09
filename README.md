# RedHatLeadScraper

Automated Lead Verifier for phone numbers and emails.

## Lead verification orchestrator

The `lead_verifier` package bundles an extensible orchestration layer that can
run multiple scrapers either sequentially or concurrently for each input lead.

### Running from the command line

```
python -m lead_verifier.cli path/to/input.xlsx path/to/output.csv --config config/lead_verifier.example.yaml
```

Key options:

* `--mode` – choose `sequential` (default) or `concurrent` execution across scrapers.
* `--max-workers` – cap the number of worker threads used in concurrent mode.
* `--raise-on-error` – propagate scraper exceptions instead of annotating the output with error details.

The CLI accepts CSV or Excel spreadsheets for both input and output. When using
Excel files make sure the `openpyxl` package is installed.

### Configuration

Scrapers are enabled and tuned through a YAML or JSON configuration file. See
[`config/lead_verifier.example.yaml`](config/lead_verifier.example.yaml) or
[`config/lead_verifier.example.json`](config/lead_verifier.example.json) for a
template. (YAML support requires the optional `pyyaml` dependency; otherwise use
the JSON variant.) Each scraper entry can:

* Enable or disable the scraper via the `enabled` flag.
* Point to the implementing class using the `class` field.
* Provide constructor arguments with the `options` mapping.
* Apply artificial delays via `delay_seconds`.
* Enforce rate limiting with `rate_limit_per_minute`.

### Bundled example scraper

The repository includes a simple `EchoScraper` implementation that echoes back
phone numbers and email addresses already present in the input spreadsheet. Use
it as a template for wiring in real-world scrapers.
