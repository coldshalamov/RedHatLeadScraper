"""Command line interface for running the verification orchestrator."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import load_configuration
from .factory import build_scrapers
from .io import load_leads, write_results
from .orchestrator import VerificationOrchestrator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate lead contact details from multiple scrapers")
    parser.add_argument("input", help="Path to the input spreadsheet (CSV or XLSX)")
    parser.add_argument("output", help="Path where the aggregated results should be written")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the orchestrator configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "--mode",
        choices=["sequential", "concurrent"],
        default="sequential",
        help="Whether to run scrapers sequentially or concurrently",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Maximum number of workers to use in concurrent mode",
    )
    parser.add_argument(
        "--raise-on-error",
        action="store_true",
        help="Propagate scraper exceptions instead of recording them in the output",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g. DEBUG, INFO, WARNING)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    config = load_configuration(args.config)
    scrapers = build_scrapers(config)
    if not scrapers:
        logging.warning("No scrapers are enabled - nothing to do")
        return 0

    leads = load_leads(args.input)
    orchestrator = VerificationOrchestrator(
        scrapers,
        concurrent=args.mode == "concurrent",
        max_workers=args.max_workers,
        raise_on_error=args.raise_on_error,
    )

    aggregated_results = orchestrator.verify(leads)
    write_results(args.output, aggregated_results)
    logging.info("Processed %s leads with %s scrapers", len(leads), len(scrapers))
    logging.info("Aggregated results written to %s", Path(args.output).resolve())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
