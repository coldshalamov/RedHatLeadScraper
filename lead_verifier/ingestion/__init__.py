"""Utilities for importing, exporting, and normalising lead verification data."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Union

from ..models import AggregatedLeadResult, LeadVerification

RowLike = Dict[str, Any]
ResultLike = Union[AggregatedLeadResult, LeadVerification, Any]


def _result_to_row(result: ResultLike) -> RowLike:
    """Best-effort conversion of various result objects into a flat row."""
    # If the object provides its own row representation, use it.
    as_row = getattr(result, "as_row", None)
    if callable(as_row):
        return dict(as_row())

    # AggregatedLeadResult → collapse contacts and sources
    if isinstance(result, AggregatedLeadResult):
        lead = result.lead
        name = f"{(lead.first_name or '').strip()} {(lead.last_name or '').strip()}".strip()
        contacts: List[str] = [c.value for c in result.contacts]
        sources: List[str] = sorted({s for c in result.contacts for s in c.sources})
        return {
            "lead_name": name,
            "lead_city": (lead.city or "").strip() if hasattr(lead, "city") else "",
            "lead_state": (lead.state or "").strip() if hasattr(lead, "state") else "",
            "lead_phone": (lead.phone or "").strip() if hasattr(lead, "phone") else "",
            "lead_email": (lead.email or "").strip() if hasattr(lead, "email") else "",
            "contacts": ", ".join(contacts),
            "sources": ", ".join(sources),
        }

    # LeadVerification → flatten minimal fields
    if isinstance(result, LeadVerification):
        contacts = getattr(result, "contacts", []) or []
        values = [getattr(c, "value", "") for c in contacts]
        return {
            "source": getattr(result, "source", ""),
            "contacts": ", ".join(v for v in values if v),
        }

    # Fallback: attempt to serialize dataclass-like objects
    try:
        from dataclasses import asdict  # type: ignore
        return asdict(result)  # type: ignore[arg-type]
    except Exception:
        pass

    # Last resort: stringified object
    return {"value": str(result)}


def export_to_csv(path: str | Path, results: Sequence[ResultLike]) -> Path:
    """Persist verification results to a CSV file."""
    import csv

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    rows: List[RowLike] = [_result_to_row(r) for r in (results or [])]

    if not rows:
        # Write a minimal header for empty outputs
        fieldnames = ["lead_name", "lead_phone", "lead_email", "source", "status", "details"]
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
        return destination

    fieldnames = sorted({k for row in rows for k in row.keys()})
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return destination


def export_to_excel(path: str | Path, results: Sequence[ResultLike]) -> Path:
    """Persist verification results to an Excel spreadsheet."""
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - pandas is optional at runtime
        raise RuntimeError("Excel export requires pandas") from exc

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    rows: List[RowLike] = [_result_to_row(r) for r in (results or [])]
    frame = pd.DataFrame(rows)
    frame.to_excel(destination, index=False)
    return destination


__all__ = ["export_to_csv", "export_to_excel"]
