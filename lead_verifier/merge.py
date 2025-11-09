"""Utility helpers for merging verification results from multiple scrapers."""
from __future__ import annotations

from typing import Iterable, List

from .models import AggregatedContact, AggregatedLeadResult, ContactDetail, LeadInput, LeadVerification


def _normalise_contact(detail: ContactDetail) -> str:
    value = detail.value.strip()
    if detail.type.lower() == "email":
        return value.lower()
    if detail.type.lower() == "phone":
        digits = [c for c in value if c.isdigit()]
        return "".join(digits)
    return value.lower()


def merge_lead_results(
    lead: LeadInput, results: Iterable[LeadVerification]
) -> AggregatedLeadResult:
    """Merge contact details from multiple scrapers, deduplicating by value."""

    aggregated: dict[str, AggregatedContact] = {}
    ordered_keys: List[str] = []

    for result in results:
        if result is None:
            continue
        for contact in result.contacts:
            key = f"{contact.type.lower()}::{_normalise_contact(contact)}"
            if not key:
                continue
            if key not in aggregated:
                aggregated[key] = AggregatedContact(
                    type=contact.type,
                    value=contact.value,
                    sources=[result.source],
                )
                ordered_keys.append(key)
            else:
                merged = aggregated[key]
                if result.source not in merged.sources:
                    merged.sources.append(result.source)

    ordered_contacts = [aggregated[key] for key in ordered_keys]
    return AggregatedLeadResult(
        lead=lead,
        contacts=ordered_contacts,
        raw_results=list(results),
    )
