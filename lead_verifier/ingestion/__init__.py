"""Utilities for importing and exporting lead verification data."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..models import LeadVerificationResult


def export_to_csv(path: str | Path, results: Sequence[LeadVerificationResult]) -> Path:
    """Persist verification results to a CSV file."""

    import csv

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        fieldnames = ["lead_name", "lead_phone", "lead_email", "source", "status", "details"]
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
        return destination

    fieldnames = sorted({key for result in results for key in result.as_row().keys()})
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_row())
    return destination


def export_to_excel(path: str | Path, results: Sequence[LeadVerificationResult]) -> Path:
    """Persist verification results to an Excel spreadsheet."""

    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - pandas is optional at runtime
        raise RuntimeError("Excel export requires pandas") from exc

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    frame = pd.DataFrame([result.as_row() for result in results])
    frame.to_excel(destination, index=False)
    return destination


__all__ = ["export_to_csv", "export_to_excel"]
