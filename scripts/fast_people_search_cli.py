"""CLI helper to exercise the :mod:`lead_verifier` scrapers."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from lead_verifier import LeadInput, LeadVerification  # noqa: E402  (import after path fix)
from lead_verifier.scrapers.fast_people_search import (  # noqa: E402
    FastPeopleSearchConfig,
    FastPeopleSearchScraper,
)

LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FastPeopleSearch scraper for debugging.")
    parser.add_argument("first_name", nargs="?", default="Jane", help="Lead first name")
    parser.add_argument("last_name", nargs="?", default="Doe", help="Lead last name")
    parser.add_argument("--city", help="Lead city")
    parser.add_argument("--state", help="Lead state")
    parser.add_argument("--address", help="Lead address")
    parser.add_argument("--driver-path", help="Path to chromedriver executable")
    parser.add_argument("--headless", dest="headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run Chrome with a visible window",
    )
    parser.set_defaults(headless=True)
    parser.add_argument(
        "--profile-dir",
        help="Chrome profile directory name (requires --user-data-dir)",
    )
    parser.add_argument("--user-data-dir", help="Chrome user data directory")
    parser.add_argument("--rate-limit", type=float, default=0.0, help="Seconds to wait between requests")
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path to save the raw JSON result",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Console log level",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level))


def run_scraper(args: argparse.Namespace) -> None:
    configure_logging(args.log_level)

    metadata = {}
    if args.city:
        metadata["city"] = args.city
    if args.state:
        metadata["state"] = args.state
    if args.address:
        metadata["address"] = args.address

    lead = LeadInput(
        first_name=args.first_name,
        last_name=args.last_name,
        name=" ".join(filter(None, [args.first_name, args.last_name])) or None,
        metadata=metadata,
    )

    config = FastPeopleSearchConfig(
        driver_path=args.driver_path,
        headless=args.headless,
        user_data_dir=args.user_data_dir,
        profile_directory=args.profile_dir,
        rate_limit_seconds=args.rate_limit,
    )

    with FastPeopleSearchScraper(config=config) as scraper:
        result = scraper.verify(lead)

    pretty_print_result(lead, result)

    if args.output_json:
        payload = {
            "lead": asdict(lead),
            "verification": asdict(result),
        }
        args.output_json.write_text(json.dumps(payload, indent=2))
        LOGGER.info("Wrote result JSON to %s", args.output_json)


def pretty_print_result(lead: LeadInput, result: LeadVerification) -> None:
    print("Lead:")
    print(f"  {lead.first_name or ''} {lead.last_name or ''}".strip())
    if lead.city or lead.state:
        print(f"  Location: {lead.city or ''} {lead.state or ''}".strip())
    if lead.address:
        print(f"  Address: {lead.address}")

    contacts = list(result.contacts)
    if not contacts:
        print("No phone numbers found.")
    else:
        print("Phone Numbers:")
        for contact in contacts:
            if contact.type.lower() != "phone":
                continue
            label = contact.metadata.get("label") if contact.metadata else None
            primary = contact.metadata.get("is_primary") if contact.metadata else None
            label_text = f" ({label})" if label else ""
            primary_text = " [primary]" if primary else ""
            print(f"  - {contact.value}{label_text}{primary_text}")

    metadata = (result.raw_data or {}).get("metadata", {})
    if metadata:
        print("Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    errors = (result.raw_data or {}).get("errors", [])
    if errors:
        print("Errors:")
        for err in errors:
            print(f"  - {err}")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    try:
        run_scraper(args)
    except Exception as exc:  # pragma: no cover - CLI convenience
        LOGGER.exception("Scraper failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
